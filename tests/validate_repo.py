#!/usr/bin/env python3
"""Static validation for the repository's Fabric item definitions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.quality_rules import (  # noqa: E402
    ACTIONABLE,
    REVIEW_REQUIRED,
    SUPPRESSED,
    grade_finding,
    grade_recommendation,
)


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
    if ordered_names.index(config["items"]["scanner_environment"]) > ordered_names.index(
        config["items"]["scanner_notebook"]
    ):
        fail("The scanner Environment must be deployed before the scanner Notebook.")
    configured_branch = config["source"]["branch"]
    deploy_notebook = json.loads(
        (ROOT / "scripts/Deploy_SMO_Analytics.ipynb").read_text(encoding="utf-8")
    )
    deploy_source = "\n".join(
        "".join(cell.get("source", [])) for cell in deploy_notebook["cells"]
    )
    if configured_branch != "codex/m6-4":
        fail(f"Development deployment must use codex/m6-4, found {configured_branch}.")
    if f'branch = "{configured_branch}"' not in deploy_source:
        fail("Deployment notebook and manifest source branches differ.")
    if "configured_branch != branch" not in deploy_source:
        fail("Deployment notebook must reject a downloaded source/config branch mismatch.")
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
    for required in (
        "def _wait_for_sql_endpoint(",
        "def _update_and_validate_direct_lake_sql_connection(",
        "def _refresh_and_validate_sql_endpoint(",
        "def _refresh_and_validate_semantic_model(",
        "def _publish_and_validate_environment(",
        "Scanner environment libraries are not published as required",
        "SQL endpoint metadata validated:",
        "DirectLakeOnSqlEndpoint",
        "groups/{workspace_id}/datasets/{semantic_model_id}",
    ):
        if required not in deploy_core:
            fail(f"Deployment engine is missing end-to-end validation: {required}")
    if "def _validate_direct_lake_connection(" in deploy_core:
        fail("Deployment must not use the retired OneLake-only binding path.")


def validate_scanner() -> None:
    path = ROOT / "src/SMO_Optimization_Scanner.Notebook/notebook-content.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") == "code":
            compile("".join(cell.get("source", [])), f"{path.name}:cell-{index}", "exec")
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    for required in (
        'output_schema = "smopt"',
        "workspace_ids = \"\"",
        "model_ids_optional = \"\"",
        "initialize_only = False",
        "def ensure_tables()",
        'SCANNER_VERSION = "2.1.3"',
        "Scanner environment dependencies validated.",
        "fail_pipeline_if_any_model_fails = True",
        '"component_errors": row["error_json"]',
        "Model analysis failures:",
        "def ensure_curated_tables()",
        "def curate_latest_model_analysis(result)",
        "def reconcile_workspace_current_state(targets)",
        "def validate_curated_scan_output(model_results)",
        "reconcile_workspace_current_state(targets)",
        "validate_curated_scan_output(model_results)",
        "Scan did not materialize the required business-layer rows",
        '"semantic_model_optimization_overview"',
        '"semantic_model_column_storage"',
        '"semantic_model_analysis_runs"',
        '"semantic_models"',
        '"semantic_model_best_practice_rule_findings"',
        '"semantic_model_table_storage"',
        '"actionability_status"',
        '"recommendation_priority_score"',
        '"suppression_reason"',
    ):
        if required not in source:
            fail(f"Scanner is missing required text: {required}")
    dependency = notebook["metadata"]["dependencies"]["lakehouse"]
    if dependency["default_lakehouse"] != "11111111-1111-1111-1111-111111111111":
        fail("Scanner Lakehouse placeholder does not match the deployment manifest.")
    environment_dependency = notebook["metadata"]["dependencies"]["environment"]
    if environment_dependency != {
        "environmentId": "66666666-6666-6666-6666-666666666666",
        "workspaceId": "00000000-0000-0000-0000-000000000000",
    }:
        fail("Scanner Environment dependency does not match the deployment manifest.")
    if notebook["metadata"].get("scanner_version") != "2.1.3":
        fail("Scanner metadata version must match the executable scanner version.")
    if "%pip" in source or "_inlineInstallationEnabled" in source:
        fail("Pipeline scanner must not use session-scoped package installation.")

    pipeline = (
        ROOT / "src/Load_SMO_Data.DataPipeline/pipeline-content.json"
    ).read_text(encoding="utf-8")
    if "_inlineInstallationEnabled" in pipeline:
        fail("Pipeline must not pass the removed inline-install parameter.")

    environment_root = ROOT / "src/SMO_Scanner_Environment.Environment"
    environment_yml = yaml.safe_load(
        (environment_root / "Libraries/PublicLibraries/environment.yml").read_text()
    )
    pip_packages = environment_yml["dependencies"][0]["pip"]
    expected_packages = {
        "semantic-link-sempy==0.14.2",
        "semantic-link-labs==0.15.2",
    }
    if set(pip_packages) != expected_packages:
        fail(f"Scanner Environment packages differ from the pinned contract: {pip_packages}")


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
    expected_source = (
        'Sql.Database("placeholder.datawarehouse.fabric.microsoft.com", '
        '"77777777-7777-7777-7777-777777777777")'
    )
    if expected_source not in expressions or "AzureStorage.DataLake" in expressions:
        fail("Direct Lake SQL analytics endpoint template is missing or invalid.")
    if 'PBI_QueryOrder = ["DatabaseQuery"]' not in model:
        fail("Model query order must reference the SQL endpoint source expression.")
    for table in refs:
        table = table.strip("'")
        if table == "Metrics":
            continue
        table_text = (model_root / "tables" / f"{table}.tmdl").read_text(encoding="utf-8")
        if "mode: directLake" not in table_text:
            fail(f"Table {table} is not configured for Direct Lake.")
        if "expressionSource: DatabaseQuery" not in table_text:
            fail(f"Table {table} does not reference the SQL endpoint expression.")
        if "schemaName:" not in table_text:
            fail(f"Table {table} is missing its Lakehouse schema mapping.")
    recommendations = (model_root / "tables/semantic_model_optimization_recommendations.tmdl").read_text()
    for required_column in (
        "actionability_status", "recommendation_priority_score", "recommendation_priority_band",
        "why_it_matters", "validation_method", "rollback_guidance",
    ):
        if f"\tcolumn {required_column}" not in recommendations:
            fail(f"Recommendation quality contract is missing {required_column}.")


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
    model_tables = ROOT / "src/SMO_Analytics_SM.SemanticModel/definition/tables"
    semantic_fields = {}
    for table_path in model_tables.glob("*.tmdl"):
        text = table_path.read_text(encoding="utf-8")
        columns = set(re.findall(r"^\tcolumn ([^\n]+)$", text, re.MULTILINE))
        measures = set(re.findall(r"^\tmeasure '([^']+)'", text, re.MULTILINE))
        semantic_fields[table_path.stem] = columns | measures

    def referenced_fields(node):
        if isinstance(node, dict):
            for kind in ("Column", "Measure"):
                expression = node.get(kind)
                if isinstance(expression, dict):
                    entity = expression.get("Expression", {}).get("SourceRef", {}).get("Entity")
                    prop = expression.get("Property")
                    if entity and prop:
                        yield entity, prop
            for value in node.values():
                yield from referenced_fields(value)
        elif isinstance(node, list):
            for value in node:
                yield from referenced_fields(value)
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
            for entity, prop in referenced_fields(visual_definition):
                if entity not in semantic_fields or prop not in semantic_fields[entity]:
                    fail(f"Report field {entity}.{prop} in {visual_path.relative_to(ROOT)} is not present in TMDL.")
            sync_group = visual_definition.get("visual", {}).get("syncGroup", {}).get("groupName")
            workspace_sync_count += sync_group == "SMO_Workspace"
            model_sync_count += sync_group == "SMO_SemanticModel"
        visual_count += len(visuals)
    if visible_pages != ["overview", "opportunities", "recommendations", "findings", "storage"]:
        fail(f"The report must expose exactly the approved five visible pages, found {visible_pages}.")
    detail_page = json.loads((report_root / "definition/pages/opportunity_detail/page.json").read_text())
    if detail_page.get("pageBinding", {}).get("type") != "Drillthrough":
        fail("Opportunity detail must be configured as a drillthrough page.")
    drill_parameters = detail_page.get("pageBinding", {}).get("parameters", [])
    drill_property = (
        drill_parameters[0]
        .get("fieldExpr", {})
        .get("Column", {})
        .get("Property")
        if drill_parameters
        else None
    )
    if drill_property != "opportunity_title":
        fail("Opportunity drillthrough must use the visible opportunity title from the source table.")
    if workspace_sync_count != 6 or model_sync_count != 6:
        fail("Workspace and semantic-model slicers must be synchronized across every report page.")
    if visual_count != 38:
        fail(f"The M6.5.1 report contract requires 38 visuals, found {visual_count}.")
    top_queue = report_root / "definition/pages/recommendations/visuals/top_actionable_recommendations/visual.json"
    if not top_queue.exists():
        fail("Recommendations must expose the Top actionable recommendations queue.")
    top_queue_text = top_queue.read_text(encoding="utf-8")
    for field in ("recommendation_priority_score", "actionability_status", "why_it_matters", "validation_method"):
        if field not in top_queue_text:
            fail(f"Top actionable recommendations is missing {field}.")
    top_queue_definition = json.loads(top_queue_text)
    top_sort = top_queue_definition["visual"]["query"].get("sortDefinition", {}).get("sort", [])
    if not top_sort or top_sort[0].get("direction") != "Descending":
        fail("Top actionable recommendations must be sorted by priority descending.")


def validate_quality_rules() -> None:
    actionable = grade_finding({
        "finding_text": "A high-cardinality text column consumes excess storage.",
        "technical_evidence": "Dictionary size 104857600 bytes.",
        "recommended_action": "Remove or encode the column.",
        "severity": "HIGH", "confidence": "HIGH", "change_risk": "LOW",
        "estimated_saving_bytes_high": 104857600,
    })
    if actionable["actionability_status"] != ACTIONABLE or actionable["finding_priority_score"] < 80:
        fail("Strong evidence with a low-risk action must enter the P1 actionable queue.")
    without_confidence = grade_finding({
        "finding_text": "BPA rule violation.", "technical_evidence": "Deterministic BPA evidence.",
        "recommended_action": "Apply the documented BPA remediation.",
        "severity": "WARNING", "change_risk": "MEDIUM",
    })
    if without_confidence["actionability_status"] != ACTIONABLE:
        fail("Missing confidence must remain neutral for deterministic BPA evidence.")

    generated = {
        "finding_text": "Generated date table detected.", "technical_evidence": "LocalDateTable object.",
        "recommended_action": "Remove it.", "severity": "HIGH", "confidence": "HIGH",
        "change_risk": "MEDIUM", "table_name": "LocalDateTable_123",
    }
    suppressed = grade_finding(generated)
    if suppressed["actionability_status"] != SUPPRESSED or suppressed["finding_priority_score"] != 0:
        fail("Generated Auto Date/Time objects must be suppressed at finding level.")
    consolidated = grade_recommendation([generated], "Performance", "Generated object", "Remove it")
    if consolidated["actionability_status"] != REVIEW_REQUIRED or consolidated["recommendation_priority_score"] < 65:
        fail("Generated date findings must roll up into one high-priority model-level review.")
    if "explicit date dimension" not in consolidated["recommendation_title"]:
        fail("Auto Date/Time remediation must use a meaningful model-level recommendation title.")


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
    validate_quality_rules()
    validate_no_secrets()
    print(f"Validation passed: {json_count} JSON/notebook/platform files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
