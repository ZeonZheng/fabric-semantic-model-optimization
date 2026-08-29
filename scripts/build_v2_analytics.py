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
            ("high_severity_finding_count", "int64"), ("actionable_recommendation_count", "int64"),
            ("review_required_recommendation_count", "int64"), ("suppressed_finding_count", "int64"),
            ("best_practice_analysis_status", "string"),
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
            ("change_risk", "string"), ("opportunity_summary", "string"),
            ("actionability_status", "string"), ("actionable_finding_count", "int64"),
            ("review_required_finding_count", "int64"), ("suppressed_finding_count", "int64"),
            ("priority_score", "int64"), ("priority_band", "string"),
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
            ("affected_finding_count", "int64"), ("actionable_finding_count", "int64"),
            ("suppressed_finding_count", "int64"), ("actionability_status", "string"),
            ("actionability_reason", "string"), ("recommendation_priority_score", "int64"),
            ("recommendation_priority_band", "string"), ("automation_eligibility", "string"),
            ("why_it_matters", "string"), ("validation_method", "string"),
            ("rollback_guidance", "string"), ("detected_at", "dateTime"),
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
            ("object_scope", "string"), ("display_table_name", "string"),
            ("display_object_name", "string"),
            ("finding_description", "string"), ("recommended_action", "string"),
            ("technical_evidence", "string"), ("estimated_saving_bytes_low", "int64"),
            ("estimated_saving_bytes_high", "int64"), ("change_risk", "string"),
            ("validation_required", "boolean"), ("actionability_status", "string"),
            ("actionability_reason", "string"), ("suppression_reason", "string"),
            ("finding_priority_score", "int64"), ("finding_priority_band", "string"),
            ("detected_at", "dateTime"),
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


CALCULATED_COLUMNS = {
    "semantic_model_optimization_findings": [
        (
            "object_scope",
            """VAR _rawTable = LOWER(COALESCE(semantic_model_optimization_findings[affected_table_name], \"\"))
VAR _rawObject = LOWER(COALESCE(semantic_model_optimization_findings[affected_object_name], \"\"))
VAR _objectType = UPPER(COALESCE(semantic_model_optimization_findings[affected_object_type], \"\"))
VAR _isAutoDate =
    CONTAINSSTRING(_rawTable, \"datetabletemplate_\") ||
    CONTAINSSTRING(_rawTable, \"localdatetable_\") ||
    CONTAINSSTRING(_rawObject, \"datetabletemplate_\") ||
    CONTAINSSTRING(_rawObject, \"localdatetable_\")
RETURN
    SWITCH(
        TRUE(),
        _isAutoDate, \"Auto Date/Time (system)\",
        _objectType IN { \"\", \"MODEL\", \"SEMANTIC MODEL\" }, \"Model-level\",
        \"Authored / imported object\"
    )""",
        ),
        (
            "display_table_name",
            """VAR _rawTable = TRIM(COALESCE(semantic_model_optimization_findings[affected_table_name], \"\"))
VAR _rawObject = TRIM(COALESCE(semantic_model_optimization_findings[affected_object_name], \"\"))
VAR _objectType = UPPER(TRIM(COALESCE(semantic_model_optimization_findings[affected_object_type], \"\")))
VAR _objectLooksLikeAutoDate =
    CONTAINSSTRING(LOWER(_rawObject), \"datetabletemplate_\") ||
    CONTAINSSTRING(LOWER(_rawObject), \"localdatetable_\")
RETURN
    SWITCH(
        TRUE(),
        _rawTable <> \"\", _rawTable,
        _objectLooksLikeAutoDate, _rawObject,
        _objectType IN { \"TABLE\", \"CALCULATED TABLE\" } && _rawObject <> \"\", _rawObject,
        \"Not applicable\"
    )""",
        ),
        (
            "display_object_name",
            """VAR _rawObject = TRIM(COALESCE(semantic_model_optimization_findings[affected_object_name], \"\"))
RETURN IF(_rawObject = \"\", \"Not applicable\", _rawObject)""",
        ),
    ],
}

# Direct Lake on SQL tables reject standard-expression calculated columns.
# These locator fields are physical curated columns populated by the scanner.
CALCULATED_COLUMNS = {}


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
    for column_name, expression in CALCULATED_COLUMNS.get(table_name, []):
        expression_lines = expression.splitlines()
        lines.append(f"\tcolumn {column_name} = ```")
        lines.extend(f"\t\t\t{line}" for line in expression_lines)
        lines.extend([
            "\t\t\t```",
            "\t\tdataType: string",
            f"\t\tlineageTag: {lineage('column', table_name, column_name)}",
            "\t\tsummarizeBy: none",
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

\tmeasure 'Actionable recommendations' =
\t\t\tCOALESCE(
\t\t\t\tCALCULATE(
\t\t\t\t\t[Total recommendations],
\t\t\t\t\tsemantic_model_optimization_recommendations[actionability_status] = "ACTIONABLE"
\t\t\t\t),
\t\t\t\t0
\t\t\t)
\t\tformatString: #,0
\t\tdisplayFolder: Recommendations

\tmeasure 'Review required recommendations' =
\t\t\tCOALESCE(
\t\t\t\tCALCULATE(
\t\t\t\t\t[Total recommendations],
\t\t\t\t\tsemantic_model_optimization_recommendations[actionability_status] = "REVIEW_REQUIRED"
\t\t\t\t),
\t\t\t\t0
\t\t\t)
\t\tformatString: #,0
\t\tdisplayFolder: Recommendations

\tmeasure 'Total findings' = COALESCE(COUNTROWS(semantic_model_optimization_findings), 0)
\t\tformatString: #,0
\t\tdisplayFolder: Findings

\tmeasure 'Suppressed findings' =
\t\t\tCOALESCE(
\t\t\t\tCALCULATE(
\t\t\t\t\t[Total findings],
\t\t\t\t\tsemantic_model_optimization_findings[actionability_status] = "SUPPRESSED"
\t\t\t\t),
\t\t\t\t0
\t\t\t)
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

\tmeasure 'Visible evidence' = COALESCE(COUNTROWS(semantic_model_optimization_findings), 0)
\t\tformatString: #,0
\t\tdisplayFolder: Report experience

\tmeasure 'Visible action evidence' =
\t\t\tVAR ActionTitle = SELECTEDVALUE(semantic_model_optimization_recommendations[recommendation_title])
\t\t\tVAR ActionOpportunity = SELECTEDVALUE(semantic_model_optimization_recommendations[opportunity_id])
\t\t\tVAR RootCause =
\t\t\t\tLOOKUPVALUE(
\t\t\t\t\tsemantic_model_optimization_opportunities[opportunity_title],
\t\t\t\t\tsemantic_model_optimization_opportunities[opportunity_id], ActionOpportunity
\t\t\t\t)
\t\t\tRETURN
\t\t\t\tIF(
\t\t\t\t\tISBLANK(ActionTitle) || ActionTitle = RootCause,
\t\t\t\t\t[Visible evidence],
\t\t\t\t\tCALCULATE(
\t\t\t\t\t\t[Visible evidence],
\t\t\t\t\t\tTREATAS({ ActionTitle }, semantic_model_optimization_findings[rule_name])
\t\t\t\t\t)
\t\t\t\t)
\t\tformatString: #,0
\t\tdisplayFolder: Report experience

\tmeasure 'Visible actions' =
\t\t\tCOALESCE(
\t\t\t\tSUMX(
\t\t\t\t\tVALUES(semantic_model_optimization_recommendations[recommendation_id]),
\t\t\t\t\tIF(CALCULATE([Visible action evidence]) > 0, 1, 0)
\t\t\t\t),
\t\t\t\t0
\t\t\t)
\t\tformatString: #,0
\t\tdisplayFolder: Report experience

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

\tmeasure 'Selected analysis context' =
\t\t\tVAR WorkspaceName = SELECTEDVALUE(semantic_models[workspace_name], "All workspaces")
\t\t\tVAR ModelName = SELECTEDVALUE(semantic_models[semantic_model_name], "All semantic models")
\t\t\tVAR AnalysisId = SELECTEDVALUE(semantic_models[latest_analysis_id], "Multiple latest analyses")
\t\t\tVAR AnalysisStatus = SELECTEDVALUE(semantic_models[latest_analysis_status], "Mixed analysis status")
\t\t\tVAR AnalysisAt = SELECTEDVALUE(semantic_models[latest_analysis_at])
\t\t\tVAR AnalysisTimestamp = IF(NOT ISBLANK(AnalysisAt), FORMAT(AnalysisAt, "yyyy-mm-dd HH:mm"), "No completed analysis")
\t\t\tVAR ScannerVersion = SELECTEDVALUE(semantic_models[scanner_version], "Multiple scanner versions")
\t\t\tRETURN
\t\t\t\tWorkspaceName & " · " & ModelName & UNICHAR(10) &
\t\t\t\tAnalysisStatus & " · " & AnalysisTimestamp & " · Scanner " & ScannerVersion & UNICHAR(10) &
\t\t\t\tAnalysisId
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

\tmeasure 'Actionability color' =
\t\t\tSWITCH(
\t\t\t\tSELECTEDVALUE(semantic_model_optimization_recommendations[actionability_status]),
\t\t\t\t"ACTIONABLE", "#D9EAD3", "REVIEW_REQUIRED", "#FCE8B2",
\t\t\t\t"INFORMATIONAL", "#D9EAF7", "SUPPRESSED", "#E5E7EB", "#FFFFFF"
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
        relation_definition = [
            f"relationship {name}",
            f"\tfromColumn: {from_table}.{from_column}",
            f"\ttoColumn: {to_table}.{to_column}",
        ]
        if name in {"opportunity_recommendations", "opportunity_findings"}:
            # Opportunities are the report's root-cause bridge. Bidirectional
            # filtering lets evidence locate its actions and lets each action row
            # resolve the correct root cause for display and drillthrough.
            relation_definition.append("\tcrossFilteringBehavior: bothDirections")
        relation_text.extend([*relation_definition, ""])
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


def field_sum(entity: str, prop: str, display: str) -> dict:
    return {
        "field": {"Aggregation": {
            "Expression": {"Column": {
                "Expression": {"SourceRef": {"Entity": entity}}, "Property": prop,
            }},
            "Function": 0,
        }},
        "queryRef": f"Sum({entity}.{prop})", "nativeQueryRef": display, "displayName": display,
    }


def literal(value: str) -> dict:
    return {"expr": {"Literal": {"Value": repr(value)}}}


def table_formatting(font_size: int = 9) -> tuple[dict, dict]:
    objects = {
        "columnHeaders": [{"properties": {
            "fontColor": {"solid": {"color": literal("#FFFFFF")}},
            "backColor": {"solid": {"color": literal("#243B53")}},
            "fontSize": {"expr": {"Literal": {"Value": f"{font_size}D"}}},
            "autoSizeColumnWidth": {"expr": {"Literal": {"Value": "true"}}},
            "columnAdjustment": literal("growToFit"),
            "wordWrap": {"expr": {"Literal": {"Value": "false"}}},
        }}],
        "values": [{"properties": {
            "backColorPrimary": {"solid": {"color": literal("#FFFFFF")}},
            "backColorSecondary": {"solid": {"color": literal("#F4F7FA")}},
            "fontColorPrimary": {"solid": {"color": literal("#102A43")}},
            "fontColorSecondary": {"solid": {"color": literal("#102A43")}},
            "fontSize": {"expr": {"Literal": {"Value": f"{font_size}D"}}},
            "wordWrap": {"expr": {"Literal": {"Value": "false"}}},
        }}],
    }
    vcos = {"stylePreset": [{"properties": {"name": literal("None")}}]}
    return objects, vcos


def categorical_slicer_filter(entity: str, prop: str, values: list[str], alias: str = "s") -> dict:
    source_column = {
        "Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}
    }
    return {
        "properties": {
            "orientation": {"expr": {"Literal": {"Value": "0D"}}},
            "filter": {
                "filter": {
                    "Version": 2,
                    "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                    "Where": [{
                        "Condition": {
                            "In": {
                                "Expressions": [source_column],
                                "Values": [[{"Literal": {"Value": repr(value)}}] for value in values],
                            }
                        },
                        "Annotations": {
                            "filterExpressionMetadata": {
                                "expressions": [source_column],
                                "decomposedIdentities": {
                                    "values": [
                                        [{"0": [{"Literal": {"Value": repr(value)}}]}]
                                        for value in values
                                    ],
                                    "columns": [{"value": source_column}],
                                },
                                "valueMap": [{"0": value} for value in values],
                            }
                        },
                    }],
                }
            }
        },
    }


def positive_measure_filter(entity: str, prop: str, scope: str, alias: str = "m") -> dict:
    field = {
        "Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}
    }
    scoped_measure = {
        "Measure": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}
    }
    return {
        "name": "Filter" + uuid.uuid5(uuid.NAMESPACE_URL, f"smo-filter/{scope}/{entity}/{prop}").hex[:24],
        "field": field,
        "type": "Advanced",
        "filter": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Where": [{"Condition": {"Comparison": {
                "ComparisonKind": 1,
                "Left": scoped_measure,
                "Right": {"Literal": {"Value": "0L"}},
            }}}],
        },
        "howCreated": "User",
    }


def visual(
    name: str, visual_type: str, x: int, y: int, width: int, height: int,
    roles: dict, title: str, z: int, *, sync_group: str | None = None,
    conditional_color: tuple[str, str] | None = None,
    conditional_colors: list[tuple[str, str]] | None = None,
    data_bars: list[tuple[str, str]] | None = None,
    sort_by: tuple[str, str] | None = None,
    selected_values: tuple[str, str, list[str]] | None = None,
    measure_filter_gt_zero: tuple[str, str] | None = None,
    show_title: bool = True,
) -> dict:
    title_objects = {
        "title": [{"properties": {
            "show": {"expr": {"Literal": {"Value": "true" if show_title else "false"}}},
            "text": literal(title),
            "fontColor": {"solid": {"color": literal("#102A43")}},
            "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
        }}],
        "general": [{"properties": {
            "altText": literal(title or name.replace("_", " ")),
        }}],
    }
    result = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": name,
        "position": {
            "x": x, "y": y, "z": z,
            "height": max(height, 76) if visual_type == "slicer" else height,
            "width": width, "tabOrder": z,
        },
        "visual": {
            "visualType": visual_type,
            "query": {"queryState": {role: {"projections": projections} for role, projections in roles.items()}},
            "visualContainerObjects": title_objects,
            "drillFilterOtherVisuals": True,
        },
    }
    if measure_filter_gt_zero:
        result["filterConfig"] = {
            "filters": [positive_measure_filter(*measure_filter_gt_zero, scope=name)]
        }
    if sort_by:
        entity, prop = sort_by
        result["visual"]["query"]["sortDefinition"] = {
            "sort": [{
                "field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
                "direction": "Descending",
            }],
            "isDefaultSort": False,
        }
    if visual_type == "slicer":
        result["visual"]["objects"] = {"data": [{"properties": {"mode": literal("Dropdown")}}]}
        if selected_values:
            entity, prop, values = selected_values
            result["visual"]["objects"]["general"] = [categorical_slicer_filter(entity, prop, values)]
        result["visual"]["visualContainerObjects"]["padding"] = [{"properties": {
            side: {"expr": {"Literal": {"Value": "4D"}}} for side in ("top", "bottom", "left", "right")
        }}]
        if sync_group:
            result["visual"]["syncGroup"] = {
                "groupName": sync_group, "fieldChanges": True, "filterChanges": True,
            }
    elif visual_type == "tableEx":
        objects, vcos = table_formatting()
        result["visual"]["objects"] = objects
        result["visual"]["visualContainerObjects"].update(vcos)
        color_specs = list(conditional_colors or [])
        if conditional_color:
            color_specs.append(conditional_color)
        for query_ref, color_kind in color_specs:
            entity, prop = query_ref.split(".", 1)
            color_rules = {
                "severity": [
                    ("CRITICAL", "#F4CCCC"), ("ERROR", "#F4CCCC"), ("HIGH", "#F4CCCC"),
                    ("WARNING", "#FCE8B2"), ("MEDIUM", "#FCE8B2"),
                    ("INFO", "#D9EAF7"), ("LOW", "#D9EAD3"),
                ],
                "risk": [("HIGH", "#F4CCCC"), ("MEDIUM", "#FCE8B2"), ("LOW", "#D9EAD3")],
                "actionability": [
                    ("ACTIONABLE", "#D9EAD3"), ("REVIEW_REQUIRED", "#FCE8B2"),
                    ("INFORMATIONAL", "#D9EAF7"), ("SUPPRESSED", "#E5E7EB"),
                ],
                "priority": [
                    ("P1_CRITICAL", "#F4CCCC"), ("P2_HIGH", "#F9CB9C"),
                    ("P3_MEDIUM", "#FCE8B2"), ("P4_LOW", "#D9EAF7"),
                ],
                "automation": [
                    ("SCRIPT_CANDIDATE", "#D9EAD3"), ("MANUAL_REVIEW", "#FCE8B2"),
                    ("NOT_ELIGIBLE", "#E5E7EB"), ("NO_AUTOMATION", "#E5E7EB"),
                ],
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
        for query_ref, color in data_bars or []:
            result["visual"]["objects"].setdefault("columnFormatting", []).append({
                "properties": {
                    "dataBars": {
                        "positiveColor": {"solid": {"color": literal(color)}},
                        "negativeColor": {"solid": {"color": literal("#F4CCCC")}},
                        "axisColor": {"solid": {"color": literal("#9FB3C8")}},
                        "reverseDirection": {"expr": {"Literal": {"Value": "false"}}},
                        "hideText": {"expr": {"Literal": {"Value": "false"}}},
                        "totalMatchingOption": {"expr": {"Literal": {"Value": "1L"}}},
                    }
                },
                "selector": {"metadata": query_ref},
            })
    elif visual_type == "cardVisual":
        result["visual"]["objects"] = {
            "value": [{"properties": {
                "fontSize": {"expr": {"Literal": {"Value": "24D"}}},
                "bold": {"expr": {"Literal": {"Value": "true"}}},
                "fontColor": {"solid": {"color": literal("#102A43")}},
            }, "selector": {"id": "default"}}],
            "label": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "fontSize": {"expr": {"Literal": {"Value": "12D"}}},
                "fontColor": {"solid": {"color": literal("#486581")}},
            }, "selector": {"id": "default"}}],
            "outline": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "false"}}},
            }, "selector": {"id": "default"}}],
            "padding": [{"properties": {
                "paddingUniform": {"expr": {"Literal": {"Value": "4L"}}},
            }, "selector": {"id": "default"}}],
            "layout": [{"properties": {
                "paddingUniform": {"expr": {"Literal": {"Value": "4L"}}},
                "topOuterMargin": {"expr": {"Literal": {"Value": "0L"}}},
                "bottomOuterMargin": {"expr": {"Literal": {"Value": "0L"}}},
                "leftOuterMargin": {"expr": {"Literal": {"Value": "0L"}}},
                "rightOuterMargin": {"expr": {"Literal": {"Value": "0L"}}},
            }, "selector": {"id": "default"}}],
            "spacing": [{"properties": {
                "verticalSpacing": {"expr": {"Literal": {"Value": "0L"}}},
            }, "selector": {"id": "default"}}],
            "cardCalloutArea": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "paddingUniform": {"expr": {"Literal": {"Value": "4L"}}},
                "rectangleRoundedCurve": {"expr": {"Literal": {"Value": "6L"}}},
                "backgroundFillColor": {"solid": {"color": literal("#F4F7FA")}},
                "backgroundTransparency": {"expr": {"Literal": {"Value": "0D"}}},
            }}],
        }
        result["visual"]["visualContainerObjects"].update({
            "background": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": literal("#FFFFFF")}},
                "transparency": {"expr": {"Literal": {"Value": "0D"}}},
            }}],
            "padding": [{"properties": {
                side: {"expr": {"Literal": {"Value": "0D"}}}
                for side in ("top", "bottom", "left", "right")
            }}],
        })
    else:
        result["visual"]["visualContainerObjects"]["background"] = [{"properties": {
            "show": {"expr": {"Literal": {"Value": "true"}}},
            "color": {"solid": {"color": literal("#FFFFFF")}},
            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
        }}]
    return result


def textbox(name: str, x: int, y: int, width: int, height: int, lines: list[tuple[str, str, str]], z: int) -> dict:
    paragraphs = []
    for value, size, color in lines:
        paragraphs.append({
            "textRuns": [{"value": value, "textStyle": {
                "fontFamily": "Segoe UI", "fontSize": size, "color": color,
            }}],
            "horizontalTextAlignment": "left",
        })
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": height, "width": width, "tabOrder": z},
        "visual": {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
            "visualContainerObjects": {
                "general": [{"properties": {"altText": literal("Page title: " + lines[0][0])}}],
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "padding": [{"properties": {
                    side: {"expr": {"Literal": {"Value": "0D"}}}
                    for side in ("top", "bottom", "left", "right")
                }}],
            },
        },
    }


def page_navigator(z: int = 500) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": "page_navigator",
        "position": {"x": 24, "y": 16, "z": z, "height": 40, "width": 1232, "tabOrder": z},
        "visual": {
            "visualType": "pageNavigator",
            "objects": {
                "pages": [{"properties": {
                    "showHiddenPages": {"expr": {"Literal": {"Value": "false"}}},
                    "showTooltipPages": {"expr": {"Literal": {"Value": "false"}}},
                    "showByDefault": {"expr": {"Literal": {"Value": "true"}}},
                }}],
                "layout": [{"properties": {
                    "orientation": {"expr": {"Literal": {"Value": "0D"}}},
                    "rowCount": {"expr": {"Literal": {"Value": "1L"}}},
                    "cellPadding": {"expr": {"Literal": {"Value": "4L"}}},
                }}],
            },
            "visualContainerObjects": {
                "general": [{"properties": {"altText": literal("Navigate report pages")}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "padding": [{"properties": {
                    side: {"expr": {"Literal": {"Value": "0D"}}}
                    for side in ("top", "bottom", "left", "right")
                }}],
            },
        },
    }


def action_button(name: str, label: str, action_type: str, x: int, y: int, width: int, height: int, z: int) -> dict:
    text_properties = {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "text": literal(label),
        "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
        "bold": {"expr": {"Literal": {"Value": "true"}}},
        "fontColor": {"solid": {"color": literal("#102A43")}},
    }
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": height, "width": width, "tabOrder": z},
        "visual": {
            "visualType": "actionButton",
            "objects": {"text": [
                {"properties": text_properties},
                {"properties": text_properties, "selector": {"id": "default"}},
            ]},
            "visualContainerObjects": {
                "general": [{"properties": {"altText": literal(label)}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "visualLink": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "type": literal(action_type),
                    "enabledTooltip": literal(label),
                }}],
            },
        },
    }


def global_slicers(z: int = 1000) -> list[dict]:
    models = "semantic_models"
    return [
        visual("workspace_filter", "slicer", 496, 64, 232, 80,
               {"Values": [field_column(models, "workspace_name", "Workspace")]},
               "Workspace", z, sync_group="SMO_Workspace"),
        visual("semantic_model_filter", "slicer", 744, 64, 232, 80,
               {"Values": [field_column(models, "semantic_model_name", "Semantic model")]},
               "Model · validation preset", z + 1, sync_group="SMO_SemanticModel",
               selected_values=(models, "semantic_model_name", ["SMO_Optimization1"])),
        visual("analysis_filter", "slicer", 992, 64, 264, 80,
               {"Values": [field_column(models, "latest_analysis_id", "Latest analysis ID")]},
               "Latest analysis ID", z + 2, sync_group="SMO_Analysis"),
    ]


def analysis_context_bar(z: int = 1100) -> dict:
    models = "semantic_models"
    return visual("selected_scope", "tableEx", 24, 144, 1232, 56, {"Values": [
        field_column(models, "workspace_name", "Workspace"),
        field_column(models, "semantic_model_name", "Model"),
        field_column(models, "latest_analysis_status", "Status"),
        field_column(models, "latest_analysis_at", "Completed"),
        field_column(models, "scanner_version", "Scanner"),
        field_column(models, "latest_analysis_id", "Analysis ID"),
    ]}, "Current analysis scope", z, show_title=False)


def report_header(title: str, subtitle: str) -> list[dict]:
    return [
        page_navigator(),
        textbox("page_title", 24, 64, 448, 72, [
            (title, "20px", "#102A43"),
            (subtitle, "11px", "#486581"),
        ], 600),
        *global_slicers(),
        analysis_context_bar(),
    ]


def object_slicer(name: str, prop: str, title: str, y: int, z: int, *, sync_group: str | None = None) -> dict:
    findings = "semantic_model_optimization_findings"
    return visual(name, "slicer", 24, y, 232, 76,
                  {"Values": [field_column(findings, prop, title)]}, title, z,
                  sync_group=sync_group, show_title=False)


def compact_slicer(
    name: str, entity: str, prop: str, title: str, y: int, z: int,
    *, sync_group: str | None = None,
    selected_values: tuple[str, str, list[str]] | None = None,
    x: int = 24, width: int = 232,
) -> dict:
    return visual(name, "slicer", x, y, width, 76,
                  {"Values": [field_column(entity, prop, title)]}, title, z,
                  sync_group=sync_group, selected_values=selected_values, show_title=False)


def drillthrough_config(fields: list[tuple[str, str]], *, hidden: bool = False) -> dict:
    filters = []
    parameters = []
    for index, (entity, prop) in enumerate(fields):
        filter_name = "Filter" + uuid.uuid5(
            uuid.NAMESPACE_URL, f"smo-drillthrough/{index}/{entity}/{prop}"
        ).hex[:24]
        field = {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}
        filters.append({
            "name": filter_name, "field": field, "type": "Categorical", "howCreated": "Drillthrough",
        })
        parameters.append({
            "name": f"Param_{filter_name}", "boundFilter": filter_name, "fieldExpr": field,
        })
    return {
        **({"visibility": "HiddenInViewMode"} if hidden else {}),
        "filterConfig": {"filters": filters},
        "pageBinding": {
            "name": "Pod", "type": "Drillthrough", "parameters": parameters,
            "acceptsFilterContext": "Default",
        },
    }


def write_page(
    page_name: str, display_name: str, visuals: list[dict], *, height: int = 720,
    visual_interactions: list[dict] | None = None, **page_properties: object,
) -> None:
    page = PAGES / page_name
    (page / "visuals").mkdir(parents=True)
    page_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.3.0/schema.json",
        "name": page_name, "displayName": display_name, "displayOption": "FitToPage", "height": height, "width": 1280,
        **({"visualInteractions": visual_interactions} if visual_interactions else {}),
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

    write_page("overview", "Start here", report_header(
        "What should I fix first?",
        "Read the four KPIs, then right-click a Priority or Decision row to drill into Review issues.",
    ) + [
        visual("optimization_kpis", "cardVisual", 24, 216, 1232, 112, {"Data": [
            field_measure("Total opportunities", "Root causes"),
            field_measure("Total recommendations", "Actions"),
            field_measure("High findings", "High-severity evidence"),
            field_measure("Review required recommendations", "Need review"),
        ]}, "", 2000, show_title=False),
        visual("priority_summary", "tableEx", 24, 344, 1232, 352, {"Values": [
            field_column(opportunities, "priority_band", "Priority"),
            field_column(opportunities, "actionability_status", "Decision"),
            field_measure("Total opportunities", "Root causes"),
            field_measure("Visible evidence", "Evidence"),
            field_measure("Visible actions", "Actions"),
        ]}, "Priority summary — right-click a row for the filtered review workbench", 3000,
               conditional_colors=[
                   (f"{opportunities}.priority_band", "priority"),
                   (f"{opportunities}.actionability_status", "actionability"),
               ],
               data_bars=[
                   ("Metrics.Visible evidence", "#6C8EBF"),
                   ("Metrics.Visible actions", "#76A5AF"),
               ],
               measure_filter_gt_zero=("Metrics", "Visible evidence")),
    ])

    review_visuals = report_header(
        "Which issue should I fix, and what proves it?",
        "Select one root-cause row. Actions and Evidence update together; object locators apply to all three sections.",
    ) + [
        compact_slicer("object_scope_slicer", findings, "object_scope", "Object category", 216, 2000,
                       x=24, width=192),
        compact_slicer("object_type_slicer", findings, "affected_object_type", "Object type", 216, 2001,
                       x=232, width=192),
        compact_slicer("table_slicer", findings, "display_table_name", "Affected table", 216, 2002,
                       x=440, width=192),
        compact_slicer("object_slicer", findings, "display_object_name", "Affected object", 216, 2003,
                       x=648, width=192),
        compact_slicer("domain_slicer", findings, "optimization_domain", "Area / domain", 216, 2004,
                       x=856, width=192),
        compact_slicer("severity_slicer", findings, "severity", "Severity", 216, 2005,
                       x=1064, width=192),
        visual("issues_table", "tableEx", 24, 308, 1232, 216, {"Values": [
            field_column(opportunities, "priority_band", "Priority"),
            field_column(opportunities, "actionability_status", "Decision"),
            field_column(opportunities, "opportunity_title", "Root cause"),
            field_column(opportunities, "optimization_domain", "Area / domain"),
            field_column(opportunities, "highest_severity", "Severity"),
            field_column(opportunities, "change_risk", "Risk"),
            field_measure("Visible evidence", "Visible evidence"),
            field_measure("Visible actions", "Visible actions"),
            field_column(opportunities, "opportunity_id", "Key · control"),
        ]},
               "1 · Issues — select one root cause; counts reflect the current object filters", 3000,
               conditional_colors=[
                   (f"{opportunities}.priority_band", "priority"),
                   (f"{opportunities}.actionability_status", "actionability"),
                   (f"{opportunities}.highest_severity", "severity"),
                   (f"{opportunities}.change_risk", "risk"),
               ],
               data_bars=[
                   ("Metrics.Visible evidence", "#6C8EBF"),
                   ("Metrics.Visible actions", "#76A5AF"),
               ],
               sort_by=(opportunities, "priority_score"),
               measure_filter_gt_zero=("Metrics", "Visible evidence")),
        visual("actions_table", "tableEx", 24, 540, 1232, 248, {"Values": [
            field_column(recommendations, "recommendation_title", "Action"),
            field_column(recommendations, "why_it_matters", "Why it matters"),
            field_column(recommendations, "recommended_action", "Recommended action"),
            field_column(recommendations, "validation_method", "Validation method"),
            field_column(recommendations, "rollback_guidance", "Rollback guidance"),
            field_column(recommendations, "change_risk", "Risk"),
            field_column(recommendations, "automation_eligibility", "Automation"),
            field_measure("Visible action evidence", "Visible evidence"),
        ]},
               "2 · Actions — rationale, implementation, validation, and rollback are inline", 4000,
               conditional_colors=[
                   (f"{recommendations}.change_risk", "risk"),
                   (f"{recommendations}.automation_eligibility", "automation"),
               ],
               data_bars=[("Metrics.Visible action evidence", "#6C8EBF")],
               sort_by=(recommendations, "recommendation_priority_score"),
               measure_filter_gt_zero=("Metrics", "Visible action evidence")),
        visual("evidence_table", "tableEx", 24, 804, 1232, 252, {"Values": [
            field_column(findings, "severity", "Severity"),
            field_column(findings, "object_scope", "Object category"),
            field_column(findings, "affected_object_type", "Object type"),
            field_column(findings, "display_table_name", "Affected table"),
            field_column(findings, "display_object_name", "Affected object"),
            field_column(findings, "finding_source", "Source"),
            field_column(findings, "rule_name", "Rule"),
            field_column(findings, "finding_description", "Finding"),
            field_column(findings, "technical_evidence", "Technical evidence"),
        ]},
               "3 · Evidence — preserved raw descriptions and technical evidence", 5000,
               conditional_colors=[(f"{findings}.severity", "severity")],
               sort_by=(findings, "finding_priority_score")),
    ]

    review_interactions = [
        {"source": "issues_table", "target": "actions_table", "type": "DataFilter"},
        {"source": "issues_table", "target": "evidence_table", "type": "DataFilter"},
        {"source": "actions_table", "target": "evidence_table", "type": "NoFilter"},
        {"source": "evidence_table", "target": "actions_table", "type": "NoFilter"},
    ]
    write_page(
        "opportunities", "Review issues", review_visuals, height=1080,
        visual_interactions=review_interactions,
        **drillthrough_config([
            (opportunities, "priority_band"),
            (opportunities, "actionability_status"),
        ]),
    )

    write_page("storage", "Storage", report_header(
        "Which tables and columns consume model storage?",
        "Storage is a separate analysis lens. Use the table filter to isolate one part of the model.",
    ) + [
        visual("storage_table_slicer", "slicer", 24, 216, 232, 80,
               {"Values": [field_column(storage, "table_name", "Table")]}, "Table", 2000),
        visual("top_columns", "clusteredBarChart", 280, 216, 456, 216,
               {"Category": [field_column(storage, "column_name", "Column")], "Y": [field_measure("Total column storage MB", "Storage MB")]},
               "Largest columns", 2001),
        visual("top_tables", "clusteredBarChart", 752, 216, 504, 216,
               {"Category": [field_column(table_storage, "table_name", "Table")], "Y": [field_sum(table_storage, "total_size_bytes", "Total bytes")]},
               "Largest tables", 2002),
        visual("storage_table", "tableEx", 24, 448, 1232, 248, {"Values": [
            field_column(storage, "table_name", "Table"), field_column(storage, "column_name", "Column"),
            field_column(storage, "data_type", "Data type"), field_column(storage, "encoding", "Encoding"),
            field_column(storage, "cardinality", "Cardinality"), field_column(storage, "total_size_bytes", "Total bytes"),
            field_column(storage, "percentage_of_semantic_model_size", "% of model"),
        ]}, "Column storage evidence", 3000),
    ])

    (PAGES / "pages.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": ["overview", "opportunities", "storage"],
        "activePageName": "overview",
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_model()
    write_report()
