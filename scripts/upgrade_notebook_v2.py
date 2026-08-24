#!/usr/bin/env python3
"""Upgrade the scanner notebook to the AI-friendly V2 current-state contract."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "src/SMO_Optimization_Scanner.Notebook/notebook-content.ipynb"
QUALITY_RULES = ROOT / "scripts/quality_rules.py"


CURATION_CELL = r'''# ---------- V2 AI-friendly current-state consumption contract ----------

# __QUALITY_RULES_SOURCE__

BUSINESS_SCHEMAS = (
    "analysis_control",
    "semantic_model_metadata",
    "semantic_model_vertipaq",
    "semantic_model_best_practice",
    "semantic_model_optimization",
)

OPTIMIZATION_OVERVIEW_SCHEMA = T.StructType([
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("workspace_id", T.StringType()),
    T.StructField("workspace_name", T.StringType()),
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("semantic_model_name", T.StringType()),
    T.StructField("storage_mode", T.StringType()),
    T.StructField("analysis_status", T.StringType()),
    T.StructField("analysis_completed_at", T.TimestampType()),
    T.StructField("scanner_version", T.StringType()),
    T.StructField("semantic_model_size_bytes", T.LongType()),
    T.StructField("optimization_opportunity_count", T.IntegerType()),
    T.StructField("optimization_recommendation_count", T.IntegerType()),
    T.StructField("optimization_finding_count", T.IntegerType()),
    T.StructField("high_severity_finding_count", T.IntegerType()),
    T.StructField("actionable_recommendation_count", T.IntegerType()),
    T.StructField("review_required_recommendation_count", T.IntegerType()),
    T.StructField("suppressed_finding_count", T.IntegerType()),
    T.StructField("best_practice_analysis_status", T.StringType()),
    T.StructField("storage_analysis_status", T.StringType()),
    T.StructField("refresh_history_status", T.StringType()),
    T.StructField("refresh_history_record_count", T.IntegerType()),
    T.StructField("object_usage_analysis_status", T.StringType()),
    T.StructField("object_usage_observation_count", T.IntegerType()),
    T.StructField("direct_lake_analysis_status", T.StringType()),
    T.StructField("direct_lake_observation_count", T.IntegerType()),
    T.StructField("item_access_snapshot_status", T.StringType()),
    T.StructField("item_access_record_count", T.IntegerType()),
    T.StructField("data_availability_explanation", T.StringType()),
])

OPTIMIZATION_OPPORTUNITY_SCHEMA = T.StructType([
    T.StructField("opportunity_id", T.StringType(), False),
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("workspace_name", T.StringType()),
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("semantic_model_name", T.StringType()),
    T.StructField("opportunity_title", T.StringType()),
    T.StructField("optimization_domain", T.StringType()),
    T.StructField("finding_source", T.StringType()),
    T.StructField("highest_severity", T.StringType()),
    T.StructField("finding_count", T.IntegerType()),
    T.StructField("recommendation_count", T.IntegerType()),
    T.StructField("estimated_saving_bytes_low", T.LongType()),
    T.StructField("estimated_saving_bytes_high", T.LongType()),
    T.StructField("change_risk", T.StringType()),
    T.StructField("opportunity_summary", T.StringType()),
    T.StructField("actionability_status", T.StringType()),
    T.StructField("actionable_finding_count", T.IntegerType()),
    T.StructField("review_required_finding_count", T.IntegerType()),
    T.StructField("suppressed_finding_count", T.IntegerType()),
    T.StructField("priority_score", T.IntegerType()),
    T.StructField("priority_band", T.StringType()),
    T.StructField("detected_at", T.TimestampType()),
])

OPTIMIZATION_RECOMMENDATION_SCHEMA = T.StructType([
    T.StructField("recommendation_id", T.StringType(), False),
    T.StructField("opportunity_id", T.StringType(), False),
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("workspace_name", T.StringType()),
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("semantic_model_name", T.StringType()),
    T.StructField("recommendation_title", T.StringType()),
    T.StructField("optimization_domain", T.StringType()),
    T.StructField("recommended_action", T.StringType()),
    T.StructField("change_risk", T.StringType()),
    T.StructField("validation_required", T.BooleanType()),
    T.StructField("estimated_saving_bytes_low", T.LongType()),
    T.StructField("estimated_saving_bytes_high", T.LongType()),
    T.StructField("finding_source", T.StringType()),
    T.StructField("affected_finding_count", T.IntegerType()),
    T.StructField("actionable_finding_count", T.IntegerType()),
    T.StructField("suppressed_finding_count", T.IntegerType()),
    T.StructField("actionability_status", T.StringType()),
    T.StructField("actionability_reason", T.StringType()),
    T.StructField("recommendation_priority_score", T.IntegerType()),
    T.StructField("recommendation_priority_band", T.StringType()),
    T.StructField("automation_eligibility", T.StringType()),
    T.StructField("why_it_matters", T.StringType()),
    T.StructField("validation_method", T.StringType()),
    T.StructField("rollback_guidance", T.StringType()),
    T.StructField("detected_at", T.TimestampType()),
])

OPTIMIZATION_FINDING_SCHEMA = T.StructType([
    T.StructField("finding_id", T.StringType(), False),
    T.StructField("opportunity_id", T.StringType(), False),
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("workspace_name", T.StringType()),
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("semantic_model_name", T.StringType()),
    T.StructField("finding_source", T.StringType()),
    T.StructField("optimization_domain", T.StringType()),
    T.StructField("rule_name", T.StringType()),
    T.StructField("severity", T.StringType()),
    T.StructField("confidence", T.StringType()),
    T.StructField("impact_area", T.StringType()),
    T.StructField("affected_object_type", T.StringType()),
    T.StructField("affected_table_name", T.StringType()),
    T.StructField("affected_object_name", T.StringType()),
    T.StructField("finding_description", T.StringType()),
    T.StructField("recommended_action", T.StringType()),
    T.StructField("technical_evidence", T.StringType()),
    T.StructField("estimated_saving_bytes_low", T.LongType()),
    T.StructField("estimated_saving_bytes_high", T.LongType()),
    T.StructField("change_risk", T.StringType()),
    T.StructField("validation_required", T.BooleanType()),
    T.StructField("actionability_status", T.StringType()),
    T.StructField("actionability_reason", T.StringType()),
    T.StructField("suppression_reason", T.StringType()),
    T.StructField("finding_priority_score", T.IntegerType()),
    T.StructField("finding_priority_band", T.StringType()),
    T.StructField("detected_at", T.TimestampType()),
])

OPTIMIZATION_LINK_SCHEMA = T.StructType([
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("opportunity_id", T.StringType(), False),
    T.StructField("related_entity_id", T.StringType(), False),
])

COLUMN_STORAGE_SCHEMA = T.StructType([
    T.StructField("column_storage_record_id", T.StringType(), False),
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("workspace_name", T.StringType()),
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("semantic_model_name", T.StringType()),
    T.StructField("table_name", T.StringType()),
    T.StructField("column_name", T.StringType()),
    T.StructField("data_type", T.StringType()),
    T.StructField("encoding", T.StringType()),
    T.StructField("cardinality", T.LongType()),
    T.StructField("data_size_bytes", T.LongType()),
    T.StructField("dictionary_size_bytes", T.LongType()),
    T.StructField("hierarchy_size_bytes", T.LongType()),
    T.StructField("total_size_bytes", T.LongType()),
    T.StructField("percentage_of_semantic_model_size", T.DoubleType()),
    T.StructField("detected_at", T.TimestampType()),
])

ANALYSIS_RUN_SCHEMA = T.StructType([
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("workspace_id", T.StringType(), False),
    T.StructField("workspace_name", T.StringType()),
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("semantic_model_name", T.StringType()),
    T.StructField("scanner_version", T.StringType()),
    T.StructField("analysis_profile", T.StringType()),
    T.StructField("analysis_status", T.StringType()),
    T.StructField("permission_precheck_status", T.StringType()),
    T.StructField("best_practice_analysis_status", T.StringType()),
    T.StructField("storage_analysis_status", T.StringType()),
    T.StructField("refresh_history_status", T.StringType()),
    T.StructField("object_usage_analysis_status", T.StringType()),
    T.StructField("direct_lake_analysis_status", T.StringType()),
    T.StructField("item_access_snapshot_status", T.StringType()),
    T.StructField("finding_count", T.IntegerType()),
    T.StructField("started_at", T.TimestampType()),
    T.StructField("completed_at", T.TimestampType()),
    T.StructField("duration_seconds", T.DoubleType()),
    T.StructField("error_details", T.StringType()),
])

SEMANTIC_MODEL_SCHEMA = T.StructType([
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("workspace_id", T.StringType(), False),
    T.StructField("workspace_name", T.StringType()),
    T.StructField("semantic_model_name", T.StringType()),
    T.StructField("capacity_id", T.StringType()),
    T.StructField("capacity_name", T.StringType()),
    T.StructField("storage_mode", T.StringType()),
    T.StructField("semantic_model_size_bytes", T.LongType()),
    T.StructField("latest_analysis_id", T.StringType()),
    T.StructField("latest_analysis_status", T.StringType()),
    T.StructField("latest_analysis_at", T.TimestampType()),
    T.StructField("scanner_version", T.StringType()),
])

BEST_PRACTICE_FINDING_SCHEMA = T.StructType([
    T.StructField("best_practice_finding_id", T.StringType(), False),
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("workspace_name", T.StringType()),
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("semantic_model_name", T.StringType()),
    T.StructField("rule_id", T.StringType()),
    T.StructField("rule_name", T.StringType()),
    T.StructField("category", T.StringType()),
    T.StructField("severity", T.StringType()),
    T.StructField("affected_object_type", T.StringType()),
    T.StructField("affected_table_name", T.StringType()),
    T.StructField("affected_object_name", T.StringType()),
    T.StructField("finding_description", T.StringType()),
    T.StructField("recommended_action", T.StringType()),
    T.StructField("technical_evidence", T.StringType()),
    T.StructField("documentation_url", T.StringType()),
    T.StructField("detected_at", T.TimestampType()),
])

TABLE_STORAGE_SCHEMA = T.StructType([
    T.StructField("table_storage_record_id", T.StringType(), False),
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("workspace_name", T.StringType()),
    T.StructField("semantic_model_id", T.StringType(), False),
    T.StructField("semantic_model_name", T.StringType()),
    T.StructField("table_name", T.StringType()),
    T.StructField("row_count", T.LongType()),
    T.StructField("data_size_bytes", T.LongType()),
    T.StructField("dictionary_size_bytes", T.LongType()),
    T.StructField("hierarchy_size_bytes", T.LongType()),
    T.StructField("total_size_bytes", T.LongType()),
    T.StructField("percentage_of_semantic_model_size", T.DoubleType()),
    T.StructField("detected_at", T.TimestampType()),
])

CURATED_TABLES = {
    "analysis_runs": ("analysis_control", "semantic_model_analysis_runs", ANALYSIS_RUN_SCHEMA),
    "semantic_models": ("semantic_model_metadata", "semantic_models", SEMANTIC_MODEL_SCHEMA),
    "best_practice_findings": ("semantic_model_best_practice", "semantic_model_best_practice_rule_findings", BEST_PRACTICE_FINDING_SCHEMA),
    "overview": ("semantic_model_optimization", "semantic_model_optimization_overview", OPTIMIZATION_OVERVIEW_SCHEMA),
    "opportunities": ("semantic_model_optimization", "semantic_model_optimization_opportunities", OPTIMIZATION_OPPORTUNITY_SCHEMA),
    "recommendations": ("semantic_model_optimization", "semantic_model_optimization_recommendations", OPTIMIZATION_RECOMMENDATION_SCHEMA),
    "findings": ("semantic_model_optimization", "semantic_model_optimization_findings", OPTIMIZATION_FINDING_SCHEMA),
    "opportunity_recommendation_links": ("semantic_model_optimization", "semantic_model_optimization_opportunity_recommendation_links", OPTIMIZATION_LINK_SCHEMA),
    "opportunity_finding_links": ("semantic_model_optimization", "semantic_model_optimization_opportunity_finding_links", OPTIMIZATION_LINK_SCHEMA),
    "column_storage": ("semantic_model_vertipaq", "semantic_model_column_storage", COLUMN_STORAGE_SCHEMA),
    "table_storage": ("semantic_model_vertipaq", "semantic_model_table_storage", TABLE_STORAGE_SCHEMA),
}

CURRENT_STATE_TABLES = tuple(
    logical_name for logical_name in CURATED_TABLES if logical_name != "analysis_runs"
)


def curated_table_name(logical_name):
    schema_name, physical_name, _ = CURATED_TABLES[logical_name]
    return f"{schema_name}.{physical_name}"


def ensure_curated_tables():
    for schema_name in BUSINESS_SCHEMAS:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{schema_name}`")
    for logical_name, (_, _, schema) in CURATED_TABLES.items():
        name = curated_table_name(logical_name)
        if not spark.catalog.tableExists(name):
            spark.createDataFrame([], schema).write.format("delta").mode("errorifexists").saveAsTable(name)
            continue
        existing_columns = {field.name.lower() for field in spark.table(name).schema.fields}
        missing_fields = [field for field in schema.fields if field.name.lower() not in existing_columns]
        if missing_fields:
            additions = ", ".join(
                f"`{field.name}` {field.dataType.simpleString().upper()}"
                for field in missing_fields
            )
            spark.sql(f"ALTER TABLE {name} ADD COLUMNS ({additions})")


def replace_semantic_model_current_state(logical_name, semantic_model_id, rows):
    _, _, schema = CURATED_TABLES[logical_name]
    name = curated_table_name(logical_name)
    escaped_model_id = semantic_model_id.replace("'", "''")
    DeltaTable.forName(spark, name).delete(f"semantic_model_id = '{escaped_model_id}'")
    if rows:
        spark.createDataFrame(rows, schema=schema).write.format("delta").mode("append").saveAsTable(name)


def reconcile_workspace_current_state(targets):
    """Remove current-state rows for models no longer eligible in a full workspace scan."""
    workspace_targets = {}
    for target in targets:
        if target.get("scope_source") != "WORKSPACE":
            continue
        workspace_targets.setdefault(target["workspace_id"], set()).add(target["model_id"])

    if not workspace_targets:
        return

    model_dimension = spark.table(curated_table_name("semantic_models"))
    stale_model_ids = set()
    for workspace_id, eligible_model_ids in workspace_targets.items():
        escaped_workspace_id = workspace_id.replace("'", "''")
        existing_model_ids = {
            row["semantic_model_id"]
            for row in (
                model_dimension
                .where(f"workspace_id = '{escaped_workspace_id}'")
                .select("semantic_model_id")
                .collect()
            )
        }
        stale_model_ids.update(existing_model_ids - eligible_model_ids)

    if not stale_model_ids:
        return

    quoted_ids = ", ".join(
        "'" + model_id.replace("'", "''") + "'"
        for model_id in sorted(stale_model_ids)
    )
    predicate = f"semantic_model_id IN ({quoted_ids})"
    for logical_name in CURRENT_STATE_TABLES:
        DeltaTable.forName(spark, curated_table_name(logical_name)).delete(predicate)
    print(
        f"Removed stale current-state rows for {len(stale_model_ids)} semantic model(s) "
        "outside the eligible full-workspace scan scope."
    )


def validate_curated_scan_output(model_results):
    """Reject a false-success scan that did not materialize its core contract."""
    analyzed_model_ids = sorted({
        row["model_id"]
        for row in model_results
        if row["overall_status"] in {"SUCCEEDED", "PARTIAL"}
    })
    if not analyzed_model_ids:
        return

    quoted_ids = ", ".join(
        "'" + model_id.replace("'", "''") + "'"
        for model_id in analyzed_model_ids
    )
    missing_by_table = {}
    for logical_name in ("analysis_runs", "semantic_models", "overview"):
        present_ids = {
            row["semantic_model_id"]
            for row in spark.sql(
                f"SELECT DISTINCT semantic_model_id "
                f"FROM {curated_table_name(logical_name)} "
                f"WHERE semantic_model_id IN ({quoted_ids})"
            ).collect()
        }
        missing_ids = sorted(set(analyzed_model_ids) - present_ids)
        if missing_ids:
            missing_by_table[curated_table_name(logical_name)] = missing_ids

    if missing_by_table:
        raise RuntimeError(
            "Scan did not materialize the required business-layer rows: "
            + json.dumps(missing_by_table, ensure_ascii=False)
        )


def upsert_curated_history(logical_name, rows, keys):
    if not rows:
        return
    _, _, schema = CURATED_TABLES[logical_name]
    source = spark.createDataFrame(rows, schema=schema)
    condition = " AND ".join(f"t.`{key}` = s.`{key}`" for key in keys)
    (
        DeltaTable.forName(spark, curated_table_name(logical_name))
        .alias("t")
        .merge(source.alias("s"), condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


def severity_value(value):
    return {
        "CRITICAL": 5,
        "ERROR": 4,
        "HIGH": 4,
        "WARNING": 3,
        "MEDIUM": 3,
        "INFO": 2,
        "LOW": 1,
    }.get((value or "").upper(), 0)


def risk_value(value):
    return {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get((value or "").upper(), 0)


def availability_explanations(model_row, result):
    notes = []
    if model_row["refresh_status"] == "SUCCEEDED" and not result["refresh_rows"]:
        notes.append("Refresh history: no records were returned for the selected history window.")
    elif model_row["refresh_status"] == "NOT_RUN":
        notes.append("Refresh history: not requested by this analysis profile.")
    if model_row["usage_status"] == "NOT_RUN":
        notes.append("Object usage: not run in the standard profile; use the deep profile to collect usage evidence.")
    elif model_row["usage_status"] == "SUCCEEDED" and not result["usage_rows"]:
        notes.append("Object usage: analysis completed and returned no observations.")
    if model_row["direct_lake_status"] == "NOT_APPLICABLE":
        notes.append("Direct Lake checks: not applicable because this semantic model uses Import storage.")
    elif model_row["direct_lake_status"] == "SUCCEEDED" and not result["direct_lake_rows"]:
        notes.append("Direct Lake checks: completed with no fallback observations.")
    if model_row["access_snapshot_status"] == "SUCCEEDED" and not result["access_rows"]:
        notes.append("Item access snapshot: completed and returned no explicit access records.")
    return " ".join(notes) or "All requested evidence sources returned data or an explicit status."


def curate_latest_model_analysis(result):
    model_row = result["model_row"]
    analysis_run_rows = [{
        "analysis_id": model_row["scan_id"],
        "workspace_id": model_row["workspace_id"],
        "workspace_name": model_row["workspace_name"],
        "semantic_model_id": model_row["model_id"],
        "semantic_model_name": model_row["model_name"],
        "scanner_version": model_row["scanner_version"],
        "analysis_profile": analysis_profile,
        "analysis_status": model_row["overall_status"],
        "permission_precheck_status": model_row["permission_precheck_status"],
        "best_practice_analysis_status": model_row["bpa_status"],
        "storage_analysis_status": model_row["vpa_status"],
        "refresh_history_status": model_row["refresh_status"],
        "object_usage_analysis_status": model_row["usage_status"],
        "direct_lake_analysis_status": model_row["direct_lake_status"],
        "item_access_snapshot_status": model_row["access_snapshot_status"],
        "finding_count": model_row["finding_count"],
        "started_at": model_row["started_at"],
        "completed_at": model_row["completed_at"],
        "duration_seconds": model_row["duration_seconds"],
        "error_details": model_row["error_json"],
    }]
    upsert_curated_history("analysis_runs", analysis_run_rows, ["analysis_id", "semantic_model_id"])
    if model_row["overall_status"] not in {"SUCCEEDED", "PARTIAL"}:
        return

    analysis_id = model_row["scan_id"]
    semantic_model_id = model_row["model_id"]
    workspace_name = model_row["workspace_name"]
    semantic_model_name = model_row["model_name"]
    findings = result["findings"]

    opportunity_groups = {}
    recommendation_groups = {}
    finding_rows = []
    finding_links = []
    recommendation_links = set()

    for finding in findings:
        finding_quality = grade_finding(finding)
        domain = finding.get("category") or finding.get("impact_area") or "General optimization"
        source = finding.get("source") or "Unknown source"
        opportunity_id = stable_id(semantic_model_id, "OPPORTUNITY", source, domain)
        opportunity = opportunity_groups.setdefault(opportunity_id, {
            "findings": [],
            "recommendations": set(),
            "domain": domain,
            "source": source,
        })
        opportunity["findings"].append(finding)

        recommendation_id = stable_id(
            semantic_model_id,
            "RECOMMENDATION",
            finding.get("rule_id") or finding.get("rule_name"),
            finding.get("recommended_action"),
        )
        recommendation = recommendation_groups.setdefault(recommendation_id, {
            "findings": [],
            "opportunity_id": opportunity_id,
            "domain": domain,
            "source": source,
            "title": finding.get("rule_name") or "Optimization recommendation",
            "action": finding.get("recommended_action"),
        })
        recommendation["findings"].append(finding)
        opportunity["recommendations"].add(recommendation_id)
        recommendation_links.add((opportunity_id, recommendation_id))
        finding_links.append({
            "analysis_id": analysis_id,
            "semantic_model_id": semantic_model_id,
            "opportunity_id": opportunity_id,
            "related_entity_id": finding["finding_id"],
        })
        finding_rows.append({
            "finding_id": finding["finding_id"],
            "opportunity_id": opportunity_id,
            "analysis_id": analysis_id,
            "workspace_name": workspace_name,
            "semantic_model_id": semantic_model_id,
            "semantic_model_name": semantic_model_name,
            "finding_source": source,
            "optimization_domain": domain,
            "rule_name": finding.get("rule_name"),
            "severity": finding.get("severity"),
            "confidence": finding.get("confidence"),
            "impact_area": finding.get("impact_area"),
            "affected_object_type": finding.get("object_type"),
            "affected_table_name": finding.get("table_name"),
            "affected_object_name": finding.get("object_name"),
            "finding_description": finding.get("finding_text"),
            "recommended_action": finding.get("recommended_action"),
            "technical_evidence": finding.get("technical_evidence"),
            "estimated_saving_bytes_low": finding.get("estimated_saving_bytes_low"),
            "estimated_saving_bytes_high": finding.get("estimated_saving_bytes_high"),
            "change_risk": finding.get("change_risk"),
            "validation_required": finding.get("validation_required"),
            **finding_quality,
            "detected_at": finding.get("detected_at"),
        })

    opportunity_rows = []
    for opportunity_id, group in opportunity_groups.items():
        grouped_findings = group["findings"]
        highest = max(grouped_findings, key=lambda row: severity_value(row.get("severity")))
        highest_risk = max(grouped_findings, key=lambda row: risk_value(row.get("change_risk")))
        opportunity_quality = grade_opportunity(grouped_findings)
        opportunity_rows.append({
            "opportunity_id": opportunity_id,
            "analysis_id": analysis_id,
            "workspace_name": workspace_name,
            "semantic_model_id": semantic_model_id,
            "semantic_model_name": semantic_model_name,
            "opportunity_title": f"{group['domain']} optimization",
            "optimization_domain": group["domain"],
            "finding_source": group["source"],
            "highest_severity": highest.get("severity"),
            "finding_count": len(grouped_findings),
            "recommendation_count": len(group["recommendations"]),
            "estimated_saving_bytes_low": sum(row.get("estimated_saving_bytes_low") or 0 for row in grouped_findings),
            "estimated_saving_bytes_high": sum(row.get("estimated_saving_bytes_high") or 0 for row in grouped_findings),
            "change_risk": highest_risk.get("change_risk"),
            "opportunity_summary": f"{len(grouped_findings)} finding(s) from {group['source']} require review in {group['domain']}.",
            **opportunity_quality,
            "detected_at": max(row.get("detected_at") for row in grouped_findings if row.get("detected_at")),
        })

    recommendation_rows = []
    for recommendation_id, group in recommendation_groups.items():
        grouped_findings = group["findings"]
        highest_risk = max(grouped_findings, key=lambda row: risk_value(row.get("change_risk")))
        recommendation_quality = grade_recommendation(
            grouped_findings, group["domain"], group["title"], group["action"]
        )
        recommendation_title = recommendation_quality.pop("recommendation_title")
        recommended_action = recommendation_quality.pop("recommended_action")
        recommendation_rows.append({
            "recommendation_id": recommendation_id,
            "opportunity_id": group["opportunity_id"],
            "analysis_id": analysis_id,
            "workspace_name": workspace_name,
            "semantic_model_id": semantic_model_id,
            "semantic_model_name": semantic_model_name,
            "recommendation_title": recommendation_title,
            "optimization_domain": group["domain"],
            "recommended_action": recommended_action,
            "change_risk": highest_risk.get("change_risk"),
            "validation_required": any(row.get("validation_required") for row in grouped_findings),
            "estimated_saving_bytes_low": sum(row.get("estimated_saving_bytes_low") or 0 for row in grouped_findings),
            "estimated_saving_bytes_high": sum(row.get("estimated_saving_bytes_high") or 0 for row in grouped_findings),
            "finding_source": group["source"],
            "affected_finding_count": len(grouped_findings),
            **recommendation_quality,
            "detected_at": max(row.get("detected_at") for row in grouped_findings if row.get("detected_at")),
        })

    recommendation_link_rows = [
        {
            "analysis_id": analysis_id,
            "semantic_model_id": semantic_model_id,
            "opportunity_id": opportunity_id,
            "related_entity_id": recommendation_id,
        }
        for opportunity_id, recommendation_id in sorted(recommendation_links)
    ]

    column_storage_rows = [{
        "column_storage_record_id": row["evidence_id"],
        "analysis_id": analysis_id,
        "workspace_name": workspace_name,
        "semantic_model_id": semantic_model_id,
        "semantic_model_name": semantic_model_name,
        "table_name": row.get("table_name"),
        "column_name": row.get("column_name"),
        "data_type": row.get("data_type"),
        "encoding": row.get("encoding"),
        "cardinality": row.get("cardinality"),
        "data_size_bytes": row.get("data_size_bytes"),
        "dictionary_size_bytes": row.get("dictionary_size_bytes"),
        "hierarchy_size_bytes": row.get("hierarchy_size_bytes"),
        "total_size_bytes": row.get("total_size_bytes"),
        "percentage_of_semantic_model_size": row.get("model_size_pct"),
        "detected_at": row.get("detected_at"),
    } for row in result["vpa_columns"]]

    table_storage_rows = [{
        "table_storage_record_id": row["evidence_id"],
        "analysis_id": analysis_id,
        "workspace_name": workspace_name,
        "semantic_model_id": semantic_model_id,
        "semantic_model_name": semantic_model_name,
        "table_name": row.get("table_name"),
        "row_count": row.get("row_count"),
        "data_size_bytes": row.get("data_size_bytes"),
        "dictionary_size_bytes": row.get("dictionary_size_bytes"),
        "hierarchy_size_bytes": row.get("hierarchy_size_bytes"),
        "total_size_bytes": row.get("total_size_bytes"),
        "percentage_of_semantic_model_size": row.get("model_size_pct"),
        "detected_at": row.get("detected_at"),
    } for row in result["vpa_tables"]]

    best_practice_rows = [{
        "best_practice_finding_id": finding["finding_id"],
        "analysis_id": analysis_id,
        "workspace_name": workspace_name,
        "semantic_model_id": semantic_model_id,
        "semantic_model_name": semantic_model_name,
        "rule_id": finding.get("rule_id"),
        "rule_name": finding.get("rule_name"),
        "category": finding.get("category"),
        "severity": finding.get("severity"),
        "affected_object_type": finding.get("object_type"),
        "affected_table_name": finding.get("table_name"),
        "affected_object_name": finding.get("object_name"),
        "finding_description": finding.get("finding_text"),
        "recommended_action": finding.get("recommended_action"),
        "technical_evidence": finding.get("technical_evidence"),
        "documentation_url": finding.get("documentation_url"),
        "detected_at": finding.get("detected_at"),
    } for finding in findings if (finding.get("source") or "").upper() == "BPA"]

    semantic_model_rows = [{
        "semantic_model_id": semantic_model_id,
        "workspace_id": model_row["workspace_id"],
        "workspace_name": workspace_name,
        "semantic_model_name": semantic_model_name,
        "capacity_id": model_row["capacity_id"],
        "capacity_name": model_row["capacity_name"],
        "storage_mode": model_row["storage_mode"],
        "semantic_model_size_bytes": model_row["model_size_bytes"],
        "latest_analysis_id": analysis_id,
        "latest_analysis_status": model_row["overall_status"],
        "latest_analysis_at": model_row["completed_at"],
        "scanner_version": model_row["scanner_version"],
    }]

    overview_rows = [{
        "analysis_id": analysis_id,
        "workspace_id": model_row["workspace_id"],
        "workspace_name": workspace_name,
        "semantic_model_id": semantic_model_id,
        "semantic_model_name": semantic_model_name,
        "storage_mode": model_row["storage_mode"],
        "analysis_status": model_row["overall_status"],
        "analysis_completed_at": model_row["completed_at"],
        "scanner_version": model_row["scanner_version"],
        "semantic_model_size_bytes": model_row["model_size_bytes"],
        "optimization_opportunity_count": len(opportunity_rows),
        "optimization_recommendation_count": len(recommendation_rows),
        "optimization_finding_count": len(finding_rows),
        "high_severity_finding_count": sum((row.get("severity") or "").upper() in {"HIGH", "CRITICAL", "ERROR"} for row in findings),
        "actionable_recommendation_count": sum(row["actionability_status"] == ACTIONABLE for row in recommendation_rows),
        "review_required_recommendation_count": sum(row["actionability_status"] == REVIEW_REQUIRED for row in recommendation_rows),
        "suppressed_finding_count": sum(row["actionability_status"] == SUPPRESSED for row in finding_rows),
        "best_practice_analysis_status": model_row["bpa_status"],
        "storage_analysis_status": model_row["vpa_status"],
        "refresh_history_status": model_row["refresh_status"],
        "refresh_history_record_count": len(result["refresh_rows"]),
        "object_usage_analysis_status": model_row["usage_status"],
        "object_usage_observation_count": len(result["usage_rows"]),
        "direct_lake_analysis_status": model_row["direct_lake_status"],
        "direct_lake_observation_count": len(result["direct_lake_rows"]),
        "item_access_snapshot_status": model_row["access_snapshot_status"],
        "item_access_record_count": len(result["access_rows"]),
        "data_availability_explanation": availability_explanations(model_row, result),
    }]

    replacements = {
        "semantic_models": semantic_model_rows,
        "best_practice_findings": best_practice_rows,
        "overview": overview_rows,
        "opportunities": opportunity_rows,
        "recommendations": recommendation_rows,
        "findings": finding_rows,
        "opportunity_recommendation_links": recommendation_link_rows,
        "opportunity_finding_links": finding_links,
        "column_storage": column_storage_rows,
        "table_storage": table_storage_rows,
    }
    for logical_name, rows in replacements.items():
        replace_semantic_model_current_state(logical_name, semantic_model_id, rows)
'''


def source_text(cell: dict) -> str:
    return "".join(cell.get("source", []))


def set_source(cell: dict, text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    notebook.setdefault("metadata", {})["scanner_version"] = "2.1.4"

    for cell in cells:
        text = source_text(cell)
        for previous_version in ("1.2.0", "2.0.0", "2.1.0", "2.1.1", "2.1.2", "2.1.3"):
            text = text.replace(
                f'SCANNER_VERSION = "{previous_version}"',
                'SCANNER_VERSION = "2.1.4"',
            )
        text = re.sub(
            r"Semantic Model Optimization Scanner — V(?:1\.2|2\.0|2\.1(?:\.\d+)*)",
            "Semantic Model Optimization Scanner — V2.1.4",
            text,
        )
        text = text.replace(
            "fail_pipeline_if_any_model_fails = False",
            "fail_pipeline_if_any_model_fails = True",
        )
        set_source(cell, text)

    quality_rules_source = QUALITY_RULES.read_text(encoding="utf-8")
    curation_cell = CURATION_CELL.replace("# __QUALITY_RULES_SOURCE__", quality_rules_source)

    existing_curation_cell = next(
        (cell for cell in cells if "V2 AI-friendly current-state consumption contract" in source_text(cell)),
        None,
    )
    if existing_curation_cell is not None:
        set_source(existing_curation_cell, curation_cell)
    else:
        execute_index = next(
            index for index, cell in enumerate(cells)
            if "# ---------- Execute scan and persist each model immediately ----------" in source_text(cell)
        )
        cells.insert(execute_index, {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": curation_cell.splitlines(keepends=True),
        })

    execute_cell = next(
        cell for cell in cells
        if "# ---------- Execute scan and persist each model immediately ----------" in source_text(cell)
    )
    execute = source_text(execute_cell)
    if "model_failure_details = [" not in execute:
        execute = execute.replace(
            'skipped_count = sum(row["overall_status"] == "SKIPPED_PERMISSION" for row in model_results)\n',
            'skipped_count = sum(row["overall_status"] == "SKIPPED_PERMISSION" for row in model_results)\n'
            'model_failure_details = [\n'
            '    f"{row[\'workspace_name\']} / {row[\'model_name\']}: {row.get(\'error_json\') or \'core analyses failed without a captured component error\'}"\n'
            '    for row in model_results\n'
            '    if row["overall_status"] == "FAILED"\n'
            ']\n'
            'model_failure_error = (\n'
            '    clean_string("Model analysis failures: " + " | ".join(model_failure_details), 4000)\n'
            '    if model_failure_details\n'
            '    else None\n'
            ')\n',
        )
        execute = execute.replace(
            '        if run_error\n        else "AUTHORIZATION"',
            '        if run_error\n        else "MODEL_ANALYSIS"\n        if model_failure_error\n        else "AUTHORIZATION"',
        )
        execute = execute.replace(
            '        if run_error\n        else f"{skipped_count} model(s) skipped',
            '        if run_error\n        else model_failure_error\n        if model_failure_error\n        else f"{skipped_count} model(s) skipped',
        )
        execute = execute.replace(
            '            "scanner_workspace_role": row["scanner_workspace_role"],\n'
            '            "finding_count": row["finding_count"],',
            '            "scanner_workspace_role": row["scanner_workspace_role"],\n'
            '            "best_practice_analysis_status": row["bpa_status"],\n'
            '            "storage_analysis_status": row["vpa_status"],\n'
            '            "refresh_history_status": row["refresh_status"],\n'
            '            "direct_lake_analysis_status": row["direct_lake_status"],\n'
            '            "finding_count": row["finding_count"],\n'
            '            "component_errors": row["error_json"],',
        )
        execute = execute.replace(
            '    "error": truncate_error(run_error) if run_error else None,',
            '    "error": truncate_error(run_error) if run_error else model_failure_error,',
        )
    execute = execute.replace(
        "    ensure_tables()\n    if initialize_only:\n        init_summary = {\"status\": \"INITIALIZED\", \"schema\": output_schema, \"table_count\": len(TABLES)}\n        print(json.dumps(init_summary, indent=2))\n        notebookutils.notebook.exit(json.dumps(init_summary))\n    with authentication_context():",
        "    ensure_tables()\n    ensure_curated_tables()\n    if initialize_only:\n        init_summary = {\"status\": \"INITIALIZED\", \"raw_table_count\": len(TABLES), \"curated_table_count\": len(CURATED_TABLES)}\n        print(json.dumps(init_summary, indent=2))\n    else:\n        with authentication_context():",
    )
    start = execute.index("        with authentication_context():")
    loop_end_marker = '            upsert_rows("item_access_snapshot", result["access_rows"])'
    end = execute.index(loop_end_marker, start) + len(loop_end_marker)
    block = execute[start:end]
    if '\n        targets = resolve_targets()' in block:
        block_lines = block.splitlines()
        block = "\n".join(
            [block_lines[0]] + ["    " + line for line in block_lines[1:]]
        )
        block = block.replace(
            '                upsert_rows("item_access_snapshot", result["access_rows"])',
            '                upsert_rows("item_access_snapshot", result["access_rows"])\n                curate_latest_model_analysis(result)',
        )
        block += "\n            reconcile_workspace_current_state(targets)"
        execute = execute[:start] + block + execute[end:]
    if "reconcile_workspace_current_state(targets)" not in execute:
        execute = execute.replace(
            "                curate_latest_model_analysis(result)\n",
            "                curate_latest_model_analysis(result)\n"
            "            reconcile_workspace_current_state(targets)\n",
        )
    if "No eligible semantic models were resolved" not in execute:
        execute = execute.replace(
            "            targets = resolve_targets()\n",
            "            targets = resolve_targets()\n"
            "            if not targets:\n"
            "                raise RuntimeError(\n"
            "                    \"No eligible semantic models were resolved for the requested scan scope.\"\n"
            "                )\n",
        )
    if "validate_curated_scan_output(model_results)" not in execute:
        execute = execute.replace(
            "            reconcile_workspace_current_state(targets)\n",
            "            reconcile_workspace_current_state(targets)\n"
            "            validate_curated_scan_output(model_results)\n",
        )
    set_source(execute_cell, execute)

    final_cell = next(cell for cell in cells if "final_status = \"FAILED\"" in source_text(cell))
    final = source_text(final_cell)
    if "if initialize_only:" not in final.split("final_status", 1)[0][-120:]:
        final = final.replace(
            'if run_error is not None:\n    final_status = "FAILED"',
            'if initialize_only:\n    final_status = "INITIALIZED"\nelif run_error is not None:\n    final_status = "FAILED"',
        )
    final = final.replace(
        '    if spark.catalog.tableExists(table_name("scan_run")):',
        '    if not initialize_only and spark.catalog.tableExists(table_name("scan_run")):',
    )
    set_source(final_cell, final)

    NOTEBOOK.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
