#!/usr/bin/env python3
"""Static validation for the repository's Fabric item definitions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def validate_json() -> int:
    count = 0
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and (path.suffix in {".json", ".ipynb"} or path.name == ".platform"):
            json.loads(path.read_text(encoding="utf-8"))
            count += 1
    return count


def validate_manifest() -> None:
    config = yaml.safe_load((ROOT / "config/deployment_config.yaml").read_text())
    order = json.loads((ROOT / "config/deployment_order.json").read_text())
    ordered_names = [item["name"] for item in order]
    expected = list(config["items"].values())
    if ordered_names != expected:
        fail(f"Deployment order differs from configured items: {ordered_names} != {expected}")
    if config["lakehouse"]["enable_schemas"] is not True:
        fail("The V1 contract requires a schema-enabled Lakehouse.")
    for item in ordered_names:
        if item.endswith(".Lakehouse"):
            continue
        if not (ROOT / "src" / item).is_dir():
            fail(f"Missing source directory for {item}")
    deploy_core = (ROOT / "scripts/deploy_core.py").read_text(encoding="utf-8")
    if "curated_contract_cell" not in deploy_core or "ensure_curated_tables()" not in deploy_core:
        fail("The deployment initializer must create the V2 curated tables before importing Direct Lake.")
    if "folder_by_item" not in deploy_core or "destination_parent" not in deploy_core:
        fail("Fabric item upgrades must address items through their configured folder paths.")


def validate_scanner() -> None:
    path = ROOT / "src/SMO_Optimization_Scanner.Notebook/notebook-content.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    for required in (
        'output_schema = "smopt"',
        "workspace_ids = \"\"",
        "model_ids_optional = \"\"",
        "initialize_only = False",
        "def ensure_tables()",
        'SCANNER_VERSION = "2.0.0"',
        "def ensure_curated_tables()",
        "def curate_latest_model_analysis(result)",
        '"semantic_model_optimization_overview"',
        '"semantic_model_column_storage"',
        '"semantic_model_analysis_runs"',
        '"semantic_models"',
        '"semantic_model_best_practice_rule_findings"',
        '"semantic_model_table_storage"',
    ):
        if required not in source:
            fail(f"Scanner is missing required text: {required}")
    dependency = notebook["metadata"]["dependencies"]["lakehouse"]
    if dependency["default_lakehouse"] != "11111111-1111-1111-1111-111111111111":
        fail("Scanner Lakehouse placeholder does not match the deployment manifest.")


def validate_model() -> None:
    model_root = ROOT / "src/SMO_Analytics_SM.SemanticModel/definition"
    model = (model_root / "model.tmdl").read_text(encoding="utf-8")
    refs = re.findall(r"^ref table (.+)$", model, flags=re.MULTILINE)
    for table in refs:
        table = table.strip("'")
        if not (model_root / "tables" / f"{table}.tmdl").exists():
            fail(f"Missing TMDL table file for {table}")
    if len(refs) != 12:
        fail(f"The M6.4 Direct Lake model must expose 11 business tables plus Metrics, found {len(refs)}.")
    if "smopt_" in model:
        fail("The V2 Direct Lake model must not expose deprecated smopt_* technical tables.")
    expressions = (model_root / "expressions.tmdl").read_text(encoding="utf-8")
    if "Sql.Database" not in expressions:
        fail("Direct Lake connection expression is missing.")


def validate_report() -> None:
    report_root = ROOT / "src/SMO_Analytics_Report.Report"
    binding = json.loads((report_root / "definition.pbir").read_text())
    connection = binding["datasetReference"]["byConnection"]["connectionString"]
    if "44444444-4444-4444-4444-444444444444" not in connection:
        fail("Report semantic-model placeholder is missing.")
    pages = json.loads((report_root / "definition/pages/pages.json").read_text())
    expected_pages = ["overview", "opportunities", "recommendations", "findings", "storage", "opportunity_detail"]
    if pages["pageOrder"] != expected_pages:
        fail("The report must retain five visible pages plus one hidden drillthrough detail page.")
    visual_count = 0
    visible_pages = []
    workspace_sync_count = 0
    model_sync_count = 0
    for page in pages["pageOrder"]:
        page_root = report_root / "definition/pages" / page
        if not (page_root / "page.json").exists():
            fail(f"Missing report page: {page}")
        page_definition = json.loads((page_root / "page.json").read_text())
        if page_definition.get("visibility") != "HiddenInViewMode":
            visible_pages.append(page)
        visuals = list((page_root / "visuals").glob("*/visual.json"))
        if not visuals:
            fail(f"Report page {page} has no visuals.")
        for visual_path in visuals:
            visual_definition = json.loads(visual_path.read_text())
            sync_group = visual_definition.get("visual", {}).get("syncGroup", {}).get("groupName")
            workspace_sync_count += sync_group == "SMO_Workspace"
            model_sync_count += sync_group == "SMO_SemanticModel"
        visual_count += len(visuals)
    if visible_pages != ["overview", "opportunities", "recommendations", "findings", "storage"]:
        fail(f"The report must expose exactly the approved five visible pages, found {visible_pages}.")
    detail_page = json.loads((report_root / "definition/pages/opportunity_detail/page.json").read_text())
    if detail_page.get("pageBinding", {}).get("type") != "Drillthrough":
        fail("Opportunity detail must be configured as a drillthrough page.")
    if workspace_sync_count != 6 or model_sync_count != 6:
        fail("Workspace and semantic-model slicers must be synchronized across every report page.")
    if visual_count != 36:
        fail(f"The M6.4 report contract requires 36 visuals, found {visual_count}.")


def validate_no_secrets() -> None:
    suspicious = re.compile(r"(?i)(client_secret|github_token)\s*=\s*[\"'][^\"']{8,}[\"']")
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if suspicious.search(content):
            fail(f"Possible committed secret in {path.relative_to(ROOT)}")


def main() -> int:
    json_count = validate_json()
    validate_manifest()
    validate_scanner()
    validate_model()
    validate_report()
    validate_no_secrets()
    print(f"Validation passed: {json_count} JSON/notebook/platform files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
