#!/usr/bin/env python3
"""Static validation for the repository's Fabric item definitions."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.quality_rules import (  # noqa: E402
    ACTIONABLE,
    AUTO_DATE_ROOT_CAUSE_SOURCE,
    AUTO_DATE_ROOT_CAUSE_TITLE,
    INFORMATIONAL,
    REVIEW_REQUIRED,
    SUPPRESSED,
    grade_finding,
    grade_opportunity,
    grade_recommendation,
    is_auto_date_root_cause_finding,
    root_cause_grouping,
    summarize_opportunity,
)
from scripts.model_quality_rules import analyze_model_bim  # noqa: E402


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
        "def _sql_endpoint_table_readiness(",
        "def _refresh_and_validate_sql_endpoint(",
        "def _refresh_and_validate_semantic_model(",
        "def _publish_and_validate_environment(",
        "def _public_definition(",
        "def _update_public_definition(",
        'formats = {"SemanticModel": "TMDL", "Report": "PBIR"}',
        'path.name == ".platform"',
        'item_type in {"SemanticModel", "Report"}',
        "updateDefinition",
        'result_error.get("errorCode") == "OperationHasNoResult"',
        "Scanner environment libraries are not published",
        "will determine compatibility",
        "SQL endpoint metadata validated:",
        'status == "notrun" and row.get("lastSuccessfulSyncDateTime")',
        "already current",
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
    code_source = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    for required in (
        'output_schema = "smopt"',
        "workspace_ids = \"\"",
        "model_ids_optional = \"\"",
        "initialize_only = False",
        "def ensure_tables()",
        'SCANNER_VERSION = "2.6.3"',
        "run_model_metadata_checks = True",
        "semantic-model metadata inspection",
        "def analyze_model_bim(",
        'statuses["metadata"] = "SUCCEEDED"',
        'scan_profile = "workspace_user"',
        'if SCAN_PROFILE == "governance_admin":\n    import sempy.fabric.admin as admin',
        'statuses["access_snapshot"] = "NOT_APPLICABLE_WORKSPACE_USER_PROFILE"',
        'error_details["optional_enrichment_warnings"] = optional_enrichment_warnings',
        "def classify_model_status(statuses)",
        "Scanner runtime modules discovered; callable capability validation follows.",
        "def module_available(module_name)",
        "def validate_runtime_capabilities()",
        "runtime capabilities validated",
        'getattr(fabric, "set_service_principal", None)',
        "fail_pipeline_if_any_model_fails = True",
        '"component_errors": row["error_json"]',
        "Model analysis failures:",
        "def ensure_curated_tables()",
        "def finding_locator_fields(finding)",
        "def normalize_display_identifier(value)",
        "def split_display_object(value)",
        'replace("\\u200b", "").replace("\\ufeff", "").replace("\\u00a0", " ")',
        '"object_scope": object_scope',
        '"display_table_name": display_table',
        'row["analysis_scope_key"] = f"{semantic_model_id}|{analysis_id}"',
        'row["issue_scope_key"] = f"{semantic_model_id}|{analysis_id}|{row[\'opportunity_id\']}"',
        "SET analysis_scope_key = concat(semantic_model_id, '|', analysis_id)",
        "SET issue_scope_key = concat(semantic_model_id, '|', analysis_id, '|', opportunity_id)",
        "UPDATE {findings_name}",
        "substring_index(affected_object_name, '[', 1)",
        "object_table, object_leaf = split_display_object(raw_object)",
        "def curate_latest_model_analysis(result)",
        "auto_date_present = any(is_auto_date_root_cause_finding(row) for row in findings)",
        "consolidation = root_cause_grouping(finding, auto_date_present)",
        '"finding_source": raw_source',
        '"source": source',
        "def reconcile_workspace_current_state(targets)",
        "def validate_curated_scan_output(model_results)",
        "reconcile_workspace_current_state(targets)",
        "validate_curated_scan_output(model_results)",
        "Scan did not materialize the required business-layer rows",
        "Business-layer quality validation failed",
        "invalid_opportunity_rollups",
        "invalid_recommendation_links",
        '"RECOMMENDATION",\n            opportunity_id,',
        "Best-practice analysis: completed with no rule violations.",
        "Storage analysis: completed with no column or table storage records.",
        "Item access snapshot: not applicable to the normal workspace-user profile.",
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
    if notebook["metadata"].get("scanner_version") != "2.6.3":
        fail("Scanner metadata version must match the executable scanner version.")
    if "%pip" in source or "_inlineInstallationEnabled" in source:
        fail("Pipeline scanner must not use session-scoped package installation.")
    for forbidden in (
        "admin.list_workspace_access_details",
        "admin.list_workspaces",
        "admin.list_items",
        "spn_object_id",
        "required_workspace_roles",
    ):
        if forbidden in source:
            fail(f"Workspace-scoped scanner must not depend on tenant-admin discovery: {forbidden}")
    if source.count("admin.list_item_access_details") != 1:
        fail("The optional governance profile must be the only Admin API consumer.")

    scanner_tree = ast.parse(code_source)
    status_nodes = [
        node
        for node in scanner_tree.body
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "ANALYSIS_STATUS_KEYS" for target in node.targets)
        )
        or (isinstance(node, ast.FunctionDef) and node.name == "classify_model_status")
    ]
    status_namespace = {"run_bpa": True, "run_vertipaq": True}
    exec(compile(ast.fix_missing_locations(ast.Module(body=status_nodes, type_ignores=[])), "status-policy", "exec"), status_namespace)

    normalizer_nodes = [
        node for node in scanner_tree.body
        if isinstance(node, ast.FunctionDef) and node.name in {
            "normalize_display_identifier", "split_display_object", "finding_locator_fields",
        }
    ]
    normalizer_namespace = {"re": re}
    exec(
        compile(ast.fix_missing_locations(ast.Module(body=normalizer_nodes, type_ignores=[])), "display-normalizer", "exec"),
        normalizer_namespace,
    )
    normalize_identifier = normalizer_namespace["normalize_display_identifier"]
    variants = ["DimDate", "'DimDate'", '"DimDate"', "`DimDate`", "\u200bDimDate\ufeff", "Dim\u00a0Date"]
    normalized = [normalize_identifier(value) for value in variants]
    if normalized[:5] != ["DimDate"] * 5 or normalized[5] != "Dim Date":
        fail(f"Display-only table-name normalization is not canonical: {normalized}.")
    finding_locator = normalizer_namespace["finding_locator_fields"]
    locator_variants = [
        {"table_name": "FactInternetSales", "object_name": "OrderDateText", "object_type": "Column"},
        {"table_name": "'FactInternetSales'", "object_name": "'FactInternetSales'[OrderDateText]", "object_type": "Column"},
    ]
    locators = [finding_locator(value) for value in locator_variants]
    if any(locator["display_table_name"] != "FactInternetSales" for locator in locators):
        fail(f"Column table locators are not canonical: {locators}.")
    if any(locator["display_object_name"] != "FactInternetSales[OrderDateText]" for locator in locators):
        fail(f"BPA and MQ column locators must share one qualified display name: {locators}.")
    ensure_curated_source = ast.get_source_segment(code_source, next(
        node for node in scanner_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "ensure_curated_tables"
    )) or ""
    if 'spark.sql(fr"""' not in ensure_curated_source:
        fail("Curated display-name normalization must use a raw f-string so Spark receives regex escapes unchanged.")
    if "concat(\n                    display_table_name,\n                    '['," not in ensure_curated_source:
        fail("Deployment-time display-object backfill must preserve qualified Table[Column] locators.")
    if "ELSE trim(affected_object_name)" in ensure_curated_source:
        fail("Deployment-time display-object backfill must not collapse qualified locators to raw leaf names.")
    classify = status_namespace["classify_model_status"]
    base = {
        "bpa": "SUCCEEDED",
        "vpa": "SUCCEEDED",
        "metadata": "SUCCEEDED",
        "refresh": "SUCCEEDED",
        "usage": "NOT_RUN",
        "direct_lake": "NOT_APPLICABLE",
        "access_snapshot": "FAILED",
    }
    if classify(base) != "SUCCEEDED":
        fail("Optional governance evidence must not downgrade a successful core scan.")
    if classify({**base, "vpa": "FAILED"}) != "PARTIAL":
        fail("A partial core-analysis failure must remain visible as PARTIAL.")
    if classify({**base, "bpa": "FAILED", "vpa": "FAILED"}) != "FAILED":
        fail("Failure of every enabled core analysis must remain FAILED.")
    if classify({**base, "metadata": "FAILED"}) != "PARTIAL":
        fail("Metadata-quality analysis failure must remain visible as PARTIAL.")

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
    if pip_packages != ["semantic-link-labs"]:
        fail(f"Scanner Environment must contain only unpinned Semantic Link Labs: {pip_packages}")
    if any("==" in package for package in pip_packages):
        fail(f"Scanner Environment packages must not use exact version pins: {pip_packages}")


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
    expected_pages = ["overview", "opportunities", "storage"]
    if pages["pageOrder"] != expected_pages:
        fail("The report must expose Start here, the consolidated review workbench, and Storage.")
    visual_count = 0
    visible_pages = []
    workspace_sync_count = 0
    model_sync_count = 0
    analysis_sync_count = 0
    model_tables = ROOT / "src/SMO_Analytics_SM.SemanticModel/definition/tables"
    semantic_fields = {}
    for table_path in model_tables.glob("*.tmdl"):
        text = table_path.read_text(encoding="utf-8")
        columns = {
            value.strip()
            for value in re.findall(r"^\tcolumn ([^\n=]+)(?: =.*)?$", text, re.MULTILINE)
        }
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
            position = visual_definition.get("position", {})
            if (
                position.get("x", 0) < 0 or position.get("y", 0) < 0
                or position.get("x", 0) + position.get("width", 0) > page_definition.get("width", 1280)
                or position.get("y", 0) + position.get("height", 0) > page_definition.get("height", 720)
            ):
                fail(f"Visual {visual_path.relative_to(ROOT)} extends outside the report canvas.")
            if (
                visual_definition.get("visual", {}).get("visualType") == "slicer"
                and position.get("height", 0) < 76
            ):
                fail(f"Dropdown slicer {visual_path.relative_to(ROOT)} is below the 76 px clipping-safe floor.")
            for entity, prop in referenced_fields(visual_definition):
                if entity not in semantic_fields or prop not in semantic_fields[entity]:
                    fail(f"Report field {entity}.{prop} in {visual_path.relative_to(ROOT)} is not present in TMDL.")
            sync_group = visual_definition.get("visual", {}).get("syncGroup", {}).get("groupName")
            workspace_sync_count += sync_group == "SMO_Workspace"
            model_sync_count += sync_group == "SMO_SemanticModel"
            analysis_sync_count += sync_group == "SMO_Analysis"
        visual_definitions = [json.loads(path.read_text()) for path in visuals]
        for index, left in enumerate(visual_definitions):
            lp = left["position"]
            for right in visual_definitions[index + 1:]:
                rp = right["position"]
                overlaps = not (
                    lp["x"] + lp["width"] <= rp["x"]
                    or rp["x"] + rp["width"] <= lp["x"]
                    or lp["y"] + lp["height"] <= rp["y"]
                    or rp["y"] + rp["height"] <= lp["y"]
                )
                if overlaps:
                    fail(f"Report page {page} contains overlapping visuals {left['name']} and {right['name']}.")
        visual_count += len(visuals)
    if visible_pages != expected_pages:
        fail(f"The report must expose exactly the approved three visible pages, found {visible_pages}.")
    display_names = [
        json.loads((report_root / "definition/pages" / page / "page.json").read_text())["displayName"]
        for page in visible_pages
    ]
    if display_names != ["Start here", "Review issues", "Storage"]:
        fail(f"The report must expose the consolidated Start here → Review issues → Storage path, found {display_names}.")
    review_page = json.loads((report_root / "definition/pages/opportunities/page.json").read_text())
    if review_page.get("height") != 1080 or review_page.get("width") != 1280:
        fail("Review issues must use the approved 1280 × 1080 analytical canvas.")
    if review_page.get("pageBinding", {}).get("type") != "Drillthrough":
        fail("Review issues must accept drillthrough from Start here.")
    drill_properties = [
        parameter.get("fieldExpr", {}).get("Column", {}).get("Property")
        for parameter in review_page.get("pageBinding", {}).get("parameters", [])
    ]
    if drill_properties != ["semantic_model_name", "priority_band", "actionability_status"]:
        fail(f"Start here drillthrough must bind Model, Priority, and Decision, found {drill_properties}.")
    if review_page.get("pageBinding", {}).get("acceptsFilterContext") != "None":
        fail("Review issues drillthrough must accept only its explicit Model/Priority/Decision fields.")
    if workspace_sync_count != 3 or model_sync_count != 3 or analysis_sync_count != 3:
        fail("Global scope slicers must stay synchronized across all three visible pages.")
    if visual_count != 35:
        fail(f"The consolidated report contract requires 35 visuals, found {visual_count}.")
    reset_button = json.loads(
        (report_root / "definition/pages/opportunities/visuals/reset_slicers_button/visual.json").read_text()
    )
    reset_action = (
        reset_button.get("visual", {}).get("visualContainerObjects", {})
        .get("visualLink", [{}])[0].get("properties", {}).get("type", {}).get("expr", {})
        .get("Literal", {}).get("Value")
    )
    reset_text = json.dumps(reset_button, ensure_ascii=False)
    if reset_action != "'ClearAllSlicers'" or "Clear prior filters" not in reset_text:
        fail(
            "Review issues must expose a clearly labelled one-click reset because Power BI "
            "retains target-page slicer state independently of drillthrough source context."
        )
    for retired_page in ("recommendations", "findings", "opportunity_detail"):
        if (report_root / "definition/pages" / retired_page).exists():
            fail(f"Retired overlapping page still exists: {retired_page}.")
    model_text = (model_tables.parent / "model.tmdl").read_text(encoding="utf-8")
    for relation_name in ("opportunity_findings", "opportunity_recommendations"):
        relation_block = model_text.split(f"relationship {relation_name}", 1)[-1].split("\n\n", 1)[0]
        if "crossFilteringBehavior: bothDirections" not in relation_block:
            fail(f"{relation_name} must bidirectionally filter the grouped root-cause bridge.")
    for relation_name in (
        "models_overview", "models_opportunities", "models_bpa_findings",
        "models_column_storage", "models_table_storage",
    ):
        relation_block = model_text.split(f"relationship {relation_name}", 1)[-1].split("\n\n", 1)[0]
        if (
            "fromColumn:" not in relation_block
            or ".analysis_scope_key" not in relation_block
            or "toColumn: semantic_models.analysis_scope_key" not in relation_block
        ):
            fail(f"{relation_name} must use the unique model-analysis scope key.")
    for relation_name in ("opportunity_findings", "opportunity_recommendations"):
        relation_block = model_text.split(f"relationship {relation_name}", 1)[-1].split("\n\n", 1)[0]
        if relation_block.count(".issue_scope_key") != 2:
            fail(f"{relation_name} must use the analysis-scoped issue key.")
    metrics_text = (model_tables / "Metrics.tmdl").read_text(encoding="utf-8")
    for context_field in (
        "measure 'Selected analysis context'", "latest_analysis_id", "latest_analysis_status",
        "latest_analysis_at", "scanner_version", "measure 'Visible evidence'",
        "measure 'Visible action evidence'", "measure 'Visible actions'",
    ):
        if context_field not in metrics_text:
            fail(f"The current analysis context is missing {context_field}.")
    findings_tmdl = (model_tables / "semantic_model_optimization_findings.tmdl").read_text(encoding="utf-8")
    for display_field in (
        "analysis_scope_key", "issue_scope_key", "object_scope",
        "display_table_name", "display_object_name",
    ):
        if (
            f"column {display_field}\n" not in findings_tmdl
            or f"sourceColumn: {display_field}" not in findings_tmdl
        ):
            fail(f"The evidence locator is missing curated source field {display_field}.")
    if "column object_scope =" in findings_tmdl:
        fail("Direct Lake on SQL locator fields must not use calculated columns.")
    overview_queue = report_root / "definition/pages/overview/visuals/priority_summary/visual.json"
    overview_queue_text = overview_queue.read_text(encoding="utf-8")
    for field in ("priority_band", "actionability_status", "Total opportunities", "Visible evidence", "Visible actions"):
        if field not in overview_queue_text:
            fail(f"The overview priority summary is missing {field}.")
    if "opportunity_title" in overview_queue_text:
        fail("Start here must summarize the queue instead of repeating the full Issues root-cause inventory.")
    if "Visible evidence" not in json.dumps(
        json.loads(overview_queue_text).get("filterConfig", {}).get("filters", [])
    ):
        fail("Start here must hide priority/decision groups with no visible evidence.")
    issues_path = report_root / "definition/pages/opportunities/visuals/issues_table/visual.json"
    actions_path = report_root / "definition/pages/opportunities/visuals/actions_table/visual.json"
    evidence_path = report_root / "definition/pages/opportunities/visuals/evidence_table/visual.json"
    issues_text = issues_path.read_text(encoding="utf-8")
    for dynamic_measure in ("Visible evidence", "Visible actions"):
        if dynamic_measure not in issues_text:
            fail(f"Issues must expose filter-aware {dynamic_measure}.")
    if "finding_count" in issues_text or "recommendation_count" in issues_text:
        fail("Issues must not present stored opportunity totals as filter-aware counts.")
    if "Visible evidence" not in json.dumps(
        json.loads(issues_text).get("filterConfig", {}).get("filters", [])
    ):
        fail("Issues must hide root causes with no evidence in the current object scope.")
    def projection_order(page, visual_name):
        definition = json.loads((
            report_root / "definition/pages" / page / "visuals" / visual_name / "visual.json"
        ).read_text(encoding="utf-8"))
        return [
            projection["queryRef"]
            for projection in definition["visual"]["query"]["queryState"]["Values"]["projections"]
        ]

    canonical_orders = {
        ("opportunities", "issues_table"): [
            f"semantic_model_optimization_opportunities.{field}"
            for field in (
                "priority_band", "actionability_status", "opportunity_title", "optimization_domain",
                "highest_severity", "change_risk",
            )
        ] + [
            "Metrics.Visible actions",
            "Metrics.Visible evidence",
            "semantic_model_optimization_opportunities.opportunity_id",
        ],
        ("opportunities", "actions_table"): [
            "semantic_model_optimization_recommendations.recommendation_title",
            "semantic_model_optimization_recommendations.why_it_matters",
            "semantic_model_optimization_recommendations.recommended_action",
            "semantic_model_optimization_recommendations.validation_method",
            "semantic_model_optimization_recommendations.rollback_guidance",
            "semantic_model_optimization_recommendations.change_risk",
            "semantic_model_optimization_recommendations.automation_eligibility",
            "Metrics.Visible action evidence",
        ],
        ("opportunities", "evidence_table"): [
            "semantic_model_optimization_findings.severity",
            "semantic_model_optimization_findings.object_scope",
            "semantic_model_optimization_findings.affected_object_type",
            "semantic_model_optimization_findings.display_table_name",
            "semantic_model_optimization_findings.display_object_name",
            "semantic_model_optimization_findings.finding_source",
            "semantic_model_optimization_findings.rule_name",
            "semantic_model_optimization_findings.finding_description",
            "semantic_model_optimization_findings.technical_evidence",
        ],
    }
    for target, expected_order in canonical_orders.items():
        actual_order = projection_order(*target)
        if actual_order != expected_order:
            fail(f"Canonical field order mismatch for {target}: {actual_order}.")
    actions_text = actions_path.read_text(encoding="utf-8")
    evidence_text = evidence_path.read_text(encoding="utf-8")
    for required in ("why_it_matters", "recommended_action", "validation_method", "rollback_guidance"):
        if required not in actions_text:
            fail(f"Actions must expose the former detail field {required} inline.")
    for required in ("finding_description", "technical_evidence", "finding_source"):
        if required not in evidence_text:
            fail(f"Evidence must expose the former detail field {required} inline.")
    for repeated in ("priority_band", "actionability_status", "opportunity_title", "opportunity_id"):
        if repeated in actions_text or repeated in evidence_text:
            fail(f"Actions and Evidence must not repeat Issues control field {repeated}.")
    if "opportunity_id" not in issues_text:
        fail("Issues must retain the unique technical issue key as its final row-grain control.")
    if '"displayName": "Max severity"' not in issues_text:
        fail("Issues must label grouped severity as Max severity.")
    if '"displayName": "Evidence severity"' not in evidence_text:
        fail("Evidence must label row-grain severity as Evidence severity.")
    report_json_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (report_root / "definition/pages").rglob("*.json")
    )
    if "opportunity_summary" in report_json_text:
        fail("The report must not mix stored opportunity summaries with filter-aware visible counts.")

    actions_definition = json.loads(actions_text)
    top_sort = actions_definition["visual"]["query"].get("sortDefinition", {}).get("sort", [])
    if not top_sort or top_sort[0].get("direction") != "Descending":
        fail("Actions must be sorted by recommendation priority descending.")
    action_filters = actions_definition.get("filterConfig", {}).get("filters", [])
    if not action_filters or "Visible action evidence" not in json.dumps(action_filters):
        fail("Actions must hide work items with no evidence in the current object scope.")

    expected_interactions = {
        ("issues_table", "actions_table", "DataFilter"),
        ("issues_table", "evidence_table", "DataFilter"),
        ("actions_table", "evidence_table", "NoFilter"),
        ("evidence_table", "actions_table", "NoFilter"),
    }
    actual_interactions = {
        (item.get("source"), item.get("target"), item.get("type"))
        for item in review_page.get("visualInteractions", [])
    }
    if actual_interactions != expected_interactions:
        fail(f"Review workbench interactions differ from the approved contract: {actual_interactions}.")

    review_visual_root = report_root / "definition/pages/opportunities/visuals"
    for button_name, expected_type in {
        "back_button": "Back",
        "reset_slicers_button": "ClearAllSlicers",
    }.items():
        button = json.loads((review_visual_root / button_name / "visual.json").read_text())
        action = button.get("visual", {}).get("visualContainerObjects", {}).get("visualLink", [])
        if expected_type not in json.dumps(action):
            fail(f"Review issues {button_name} must use the {expected_type} action.")

    slicer_fields = {}
    for slicer_name in (
        "object_scope_slicer", "object_type_slicer", "table_slicer",
        "object_slicer", "domain_slicer", "severity_slicer",
    ):
        slicer = json.loads((review_visual_root / slicer_name / "visual.json").read_text())
        projection = slicer["visual"]["query"]["queryState"]["Values"]["projections"]
        slicer_fields[slicer_name] = projection[0]["queryRef"]
    expected_slicer_fields = {
        "object_scope_slicer": "semantic_model_optimization_findings.object_scope",
        "object_type_slicer": "semantic_model_optimization_findings.affected_object_type",
        "table_slicer": "semantic_model_optimization_findings.display_table_name",
        "object_slicer": "semantic_model_optimization_findings.display_object_name",
        "domain_slicer": "semantic_model_optimization_findings.optimization_domain",
        "severity_slicer": "semantic_model_optimization_findings.severity",
    }
    if slicer_fields != expected_slicer_fields:
        fail(f"Review workbench locator fields differ from the approved contract: {slicer_fields}.")

    def conditional_targets(path):
        definition = json.loads(path.read_text())
        values = definition.get("visual", {}).get("objects", {}).get("values", [])
        return {
            item.get("selector", {}).get("metadata")
            for item in values
            if item.get("selector", {}).get("metadata")
        }

    required_conditional_targets = {
        overview_queue: {
            "semantic_model_optimization_opportunities.priority_band",
            "semantic_model_optimization_opportunities.actionability_status",
        },
        issues_path: {
            "semantic_model_optimization_opportunities.priority_band",
            "semantic_model_optimization_opportunities.actionability_status",
            "semantic_model_optimization_opportunities.highest_severity",
            "semantic_model_optimization_opportunities.change_risk",
        },
        actions_path: {
            "semantic_model_optimization_recommendations.change_risk",
            "semantic_model_optimization_recommendations.automation_eligibility",
        },
        evidence_path: {"semantic_model_optimization_findings.severity"},
    }
    for path, expected_targets in required_conditional_targets.items():
        actual_targets = conditional_targets(path)
        if not expected_targets.issubset(actual_targets):
            fail(f"Conditional formatting is incomplete for {path.name}: {actual_targets}.")

    required_data_bars = {
        overview_queue: {"Metrics.Visible evidence", "Metrics.Visible actions"},
        issues_path: {"Metrics.Visible evidence", "Metrics.Visible actions"},
        actions_path: {"Metrics.Visible action evidence"},
    }
    for path, expected_targets in required_data_bars.items():
        definition = json.loads(path.read_text())
        targets = {
            item.get("selector", {}).get("metadata")
            for item in definition.get("visual", {}).get("objects", {}).get("columnFormatting", [])
            if item.get("properties", {}).get("dataBars")
        }
        if targets != expected_targets:
            fail(f"Data-bar formatting is incomplete for {path.name}: {targets}.")
    for page in pages["pageOrder"]:
        model_slicer = report_root / "definition/pages" / page / "visuals/semantic_model_filter/visual.json"
        if not model_slicer.exists():
            fail(f"Page {page} is missing the semantic-model context slicer.")
        if "SMO_Optimization1" not in model_slicer.read_text(encoding="utf-8"):
            fail(f"Page {page} must retain the adverse-model validation preset.")
    overview_kpis = json.loads((
        report_root / "definition/pages/overview/visuals/optimization_kpis/visual.json"
    ).read_text(encoding="utf-8"))
    kpi_projections = overview_kpis["visual"]["query"]["queryState"]["Data"]["projections"]
    if len(kpi_projections) != 4 or overview_kpis["position"]["height"] < 112:
        fail("The Start here KPI strip must use four legible metrics in a clipping-safe card.")


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

    missing_evidence = grade_finding({
        "finding_text": "A potential issue was described.",
        "recommended_action": "Change the model.",
        "severity": "HIGH", "confidence": "HIGH", "change_risk": "LOW",
    })
    if missing_evidence["actionability_status"] != REVIEW_REQUIRED:
        fail("A finding without technical evidence must require confirmation, not become actionable.")

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

    mq020 = {
        "finding_text": "Generated date tables are present.",
        "technical_evidence": "generated_table_count=2",
        "recommended_action": "Disable Auto Date/Time.",
        "severity": "ERROR", "confidence": "HIGH", "change_risk": "HIGH",
        "rule_name": "MQ020: Auto Date/Time tables present", "source": "MODEL_METADATA_HEURISTIC",
    }
    mq022 = {
        "finding_text": "No table is marked as a date table.",
        "technical_evidence": "marked_date_table_count=0",
        "recommended_action": "Mark the conformed date dimension.",
        "severity": "ERROR", "confidence": "HIGH", "change_risk": "HIGH",
        "rule_name": "MQ022: No explicit table marked as the date table", "source": "MODEL_METADATA_HEURISTIC",
    }
    if not is_auto_date_root_cause_finding(generated) or not is_auto_date_root_cause_finding(mq020):
        fail("Generated objects and MQ020 must both identify the Auto Date/Time root cause.")
    if root_cause_grouping(mq022, auto_date_present=False) is not None:
        fail("MQ022 without Auto Date/Time evidence must remain an independent date-table finding.")
    grouped_mq022 = root_cause_grouping(mq022, auto_date_present=True)
    if not grouped_mq022 or grouped_mq022["source"] != AUTO_DATE_ROOT_CAUSE_SOURCE:
        fail("MQ022 must join the Auto Date/Time root cause only when direct evidence exists.")
    if root_cause_grouping({"rule_name": "MQ017: Too many inactive relationships"}, True) is not None:
        fail("Unrelated metadata findings must not be absorbed into the Auto Date/Time root cause.")

    cross_source = grade_recommendation(
        [generated, mq020, mq022],
        "Date handling",
        AUTO_DATE_ROOT_CAUSE_TITLE,
        grouped_mq022["action"],
    )
    if (
        cross_source["recommendation_title"] != AUTO_DATE_ROOT_CAUSE_TITLE
        or cross_source["actionability_status"] != REVIEW_REQUIRED
        or cross_source["recommendation_priority_score"] != 72
    ):
        fail("Cross-source Auto Date/Time evidence must produce one stable P2 review recommendation.")
    cross_source_opportunity = grade_opportunity([generated, mq020, mq022])
    if (
        cross_source_opportunity["actionability_status"] != REVIEW_REQUIRED
        or cross_source_opportunity["priority_score"] != 72
    ):
        fail("The consolidated Auto Date/Time opportunity must retain its stable P2 review grade.")

    informational = grade_recommendation([{
        "finding_text": "Context only.", "technical_evidence": "Observed metadata.",
        "severity": "LOW", "confidence": "HIGH", "change_risk": "LOW",
    }], "Formatting", "Context", None)
    if informational["actionability_status"] != INFORMATIONAL:
        fail("Low-severity context without an action must remain informational.")
    if informational["automation_eligibility"] != "NOT_ELIGIBLE":
        fail("Informational recommendations must never be offered as automation candidates.")

    review_only = grade_recommendation([{
        "finding_text": "Potential formatting issue.",
        "technical_evidence": "Evidence requires confirmation.",
        "recommended_action": "Review and standardize the format.",
        "severity": "HIGH", "confidence": "LOW", "change_risk": "LOW",
    }], "Formatting", "Review formatting", "Review and standardize the format.")
    if review_only["automation_eligibility"] != "MANUAL_REVIEW":
        fail("Review-required recommendations must not be promoted to script candidates.")

    bulk_hygiene = grade_recommendation([{
        "finding_text": "A visible object has no description.",
        "technical_evidence": "Deterministic BPA rule violation.",
        "recommended_action": "Add a business description.",
        "severity": "WARNING", "confidence": "HIGH", "change_risk": "MEDIUM",
    }] * 50, "Maintenance", "Visible objects with no description", "Add descriptions.")
    if bulk_hygiene["recommendation_priority_band"] in {"P1_CRITICAL", "P2_HIGH"}:
        fail("Finding volume must not promote maintenance hygiene into P1/P2 priority.")

    high_risk_unquantified = grade_recommendation([{
        "finding_text": "A structural model issue requires redesign.",
        "technical_evidence": "Deterministic model metadata evidence.",
        "recommended_action": "Redesign and regression-test the model.",
        "severity": "ERROR", "confidence": "HIGH", "change_risk": "HIGH",
    }], "Model structure", "Structural redesign", "Redesign the model.")
    if high_risk_unquantified["actionability_status"] != REVIEW_REQUIRED:
        fail("High-risk structural changes must require review.")
    if high_risk_unquantified["recommendation_priority_band"] != "P2_HIGH":
        fail("Unquantified high-risk design findings must not enter P1.")

    safe_script = grade_recommendation([{
        "finding_text": "A foreign key is visible.",
        "technical_evidence": "The key column is not hidden.",
        "recommended_action": "Hide the foreign key.",
        "severity": "WARNING", "confidence": "HIGH", "change_risk": "MEDIUM",
    }], "Formatting", "Hide foreign keys", "Hide the foreign key.")
    if safe_script["automation_eligibility"] != "SCRIPT_CANDIDATE":
        fail("Explicitly allowlisted metadata changes must remain script candidates.")

    ambiguous_formatting = grade_recommendation([{
        "finding_text": "A column has no data category.",
        "technical_evidence": "The Data Category property is empty.",
        "recommended_action": "Select an appropriate data category.",
        "severity": "WARNING", "confidence": "HIGH", "change_risk": "MEDIUM",
    }], "Formatting", "Add data category for columns", "Select a data category.")
    if ambiguous_formatting["automation_eligibility"] != "MANUAL_REVIEW":
        fail("A broad Formatting category must not imply script eligibility.")

    bulk_opportunity = grade_opportunity([{
        "finding_text": "A visible object has no description.",
        "technical_evidence": "Deterministic BPA rule violation.",
        "recommended_action": "Add a business description.",
        "severity": "WARNING", "confidence": "HIGH", "change_risk": "MEDIUM",
    }] * 50)
    if bulk_opportunity["priority_band"] in {"P1_CRITICAL", "P2_HIGH"}:
        fail("Opportunity priority must remain evidence-based when finding volume is high.")

    summary = summarize_opportunity([
        {
            "finding_text": "Actionable.", "technical_evidence": "Evidence.",
            "recommended_action": "Fix it.", "severity": "HIGH",
            "confidence": "HIGH", "change_risk": "LOW",
        },
        {
            "finding_text": "Context.", "technical_evidence": "Evidence.",
            "severity": "LOW", "confidence": "HIGH", "change_risk": "LOW",
        },
    ], "BPA", "Performance")
    if "1 actionable" not in summary or "1 informational" not in summary:
        fail("Opportunity summaries must expose the actionability mix in plain language.")


def validate_model_quality_rules() -> None:
    def column(name, data_type="string", **extra):
        return {"name": name, "dataType": data_type, **extra}

    customer_columns = [column("CustomerKey", "int64"), column("Name"), column("YearlyIncome", "decimal")]
    wide_columns = [column(f"Number{i}", "int64") for i in range(25)] + [
        column("Product Name"), column("Product Color"), column("Customer Name"),
        column("Sales Territory"), column("Currency"),
    ]
    model_bim = {
        "model": {
            "discourageImplicitMeasures": False,
            "roles": [],
            "perspectives": [],
            "tables": [
                {"name": "vw_AllSales", "columns": wide_columns},
                {"name": "DimCustomer", "columns": customer_columns + [
                    column("YearlyIncomeText", expression='FORMAT([YearlyIncome], "#,##0")'),
                    column("Month Abbr", expression='FORMAT([Birth Date], "mmm")'),
                    column("Birth Date", "dateTime"),
                ]},
                {"name": "DimCustomerCopy", "columns": customer_columns, "partitions": [
                    {"source": {"expression": "DimCustomer"}},
                ]},
                {"name": "FactOrphanEmpty", "columns": [column("Orphan ID", "int64"), column("Orphan Status")]},
                {"name": "STG_TestLoad", "columns": [column("Load ID", "int64")]},
                {"name": "TEMP_Calc", "columns": [column("Value", "int64")]},
                {"name": "Dim_Calendar2", "columns": [column("Date", "dateTime")]},
                {"name": "FactInternetSales", "columns": [
                    column("OrderDateText", expression='FORMAT(DATEVALUE([OrderDateKey]), "dd/MM/yyyy")'),
                    column("SalesAmount_CalcCol", "decimal", expression="[ExtendedAmount] * (1 - [UnitPriceDiscountPct])"),
                    column("ProductName", expression="RELATED(DimProduct[EnglishProductName])"),
                    column("CarrierTrackingNumber"),
                    column("UnitPriceDiscountPct", "double"),
                    column("SalesOrderLineNumber", "int64", summarizeBy="sum"),
                    column("ShipDateKey", "int64"),
                ], "measures": [
                    {"name": "Total Sales Alias", "expression": "[Total Sales Amount]"},
                    {"name": "Sales 2013 Only", "expression": "CALCULATE(SUM(FactInternetSales[SalesAmount]), DimDate[CalendarYear] = 2013)", "formatString": "#,0"},
                    {"name": "Sales All Products", "expression": "CALCULATE(SUM(FactInternetSales[SalesAmount]), FILTER(ALL(DimProduct), DimProduct[ProductKey] >= 0))", "formatString": "#,0"},
                    {"name": "Money Total", "expression": "SUM(FactInternetSales[ExtendedAmount])"},
                    {"name": "Monthly Sales Label", "expression": 'FORMAT([Money Total], "#,0") & " sales"'},
                ]},
                {"name": "FactResellerSales", "columns": [
                    column("SalesAmount", "decimal"), column("ShipDateKey", "int64"),
                ], "measures": [
                    {"name": "Total Sales Amount (2)", "expression": "SUM(FactInternetSales[SalesAmount])", "formatString": "#,0"},
                    {"name": "Reseller Ship Sales", "expression": "CALCULATE([Total Sales Amount], USERELATIONSHIP(FactResellerSales[ShipDateKey], DimDate[DateKey]))", "formatString": "#,0"},
                ]},
                {"name": "DimProduct", "columns": [
                    column("Name", expression="[EnglishProductName]"),
                    column("RandomRank", "double", expression="RAND()"),
                    column("ProductAttributes", expression="CONCATENATE([Style], [Class])"),
                    column("zz_Info", expression='"n/a"'),
                    column("Column9", expression="[ProductKey] + 0"),
                ], "measures": [
                    {"name": "Total Sales Amount", "expression": "SUM(FactInternetSales[SalesAmount])", "formatString": "#,0"},
                ]},
                {"name": "DimDate", "columns": [
                    column("DateKey", "int64"),
                    column("CalendarYear", "int64", summarizeBy="sum"),
                    column("EnglishMonthName"),
                    column("MonthFullName", expression="[EnglishMonthName]"),
                ]},
                {"name": "LocalDateTable_1", "isHidden": True, "columns": [
                    column("Date", "dateTime"), column("Name"),
                    column("YearLabel", expression='FORMAT([Date], "yyyy")'),
                ]},
                {"name": "DateTableTemplate_1", "isHidden": True, "columns": [
                    column("Date", "dateTime"), column("Name"),
                    column("YearLabel", expression='FORMAT([Date], "yyyy")'),
                ]},
            ],
            "relationships": [
                {"fromTable": "FactInternetSales", "fromColumn": "OrderDateText", "toTable": "LocalDateTable_1", "toColumn": "Date", "isActive": True},
                {"fromTable": "FactInternetSales", "fromColumn": "OrderDateText", "toTable": "DimDate", "toColumn": "CalendarYear", "isActive": False},
                {"fromTable": "FactInternetSales", "fromColumn": "ShipDateKey", "toTable": "DimDate", "toColumn": "DateKey", "isActive": False},
                {"fromTable": "FactResellerSales", "fromColumn": "ShipDateKey", "toTable": "DimDate", "toColumn": "DateKey", "isActive": False},
            ],
        }
    }
    vpa_columns = [{
        "table_name": "FactInternetSales", "column_name": "CarrierTrackingNumber",
        "data_type": "String", "cardinality": 18484, "total_size_bytes": 2000000,
    }]
    findings = analyze_model_bim(model_bim, vpa_columns, [])
    detected = {row["rule_code"] for row in findings}
    expected = {f"MQ{number:03d}" for number in range(1, 31)}
    missing = sorted(expected - detected)
    if missing:
        fail(f"Deterministic model-quality fixture missed rules: {missing}")
    if sum(row["rule_code"] == "MQ028" for row in findings) != 1:
        fail("Missing descriptions must be consolidated into one model-level root-cause finding.")
    if sum(row["rule_code"] == "MQ020" for row in findings) != 1:
        fail("Auto Date/Time tables must be consolidated into one model-level root-cause finding.")
    mq009 = [row for row in findings if row["rule_code"] == "MQ009"]
    mq009_objects = {(row["table_name"], row["object_name"]) for row in mq009}
    if mq009_objects != {("DimCustomer", "Name"), ("DimProduct", "Name")}:
        fail(f"MQ009 must locate both visible conflicting columns, found {mq009_objects}.")
    if any(
        "DimCustomerCopy" in row["technical_evidence"] or "LocalDateTable" in row["technical_evidence"]
        for row in mq009
    ):
        fail("MQ009 must not repeat copy-table or generated-date-table root causes.")
    mq011 = [row for row in findings if row["rule_code"] == "MQ011"]
    if len(mq011) != 1 or mq011[0]["object_name"] != "YearlyIncomeText":
        fail("MQ011 must require FORMAT to reference a known numeric column.")
    mq002 = [row for row in findings if row["rule_code"] == "MQ002"]
    if len(mq002) != 1 or mq002[0]["object_name"] != "DimCustomerCopy":
        fail("MQ002 must keep direct copies while excluding generated date-table signatures.")
    mq019 = [row for row in findings if row["rule_code"] == "MQ019"]
    if len(mq019) != 2 or any(row["object_name"] == "Monthly Sales Label" for row in mq019):
        fail("MQ019 must retain numeric measures and exclude intentional text/label measures.")
    mq030 = [row for row in findings if row["rule_code"] == "MQ030"]
    if len(mq030) != 1 or "count=2" not in mq030[0]["technical_evidence"]:
        fail("MQ030 must group unresolved inactive relationships by table pair.")
    if "FactResellerSales" in mq030[0]["technical_evidence"]:
        fail("MQ030 must exclude the specific relationship invoked by USERELATIONSHIP.")

    expected_ap_objects = {
        "MQ004": {
            ("STG_TestLoad", "STG_TestLoad"),
            ("TEMP_Calc", "TEMP_Calc"),
            ("Dim_Calendar2", "Dim_Calendar2"),
        },
        "MQ005": {("FactInternetSales", "OrderDateText")},
        "MQ008": {("DimProduct", "RandomRank")},
        "MQ009": {("DimCustomer", "Name"), ("DimProduct", "Name")},
        "MQ010": {("DimProduct", "ProductAttributes")},
        "MQ011": {("DimCustomer", "YearlyIncomeText")},
    }
    for rule_code, expected_objects in expected_ap_objects.items():
        actual_objects = {
            (row.get("table_name"), row.get("object_name"))
            for row in findings if row["rule_code"] == rule_code
        }
        if not expected_objects.issubset(actual_objects):
            fail(
                f"{rule_code} missed required adverse-model objects: "
                f"{sorted(expected_objects - actual_objects)}"
            )

    classification_bim = {
        "model": {
            "discourageImplicitMeasures": True,
            "roles": [{"name": "Reader"}],
            "perspectives": [{"name": "Default"}],
            "tables": [{
                "name": "Bank_Churn",
                "columns": [
                    column("Age", "int64", description="Customer age"),
                    column("Geography", description="Customer geography"),
                    column("CustomerId", "int64", description="Customer identifier"),
                    column("Surname", description="Customer surname"),
                    column(
                        "GeoRankLegacy",
                        "int64",
                        description="Legacy rank",
                        expression=(
                            "COUNTROWS(FILTER(Bank_Churn, "
                            "Bank_Churn[Geography] = EARLIER(Bank_Churn[Geography]) && "
                            "Bank_Churn[Age] > EARLIER(Bank_Churn[Age])))"
                        ),
                    ),
                    column(
                        "CustomerKeyText",
                        description="Display key",
                        expression='FORMAT([CustomerId], "0") & "-" & [Surname]',
                    ),
                ],
                "measures": [{
                    "name": "Exited Ratio Raw",
                    "description": "Exited customers divided by customers",
                    "expression": "DIVIDE([Exited Customers], [Customers])",
                    "formatString": "0.00",
                }],
            }],
        }
    }
    classification_findings = analyze_model_bim(classification_bim, [], [])
    mq010_objects = {
        row["object_name"] for row in classification_findings if row["rule_code"] == "MQ010"
    }
    if mq010_objects != {"CustomerKeyText"}:
        fail(f"MQ010 must distinguish DAX && from text concatenation: {sorted(mq010_objects)}")
    ratio_findings = [
        row for row in classification_findings
        if row["rule_code"] == "MQ039" and row["object_name"] == "Exited Ratio Raw"
    ]
    if len(ratio_findings) != 1 or ratio_findings[0]["severity"] != "ERROR":
        fail("A DIVIDE ratio with a non-percent format string must produce one MQ039 ERROR finding.")

    structure_bim = {
        "model": {
            "discourageImplicitMeasures": True,
            "roles": [{"name": "Reader"}],
            "perspectives": [{"name": "Default"}],
            "tables": [
                {
                    "name": "vgchartz-2024",
                    "description": "Game sales fact grain",
                    "columns": [
                        *(column(f"metric_{number}", "decimal", description="Metric") for number in range(10)),
                        column("genre", description="Genre"),
                        column("publisher", description="Publisher"),
                        column("console", description="Console"),
                        column("developer", description="Developer"),
                        column("title", description="Game title"),
                    ],
                },
                {
                    "name": "LocalDateTable_release",
                    "isHidden": True,
                    "columns": [column("Date", "dateTime")],
                },
                {
                    "name": "LocalDateTable_update",
                    "isHidden": True,
                    "columns": [column("Date", "dateTime")],
                },
                {
                    "name": "PublisherList",
                    "description": "Calculated publisher list",
                    "columns": [column("publisher", description="Publisher")],
                    "partitions": [{"source": {"expression": "DISTINCT('vgchartz-2024'[publisher])"}}],
                },
            ],
            "relationships": [
                {
                    "fromTable": "vgchartz-2024", "fromColumn": "release_date",
                    "toTable": "LocalDateTable_release", "toColumn": "Date",
                    "isActive": True, "crossFilteringBehavior": "bothDirections",
                },
                {
                    "fromTable": "vgchartz-2024", "fromColumn": "last_update",
                    "toTable": "LocalDateTable_update", "toColumn": "Date",
                    "isActive": True,
                },
            ],
        }
    }
    structure_findings = analyze_model_bim(structure_bim, [], [])
    structure_codes = {row["rule_code"] for row in structure_findings}
    required_structure_codes = {"MQ001", "MQ031", "MQ032", "MQ052"}
    if not required_structure_codes.issubset(structure_codes):
        fail(f"Relationship/flat-model fixture missed: {sorted(required_structure_codes - structure_codes)}")
    if any(
        "unused" in row["finding_text"].lower()
        for row in structure_findings
        if row.get("object_name") == "PublisherList"
    ):
        fail("Metadata-only disconnected-table findings must not assert that PublisherList is unused.")


def validate_m665_acceptance_corpus() -> None:
    path = ROOT / "tests/fixtures/m6_6_5_antipattern_acceptance.json"
    fixture = json.loads(path.read_text(encoding="utf-8"))
    items = fixture["items"]
    item_keys = {(row["model"], row["id"]) for row in items}
    expected_bank_ids = {
        *(f"AP-M{number:02d}" for number in range(1, 10)),
        *(f"AP-C{number:02d}" for number in range(1, 7)),
        *(f"AP-T{number:02d}" for number in range(1, 3)),
        *(f"AP-R{number:02d}" for number in range(1, 3)),
        "AP-E01", "AP-E03", "AP-E04", "AP-E05", "AP-E06", "AP-E07", "AP-E08", "AP-E09",
    }
    expected_video_ids = {f"AP-{number:02d}" for number in range(1, 25)}
    actual_bank_ids = {item_id for model, item_id in item_keys if model == "Bank Customer Churn"}
    actual_video_ids = {item_id for model, item_id in item_keys if model == "Video Game Sales"}

    if fixture["valid_item_count"] != 51 or len(items) != 51 or len(item_keys) != 51:
        fail("M6.6.5 acceptance corpus must contain exactly 51 unique valid items.")
    if actual_bank_ids != expected_bank_ids:
        fail(f"M6.6.5 Bank acceptance IDs differ: {sorted(actual_bank_ids ^ expected_bank_ids)}")
    if actual_video_ids != expected_video_ids:
        fail(f"M6.6.5 Video acceptance IDs differ: {sorted(actual_video_ids ^ expected_video_ids)}")
    if fixture["excluded_items"] != [{
        "model": "Bank Customer Churn",
        "id": "AP-E02",
        "reason": "conflicts with injected Fake_Calendar",
    }]:
        fail("Bank AP-E02 must be the single documented conflicting exclusion.")
    if "AgeGroup" in fixture.get("negative_control_objects", []) or "AgeGroupOrder" in fixture.get(
        "negative_control_objects", []
    ):
        fail("AgeGroup objects must not be hard-coded as M6.6.5 negative controls.")
    if any(not row.get("expected_rules") for row in items):
        fail("Every M6.6.5 acceptance item must declare at least one expected rule.")


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
    validate_model_quality_rules()
    validate_m665_acceptance_corpus()
    validate_no_secrets()
    print(f"Validation passed: {json_count} JSON/notebook/platform files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
