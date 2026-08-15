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


def _wait_for_lakehouse(workspace_name: str, lakehouse_name: str) -> tuple[str, str]:
    for attempt in range(30):
        endpoint_id = run_fab(
            f"get /{workspace_name}.Workspace/{lakehouse_name} "
            "-q properties.sqlEndpointProperties.id",
            allow_failure=True,
        )
        connection = run_fab(
            f"get /{workspace_name}.Workspace/{lakehouse_name} "
            "-q properties.sqlEndpointProperties.connectionString",
            allow_failure=True,
        )
        if endpoint_id and connection:
            return endpoint_id, connection
        time.sleep(min(5 + attempt, 15))
    raise TimeoutError("Lakehouse SQL analytics endpoint was not provisioned in time.")


def _update_direct_lake_connection(
    item_root: Path, endpoint_id: str, connection_string: str
) -> None:
    expressions = item_root / "definition" / "expressions.tmdl"
    content = expressions.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'Sql\.Database\("[^"]+",\s*"[^"]+"\)',
        f'Sql.Database("{connection_string}", "{endpoint_id}")',
        content,
        count=1,
    )
    if count != 1:
        raise ValueError("Unable to locate the Direct Lake Sql.Database expression.")
    expressions.write_text(updated, encoding="utf-8")


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


def _resolve_item_id(workspace_name: str, qualified_name: str) -> str:
    item_id = run_fab(
        f"get /{workspace_name}.Workspace/{qualified_name} -q id",
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


def _initialize_tables(workspace_name: str, notebook_name: str) -> None:
    parameters = json.dumps(
        {
            "parameters": {
                "initialize_only": {"type": "Bool", "value": "True"},
                "_inlineInstallationEnabled": {"type": "Bool", "value": "True"},
            }
        }
    )
    run_fab(
        f"job run /{workspace_name}.Workspace/{notebook_name} -i '{parameters}' "
        "--timeout 3600 --polling_interval 20",
        timeout=3600,
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
    endpoint_connection = None

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
            if not any(m["source_id"] == item["source_id"] for m in mappings):
                mappings.append(
                    {"source_id": item["source_id"], "target_id": target_id}
                )
            endpoint_id, endpoint_connection = _wait_for_lakehouse(
                workspace_name, qualified_name
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
            if item_type == "SemanticModel":
                if not endpoint_id or not endpoint_connection:
                    raise RuntimeError("Lakehouse SQL endpoint is unavailable.")
                _update_direct_lake_connection(
                    target_path, endpoint_id, endpoint_connection
                )
            format_argument = " --format .ipynb" if item_type == "Notebook" else ""
            run_fab(
                f"import /{workspace_name}.Workspace/{qualified_name} "
                f"-i '{target_path}' -f{format_argument}",
                timeout=1200,
            )

        target_id = _resolve_item_id(workspace_name, qualified_name)
        if not any(m["source_id"] == item["source_id"] for m in mappings):
            mappings.append({"source_id": item["source_id"], "target_id": target_id})
        deployed.append({"name": qualified_name, "id": target_id})

        if qualified_name == scanner_qualified and not initialized:
            _initialize_tables(workspace_name, scanner_qualified)
            _refresh_sql_endpoint(workspace_id, endpoint_id)
            initialized = True

    _move_items_to_folders(workspace_id, workspace_name, config.get("folders", []))

    semantic_model_id = _resolve_item_id(
        workspace_name, config["items"]["semantic_model"]
    )
    run_fab(
        f"api -A powerbi -X post datasets/{semantic_model_id}/refreshes "
        "-i '{\"retryCount\":\"3\"}'",
        allow_failure=True,
    )

    result = {
        "status": "SUCCEEDED",
        "solution_version": config["solution"]["version"],
        "workspace_id": workspace_id,
        "workspace_name": workspace_name,
        "items": deployed,
    }
    print(json.dumps(result, indent=2))
    return result
