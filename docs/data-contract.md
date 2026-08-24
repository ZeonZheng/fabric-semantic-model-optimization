# Lakehouse V2 data contract

V2 separates append-only technical evidence from a meaningful, AI-friendly consumption layer. The report and downstream AI experiences use only the eleven business tables below.

## Direct Lake on SQL consumption tables

| Schema and table | Grain / key | Business meaning |
| --- | --- | --- |
| `analysis_control.semantic_model_analysis_runs` | one historical row per analysis and semantic model | Auditable scan profile, status, component coverage, timing, and errors |
| `semantic_model_metadata.semantic_models` | one current row per semantic model | Central, human-readable model dimension used by all report filters and facts |
| `semantic_model_best_practice.semantic_model_best_practice_rule_findings` | one current row per BPA rule finding and affected object | Best-practice-specific rule evidence, documentation, and remediation |
| `semantic_model_optimization.semantic_model_optimization_overview` | one current row per semantic model | Latest analysis status, action-queue counts, evidence-source coverage, and explanations for unavailable data |
| `semantic_model_optimization.semantic_model_optimization_opportunities` | one current row per model and optimization domain/source | Prioritized opportunities with actionability and actionable/review/suppressed finding rollups |
| `semantic_model_optimization.semantic_model_optimization_recommendations` | one current row per distinct model/rule/action | Implementation-ready actions with priority, business impact, validation, rollback, automation, risk, and evidence counts |
| `semantic_model_optimization.semantic_model_optimization_findings` | one current row per affected object finding | Complete evidence plus actionability, suppression reason, and deterministic priority |
| `semantic_model_vertipaq.semantic_model_column_storage` | one current row per analyzed model column | VertiPaq size, encoding, cardinality, and percentage of model size |
| `semantic_model_vertipaq.semantic_model_table_storage` | one current row per analyzed model table | Table row count and aggregate VertiPaq storage footprint |
| `semantic_model_optimization.semantic_model_optimization_opportunity_recommendation_links` | one opportunity/recommendation relationship | Explicit bridge for AI and analytical navigation |
| `semantic_model_optimization.semantic_model_optimization_opportunity_finding_links` | one opportunity/finding relationship | Explicit bridge from summarized opportunities to evidence |

The five reserved business schemas are:

- `analysis_control`
- `semantic_model_metadata`
- `semantic_model_vertipaq`
- `semantic_model_best_practice`
- `semantic_model_optimization`

Names use complete business entities rather than abbreviations. Columns explicitly use terms such as `semantic_model_id`, `analysis_status`, `affected_object_name`, and `data_availability_explanation` so both people and AI can infer grain and meaning.

## Empty-table expectations

Deployment initializes all eleven tables before importing the Direct Lake model.
It then synchronizes those schema-qualified tables to the Lakehouse SQL analytics
endpoint and refuses to import the model until every table reports a successful
metadata refresh.
Therefore, a reserved business schema with no tables indicates an initialization
failure and is not expected. Rows are populated only by `Load_SMO_Data`.

After a successful scan, three core tables must contain rows for each successfully
analyzed model: `semantic_model_analysis_runs`, `semantic_models`, and
`semantic_model_optimization_overview`. The remaining tables are evidence-driven:

- best-practice findings can be empty when BPA returns no violations;
- column and table storage can be empty when VertiPaq evidence is unavailable or
  not applicable;
- opportunities, recommendations, findings, and their link tables can be empty
  when the scan produces no corresponding actionable or reviewable evidence.

The overview row records whether a collector succeeded, was not run, was not
applicable, or returned zero records, so downstream AI/report consumers can
distinguish a valid empty result from missing data.

## Current-state behavior

- A successful or partially successful model analysis replaces only that semantic model's current-state slices.
- A full workspace scan reconciles the consumption layer to the eligible model inventory and removes stale rows for deleted, excluded, or no-longer-eligible models. A selected-model scan never removes other models.
- Analysis runs are retained as history and upserted by `analysis_id` plus `semantic_model_id`.
- A failed model analysis preserves the last usable current state.
- Re-running a scan does not duplicate report counts.
- The overview row records `NOT_RUN`, `NOT_APPLICABLE`, successful zero-record results, and a plain-language explanation.
- The default `workspace_user` profile records item-access evidence as `NOT_APPLICABLE_WORKSPACE_USER_PROFILE`; only the explicit `governance_admin` profile attempts that optional snapshot.
- Capacity labels, model-size metadata, and governance access snapshots are optional enrichment. Failures are retained under `optional_enrichment_warnings` and do not downgrade the core analysis status.
- High-severity counts return zero rather than blank.

## Actionability and priority

Raw findings are never deleted by quality grading. Each finding receives one of four explicit states:

| State | Meaning |
| --- | --- |
| `ACTIONABLE` | Evidence, confidence, recommended action, and change risk meet the execution threshold |
| `REVIEW_REQUIRED` | A human must confirm the evidence or review a high-risk design change |
| `INFORMATIONAL` | Useful context that does not yet form an executable change |
| `SUPPRESSED` | Retained for audit but removed from the action queue, for example a generated Auto Date/Time object or missing evidence |

`finding_priority_score` and `recommendation_priority_score` use a deterministic 0–100 scale. The corresponding bands are `P1_CRITICAL`, `P2_HIGH`, `P3_MEDIUM`, and `P4_LOW`. Generated Auto Date/Time objects are suppressed individually and consolidated into one model-level recommendation to replace them with an explicit date dimension.

## Technical evidence compatibility

The scanner continues writing the legacy `smopt.smopt_*` tables as a raw technical history and upgrade compatibility layer. They are intentionally excluded from the Direct Lake semantic model and should not be used for AI-generated reporting.

Byte-saving estimates remain directional discovery evidence, not validated CU savings. CU improvement requires a separate controlled before/after validation lifecycle.
