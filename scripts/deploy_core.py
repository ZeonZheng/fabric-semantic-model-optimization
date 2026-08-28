"""FUAM-style deployment engine for the SMO Analytics solution.

This module is executed inside Microsoft Fabric by Deploy_SMO_Analytics.ipynb.
It intentionally uses the signed-in notebook user's token and never persists
credentials in the repository or the deployed workspace.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sysconfig
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import sempy.fabric as fabric
import notebookutils
import yaml


FABRIC_API = "https://api.fabric.microsoft.com"
WORKSPACE_PLACEHOLDER = "00000000-0000-0000-0000-000000000000"
SCANNER_ENVIRONMENT_PACKAGES = {"semantic-link-labs"}


def run_fab(command: str, *, timeout: int = 600, allow_failure: bool = False) -> str:
    """Run one ms-fabric-cli command and return stdout."""
    fab_executable = shutil.which("fab")
    if not fab_executable:
        environment_fab = Path(sysconfig.get_path("scripts")) / "fab"
        if environment_fab.is_file():
            fab_executable = str(environment_fab)
    if not fab_executable:
        raise FileNotFoundError(
            "ms-fabric-cli is installed but the fab entry point could not be located."
        )

    result = subprocess.run(
        [fab_executable, "-c", command],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0 and not allow_failure:
        raise RuntimeError(
            f"fab command failed ({result.returncode}): {command}\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def _api_json(command: str) -> dict:
    raw = run_fab(command)
    parsed = json.loads(raw)
    return parsed.get("text", parsed)


def _item_type(qualified_name: str) -> str:
    return qualified_name.rsplit(".", 1)[-1]


def _item_display_name(qualified_name: str) -> str:
    return qualified_name.rsplit(".", 1)[0]


def _replace_ids(root: Path, mappings: list[dict[str, str]]) -> None:
    text_suffixes = {".json", ".pbir", ".tmdl", ".platform", ".py", ".sql"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".ipynb":
            notebook = json.loads(path.read_text(encoding="utf-8"))
            dependencies = notebook.get("metadata", {}).get("dependencies", {})
            dependency_text = json.dumps(dependencies)
            for mapping in mappings:
                dependency_text = dependency_text.replace(
                    mapping["source_id"], mapping["target_id"]
                )
            notebook.setdefault("metadata", {})["dependencies"] = json.loads(
                dependency_text
            )
            path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
        elif path.suffix in text_suffixes or path.name == ".platform":
            content = path.read_text(encoding="utf-8")
            for mapping in mappings:
                content = content.replace(mapping["source_id"], mapping["target_id"])
            path.write_text(content, encoding="utf-8")


def _public_definition(root: Path, item_type: str) -> dict:
    """Build a complete Fabric public definition without Git-only metadata."""
    formats = {"SemanticModel": "TMDL", "Report": "PBIR"}
    if item_type not in formats:
        raise ValueError(f"Public-definition update is unsupported for {item_type}.")

    parts = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == ".platform":
            continue
        parts.append(
            {
                "path": path.relative_to(root).as_posix(),
                "payload": base64.b64encode(path.read_bytes()).decode("ascii"),
                "payloadType": "InlineBase64",
            }
        )
    if not parts:
        raise ValueError(f"No public definition parts found under {root}.")
    return {"format": formats[item_type], "parts": parts}


def _update_public_definition(
    workspace_id: str,
    item_id: str,
    item_type: str,
    root: Path,
) -> None:
    """Update an existing Power BI item through its definition REST API."""
    collections = {"SemanticModel": "semanticModels", "Report": "reports"}
    collection = collections[item_type]
    _fabric_request_json(
        "POST",
        f"workspaces/{workspace_id}/{collection}/{item_id}/updateDefinition",
        body={"definition": _public_definition(root, item_type)},
        timeout_seconds=1200,
    )
    print(f"Updated {item_type} definition through Fabric REST API.")


def _make_initialization_notebook(root: Path, output_schema: str) -> None:
    for path in root.rglob("*.ipynb"):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        contract_cell = next(
            (
                cell
                for cell in notebook.get("cells", [])
                if "Delta table contracts and idempotent writers"
                in "".join(cell.get("source", []))
            ),
            None,
        )
        if contract_cell is None:
            continue
        curated_contract_cell = next(
            (
                cell
                for cell in notebook.get("cells", [])
                if "V2 AI-friendly current-state consumption contract"
                in "".join(cell.get("source", []))
            ),
            None,
        )
        if curated_contract_cell is None:
            raise ValueError("V2 curated consumption contract cell not found in scanner notebook.")
        notebook["cells"] = [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"microsoft": {"language": "python"}},
                "outputs": [],
                "source": [
                    "import json\n",
                    "import re\n",
                    "from pyspark.sql import types as T\n",
                    f"output_schema = {json.dumps(output_schema)}\n",
                ],
            },
            contract_cell,
            curated_contract_cell,
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"microsoft": {"language": "python"}},
                "outputs": [],
                "source": [
                    "ensure_tables()\n",
                    "ensure_curated_tables()\n",
                    "print(json.dumps({\"status\": \"INITIALIZED\", "
                    "\"raw_table_count\": len(TABLES), "
                    "\"curated_table_count\": len(CURATED_TABLES)}, "
                    "indent=2))\n",
                ],
            },
        ]
        path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
        return
    raise ValueError("Delta table contract cell not found in scanner notebook.")


def _wait_for_sql_endpoint(
    workspace_name: str, lakehouse_name: str, *, timeout_seconds: int = 600
) -> tuple[str, str]:
    """Wait until Fabric exposes both the endpoint ID and TDS connection string."""
    lakehouse_qualified = (
        lakehouse_name
        if lakehouse_name.endswith(".Lakehouse")
        else f"{lakehouse_name}.Lakehouse"
    )
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        endpoint_id = run_fab(
            f"get /{workspace_name}.Workspace/{lakehouse_qualified} "
            "-q properties.sqlEndpointProperties.id",
            allow_failure=True,
        ).strip()
        connection = run_fab(
            f"get /{workspace_name}.Workspace/{lakehouse_qualified} "
            "-q properties.sqlEndpointProperties.connectionString",
            allow_failure=True,
        ).strip()
        endpoint_ready = bool(re.fullmatch(r"[0-9a-fA-F-]{36}", endpoint_id))
        connection_ready = bool(
            connection
            and ".datawarehouse.fabric.microsoft.com" in connection.lower()
            and "invalidpath" not in connection.lower()
            and not connection.lower().startswith("x get:")
        )
        if endpoint_ready and connection_ready:
            return endpoint_id, connection
        time.sleep(10)
    raise TimeoutError(
        "Lakehouse SQL analytics endpoint did not expose a valid ID and "
        f"connection string within {timeout_seconds} seconds."
    )


def _response_json(status_code: int, content: bytes) -> dict:
    if not content:
        return {}
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Fabric API returned non-JSON content ({status_code}): "
            f"{content[:2000]!r}"
        ) from exc
    return payload if isinstance(payload, dict) else {"value": payload}


def _http_request(
    method: str,
    url: str,
    token: str,
    *,
    body: dict | None = None,
    timeout_seconds: int = 120,
) -> tuple[int, object, bytes]:
    encoded = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        url,
        data=encoded,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.getcode(), response.headers, response.read()
    except HTTPError as exc:
        return exc.code, exc.headers, exc.read()


def _fabric_request_json(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    timeout_seconds: int = 1200,
) -> dict:
    """Call a Fabric API and fully resolve its standard LRO contract."""
    token = os.environ.get("FAB_TOKEN")
    if not token:
        raise RuntimeError("FAB_TOKEN is unavailable for the Fabric API request.")
    url = urljoin(f"{FABRIC_API}/v1/", path.lstrip("/"))
    status_code, response_headers, content = _http_request(
        method,
        url,
        token,
        body=body,
        timeout_seconds=min(timeout_seconds, 120),
    )
    if status_code not in {200, 201, 202}:
        raise RuntimeError(
            f"Fabric API {method} {path} failed ({status_code}): "
            f"{content[:4000]!r}"
        )
    if status_code != 202:
        return _response_json(status_code, content)

    operation_id = response_headers.get("x-ms-operation-id")
    poll_url = response_headers.get("Location")
    if not poll_url and operation_id:
        poll_url = f"{FABRIC_API}/v1/operations/{operation_id}"
    if not poll_url:
        raise RuntimeError("Fabric LRO response omitted Location and x-ms-operation-id.")
    poll_url = urljoin(f"{FABRIC_API}/v1/", poll_url)

    deadline = time.monotonic() + timeout_seconds
    retry_after = int(response_headers.get("Retry-After", "5"))
    while time.monotonic() < deadline:
        time.sleep(max(1, min(retry_after, 30)))
        status_code, response_headers, content = _http_request(
            "GET", poll_url, token, timeout_seconds=120
        )
        if status_code not in {200, 202}:
            raise RuntimeError(
                f"Fabric LRO polling failed ({status_code}): {content[:4000]!r}"
            )
        retry_after = int(response_headers.get("Retry-After", "5"))
        poll_url = urljoin(
            f"{FABRIC_API}/v1/", response_headers.get("Location", poll_url)
        )
        if status_code == 202:
            continue
        operation = _response_json(status_code, content)
        status = str(operation.get("status", "")).lower()
        if status in {"failed", "cancelled"}:
            raise RuntimeError(
                "Fabric LRO failed: "
                + json.dumps(operation, default=str, ensure_ascii=False)
            )
        if status and status != "succeeded":
            continue

        if operation_id:
            result_status, _, result_content = _http_request(
                "GET",
                f"{FABRIC_API}/v1/operations/{operation_id}/result",
                token,
                timeout_seconds=120,
            )
            if result_status == 200:
                return _response_json(result_status, result_content)
            if result_status == 400:
                result_error = _response_json(result_status, result_content)
                if result_error.get("errorCode") == "OperationHasNoResult":
                    return operation
            if result_status not in {204, 404}:
                raise RuntimeError(
                    "Fabric LRO result retrieval failed "
                    f"({result_status}): {result_content[:4000]!r}"
                )
        return operation
    raise TimeoutError(
        f"Fabric API operation did not complete within {timeout_seconds} seconds."
    )


def _environment_publish_details(workspace_id: str, environment_id: str) -> dict:
    payload = _api_json(
        "api -A fabric -X get "
        f"workspaces/{workspace_id}/environments/{environment_id}"
    )
    return payload.get("properties", {}).get("publishDetails", {})


def _wait_for_environment_publish(
    workspace_id: str, environment_id: str, *, timeout_seconds: int = 1800
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_state = None
    while time.monotonic() < deadline:
        details = _environment_publish_details(workspace_id, environment_id)
        state = details.get("state")
        if state != last_state:
            print(f"Scanner environment publish status: {state or 'UNKNOWN'}")
            last_state = state
        if state == "Success":
            return
        if state in {"Failed", "Cancelled"}:
            raise RuntimeError(
                "Scanner environment publish failed: "
                + json.dumps(details, default=str, ensure_ascii=False)
            )
        time.sleep(15)
    raise TimeoutError(
        f"Scanner environment publish did not complete within {timeout_seconds} seconds."
    )


def _validate_environment_libraries(
    workspace_id: str, environment_id: str
) -> None:
    payload = _api_json(
        "api -A fabric -X get "
        f"workspaces/{workspace_id}/environments/{environment_id}/libraries?beta=False"
    )
    published = {
        re.sub(r"[-_.]+", "-", str(library.get("name", "")).lower()): str(
            library.get("version", "")
        )
        for library in payload.get("libraries", [])
        if str(library.get("libraryType", "")).lower() == "external"
    }
    missing = sorted(SCANNER_ENVIRONMENT_PACKAGES - set(published))
    if missing:
        raise RuntimeError(
            "Scanner environment libraries are not published: "
            + json.dumps({"missing": missing, "published": published}, ensure_ascii=False)
        )
    versions = {name: published[name] for name in sorted(SCANNER_ENVIRONMENT_PACKAGES)}
    print(
        "Scanner environment libraries published; runtime capability validation "
        "will determine compatibility: "
        + json.dumps(versions, ensure_ascii=False)
    )


def _publish_and_validate_environment(
    workspace_id: str, environment_id: str
) -> None:
    """Publish scanner extensions before any notebook can reference them."""
    details = _environment_publish_details(workspace_id, environment_id)
    if details.get("state") in {"Running", "Waiting", "Cancelling"}:
        _wait_for_environment_publish(workspace_id, environment_id)

    run_fab(
        "api -A fabric -X post "
        f"workspaces/{workspace_id}/environments/{environment_id}/staging/"
        "publish?beta=False -i {}",
        timeout=120,
        allow_failure=True,
    )
    time.sleep(5)
    _wait_for_environment_publish(workspace_id, environment_id)
    _validate_environment_libraries(workspace_id, environment_id)


def _update_and_validate_direct_lake_sql_connection(
    item_root: Path, endpoint_id: str, connection_string: str
) -> None:
    """Bind Direct Lake to this Lakehouse's SQL analytics endpoint by GUID."""
    expressions = item_root / "definition" / "expressions.tmdl"
    content = expressions.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'Sql\.Database\("[^"]+",\s*"[^"]+"\)',
        f'Sql.Database("{connection_string}", "{endpoint_id}")',
        content,
        count=1,
    )
    if count != 1:
        raise ValueError(
            "Unable to locate the Direct Lake Sql.Database connection expression."
        )
    expressions.write_text(updated, encoding="utf-8")
    invalid_tokens = (
        "placeholder.datawarehouse.fabric.microsoft.com",
        "77777777-7777-7777-7777-777777777777",
        "AzureStorage.DataLake(",
        '"server":"none"',
        '"database":"none"',
    )
    if any(token.lower() in updated.lower() for token in invalid_tokens):
        raise ValueError(
            "Direct Lake SQL endpoint expression still contains a placeholder "
            "or invalid source."
        )
    expected = f'Sql.Database("{connection_string}", "{endpoint_id}")'
    if expected not in updated:
        raise ValueError("Direct Lake SQL endpoint expression was not bound as expected.")


def _semantic_model_source_tables(item_root: Path) -> dict[str, list[str]]:
    """Read the schema/entity pairs used by Direct Lake partitions."""
    grouped: dict[str, list[str]] = {}
    for table_path in sorted((item_root / "definition" / "tables").glob("*.tmdl")):
        content = table_path.read_text(encoding="utf-8")
        entity = re.search(r"^\s*entityName:\s*(.+?)\s*$", content, re.MULTILINE)
        schema = re.search(r"^\s*schemaName:\s*(.+?)\s*$", content, re.MULTILINE)
        if entity and schema:
            grouped.setdefault(schema.group(1), []).append(entity.group(1))
    if not grouped:
        raise ValueError("No schema/entity Direct Lake partitions were found in TMDL.")
    return grouped


def _refresh_history(workspace_id: str, semantic_model_id: str) -> list[dict]:
    payload = _api_json(
        "api -A powerbi -X get "
        f"groups/{workspace_id}/datasets/{semantic_model_id}/refreshes?$top=10"
    )
    return payload.get("value", [])


def _refresh_key(refresh: dict) -> str:
    return str(
        refresh.get("requestId")
        or refresh.get("id")
        or f"{refresh.get('startTime')}|{refresh.get('refreshType')}"
    )


def _validate_semantic_model_datasource(
    workspace_id: str,
    semantic_model_id: str,
    endpoint_id: str,
    connection_string: str,
) -> None:
    payload = _api_json(
        "api -A powerbi -X get "
        f"groups/{workspace_id}/datasets/{semantic_model_id}/datasources"
    )
    normalized = json.dumps(payload, separators=(",", ":")).lower()
    if '"server":"none"' in normalized or '"database":"none"' in normalized:
        raise RuntimeError(
            "Semantic model was published with an invalid server/database datasource."
        )
    if endpoint_id.lower() not in normalized or connection_string.lower() not in normalized:
        raise RuntimeError(
            "Semantic model datasource does not match the deployed Lakehouse SQL "
            f"analytics endpoint {endpoint_id}."
        )


def _refresh_and_validate_semantic_model(
    workspace_id: str,
    semantic_model_id: str,
    endpoint_id: str,
    connection_string: str,
) -> None:
    """Reframe Direct Lake and fail deployment when the model cannot read its source."""
    _validate_semantic_model_datasource(
        workspace_id, semantic_model_id, endpoint_id, connection_string
    )
    previous_refreshes = {
        _refresh_key(refresh)
        for refresh in _refresh_history(workspace_id, semantic_model_id)
    }
    run_fab(
        "api -A powerbi -X post "
        f"groups/{workspace_id}/datasets/{semantic_model_id}/refreshes "
        "-i '{\"retryCount\":3}'",
        timeout=120,
    )

    deadline = time.monotonic() + 900
    last_status = None
    while time.monotonic() < deadline:
        current = next(
            (
                refresh
                for refresh in _refresh_history(workspace_id, semantic_model_id)
                if _refresh_key(refresh) not in previous_refreshes
            ),
            None,
        )
        if current is None:
            time.sleep(10)
            continue
        status = current.get("status")
        if status != last_status:
            print(f"Semantic model refresh status: {status}")
            last_status = status
        if status == "Completed":
            _validate_semantic_model_datasource(
                workspace_id, semantic_model_id, endpoint_id, connection_string
            )
            return
        if status in {"Failed", "Cancelled", "Disabled"}:
            raise RuntimeError(
                "Semantic model refresh failed: "
                + json.dumps(current, default=str, ensure_ascii=False)
            )
        time.sleep(10)
    raise TimeoutError("Semantic model refresh did not complete within 900 seconds.")


def _workspace_context() -> tuple[str, str]:
    workspace_id = fabric.get_notebook_workspace_id()
    workspace = _api_json(f"api -X get workspaces/{workspace_id}")
    return workspace_id, workspace["displayName"]


def _existing_items(workspace_id: str) -> dict[tuple[str, str], str]:
    payload = _api_json(f"api -A fabric -X get workspaces/{workspace_id}/items")
    return {
        (item["displayName"], item["type"]): item["id"]
        for item in payload.get("value", [])
    }


def _resolve_item_id(
    workspace_name: str, qualified_name: str, folder_name: str | None = None
) -> str:
    parent = f"/{workspace_name}.Workspace"
    if folder_name:
        parent += f"/{folder_name}.Folder"
    item_id = run_fab(
        f"get {parent}/{qualified_name} -q id",
        allow_failure=True,
    )
    if not item_id:
        raise RuntimeError(f"Unable to resolve deployed item: {qualified_name}")
    return item_id


def _sql_endpoint_table_readiness(row: dict) -> str | None:
    """Classify a table sync result without rejecting an already-synced table."""
    status = str(row.get("status", "")).strip().lower()
    if status == "success":
        return "REFRESHED"
    if status == "notrun" and row.get("lastSuccessfulSyncDateTime"):
        return "ALREADY_CURRENT"
    return None


def _refresh_and_validate_sql_endpoint(
    workspace_id: str,
    endpoint_id: str,
    source_tables: dict[str, list[str]],
) -> None:
    """Synchronize and verify every table before importing the semantic model."""
    table_count = sum(len(names) for names in source_tables.values())
    if table_count > 25:
        raise ValueError(
            "SQL endpoint metadata refresh supports at most 25 selective tables; "
            f"the semantic model declares {table_count}."
        )
    body = {
        "tables": [
            {"schema": schema, "tableNames": names}
            for schema, names in sorted(source_tables.items())
        ],
        "timeout": {"value": 15, "timeUnit": "Minutes"},
    }
    payload = _fabric_request_json(
        "POST",
        f"workspaces/{workspace_id}/sqlEndpoints/{endpoint_id}/refreshMetadata",
        body=body,
        timeout_seconds=1200,
    )
    statuses = payload.get("value", [])
    if not statuses:
        raise RuntimeError(
            "SQL endpoint metadata refresh completed without table-level results; "
            "deployment cannot prove that the semantic-model source is ready."
        )

    actual = {
        str(row.get("tableName", "")).lower(): row
        for row in statuses
    }
    expected = {
        f"{schema}.{table}".lower()
        for schema, names in source_tables.items()
        for table in names
    }
    missing = sorted(expected - set(actual))
    readiness = {
        name: _sql_endpoint_table_readiness(actual[name])
        for name in sorted(expected & set(actual))
    }
    failed = {
        name: actual[name]
        for name, state in readiness.items()
        if state is None
    }
    if missing or failed:
        raise RuntimeError(
            "Lakehouse tables are not ready in the SQL analytics endpoint: "
            + json.dumps(
                {"missing": missing, "failed": failed},
                default=str,
                ensure_ascii=False,
            )
        )
    refreshed_count = sum(state == "REFRESHED" for state in readiness.values())
    current_count = sum(state == "ALREADY_CURRENT" for state in readiness.values())
    print(
        f"SQL endpoint metadata validated: {len(expected)}/{len(expected)} "
        f"semantic-model source tables ready ({refreshed_count} refreshed, "
        f"{current_count} already current)."
    )


def _initialize_tables(
    workspace_id: str,
    workspace_name: str,
    notebook_name: str,
    notebook_id: str,
    folder_name: str | None = None,
) -> None:
    parent = f"/{workspace_name}.Workspace"
    if folder_name:
        parent += f"/{folder_name}.Folder"
    start_output = run_fab(
        f"job start {parent}/{notebook_name}"
    )
    instance_match = re.search(
        r"Job instance '([0-9a-fA-F-]{36})' created", start_output
    )
    if not instance_match:
        raise RuntimeError(
            f"Unable to resolve scanner initialization job ID:\n{start_output}"
        )

    instance_id = instance_match.group(1)
    print(f"Scanner initialization job: {instance_id}")
    deadline = time.monotonic() + 3600
    last_status = None
    while time.monotonic() < deadline:
        try:
            job = _api_json(
                "api -A fabric -X get "
                f"workspaces/{workspace_id}/items/{notebook_id}/jobs/instances/{instance_id}"
            )
        except RuntimeError as exc:
            print(f"Job status check retry: {exc}")
            time.sleep(20)
            continue

        status = job.get("status")
        if status != last_status:
            print(f"Scanner initialization status: {status}")
            last_status = status
        if status in {"Completed", "Deduped"}:
            return
        if status in {"Failed", "Cancelled"}:
            raise RuntimeError(
                "Scanner initialization failed: "
                + json.dumps(job, default=str, ensure_ascii=False)
            )
        time.sleep(20)

    raise TimeoutError(
        f"Scanner initialization job {instance_id} did not finish within 3600 seconds."
    )


def _move_items_to_folders(
    workspace_id: str, workspace_name: str, folders: list[dict]
) -> None:
    items = _existing_items(workspace_id)
    for folder in folders:
        folder_name = folder["name"]
        exists = run_fab(
            f"exists /{workspace_name}.Workspace/{folder_name}.Folder",
            allow_failure=True,
        )
        if "true" not in exists.lower():
            run_fab(f"create /{workspace_name}.Workspace/{folder_name}.Folder")
        folder_id = _resolve_item_id(workspace_name, f"{folder_name}.Folder")
        item_ids = []
        for qualified_name in folder.get("items", []):
            key = (_item_display_name(qualified_name), _item_type(qualified_name))
            if key in items:
                item_ids.append(items[key])
        if not item_ids:
            continue
        body = json.dumps({"targetFolderId": folder_id, "items": item_ids})
        run_fab(
            f"api -A fabric -X post workspaces/{workspace_id}/items/bulkmove -i '{body}'"
        )


def deploy_solution(repo_root: str | Path) -> dict:
    """Create or update every solution item in the current Fabric workspace."""
    repo_root = Path(repo_root).resolve()
    config = yaml.safe_load(
        (repo_root / "config" / "deployment_config.yaml").read_text(encoding="utf-8")
    )
    order = json.loads(
        (repo_root / "config" / "deployment_order.json").read_text(encoding="utf-8")
    )

    token = notebookutils.credentials.getToken("pbi")  # noqa: F821 - Fabric runtime
    os.environ["FAB_TOKEN"] = token
    os.environ["FAB_TOKEN_ONELAKE"] = token

    workspace_id, workspace_name = _workspace_context()
    print(f"Target workspace: {workspace_name} ({workspace_id})")

    folder_by_item = {
        qualified_name: folder["name"]
        for folder in config.get("folders", [])
        for qualified_name in folder.get("items", [])
    }
    for folder_name in {folder["name"] for folder in config.get("folders", [])}:
        exists = run_fab(
            f"exists /{workspace_name}.Workspace/{folder_name}.Folder",
            allow_failure=True,
        )
        if "true" not in exists.lower():
            run_fab(f"create /{workspace_name}.Workspace/{folder_name}.Folder")

    mappings = [{"source_id": WORKSPACE_PLACEHOLDER, "target_id": workspace_id}]
    existing = _existing_items(workspace_id)
    for item in order:
        key = (_item_display_name(item["name"]), _item_type(item["name"]))
        if key in existing:
            mappings.append(
                {"source_id": item["source_id"], "target_id": existing[key]}
            )

    lakehouse_qualified = config["items"]["lakehouse"]
    lakehouse_name = _item_display_name(lakehouse_qualified)
    scanner_qualified = config["items"]["scanner_notebook"]
    semantic_model_qualified = config["items"]["semantic_model"]
    semantic_model_source_tables = _semantic_model_source_tables(
        repo_root / "src" / semantic_model_qualified
    )
    initialized = False
    deployed = []
    endpoint_id = None
    endpoint_connection = None
    lakehouse_id = None

    for item in order:
        qualified_name = item["name"]
        item_type = _item_type(qualified_name)
        item_key = (_item_display_name(qualified_name), item_type)
        print(f"Deploying {qualified_name} ...")

        if item_type == "Lakehouse":
            enable_schemas = str(config["lakehouse"]["enable_schemas"])
            run_fab(
                f"create /{workspace_name}.Workspace/{qualified_name} "
                f"-P enableSchemas={enable_schemas}",
                allow_failure=True,
            )
            target_id = _resolve_item_id(workspace_name, qualified_name)
            lakehouse_id = target_id
            endpoint_id, endpoint_connection = _wait_for_sql_endpoint(
                workspace_name, qualified_name
            )
            if not any(m["source_id"] == item["source_id"] for m in mappings):
                mappings.append(
                    {"source_id": item["source_id"], "target_id": target_id}
                )
            deployed.append({"name": qualified_name, "id": target_id})
            continue

        source_path = repo_root / "src" / qualified_name
        if not source_path.exists():
            raise FileNotFoundError(f"Missing Fabric item source: {source_path}")

        with tempfile.TemporaryDirectory() as temporary:
            target_path = Path(temporary) / qualified_name
            shutil.copytree(source_path, target_path)
            _replace_ids(target_path, mappings)
            if qualified_name == scanner_qualified:
                _make_initialization_notebook(
                    target_path, str(config["lakehouse"]["output_schema"])
                )
            if item_type == "SemanticModel":
                if not endpoint_id or not endpoint_connection:
                    raise RuntimeError("Lakehouse SQL analytics endpoint is unavailable.")
                _update_and_validate_direct_lake_sql_connection(
                    target_path, endpoint_id, endpoint_connection
                )
            format_argument = " --format .ipynb" if item_type == "Notebook" else ""
            folder_name = folder_by_item.get(qualified_name)
            destination_parent = f"/{workspace_name}.Workspace"
            if folder_name:
                destination_parent += f"/{folder_name}.Folder"
            if item_key in existing and item_type in {"SemanticModel", "Report"}:
                target_id = existing[item_key]
                _update_public_definition(
                    workspace_id,
                    target_id,
                    item_type,
                    target_path,
                )
            else:
                run_fab(
                    f"import {destination_parent}/{qualified_name} "
                    f"-i '{target_path}' -f{format_argument}",
                    timeout=1200,
                )

        if item_key not in existing or item_type not in {"SemanticModel", "Report"}:
            target_id = _resolve_item_id(
                workspace_name, qualified_name, folder_by_item.get(qualified_name)
            )
        if not any(m["source_id"] == item["source_id"] for m in mappings):
            mappings.append({"source_id": item["source_id"], "target_id": target_id})
        deployed.append({"name": qualified_name, "id": target_id})

        if item_type == "Environment":
            _publish_and_validate_environment(workspace_id, target_id)

        if qualified_name == scanner_qualified and not initialized:
            _initialize_tables(
                workspace_id,
                workspace_name,
                scanner_qualified,
                target_id,
                folder_by_item.get(scanner_qualified),
            )
            if not endpoint_id:
                raise RuntimeError("Lakehouse SQL analytics endpoint ID is unavailable.")
            _refresh_and_validate_sql_endpoint(
                workspace_id,
                endpoint_id,
                semantic_model_source_tables,
            )
            with tempfile.TemporaryDirectory() as temporary:
                restore_path = Path(temporary) / qualified_name
                shutil.copytree(source_path, restore_path)
                _replace_ids(restore_path, mappings)
                run_fab(
                    f"import {destination_parent}/{qualified_name} "
                    f"-i '{restore_path}' -f --format .ipynb",
                    timeout=1200,
                )
            initialized = True

    _move_items_to_folders(workspace_id, workspace_name, config.get("folders", []))

    semantic_model_id = _resolve_item_id(
        workspace_name,
        config["items"]["semantic_model"],
        folder_by_item.get(config["items"]["semantic_model"]),
    )
    if not endpoint_id or not endpoint_connection:
        raise RuntimeError("Lakehouse SQL analytics endpoint binding is unavailable.")
    _refresh_and_validate_semantic_model(
        workspace_id,
        semantic_model_id,
        endpoint_id,
        endpoint_connection,
    )

    result = {
        "status": "SUCCEEDED",
        "solution_version": config["solution"]["version"],
        "workspace_id": workspace_id,
        "workspace_name": workspace_name,
        "semantic_model_source": {
            "mode": "DirectLakeOnSqlEndpoint",
            "lakehouse_id": lakehouse_id,
            "sql_endpoint_id": endpoint_id,
        },
        "items": deployed,
    }
    print(json.dumps(result, indent=2))
    return result
