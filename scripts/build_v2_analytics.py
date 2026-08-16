#!/usr/bin/env python3
"""Build the V2 Direct Lake semantic model and five-page PBIR report."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/SMO_Analytics_SM.SemanticModel/definition"
TABLES = MODEL / "tables"
REPORT = ROOT / "src/SMO_Analytics_Report.Report/definition"
PAGES = REPORT / "pages"


TABLE_DEFINITIONS = {
    "semantic_models": {
        "schema": "semantic_model_metadata", "entity": "semantic_models", "key": "semantic_model_id",
        "columns": [
            ("semantic_model_id", "string"), ("workspace_id", "string"), ("workspace_name", "string"),
            ("semantic_model_name", "string"), ("capacity_id", "string"), ("capacity_name", "string"),
            ("storage_mode", "string"), ("semantic_model_size_bytes", "int64"),
            ("latest_analysis_id", "string"), ("latest_analysis_status", "string"),
            ("latest_analysis_at", "dateTime"), ("scanner_version", "string"),
        ],
    },
    "semantic_model_analysis_runs": {
        "schema": "analysis_control", "entity": "semantic_model_analysis_runs", "key": None,
        "columns": [
            ("analysis_id", "string"), ("workspace_id", "string"), ("workspace_name", "string"),
            ("semantic_model_id", "string"), ("semantic_model_name", "string"), ("scanner_version", "string"),
            ("analysis_profile", "string"), ("analysis_status", "string"),
            ("permission_precheck_status", "string"), ("best_practice_analysis_status", "string"),
            ("storage_analysis_status", "string"), ("refresh_history_status", "string"),
            ("object_usage_analysis_status", "string"), ("direct_lake_analysis_status", "string"),
            ("item_access_snapshot_status", "string"), ("finding_count", "int64"),
            ("started_at", "dateTime"), ("completed_at", "dateTime"),
            ("duration_seconds", "double"), ("error_details", "string"),
        ],
    },
    "semantic_model_optimization_overview": {
        "schema": "semantic_model_optimization",
        "entity": "semantic_model_optimization_overview",
        "key": "semantic_model_id",
        "columns": [
            ("analysis_id", "string"), ("workspace_id", "string"), ("workspace_name", "string"),
            ("semantic_model_id", "string"), ("semantic_model_name", "string"), ("storage_mode", "string"),
            ("analysis_status", "string"), ("analysis_completed_at", "dateTime"), ("scanner_version", "string"),
            ("semantic_model_size_bytes", "int64"), ("optimization_opportunity_count", "int64"),
            ("optimization_recommendation_count", "int64"), ("optimization_finding_count", "int64"),
            ("high_severity_finding_count", "int64"), ("best_practice_analysis_status", "string"),
            ("storage_analysis_status", "string"), ("refresh_history_status", "string"),
            ("refresh_history_record_count", "int64"), ("object_usage_analysis_status", "string"),
            ("object_usage_observation_count", "int64"), ("direct_lake_analysis_status", "string"),
            ("direct_lake_observation_count", "int64"), ("item_access_snapshot_status", "string"),
            ("item_access_record_count", "int64"), ("data_availability_explanation", "string"),
        ],
    },
    "semantic_model_optimization_opportunities": {
        "schema": "semantic_model_optimization", "entity": "semantic_model_optimization_opportunities", "key": "opportunity_id",
        "columns": [
            ("opportunity_id", "string"), ("analysis_id", "string"), ("workspace_name", "string"),
            ("semantic_model_id", "string"), ("semantic_model_name", "string"), ("opportunity_title", "string"),
            ("optimization_domain", "string"), ("finding_source", "string"), ("highest_severity", "string"),
            ("finding_count", "int64"), ("recommendation_count", "int64"),
            ("estimated_saving_bytes_low", "int64"), ("estimated_saving_bytes_high", "int64"),
            ("change_risk", "string"), ("opportunity_summary", "string"), ("priority_score", "int64"),
            ("detected_at", "dateTime"),
        ],
    },
    "semantic_model_optimization_recommendations": {
        "schema": "semantic_model_optimization", "entity": "semantic_model_optimization_recommendations", "key": "recommendation_id",
        "columns": [
            ("recommendation_id", "string"), ("opportunity_id", "string"), ("analysis_id", "string"), ("workspace_name", "string"),
            ("semantic_model_id", "string"), ("semantic_model_name", "string"), ("recommendation_title", "string"),
            ("optimization_domain", "string"), ("recommended_action", "string"), ("change_risk", "string"),
            ("validation_required", "boolean"), ("estimated_saving_bytes_low", "int64"),
            ("estimated_saving_bytes_high", "int64"), ("finding_source", "string"),
            ("affected_finding_count", "int64"), ("detected_at", "dateTime"),
        ],
    },
    "semantic_model_optimization_findings": {
        "schema": "semantic_model_optimization", "entity": "semantic_model_optimization_findings", "key": "finding_id",
        "columns": [
            ("finding_id", "string"), ("opportunity_id", "string"), ("analysis_id", "string"), ("workspace_name", "string"),
            ("semantic_model_id", "string"), ("semantic_model_name", "string"), ("finding_source", "string"),
            ("optimization_domain", "string"), ("rule_name", "string"), ("severity", "string"),
            ("confidence", "string"), ("impact_area", "string"), ("affected_object_type", "string"),
            ("affected_table_name", "string"), ("affected_object_name", "string"),
            ("finding_description", "string"), ("recommended_action", "string"),
            ("technical_evidence", "string"), ("estimated_saving_bytes_low", "int64"),
            ("estimated_saving_bytes_high", "int64"), ("change_risk", "string"),
            ("validation_required", "boolean"), ("detected_at", "dateTime"),
        ],
    },
    "semantic_model_column_storage": {
        "schema": "semantic_model_vertipaq", "entity": "semantic_model_column_storage", "key": "column_storage_record_id",
        "columns": [
            ("column_storage_record_id", "string"), ("analysis_id", "string"), ("workspace_name", "string"),
            ("semantic_model_id", "string"), ("semantic_model_name", "string"), ("table_name", "string"),
            ("column_name", "string"), ("data_type", "string"), ("encoding", "string"),
            ("cardinality", "int64"), ("data_size_bytes", "int64"), ("dictionary_size_bytes", "int64"),
            ("hierarchy_size_bytes", "int64"), ("total_size_bytes", "int64"),
            ("percentage_of_semantic_model_size", "double"), ("detected_at", "dateTime"),
        ],
    },
    "semantic_model_table_storage": {
        "schema": "semantic_model_vertipaq", "entity": "semantic_model_table_storage", "key": "table_storage_record_id",
        "columns": [
            ("table_storage_record_id", "string"), ("analysis_id", "string"), ("workspace_name", "string"),
            ("semantic_model_id", "string"), ("semantic_model_name", "string"), ("table_name", "string"),
            ("row_count", "int64"), ("data_size_bytes", "int64"), ("dictionary_size_bytes", "int64"),
            ("hierarchy_size_bytes", "int64"), ("total_size_bytes", "int64"),
            ("percentage_of_semantic_model_size", "double"), ("detected_at", "dateTime"),
        ],
    },
    "semantic_model_best_practice_rule_findings": {
        "schema": "semantic_model_best_practice", "entity": "semantic_model_best_practice_rule_findings", "key": "best_practice_finding_id",
        "columns": [
            ("best_practice_finding_id", "string"), ("analysis_id", "string"), ("workspace_name", "string"),
            ("semantic_model_id", "string"), ("semantic_model_name", "string"), ("rule_id", "string"),
            ("rule_name", "string"), ("category", "string"), ("severity", "string"),
            ("affected_object_type", "string"), ("affected_table_name", "string"),
            ("affected_object_name", "string"), ("finding_description", "string"),
            ("recommended_action", "string"), ("technical_evidence", "string"),
            ("documentation_url", "string"), ("detected_at", "dateTime"),
        ],
    },
    "semantic_model_optimization_opportunity_recommendation_links": {
        "schema": "semantic_model_optimization", "entity": "semantic_model_optimization_opportunity_recommendation_links", "key": None,
        "columns": [("analysis_id", "string"), ("semantic_model_id", "string"), ("opportunity_id", "string"), ("related_entity_id", "string")],
    },
    "semantic_model_optimization_opportunity_finding_links": {
        "schema": "semantic_model_optimization", "entity": "semantic_model_optimization_opportunity_finding_links", "key": None,
        "columns": [("analysis_id", "string"), ("semantic_model_id", "string"), ("opportunity_id", "string"), ("related_entity_id", "string")],
    },
}


def lineage(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "smo-v2/" + "/".join(parts)))


def tmdl_table(table_name: str, definition: dict) -> str:
    lines = [
        f"table {table_name}",
        f"\tlineageTag: {lineage('table', table_name)}",
        f"\tsourceLineageTag: [{definition['schema']}].[{definition['entity']}]",
        "",
    ]
    for column_name, data_type in definition["columns"]:
        lines.extend([f"\tcolumn {column_name}", f"\t\tdataType: {data_type}"])
        if column_name == definition["key"]:
            lines.append("\t\tisKey")
        if data_type == "dateTime":
            lines.append("\t\tformatString: General Date")
        elif data_type in {"int64", "double"}:
            lines.append("\t\tformatString: #,0.00" if data_type == "double" else "\t\tformatString: #,0")
        lines.extend([
            f"\t\tsourceColumn: {column_name}",
            f"\t\tsourceLineageTag: {column_name}",
            "\t\tsummarizeBy: none" if data_type in {"string", "dateTime", "boolean"} else "\t\tsummarizeBy: sum",
            "",
        ])
    lines.extend([
        f"\tpartition '{definition['entity']}' = entity",
        "\t\tmode: directLake",
        "\t\tsource",
        f"\t\t\tentityName: {definition['entity']}",
        f"\t\t\tschemaName: {definition['schema']}",
        "\t\t\texpressionSource: DatabaseQuery",
        "",
    ])
    return "\n".join(lines)


METRICS = """table Metrics
\tlineageTag: 0cf621e7-94ae-437e-827a-e2c35635a284

\tmeasure 'Models scanned' = COALESCE(DISTINCTCOUNT(semantic_models[semantic_model_id]), 0)
\t\tformatString: #,0
\t\tdisplayFolder: Overview

\tmeasure 'Total opportunities' = COALESCE(COUNTROWS(semantic_model_optimization_opportunities), 0)
\t\tformatString: #,0
\t\tdisplayFolder: Opportunities

\tmeasure 'Total recommendations' = COALESCE(COUNTROWS(semantic_model_optimization_recommendations), 0)
\t\tformatString: #,0
\t\tdisplayFolder: Recommendations

\tmeasure 'Total findings' = COALESCE(COUNTROWS(semantic_model_optimization_findings), 0)
\t\tformatString: #,0
\t\tdisplayFolder: Findings

\tmeasure 'High findings' =
\t\t\tCOALESCE(
\t\t\t\tCALCULATE(
\t\t\t\t\t[Total findings],
\t\t\t\t\tsemantic_model_optimization_findings[severity] IN { "HIGH", "CRITICAL", "ERROR" }
\t\t\t\t),
\t\t\t\t0
\t\t\t)
\t\tformatString: #,0
\t\tdisplayFolder: Findings

\tmeasure 'Columns analyzed' = COALESCE(COUNTROWS(semantic_model_column_storage), 0)
\t\tformatString: #,0
\t\tdisplayFolder: Storage

\tmeasure 'Total column storage MB' = COALESCE(DIVIDE(SUM(semantic_model_column_storage[total_size_bytes]), 1048576), 0)
\t\tformatString: #,0.00
\t\tdisplayFolder: Storage

\tmeasure 'Estimated saving MB low' = COALESCE(DIVIDE(SUM(semantic_model_optimization_findings[estimated_saving_bytes_low]), 1048576), 0)
\t\tformatString: #,0.00
\t\tdisplayFolder: Benefits

\tmeasure 'Estimated saving MB high' = COALESCE(DIVIDE(SUM(semantic_model_optimization_findings[estimated_saving_bytes_high]), 1048576), 0)
\t\tformatString: #,0.00
\t\tdisplayFolder: Benefits

\tmeasure 'Latest analysis at' = MAX(semantic_model_optimization_overview[analysis_completed_at])
\t\tformatString: General Date
\t\tdisplayFolder: Overview

\tmeasure 'Selected scope title' =
\t\t\tVAR WorkspaceName = SELECTEDVALUE(semantic_models[workspace_name], "All workspaces")
\t\t\tVAR ModelName = SELECTEDVALUE(semantic_models[semantic_model_name], "All semantic models")
\t\t\tRETURN WorkspaceName & " · " & ModelName
\t\tdisplayFolder: Report experience

\tmeasure 'Severity color' =
\t\t\tSWITCH(
\t\t\t\tSELECTEDVALUE(semantic_model_optimization_findings[severity]),
\t\t\t\t"CRITICAL", "#A4262C", "ERROR", "#A4262C", "HIGH", "#D13438",
\t\t\t\t"WARNING", "#F59E0B", "MEDIUM", "#F59E0B", "INFO", "#0078D4",
\t\t\t\t"LOW", "#107C10", "#605E5C"
\t\t\t)
\t\tdisplayFolder: Report experience

\tmeasure 'Risk color' =
\t\t\tSWITCH(
\t\t\t\tSELECTEDVALUE(semantic_model_optimization_recommendations[change_risk]),
\t\t\t\t"HIGH", "#D13438", "MEDIUM", "#F59E0B", "LOW", "#107C10", "#605E5C"
\t\t\t)
\t\tdisplayFolder: Report experience
"""


def write_model() -> None:
    shutil.rmtree(TABLES)
    TABLES.mkdir(parents=True)
    for table_name, definition in TABLE_DEFINITIONS.items():
        (TABLES / f"{table_name}.tmdl").write_text(tmdl_table(table_name, definition), encoding="utf-8")
    (TABLES / "Metrics.tmdl").write_text(METRICS, encoding="utf-8")

    refs = [f"ref table {name}" for name in TABLE_DEFINITIONS] + ["ref table Metrics"]
    relationships = [
        ("models_overview", "semantic_model_optimization_overview", "semantic_model_id", "semantic_models", "semantic_model_id"),
        ("models_analysis_runs", "semantic_model_analysis_runs", "semantic_model_id", "semantic_models", "semantic_model_id"),
        ("models_opportunities", "semantic_model_optimization_opportunities", "semantic_model_id", "semantic_models", "semantic_model_id"),
        ("models_bpa_findings", "semantic_model_best_practice_rule_findings", "semantic_model_id", "semantic_models", "semantic_model_id"),
        ("models_column_storage", "semantic_model_column_storage", "semantic_model_id", "semantic_models", "semantic_model_id"),
        ("models_table_storage", "semantic_model_table_storage", "semantic_model_id", "semantic_models", "semantic_model_id"),
        ("opportunity_recommendations", "semantic_model_optimization_recommendations", "opportunity_id", "semantic_model_optimization_opportunities", "opportunity_id"),
        ("opportunity_findings", "semantic_model_optimization_findings", "opportunity_id", "semantic_model_optimization_opportunities", "opportunity_id"),
    ]
    relation_text = []
    for name, from_table, from_column, to_table, to_column in relationships:
        relation_text.extend([
            f"relationship {name}",
            f"\tfromColumn: {from_table}.{from_column}",
            f"\ttoColumn: {to_table}.{to_column}",
            "",
        ])
    model = "\n".join([
        "model Model",
        "\tculture: en-US",
        "\tcollation: Latin1_General_100_BIN2_UTF8",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: en-US",
        "\tdirectLakeBehavior: directLakeOnly",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "annotation PBI_QueryOrder = [\"DatabaseQuery\"]",
        "annotation PBI_ProTooling = [\"WebModelingEdit\",\"RemoteModeling\"]",
        "",
        *refs,
        "",
        *relation_text,
        "ref cultureInfo en-US",
        "",
    ])
    (MODEL / "model.tmdl").write_text(model, encoding="utf-8")


def field_column(entity: str, prop: str, display: str) -> dict:
    return {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}", "nativeQueryRef": display, "displayName": display,
    }


def field_measure(prop: str, display: str) -> dict:
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": "Metrics"}}, "Property": prop}},
        "queryRef": f"Metrics.{prop}", "nativeQueryRef": display, "displayName": display,
    }


def literal(value: str) -> dict:
    return {"expr": {"Literal": {"Value": repr(value)}}}


def table_formatting() -> tuple[dict, dict]:
    objects = {
        "columnHeaders": [{"properties": {
            "fontColor": {"solid": {"color": literal("#FFFFFF")}},
            "backColor": {"solid": {"color": literal("#243B53")}},
            "autoSizeColumnWidth": {"expr": {"Literal": {"Value": "true"}}},
        }}],
        "values": [{"properties": {
            "backColorPrimary": {"solid": {"color": literal("#FFFFFF")}},
            "backColorSecondary": {"solid": {"color": literal("#F4F7FA")}},
            "fontColorPrimary": {"solid": {"color": literal("#102A43")}},
            "fontColorSecondary": {"solid": {"color": literal("#102A43")}},
        }}],
    }
    vcos = {"stylePreset": [{"properties": {"name": literal("None")}}]}
    return objects, vcos


def visual(
    name: str, visual_type: str, x: int, y: int, width: int, height: int,
    roles: dict, title: str, z: int, *, sync_group: str | None = None,
    conditional_color: tuple[str, str] | None = None,
) -> dict:
    title_objects = {"title": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "text": literal(title),
        "fontColor": {"solid": {"color": literal("#102A43")}},
    }}]}
    result = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": height, "width": width, "tabOrder": z},
        "visual": {
            "visualType": visual_type,
            "query": {"queryState": {role: {"projections": projections} for role, projections in roles.items()}},
            "visualContainerObjects": title_objects,
            "drillFilterOtherVisuals": True,
        },
    }
    if visual_type == "slicer":
        result["visual"]["objects"] = {"data": [{"properties": {"mode": literal("Dropdown")}}]}
        result["visual"]["visualContainerObjects"]["padding"] = [{"properties": {
            side: {"expr": {"Literal": {"Value": "8D"}}} for side in ("top", "bottom", "left", "right")
        }}]
        if sync_group:
            result["visual"]["syncGroup"] = {
                "groupName": sync_group, "fieldChanges": True, "filterChanges": True,
            }
    elif visual_type == "tableEx":
        objects, vcos = table_formatting()
        result["visual"]["objects"] = objects
        result["visual"]["visualContainerObjects"].update(vcos)
        if conditional_color:
            query_ref, color_kind = conditional_color
            entity, prop = query_ref.split(".", 1)
            color_rules = {
                "severity": [
                    ("CRITICAL", "#F4CCCC"), ("ERROR", "#F4CCCC"), ("HIGH", "#F4CCCC"),
                    ("WARNING", "#FCE8B2"), ("MEDIUM", "#FCE8B2"),
                    ("INFO", "#D9EAF7"), ("LOW", "#D9EAD3"),
                ],
                "risk": [("HIGH", "#F4CCCC"), ("MEDIUM", "#FCE8B2"), ("LOW", "#D9EAD3")],
            }[color_kind]
            left = {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}
            conditional = {
                "Cases": [{
                    "Condition": {"Comparison": {
                        "ComparisonKind": 0, "Left": left,
                        "Right": {"Literal": {"Value": repr(value)}},
                    }},
                    "Value": {"Literal": {"Value": repr(color)}},
                } for value, color in color_rules],
                "DefaultValue": {"Literal": {"Value": "'#FFFFFF'"}},
            }
            result["visual"]["objects"]["values"].append({
                "properties": {"backColor": {
                    "solid": {"color": {"expr": {"Conditional": conditional}}}
                }},
                "selector": {
                    "data": [{"dataViewWildcard": {"matchingOption": 1}}],
                    "metadata": query_ref,
                },
            })
    else:
        result["visual"]["visualContainerObjects"]["background"] = [{"properties": {
            "show": {"expr": {"Literal": {"Value": "true"}}},
            "color": {"solid": {"color": literal("#FFFFFF")}},
            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
        }}]
    return result


def global_slicers(z: int = 1000) -> list[dict]:
    models = "semantic_models"
    return [
        visual("workspace_filter", "slicer", 30, 22, 260, 88,
               {"Values": [field_column(models, "workspace_name", "Workspace")]},
               "Workspace", z, sync_group="SMO_Workspace"),
        visual("semantic_model_filter", "slicer", 310, 22, 330, 88,
               {"Values": [field_column(models, "semantic_model_name", "Semantic model")]},
               "Semantic model", z + 1, sync_group="SMO_SemanticModel"),
        visual("selected_scope", "cardVisual", 665, 22, 565, 88,
               {"Data": [field_measure("Selected scope title", "Current scope")]},
               "Current report scope", z + 2),
    ]


def drillthrough_config(entity: str, prop: str) -> dict:
    filter_name = "Filter9f9d2c44a76c4b589ea25720"
    field = {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}
    return {
        "visibility": "HiddenInViewMode",
        "filterConfig": {"filters": [{
            "name": filter_name, "field": field, "type": "Categorical", "howCreated": "Drillthrough",
        }]},
        "pageBinding": {"name": "Pod", "type": "Drillthrough", "parameters": [{
            "name": f"Param_{filter_name}", "boundFilter": filter_name, "fieldExpr": field,
        }]},
    }


def write_page(page_name: str, display_name: str, visuals: list[dict], **page_properties: object) -> None:
    page = PAGES / page_name
    (page / "visuals").mkdir(parents=True)
    page_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.3.0/schema.json",
        "name": page_name, "displayName": display_name, "displayOption": "FitToPage", "height": 720, "width": 1280,
        **page_properties,
    }
    (page / "page.json").write_text(json.dumps(page_json, indent=2) + "\n", encoding="utf-8")
    for item in visuals:
        folder = page / "visuals" / item["name"]
        folder.mkdir()
        (folder / "visual.json").write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")


def write_report() -> None:
    shutil.rmtree(PAGES)
    PAGES.mkdir(parents=True)
    overview = "semantic_model_optimization_overview"
    opportunities = "semantic_model_optimization_opportunities"
    recommendations = "semantic_model_optimization_recommendations"
    findings = "semantic_model_optimization_findings"
    storage = "semantic_model_column_storage"
    table_storage = "semantic_model_table_storage"

    write_page("overview", "Optimization overview", global_slicers() + [
        visual("optimization_kpis", "cardVisual", 30, 130, 1200, 110, {"Data": [
            field_measure("Models scanned", "Models scanned"), field_measure("Total opportunities", "Opportunities"),
            field_measure("Total findings", "Findings"), field_measure("High findings", "High findings"),
        ]}, "Current optimization analysis", 2000),
        visual("findings_by_severity", "clusteredColumnChart", 30, 260, 470, 420,
               {"Category": [field_column(findings, "severity", "Severity")], "Y": [field_measure("Total findings", "Findings")]},
               "Findings by severity", 3000),
        visual("analysis_coverage", "tableEx", 520, 260, 710, 420, {"Values": [
            field_column(overview, "semantic_model_name", "Semantic model"), field_column(overview, "analysis_status", "Analysis status"),
            field_column(overview, "refresh_history_status", "Refresh history"), field_column(overview, "object_usage_analysis_status", "Object usage"),
            field_column(overview, "direct_lake_analysis_status", "Direct Lake"),
            field_column(overview, "data_availability_explanation", "Data availability explanation"),
        ]}, "Coverage and explicit data availability", 4000),
    ])

    write_page("opportunities", "Optimization opportunities", global_slicers() + [
        visual("severity_slicer", "slicer", 30, 130, 250, 88,
               {"Values": [field_column(opportunities, "highest_severity", "Severity")]}, "Severity", 2000),
        visual("domain_slicer", "slicer", 300, 130, 360, 88,
               {"Values": [field_column(opportunities, "optimization_domain", "Optimization domain")]}, "Optimization domain", 2001),
        visual("opportunities_table", "tableEx", 30, 240, 1200, 440, {"Values": [
            field_column(opportunities, "opportunity_title", "Opportunity"), field_column(opportunities, "highest_severity", "Severity"),
            field_column(opportunities, "optimization_domain", "Domain"), field_column(opportunities, "finding_count", "Findings"),
            field_column(opportunities, "recommendation_count", "Recommendations"), field_column(opportunities, "change_risk", "Change risk"),
            field_column(opportunities, "opportunity_summary", "Summary"),
        ]}, "Right-click an opportunity to drill through to all related details", 3000),
    ])

    write_page("recommendations", "Recommendations", global_slicers() + [
        visual("risk_slicer", "slicer", 30, 130, 250, 88,
               {"Values": [field_column(recommendations, "change_risk", "Change risk")]}, "Change risk", 2000),
        visual("recommendations_by_domain", "clusteredBarChart", 300, 130, 930, 210,
               {"Category": [field_column(recommendations, "optimization_domain", "Optimization domain")], "Y": [field_measure("Total recommendations", "Recommendations")]},
               "Recommendations by domain", 2001),
        visual("recommendations_table", "tableEx", 30, 365, 1200, 315, {"Values": [
            field_column(recommendations, "recommendation_title", "Recommendation"),
            field_column(recommendations, "recommended_action", "Recommended action"), field_column(recommendations, "change_risk", "Change risk"),
            field_column(recommendations, "validation_required", "Validation required"),
            field_column(recommendations, "affected_finding_count", "Affected findings"),
        ]}, "Recommended actions with risk highlighting", 3000,
               conditional_color=(f"{recommendations}.change_risk", "risk")),
    ])

    write_page("findings", "Detailed findings", global_slicers() + [
        visual("finding_severity_slicer", "slicer", 30, 130, 250, 88,
               {"Values": [field_column(findings, "severity", "Severity")]}, "Severity", 2000),
        visual("findings_by_rule", "clusteredBarChart", 300, 130, 930, 210,
               {"Category": [field_column(findings, "rule_name", "Rule")], "Y": [field_measure("Total findings", "Findings")]},
               "Findings by rule", 2001),
        visual("findings_table", "tableEx", 30, 365, 1200, 315, {"Values": [
            field_column(findings, "severity", "Severity"), field_column(findings, "rule_name", "Rule"),
            field_column(findings, "affected_table_name", "Table"), field_column(findings, "affected_object_name", "Affected object"),
            field_column(findings, "finding_description", "Finding"), field_column(findings, "recommended_action", "Recommended action"),
        ]}, "Affected objects and findings", 3000,
               conditional_color=(f"{findings}.severity", "severity")),
    ])

    write_page("storage", "Storage analysis", global_slicers() + [
        visual("top_columns", "clusteredBarChart", 30, 130, 560, 220,
               {"Category": [field_column(storage, "column_name", "Column")], "Y": [field_measure("Total column storage MB", "Storage MB")]},
               "Largest columns by storage", 2000),
        visual("top_tables", "clusteredBarChart", 610, 130, 620, 220,
               {"Category": [field_column(table_storage, "table_name", "Table")], "Y": [field_column(table_storage, "total_size_bytes", "Total bytes")]},
               "Largest tables by storage", 2001),
        visual("storage_table", "tableEx", 30, 375, 1200, 305, {"Values": [
            field_column(storage, "table_name", "Table"), field_column(storage, "column_name", "Column"),
            field_column(storage, "data_type", "Data type"), field_column(storage, "encoding", "Encoding"),
            field_column(storage, "cardinality", "Cardinality"), field_column(storage, "total_size_bytes", "Total bytes"),
            field_column(storage, "percentage_of_semantic_model_size", "% of model"),
        ]}, "Complete column storage evidence", 3000),
    ])

    write_page("opportunity_detail", "Opportunity details", global_slicers() + [
        visual("opportunity_summary", "tableEx", 30, 130, 1200, 140, {"Values": [
            field_column(opportunities, "opportunity_title", "Opportunity"), field_column(opportunities, "highest_severity", "Severity"),
            field_column(opportunities, "change_risk", "Change risk"), field_column(opportunities, "opportunity_summary", "Summary"),
        ]}, "Selected opportunity", 2000),
        visual("related_recommendations", "tableEx", 30, 290, 1200, 170, {"Values": [
            field_column(recommendations, "recommendation_title", "Recommendation"),
            field_column(recommendations, "recommended_action", "Recommended action"), field_column(recommendations, "change_risk", "Change risk"),
        ]}, "Related recommendations", 3000,
               conditional_color=(f"{recommendations}.change_risk", "risk")),
        visual("related_findings", "tableEx", 30, 480, 1200, 200, {"Values": [
            field_column(findings, "severity", "Severity"), field_column(findings, "rule_name", "Rule"),
            field_column(findings, "affected_object_name", "Affected object"), field_column(findings, "finding_description", "Finding"),
        ]}, "Related detailed findings", 4000,
               conditional_color=(f"{findings}.severity", "severity")),
    ], **drillthrough_config(opportunities, "opportunity_id"))

    (PAGES / "pages.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": ["overview", "opportunities", "recommendations", "findings", "storage", "opportunity_detail"],
        "activePageName": "overview",
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_model()
    write_report()
