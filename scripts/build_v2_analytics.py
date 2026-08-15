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
            ("recommendation_id", "string"), ("analysis_id", "string"), ("workspace_name", "string"),
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
            ("finding_id", "string"), ("analysis_id", "string"), ("workspace_name", "string"),
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

\tmeasure 'Models scanned' = COALESCE(DISTINCTCOUNT(semantic_model_optimization_overview[semantic_model_id]), 0)
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
"""


def write_model() -> None:
    shutil.rmtree(TABLES)
    TABLES.mkdir(parents=True)
    for table_name, definition in TABLE_DEFINITIONS.items():
        (TABLES / f"{table_name}.tmdl").write_text(tmdl_table(table_name, definition), encoding="utf-8")
    (TABLES / "Metrics.tmdl").write_text(METRICS, encoding="utf-8")

    refs = [f"ref table {name}" for name in TABLE_DEFINITIONS] + ["ref table Metrics"]
    relationships = [
        ("overview_opportunities", "semantic_model_optimization_opportunities", "semantic_model_id", "semantic_model_optimization_overview", "semantic_model_id"),
        ("overview_recommendations", "semantic_model_optimization_recommendations", "semantic_model_id", "semantic_model_optimization_overview", "semantic_model_id"),
        ("overview_findings", "semantic_model_optimization_findings", "semantic_model_id", "semantic_model_optimization_overview", "semantic_model_id"),
        ("overview_column_storage", "semantic_model_column_storage", "semantic_model_id", "semantic_model_optimization_overview", "semantic_model_id"),
        ("opportunity_recommendation_bridge", "semantic_model_optimization_opportunity_recommendation_links", "opportunity_id", "semantic_model_optimization_opportunities", "opportunity_id"),
        ("opportunity_finding_bridge", "semantic_model_optimization_opportunity_finding_links", "opportunity_id", "semantic_model_optimization_opportunities", "opportunity_id"),
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


def visual(name: str, visual_type: str, x: int, y: int, width: int, height: int, roles: dict, title: str, z: int) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": height, "width": width, "tabOrder": z},
        "visual": {
            "visualType": visual_type,
            "query": {"queryState": {role: {"projections": projections} for role, projections in roles.items()}},
            "visualContainerObjects": {"title": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": repr(title)}}},
            }}]},
            "drillFilterOtherVisuals": True,
        },
    }


def write_page(page_name: str, display_name: str, visuals: list[dict]) -> None:
    page = PAGES / page_name
    (page / "visuals").mkdir(parents=True)
    (page / "page.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.3.0/schema.json",
        "name": page_name, "displayName": display_name, "displayOption": "FitToPage", "height": 720, "width": 1280,
    }, indent=2) + "\n", encoding="utf-8")
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

    write_page("overview", "Optimization overview", [
        visual("optimization_kpis", "cardVisual", 30, 30, 1200, 130, {"Data": [
            field_measure("Models scanned", "Models scanned"), field_measure("Total opportunities", "Opportunities"),
            field_measure("Total findings", "Findings"), field_measure("High findings", "High findings"),
        ]}, "Current optimization analysis", 1000),
        visual("findings_by_severity", "clusteredColumnChart", 30, 190, 1200, 220, {"Category": [field_column(findings, "severity", "Severity")], "Y": [field_measure("Total findings", "Findings")]}, "Findings by severity", 2000),
        visual("analysis_coverage", "tableEx", 30, 435, 1200, 250, {"Values": [
            field_column(overview, "workspace_name", "Workspace"), field_column(overview, "semantic_model_name", "Semantic model"),
            field_column(overview, "analysis_status", "Analysis status"), field_column(overview, "refresh_history_status", "Refresh history"),
            field_column(overview, "object_usage_analysis_status", "Object usage"), field_column(overview, "direct_lake_analysis_status", "Direct Lake"),
            field_column(overview, "data_availability_explanation", "Data availability explanation"),
        ]}, "Analysis coverage and data availability", 3000),
    ])

    write_page("opportunities", "Optimization opportunities", [
        visual("severity_slicer", "slicer", 30, 30, 280, 120, {"Values": [field_column(opportunities, "highest_severity", "Severity")]}, "Severity", 1000),
        visual("domain_slicer", "slicer", 330, 30, 400, 120, {"Values": [field_column(opportunities, "optimization_domain", "Optimization domain")]}, "Optimization domain", 2000),
        visual("opportunities_table", "tableEx", 30, 175, 1200, 510, {"Values": [
            field_column(opportunities, "semantic_model_name", "Semantic model"), field_column(opportunities, "opportunity_title", "Opportunity"),
            field_column(opportunities, "highest_severity", "Severity"), field_column(opportunities, "optimization_domain", "Domain"),
            field_column(opportunities, "finding_count", "Findings"), field_column(opportunities, "recommendation_count", "Recommendations"),
            field_column(opportunities, "opportunity_summary", "Summary"),
        ]}, "Prioritized optimization opportunities", 3000),
    ])

    write_page("recommendations", "Recommendations", [
        visual("risk_slicer", "slicer", 30, 30, 300, 120, {"Values": [field_column(recommendations, "change_risk", "Change risk")]}, "Change risk", 1000),
        visual("recommendations_by_domain", "clusteredBarChart", 360, 30, 870, 220, {"Category": [field_column(recommendations, "optimization_domain", "Optimization domain")], "Y": [field_measure("Total recommendations", "Recommendations")]}, "Recommendations by domain", 2000),
        visual("recommendations_table", "tableEx", 30, 280, 1200, 405, {"Values": [
            field_column(recommendations, "semantic_model_name", "Semantic model"), field_column(recommendations, "recommendation_title", "Recommendation"),
            field_column(recommendations, "recommended_action", "Recommended action"), field_column(recommendations, "change_risk", "Change risk"),
            field_column(recommendations, "affected_finding_count", "Affected findings"),
        ]}, "Recommended actions", 3000),
    ])

    write_page("findings", "Detailed findings", [
        visual("finding_severity_slicer", "slicer", 30, 30, 300, 120, {"Values": [field_column(findings, "severity", "Severity")]}, "Severity", 1000),
        visual("findings_by_rule", "clusteredBarChart", 360, 30, 870, 220, {"Category": [field_column(findings, "rule_name", "Rule")], "Y": [field_measure("Total findings", "Findings")]}, "Findings by rule", 2000),
        visual("findings_table", "tableEx", 30, 280, 1200, 405, {"Values": [
            field_column(findings, "semantic_model_name", "Semantic model"), field_column(findings, "severity", "Severity"),
            field_column(findings, "rule_name", "Rule"), field_column(findings, "affected_object_name", "Affected object"),
            field_column(findings, "finding_description", "Finding"),
        ]}, "Affected objects and findings", 3000),
    ])

    write_page("storage", "Column storage", [
        visual("storage_model_slicer", "slicer", 30, 30, 300, 120, {"Values": [field_column(storage, "semantic_model_name", "Semantic model")]}, "Semantic model", 1000),
        visual("top_columns", "clusteredBarChart", 360, 30, 870, 220, {"Category": [field_column(storage, "column_name", "Column")], "Y": [field_measure("Total column storage MB", "Storage MB")]}, "Largest columns by storage", 2000),
        visual("storage_table", "tableEx", 30, 280, 1200, 405, {"Values": [
            field_column(storage, "semantic_model_name", "Semantic model"), field_column(storage, "table_name", "Table"),
            field_column(storage, "column_name", "Column"), field_column(storage, "data_type", "Data type"),
            field_column(storage, "cardinality", "Cardinality"), field_column(storage, "total_size_bytes", "Total bytes"),
            field_column(storage, "percentage_of_semantic_model_size", "% of model"),
        ]}, "Complete column storage evidence", 3000),
    ])

    (PAGES / "pages.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": ["overview", "opportunities", "recommendations", "findings", "storage"],
        "activePageName": "overview",
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_model()
    write_report()
