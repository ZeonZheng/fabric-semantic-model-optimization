"""FUAM-style deployment engine for the SMO Analytics solution.

This module is executed inside Microsoft Fabric by Deploy_SMO_Analytics.ipynb.
It intentionally uses the signed-in notebook user's token and never persists
credentials in the repository or the deployed workspace.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sysconfig
import tempfile
import time
from pathlib import Path

import sempy.fabric as fabric
import notebookutils
import yaml


FABRIC_API = "https://api.fabric.microsoft.com"
WORKSPACE_PLACEHOLDER = "00000000-0000-0000-0000-000000000000"


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


def _get_sql_endpoint_id(workspace_name: str, lakehouse_name: str) -> str | None:
    """Return the Lakehouse SQL endpoint ID when Fabric has provisioned it."""
    lakehouse_qualified = (
        lakehouse_name
        if lakehouse_name.endswith(".Lakehouse")
        else f"{lakehouse_name}.Lakehouse"
    )
    endpoint_id = run_fab(
        f"get /{workspace_name}.Workspace/{lakehouse_qualified} "
        "-q properties.sqlEndpointProperties.id",
        allow_failure=True,
    ).strip()
    return endpoint_id if re.fullmatch(r"[0-9a-fA-F-]{36}", endpoint_id) else None


def _validate_direct_lake_connection(
    item_root: Path, workspace_id: str, lakehouse_id: str
) -> None:
    """Fail before import unless TMDL targets the deployed Lakehouse in OneLake."""
    expressions = item_root / "definition" / "expressions.tmdl"
    content = expressions.read_text(encoding="utf-8")
    expected_path = (
        "https://onelake.dfs.fabric.microsoft.com/"
        f"{workspace_id}/{lakehouse_id}"
    )
    if "AzureStorage.DataLake" not in content or expected_path not in content:
        raise ValueError(
            "Direct Lake on OneLake expression does not target the deployed "
            f"Lakehouse: {expected_path}"
        )
    invalid_tokens = (
        WORKSPACE_PLACEHOLDER,
        "11111111-1111-1111-1111-111111111111",
        "Sql.Database(",
        '"server":"none"',
        '"database":"none"',
    )
    if any(token.lower() in content.lower() for token in invalid_tokens):
        raise ValueError("Direct Lake expression still contains a placeholder or invalid SQL source.")


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
    workspace_id: str, semantic_model_id: str
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


def _refresh_and_validate_semantic_model(
    workspace_id: str, semantic_model_id: str
) -> None:
    """Reframe Direct Lake and fail deployment when the model cannot read its source."""
    _validate_semantic_model_datasource(workspace_id, semantic_model_id)
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
            _validate_semantic_model_datasource(workspace_id, semantic_model_id)
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


def _refresh_sql_endpoint(workspace_id: str, endpoint_id: str) -> None:
    run_fab(
        "api -A fabric -X post "
        f"workspaces/{workspace_id}/sqlEndpoints/{endpoint_id}/refreshMetadata?preview=True "
        "-i {}",
        timeout=900,
        allow_failure=True,
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
    initialized = False
    deployed = []
    endpoint_id = None
    lakehouse_id = None

    for item in order:
        qualified_name = item["name"]
        item_type = _item_type(qualified_name)
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
                if not lakehouse_id:
                    raise RuntimeError("Lakehouse item ID is unavailable.")
                _validate_direct_lake_connection(
                    target_path, workspace_id, lakehouse_id
                )
            format_argument = " --format .ipynb" if item_type == "Notebook" else ""
            folder_name = folder_by_item.get(qualified_name)
            destination_parent = f"/{workspace_name}.Workspace"
            if folder_name:
                destination_parent += f"/{folder_name}.Folder"
            run_fab(
                f"import {destination_parent}/{qualified_name} "
                f"-i '{target_path}' -f{format_argument}",
                timeout=1200,
            )

        target_id = _resolve_item_id(
            workspace_name, qualified_name, folder_by_item.get(qualified_name)
        )
        if not any(m["source_id"] == item["source_id"] for m in mappings):
            mappings.append({"source_id": item["source_id"], "target_id": target_id})
        deployed.append({"name": qualified_name, "id": target_id})

        if qualified_name == scanner_qualified and not initialized:
            _initialize_tables(
                workspace_id,
                workspace_name,
                scanner_qualified,
                target_id,
                folder_by_item.get(scanner_qualified),
            )
            endpoint_id = _get_sql_endpoint_id(workspace_name, lakehouse_qualified)
            if endpoint_id:
                _refresh_sql_endpoint(workspace_id, endpoint_id)
            else:
                print(
                    "Lakehouse SQL endpoint metadata is not ready yet; "
                    "Direct Lake on OneLake deployment can continue without it."
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
    _refresh_and_validate_semantic_model(workspace_id, semantic_model_id)

    result = {
        "status": "SUCCEEDED",
        "solution_version": config["solution"]["version"],
        "workspace_id": workspace_id,
        "workspace_name": workspace_name,
        "semantic_model_source": {
            "mode": "DirectLakeOnOneLake",
            "lakehouse_id": lakehouse_id,
        },
        "items": deployed,
    }
    print(json.dumps(result, indent=2))
    return result
