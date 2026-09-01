#!/usr/bin/env python3
"""Upgrade the scanner notebook to the AI-friendly V2 current-state contract."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "src/SMO_Optimization_Scanner.Notebook/notebook-content.ipynb"
QUALITY_RULES = ROOT / "scripts/quality_rules.py"
MODEL_QUALITY_RULES = ROOT / "scripts/model_quality_rules.py"


CURATION_CELL = r'''# ---------- V2 AI-friendly current-state consumption contract ----------

# __QUALITY_RULES_SOURCE__

# __MODEL_QUALITY_RULES_SOURCE__


def normalize_model_metadata(target, model_bim, vpa_columns, vpa_tables):
    findings = []
    for issue in analyze_model_bim(model_bim, vpa_columns, vpa_tables):
        rule_name = f"{issue['rule_code']}: {issue['rule_name']}"
        finding = finding_base(
            target,
            issue.get("source") or "MODEL_METADATA_HEURISTIC",
            rule_name,
            issue.get("object_type"),
            issue.get("table_name"),
            issue.get("object_name"),
        )
        finding.update({
            "category": issue.get("category"),
            "severity": issue.get("severity") or "INFO",
            "confidence": issue.get("confidence") or "HIGH",
            "impact_area": issue.get("impact_area") or "MODEL_QUALITY",
            "finding_text": issue.get("finding_text"),
            "recommended_action": issue.get("recommended_action"),
            "technical_evidence": issue.get("technical_evidence"),
            "evidence_json": issue.get("evidence_json"),
            "change_risk": issue.get("change_risk") or "MEDIUM",
        })
        findings.append(finding)
    return findings

BUSINESS_SCHEMAS = (
    "analysis_control",
    "semantic_model_metadata",
    "semantic_model_vertipaq",
    "semantic_model_best_practice",
    "semantic_model_optimization",
)

OPTIMIZATION_OVERVIEW_SCHEMA = T.StructType([
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("analysis_scope_key", T.StringType(), False),
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
    T.StructField("analysis_scope_key", T.StringType(), False),
    T.StructField("issue_scope_key", T.StringType(), False),
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
    T.StructField("analysis_scope_key", T.StringType(), False),
    T.StructField("issue_scope_key", T.StringType(), False),
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
    T.StructField("analysis_scope_key", T.StringType(), False),
    T.StructField("issue_scope_key", T.StringType(), False),
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
    T.StructField("object_scope", T.StringType()),
    T.StructField("display_table_name", T.StringType()),
    T.StructField("display_object_name", T.StringType()),
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
    T.StructField("analysis_scope_key", T.StringType(), False),
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
    T.StructField("analysis_scope_key", T.StringType(), False),
    T.StructField("latest_analysis_status", T.StringType()),
    T.StructField("latest_analysis_at", T.TimestampType()),
    T.StructField("scanner_version", T.StringType()),
])

BEST_PRACTICE_FINDING_SCHEMA = T.StructType([
    T.StructField("best_practice_finding_id", T.StringType(), False),
    T.StructField("analysis_id", T.StringType(), False),
    T.StructField("analysis_scope_key", T.StringType(), False),
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
    T.StructField("analysis_scope_key", T.StringType(), False),
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

    findings_name = curated_table_name("findings")
    # Keep the regex backslashes intact through Python and Spark SQL parsing.
    # A normal f-string turns ``\\s`` into ``\s`` before Spark sees it; Spark's
    # SQL string parser then drops that remaining slash and the regex becomes
    # ``s+``, which corrupts identifiers such as ``FactInternetSales``.
    spark.sql(fr"""
        UPDATE {findings_name}
        SET
            object_scope = CASE
                WHEN instr(lower(coalesce(affected_table_name, '')), 'datetabletemplate_') > 0
                  OR instr(lower(coalesce(affected_table_name, '')), 'localdatetable_') > 0
                  OR instr(lower(coalesce(affected_object_name, '')), 'datetabletemplate_') > 0
                  OR instr(lower(coalesce(affected_object_name, '')), 'localdatetable_') > 0
                    THEN 'Auto Date/Time (system)'
                WHEN upper(trim(coalesce(affected_object_type, ''))) IN ('', 'MODEL', 'SEMANTIC MODEL')
                    THEN 'Model-level'
                ELSE 'Authored / imported object'
            END,
            display_table_name = CASE
                WHEN trim(coalesce(affected_table_name, '')) <> '' THEN
                    regexp_replace(
                        regexp_replace(
                            regexp_replace(
                                trim(regexp_replace(
                                    replace(replace(replace(affected_table_name, chr(8203), ''), chr(65279), ''), chr(160), ' '),
                                    '\\s+', ' '
                                )),
                                '^\\x27+|\\x27+$', ''
                            ),
                            '^"+|"+$', ''
                        ),
                        '^`+|`+$', ''
                    )
                WHEN instr(coalesce(affected_object_name, ''), '[') > 0
                    THEN regexp_replace(
                        regexp_replace(
                            regexp_replace(
                                trim(regexp_replace(
                                    replace(replace(replace(substring_index(affected_object_name, '[', 1), chr(8203), ''), chr(65279), ''), chr(160), ' '),
                                    '\\s+', ' '
                                )),
                                '^\\x27+|\\x27+$', ''
                            ),
                            '^"+|"+$', ''
                        ),
                        '^`+|`+$', ''
                    )
                WHEN upper(trim(coalesce(affected_object_type, ''))) IN ('TABLE', 'CALCULATED TABLE')
                  AND trim(coalesce(affected_object_name, '')) <> ''
                    THEN regexp_replace(
                        regexp_replace(
                            regexp_replace(
                                trim(regexp_replace(
                                    replace(replace(replace(affected_object_name, chr(8203), ''), chr(65279), ''), chr(160), ' '),
                                    '\\s+', ' '
                                )),
                                '^\\x27+|\\x27+$', ''
                            ),
                            '^"+|"+$', ''
                        ),
                        '^`+|`+$', ''
                    )
                ELSE 'Not applicable'
            END
    """)

    # Keep the physical locator at the same grain as finding_locator_fields().
    # The deployment-time backfill runs for historical rows as well as new scans;
    # it must not overwrite qualified Table[Column] / Table[Measure] locators with
    # the raw leaf name stored in affected_object_name.
    spark.sql(fr"""
        UPDATE {findings_name}
        SET display_object_name = CASE
            WHEN trim(coalesce(affected_object_name, '')) = '' THEN 'Not applicable'
            WHEN upper(trim(coalesce(affected_object_type, ''))) IN ('COLUMN', 'MEASURE')
              AND display_table_name <> 'Not applicable'
                THEN concat(
                    display_table_name,
                    '[',
                    regexp_replace(
                        regexp_replace(
                            regexp_replace(
                                trim(regexp_replace(
                                    replace(replace(replace(
                                        CASE
                                            WHEN instr(affected_object_name, '[') > 0
                                                THEN regexp_replace(substring_index(affected_object_name, '[', -1), ']$', '')
                                            ELSE affected_object_name
                                        END,
                                        chr(8203), ''), chr(65279), ''), chr(160), ' '
                                    ),
                                    '\\s+', ' '
                                )),
                                '^\\x27+|\\x27+$', ''
                            ),
                            '^"+|"+$', ''
                        ),
                        '^`+|`+$', ''
                    ),
                    ']'
                )
            WHEN upper(trim(coalesce(affected_object_type, ''))) IN ('TABLE', 'CALCULATED TABLE')
              AND display_table_name <> 'Not applicable'
                THEN display_table_name
            ELSE regexp_replace(
                regexp_replace(
                    regexp_replace(
                        trim(regexp_replace(
                            replace(replace(replace(affected_object_name, chr(8203), ''), chr(65279), ''), chr(160), ' '),
                            '\\s+', ' '
                        )),
                        '^\\x27+|\\x27+$', ''
                    ),
                    '^"+|"+$', ''
                ),
                '^`+|`+$', ''
            )
        END
    """)

    semantic_models_name = curated_table_name("semantic_models")
    spark.sql(f"""
        UPDATE {semantic_models_name}
        SET analysis_scope_key = concat(semantic_model_id, '|', latest_analysis_id)
        WHERE latest_analysis_id IS NOT NULL
    """)
    for logical_name in (
        "overview", "opportunities", "recommendations", "findings",
        "best_practice_findings", "column_storage", "table_storage",
    ):
        spark.sql(f"""
            UPDATE {curated_table_name(logical_name)}
            SET analysis_scope_key = concat(semantic_model_id, '|', analysis_id)
            WHERE analysis_id IS NOT NULL
        """)
    for logical_name in ("opportunities", "recommendations", "findings"):
        spark.sql(f"""
            UPDATE {curated_table_name(logical_name)}
            SET issue_scope_key = concat(semantic_model_id, '|', analysis_id, '|', opportunity_id)
            WHERE analysis_id IS NOT NULL AND opportunity_id IS NOT NULL
        """)


def replace_semantic_model_current_state(logical_name, semantic_model_id, rows):
    _, _, schema = CURATED_TABLES[logical_name]
    name = curated_table_name(logical_name)
    escaped_model_id = semantic_model_id.replace("'", "''")
    DeltaTable.forName(spark, name).delete(f"semantic_model_id = '{escaped_model_id}'")
    if rows:
        keyed_rows = []
        for source_row in rows:
            row = dict(source_row)
            analysis_id = row.get("latest_analysis_id") if logical_name == "semantic_models" else row.get("analysis_id")
            if "analysis_scope_key" in schema.fieldNames() and analysis_id:
                row["analysis_scope_key"] = f"{semantic_model_id}|{analysis_id}"
            if "issue_scope_key" in schema.fieldNames() and analysis_id and row.get("opportunity_id"):
                row["issue_scope_key"] = f"{semantic_model_id}|{analysis_id}|{row['opportunity_id']}"
            keyed_rows.append(row)
        spark.createDataFrame(keyed_rows, schema=schema).write.format("delta").mode("append").saveAsTable(name)


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
    """Reject false-success and internally inconsistent business-layer output."""
    analyzed_model_ids = sorted({
        row["model_id"]
        for row in model_results
        if row["overall_status"] in {"SUCCEEDED", "PARTIAL"}
    })
    if not analyzed_model_ids:
        return
    expected_result_by_model = {
        row["model_id"]: row
        for row in model_results
        if row["overall_status"] in {"SUCCEEDED", "PARTIAL"}
    }

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

    def grouped_counts(logical_name, extra_expressions=()):
        expressions = ["COUNT(*) AS row_count", *extra_expressions]
        rows = spark.sql(
            "SELECT semantic_model_id, "
            + ", ".join(expressions)
            + f" FROM {curated_table_name(logical_name)}"
            + f" WHERE semantic_model_id IN ({quoted_ids})"
            + " GROUP BY semantic_model_id"
        ).collect()
        return {row["semantic_model_id"]: row.asDict(recursive=True) for row in rows}

    overview_by_model = {
        row["semantic_model_id"]: row.asDict(recursive=True)
        for row in spark.sql(
            "SELECT * FROM " + curated_table_name("overview")
            + f" WHERE semantic_model_id IN ({quoted_ids})"
        ).collect()
    }
    dimension_by_model = {
        row["semantic_model_id"]: row.asDict(recursive=True)
        for row in spark.sql(
            "SELECT semantic_model_id, latest_analysis_id, latest_analysis_status "
            "FROM " + curated_table_name("semantic_models")
            + f" WHERE semantic_model_id IN ({quoted_ids})"
        ).collect()
    }
    analysis_history_pairs = {
        (row["semantic_model_id"], row["analysis_id"])
        for row in spark.sql(
            "SELECT semantic_model_id, analysis_id FROM "
            + curated_table_name("analysis_runs")
            + f" WHERE semantic_model_id IN ({quoted_ids})"
        ).collect()
    }
    opportunity_counts = grouped_counts("opportunities")
    recommendation_counts = grouped_counts("recommendations", (
        "SUM(CASE WHEN actionability_status = 'ACTIONABLE' THEN 1 ELSE 0 END) AS actionable_count",
        "SUM(CASE WHEN actionability_status = 'REVIEW_REQUIRED' THEN 1 ELSE 0 END) AS review_required_count",
    ))
    finding_counts = grouped_counts("findings", (
        "SUM(CASE WHEN actionability_status = 'SUPPRESSED' THEN 1 ELSE 0 END) AS suppressed_count",
    ))
    recommendation_link_counts = grouped_counts("opportunity_recommendation_links")
    finding_link_counts = grouped_counts("opportunity_finding_links")

    consistency_issues = []
    for semantic_model_id in analyzed_model_ids:
        overview = overview_by_model[semantic_model_id]
        dimension = dimension_by_model[semantic_model_id]
        expected_result = expected_result_by_model[semantic_model_id]
        expected_counts = {
            "optimization_opportunity_count": opportunity_counts.get(semantic_model_id, {}).get("row_count", 0),
            "optimization_recommendation_count": recommendation_counts.get(semantic_model_id, {}).get("row_count", 0),
            "optimization_finding_count": finding_counts.get(semantic_model_id, {}).get("row_count", 0),
            "actionable_recommendation_count": recommendation_counts.get(semantic_model_id, {}).get("actionable_count", 0),
            "review_required_recommendation_count": recommendation_counts.get(semantic_model_id, {}).get("review_required_count", 0),
            "suppressed_finding_count": finding_counts.get(semantic_model_id, {}).get("suppressed_count", 0),
        }
        mismatches = {
            name: {"overview": overview.get(name), "detail": expected}
            for name, expected in expected_counts.items()
            if overview.get(name) != expected
        }
        if dimension.get("latest_analysis_id") != overview.get("analysis_id"):
            mismatches["latest_analysis_id"] = {
                "semantic_models": dimension.get("latest_analysis_id"),
                "overview": overview.get("analysis_id"),
            }
        if overview.get("analysis_id") != expected_result.get("scan_id"):
            mismatches["current_scan_analysis_id"] = {
                "expected": expected_result.get("scan_id"),
                "overview": overview.get("analysis_id"),
            }
        if (semantic_model_id, expected_result.get("scan_id")) not in analysis_history_pairs:
            mismatches["analysis_history"] = {
                "semantic_model_id": semantic_model_id,
                "analysis_id": expected_result.get("scan_id"),
                "status": "missing",
            }
        if dimension.get("latest_analysis_status") != overview.get("analysis_status"):
            mismatches["latest_analysis_status"] = {
                "semantic_models": dimension.get("latest_analysis_status"),
                "overview": overview.get("analysis_status"),
            }
        if overview.get("analysis_status") != expected_result.get("overall_status"):
            mismatches["current_scan_analysis_status"] = {
                "expected": expected_result.get("overall_status"),
                "overview": overview.get("analysis_status"),
            }
        if not str(overview.get("data_availability_explanation") or "").strip():
            mismatches["data_availability_explanation"] = "missing"
        recommendation_row_count = recommendation_counts.get(semantic_model_id, {}).get("row_count", 0)
        recommendation_link_count = recommendation_link_counts.get(semantic_model_id, {}).get("row_count", 0)
        if recommendation_link_count != recommendation_row_count:
            mismatches["opportunity_recommendation_link_count"] = {
                "links": recommendation_link_count,
                "recommendations": recommendation_row_count,
            }
        finding_row_count = finding_counts.get(semantic_model_id, {}).get("row_count", 0)
        finding_link_count = finding_link_counts.get(semantic_model_id, {}).get("row_count", 0)
        if finding_link_count != finding_row_count:
            mismatches["opportunity_finding_link_count"] = {
                "links": finding_link_count,
                "findings": finding_row_count,
            }
        if mismatches:
            consistency_issues.append({"semantic_model_id": semantic_model_id, "mismatches": mismatches})

    quality_checks = {
        "invalid_findings": f"""
            SELECT COUNT(*) AS issue_count
            FROM {curated_table_name('findings')}
            WHERE semantic_model_id IN ({quoted_ids}) AND (
                actionability_status NOT IN ('ACTIONABLE', 'REVIEW_REQUIRED', 'INFORMATIONAL', 'SUPPRESSED')
                OR finding_priority_score IS NULL OR finding_priority_score < 0 OR finding_priority_score > 100
                OR finding_priority_band <> CASE
                    WHEN finding_priority_score >= 80 THEN 'P1_CRITICAL'
                    WHEN finding_priority_score >= 65 THEN 'P2_HIGH'
                    WHEN finding_priority_score >= 40 THEN 'P3_MEDIUM'
                    ELSE 'P4_LOW' END
                OR TRIM(COALESCE(actionability_reason, '')) = ''
                OR (actionability_status = 'SUPPRESSED' AND TRIM(COALESCE(suppression_reason, '')) = '')
            )
        """,
        "invalid_recommendations": f"""
            SELECT COUNT(*) AS issue_count
            FROM {curated_table_name('recommendations')}
            WHERE semantic_model_id IN ({quoted_ids}) AND (
                actionability_status NOT IN ('ACTIONABLE', 'REVIEW_REQUIRED', 'INFORMATIONAL', 'SUPPRESSED')
                OR recommendation_priority_score IS NULL OR recommendation_priority_score < 0 OR recommendation_priority_score > 100
                OR recommendation_priority_band <> CASE
                    WHEN recommendation_priority_score >= 80 THEN 'P1_CRITICAL'
                    WHEN recommendation_priority_score >= 65 THEN 'P2_HIGH'
                    WHEN recommendation_priority_score >= 40 THEN 'P3_MEDIUM'
                    ELSE 'P4_LOW' END
                OR automation_eligibility NOT IN ('SCRIPT_CANDIDATE', 'MANUAL_ONLY', 'MANUAL_REVIEW', 'NOT_ELIGIBLE')
                OR TRIM(COALESCE(recommendation_title, '')) = ''
                OR TRIM(COALESCE(actionability_reason, '')) = ''
                OR TRIM(COALESCE(why_it_matters, '')) = ''
                OR TRIM(COALESCE(validation_method, '')) = ''
                OR TRIM(COALESCE(rollback_guidance, '')) = ''
                OR (actionability_status IN ('ACTIONABLE', 'REVIEW_REQUIRED') AND TRIM(COALESCE(recommended_action, '')) = '')
                OR (actionability_status IN ('INFORMATIONAL', 'SUPPRESSED') AND automation_eligibility <> 'NOT_ELIGIBLE')
                OR (actionability_status = 'REVIEW_REQUIRED' AND automation_eligibility <> 'MANUAL_REVIEW')
            )
        """,
        "invalid_opportunities": f"""
            SELECT COUNT(*) AS issue_count
            FROM {curated_table_name('opportunities')}
            WHERE semantic_model_id IN ({quoted_ids}) AND (
                actionability_status NOT IN ('ACTIONABLE', 'REVIEW_REQUIRED', 'INFORMATIONAL', 'SUPPRESSED')
                OR priority_score IS NULL OR priority_score < 0 OR priority_score > 100
                OR priority_band <> CASE
                    WHEN priority_score >= 80 THEN 'P1_CRITICAL'
                    WHEN priority_score >= 65 THEN 'P2_HIGH'
                    WHEN priority_score >= 40 THEN 'P3_MEDIUM'
                    ELSE 'P4_LOW' END
                OR TRIM(COALESCE(opportunity_title, '')) = ''
                OR TRIM(COALESCE(opportunity_summary, '')) = ''
            )
        """,
        "invalid_opportunity_rollups": f"""
            SELECT COUNT(*) AS issue_count
            FROM {curated_table_name('opportunities')} o
            LEFT JOIN (
                SELECT semantic_model_id, opportunity_id, COUNT(*) AS finding_count
                FROM {curated_table_name('findings')}
                GROUP BY semantic_model_id, opportunity_id
            ) f ON o.semantic_model_id = f.semantic_model_id AND o.opportunity_id = f.opportunity_id
            LEFT JOIN (
                SELECT semantic_model_id, opportunity_id, COUNT(*) AS recommendation_count
                FROM {curated_table_name('recommendations')}
                GROUP BY semantic_model_id, opportunity_id
            ) r ON o.semantic_model_id = r.semantic_model_id AND o.opportunity_id = r.opportunity_id
            WHERE o.semantic_model_id IN ({quoted_ids}) AND (
                o.finding_count <> COALESCE(f.finding_count, 0)
                OR o.recommendation_count <> COALESCE(r.recommendation_count, 0)
            )
        """,
        "orphan_recommendations": f"""
            SELECT COUNT(*) AS issue_count
            FROM {curated_table_name('recommendations')} r
            LEFT ANTI JOIN {curated_table_name('opportunities')} o
              ON r.semantic_model_id = o.semantic_model_id AND r.opportunity_id = o.opportunity_id
            WHERE r.semantic_model_id IN ({quoted_ids})
        """,
        "orphan_findings": f"""
            SELECT COUNT(*) AS issue_count
            FROM {curated_table_name('findings')} f
            LEFT ANTI JOIN {curated_table_name('opportunities')} o
              ON f.semantic_model_id = o.semantic_model_id AND f.opportunity_id = o.opportunity_id
            WHERE f.semantic_model_id IN ({quoted_ids})
        """,
        "invalid_recommendation_links": f"""
            SELECT COUNT(*) AS issue_count
            FROM {curated_table_name('opportunity_recommendation_links')} l
            LEFT ANTI JOIN {curated_table_name('recommendations')} r
              ON l.semantic_model_id = r.semantic_model_id
             AND l.opportunity_id = r.opportunity_id
             AND l.related_entity_id = r.recommendation_id
            WHERE l.semantic_model_id IN ({quoted_ids})
        """,
        "invalid_finding_links": f"""
            SELECT COUNT(*) AS issue_count
            FROM {curated_table_name('opportunity_finding_links')} l
            LEFT ANTI JOIN {curated_table_name('findings')} f
              ON l.semantic_model_id = f.semantic_model_id
             AND l.opportunity_id = f.opportunity_id
             AND l.related_entity_id = f.finding_id
            WHERE l.semantic_model_id IN ({quoted_ids})
        """,
    }
    failed_quality_checks = {}
    for name, query in quality_checks.items():
        issue_count = spark.sql(query).first()["issue_count"]
        if issue_count:
            failed_quality_checks[name] = issue_count
    if consistency_issues or failed_quality_checks:
        raise RuntimeError(
            "Business-layer quality validation failed: "
            + json.dumps({
                "consistency_issues": consistency_issues,
                "failed_quality_checks": failed_quality_checks,
            }, ensure_ascii=False)
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


def normalize_display_identifier(value):
    normalized = str(value or "").replace("\u200b", "").replace("\ufeff", "").replace("\u00a0", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    while len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in "'\"`":
        normalized = normalized[1:-1].strip()
    return normalized


def split_display_object(value):
    normalized = str(value or "").strip()
    if "[" not in normalized:
        return "", normalize_display_identifier(normalized)
    raw_table, raw_leaf = normalized.split("[", 1)
    if raw_leaf.endswith("]"):
        raw_leaf = raw_leaf[:-1]
    return normalize_display_identifier(raw_table), normalize_display_identifier(raw_leaf)


def finding_locator_fields(finding):
    raw_table = (finding.get("table_name") or "").strip()
    raw_object = (finding.get("object_name") or "").strip()
    object_type = (finding.get("object_type") or "").strip().upper()
    auto_date = any(
        marker in value.lower()
        for marker in ("datetabletemplate_", "localdatetable_")
        for value in (raw_table, raw_object)
    )
    object_scope = (
        "Auto Date/Time (system)" if auto_date
        else "Model-level" if object_type in {"", "MODEL", "SEMANTIC MODEL"}
        else "Authored / imported object"
    )
    object_table, object_leaf = split_display_object(raw_object)
    display_table = normalize_display_identifier(raw_table) or object_table
    if not display_table and object_type in {"TABLE", "CALCULATED TABLE"}:
        display_table = normalize_display_identifier(raw_object)
    display_table = display_table or "Not applicable"
    if object_type in {"COLUMN", "MEASURE"} and display_table != "Not applicable" and object_leaf:
        display_object = f"{display_table}[{object_leaf}]"
    elif object_type in {"TABLE", "CALCULATED TABLE"} and display_table != "Not applicable":
        display_object = display_table
    else:
        display_object = normalize_display_identifier(raw_object) or "Not applicable"
    return {
        "object_scope": object_scope,
        "display_table_name": display_table,
        "display_object_name": display_object,
    }


def risk_value(value):
    return {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get((value or "").upper(), 0)


def availability_explanations(model_row, result):
    notes = []
    bpa_findings = [
        row for row in result["findings"]
        if (row.get("source") or "").upper() == "BPA"
    ]
    if model_row["bpa_status"] == "SUCCEEDED" and not bpa_findings:
        notes.append("Best-practice analysis: completed with no rule violations.")
    elif model_row["bpa_status"] == "NOT_RUN":
        notes.append("Best-practice analysis: not requested by this analysis profile.")
    elif model_row["bpa_status"] == "FAILED":
        notes.append("Best-practice analysis: failed; see analysis run error details.")
    if model_row["vpa_status"] == "SUCCEEDED" and not result["vpa_columns"] and not result["vpa_tables"]:
        notes.append("Storage analysis: completed with no column or table storage records.")
    elif model_row["vpa_status"] == "NOT_RUN":
        notes.append("Storage analysis: not requested by this analysis profile.")
    elif model_row["vpa_status"] == "FAILED":
        notes.append("Storage analysis: failed; see analysis run error details.")
    if model_row["refresh_status"] == "SUCCEEDED" and not result["refresh_rows"]:
        notes.append("Refresh history: no records were returned for the selected history window.")
    elif model_row["refresh_status"] == "NOT_RUN":
        notes.append("Refresh history: not requested by this analysis profile.")
    elif model_row["refresh_status"] == "FAILED":
        notes.append("Refresh history: failed; see analysis run error details.")
    if model_row["usage_status"] == "NOT_RUN":
        notes.append("Object usage: not run in the standard profile; use the deep profile to collect usage evidence.")
    elif model_row["usage_status"] == "SUCCEEDED" and not result["usage_rows"]:
        notes.append("Object usage: analysis completed and returned no observations.")
    elif model_row["usage_status"] == "FAILED":
        notes.append("Object usage: failed; see analysis run error details.")
    if model_row["direct_lake_status"] == "NOT_APPLICABLE":
        notes.append(
            "Direct Lake checks: not applicable to storage mode "
            + str(model_row.get("storage_mode") or "UNKNOWN")
            + "."
        )
    elif model_row["direct_lake_status"] == "SUCCEEDED" and not result["direct_lake_rows"]:
        notes.append("Direct Lake checks: completed with no fallback observations.")
    elif model_row["direct_lake_status"] == "NOT_RUN":
        notes.append("Direct Lake checks: not requested by this analysis profile.")
    elif model_row["direct_lake_status"] == "FAILED":
        notes.append("Direct Lake checks: failed; see analysis run error details.")
    if model_row["access_snapshot_status"] == "SUCCEEDED" and not result["access_rows"]:
        notes.append("Item access snapshot: completed and returned no explicit access records.")
    elif model_row["access_snapshot_status"] == "NOT_APPLICABLE_WORKSPACE_USER_PROFILE":
        notes.append("Item access snapshot: not applicable to the normal workspace-user profile.")
    elif model_row["access_snapshot_status"] == "NOT_RUN":
        notes.append("Item access snapshot: not requested by this analysis profile.")
    elif model_row["access_snapshot_status"] == "FAILED":
        notes.append("Item access snapshot: failed optional governance enrichment; see analysis run error details.")
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
    auto_date_present = any(is_auto_date_root_cause_finding(row) for row in findings)

    opportunity_groups = {}
    recommendation_groups = {}
    finding_rows = []
    finding_links = []
    recommendation_links = set()

    for finding in findings:
        finding_quality = grade_finding(finding)
        raw_domain = finding.get("category") or finding.get("impact_area") or "General optimization"
        raw_source = finding.get("source") or "Unknown source"
        consolidation = root_cause_grouping(finding, auto_date_present)
        domain = consolidation["domain"] if consolidation else raw_domain
        source = consolidation["source"] if consolidation else raw_source
        grouping_key = consolidation["key"] if consolidation else f"{source}|{domain}"
        opportunity_id = stable_id(semantic_model_id, "OPPORTUNITY", grouping_key)
        opportunity = opportunity_groups.setdefault(opportunity_id, {
            "findings": [],
            "recommendations": set(),
            "domain": domain,
            "source": source,
            "title": consolidation["title"] if consolidation else f"{domain} optimization",
        })
        opportunity["findings"].append(finding)

        recommendation_id = stable_id(
            semantic_model_id,
            "RECOMMENDATION",
            opportunity_id,
            consolidation["key"] if consolidation else finding.get("rule_id") or finding.get("rule_name"),
            consolidation["action"] if consolidation else finding.get("recommended_action"),
        )
        recommendation = recommendation_groups.setdefault(recommendation_id, {
            "findings": [],
            "opportunity_id": opportunity_id,
            "domain": domain,
            "source": source,
            "title": consolidation["title"] if consolidation else finding.get("rule_name") or "Optimization recommendation",
            "action": consolidation["action"] if consolidation else finding.get("recommended_action"),
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
            "finding_source": raw_source,
            "optimization_domain": raw_domain,
            "rule_name": finding.get("rule_name"),
            "severity": finding.get("severity"),
            "confidence": finding.get("confidence"),
            "impact_area": finding.get("impact_area"),
            "affected_object_type": finding.get("object_type"),
            "affected_table_name": finding.get("table_name"),
            "affected_object_name": finding.get("object_name"),
            **finding_locator_fields(finding),
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
            "opportunity_title": group["title"],
            "optimization_domain": group["domain"],
            "finding_source": group["source"],
            "highest_severity": highest.get("severity"),
            "finding_count": len(grouped_findings),
            "recommendation_count": len(group["recommendations"]),
            "estimated_saving_bytes_low": sum(row.get("estimated_saving_bytes_low") or 0 for row in grouped_findings),
            "estimated_saving_bytes_high": sum(row.get("estimated_saving_bytes_high") or 0 for row in grouped_findings),
            "change_risk": highest_risk.get("change_risk"),
            "opportunity_summary": summarize_opportunity(
                grouped_findings, group["source"], group["domain"]
            ),
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
    notebook.setdefault("metadata", {})["scanner_version"] = "2.6.3"

    for cell in cells:
        text = source_text(cell)
        text = re.sub(
            r'SCANNER_VERSION = "\d+\.\d+\.\d+"',
            'SCANNER_VERSION = "2.6.3"',
            text,
        )
        text = re.sub(
            r"Semantic Model Optimization Scanner — V(?:1\.2|2\.\d+(?:\.\d+)*)",
            "Semantic Model Optimization Scanner — V2.6.3",
            text,
        )
        if "bpa_extended = False" in text and "run_model_metadata_checks" not in text:
            text = text.replace(
                "bpa_extended = False\n",
                "bpa_extended = False\nrun_model_metadata_checks = True\n",
            )
        if "def validate_runtime_capabilities" in text and "semantic-model metadata inspection" not in text:
            text = text.replace(
                "    if run_bpa:\n        required.append((labs, \"run_model_bpa\", \"best-practice analysis\"))\n",
                "    if run_bpa:\n        required.append((labs, \"run_model_bpa\", \"best-practice analysis\"))\n"
                "    if run_model_metadata_checks:\n"
                "        required.append((labs, \"get_semantic_model_bim\", \"semantic-model metadata inspection\"))\n",
            )
        if "def safe_parameters_hash" in text and '"run_model_metadata_checks"' not in text:
            text = text.replace(
                '        "bpa_extended": bpa_extended,\n',
                '        "bpa_extended": bpa_extended,\n'
                '        "run_model_metadata_checks": run_model_metadata_checks,\n',
            )
        if "ANALYSIS_STATUS_KEYS" in text:
            text = text.replace(
                'ANALYSIS_STATUS_KEYS = ("bpa", "vpa", "refresh", "usage", "direct_lake")',
                'ANALYSIS_STATUS_KEYS = ("bpa", "vpa", "metadata", "refresh", "usage", "direct_lake")',
            )
            text = text.replace(
                '        "vpa": "NOT_RUN",\n        "refresh": "NOT_RUN",',
                '        "vpa": "NOT_RUN",\n        "metadata": "NOT_RUN",\n        "refresh": "NOT_RUN",',
            )
            text = text.replace(
                '        "vpa_status": gated_status if run_vertipaq else "NOT_RUN",\n        "refresh_status":',
                '        "vpa_status": gated_status if run_vertipaq else "NOT_RUN",\n'
                '        "metadata_status": gated_status if run_model_metadata_checks else "NOT_RUN",\n'
                '        "refresh_status":',
            )
            text = text.replace(
                '        "vpa_status": statuses["vpa"],\n        "refresh_status":',
                '        "vpa_status": statuses["vpa"],\n'
                '        "metadata_status": statuses["metadata"],\n'
                '        "refresh_status":',
            )
            if "model_metadata_bim" not in text:
                metadata_block = '''    if run_model_metadata_checks:
        try:
            model_metadata_bim = with_retry(
                "model_metadata",
                lambda: labs.get_semantic_model_bim(
                    dataset=target["model_id"],
                    workspace=target["workspace_id"],
                ),
            )
            findings.extend(normalize_model_metadata(target, model_metadata_bim, vpa_columns, vpa_tables))
            statuses["metadata"] = "SUCCEEDED"
        except Exception as exc:
            statuses["metadata"] = "FAILED"
            analysis_errors["model_metadata"] = truncate_error(exc)
    else:
        statuses["metadata"] = "NOT_RUN"

'''
                text = text.replace("    if run_refresh_history:\n", metadata_block + "    if run_refresh_history:\n")
        text = text.replace(
            "fail_pipeline_if_any_model_fails = False",
            "fail_pipeline_if_any_model_fails = True",
        )
        set_source(cell, text)

    quality_rules_source = QUALITY_RULES.read_text(encoding="utf-8")
    model_quality_rules_source = MODEL_QUALITY_RULES.read_text(encoding="utf-8").replace(
        "from __future__ import annotations\n", ""
    )
    curation_cell = (
        CURATION_CELL
        .replace("# __QUALITY_RULES_SOURCE__", quality_rules_source)
        .replace("# __MODEL_QUALITY_RULES_SOURCE__", model_quality_rules_source)
    )

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
            '            "model_metadata_analysis_status": row.get("metadata_status"),\n'
            '            "refresh_history_status": row["refresh_status"],\n'
            '            "direct_lake_analysis_status": row["direct_lake_status"],\n'
            '            "finding_count": row["finding_count"],\n'
            '            "component_errors": row["error_json"],',
        )
        execute = execute.replace(
            '    "error": truncate_error(run_error) if run_error else None,',
            '    "error": truncate_error(run_error) if run_error else model_failure_error,',
        )
    if '"model_metadata_analysis_status"' not in execute:
        execute = execute.replace(
            '            "storage_analysis_status": row["vpa_status"],\n',
            '            "storage_analysis_status": row["vpa_status"],\n'
            '            "model_metadata_analysis_status": row.get("metadata_status"),\n',
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
