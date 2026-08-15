# Lakehouse V2 data contract

V2 separates append-only technical evidence from a meaningful, AI-friendly current-state consumption layer. The report and downstream AI experiences use only the seven business tables below.

## Direct Lake consumption tables

| Schema and table | Grain / key | Business meaning |
| --- | --- | --- |
| `semantic_model_optimization.semantic_model_optimization_overview` | one current row per semantic model | Latest analysis status, business counts, evidence-source coverage, and explanations for unavailable data |
| `semantic_model_optimization.semantic_model_optimization_opportunities` | one current row per model and optimization domain/source | Prioritized optimization opportunities derived from normalized findings |
| `semantic_model_optimization.semantic_model_optimization_recommendations` | one current row per distinct model/rule/action | Recommended actions with risk, validation, and estimated storage benefit context |
| `semantic_model_optimization.semantic_model_optimization_findings` | one current row per affected object finding | Detailed evidence, severity, affected object, and recommended action |
| `semantic_model_vertipaq.semantic_model_column_storage` | one current row per analyzed model column | VertiPaq size, encoding, cardinality, and percentage of model size |
| `semantic_model_optimization.semantic_model_optimization_opportunity_recommendation_links` | one opportunity/recommendation relationship | Explicit bridge for AI and analytical navigation |
| `semantic_model_optimization.semantic_model_optimization_opportunity_finding_links` | one opportunity/finding relationship | Explicit bridge from summarized opportunities to evidence |

The five reserved business schemas are:

- `analysis_control`
- `semantic_model_metadata`
- `semantic_model_vertipaq`
- `semantic_model_best_practice`
- `semantic_model_optimization`

Names use complete business entities rather than abbreviations. Columns explicitly use terms such as `semantic_model_id`, `analysis_status`, `affected_object_name`, and `data_availability_explanation` so both people and AI can infer grain and meaning.

## Current-state behavior

- A successful or partially successful model analysis replaces only that semantic model's seven current-state slices.
- A failed model analysis preserves the last usable current state.
- Re-running a scan does not duplicate report counts.
- The overview row records `NOT_RUN`, `NOT_APPLICABLE`, successful zero-record results, and a plain-language explanation.
- High-severity counts return zero rather than blank.

## Technical evidence compatibility

The scanner continues writing the legacy `smopt.smopt_*` tables as a technical history and upgrade compatibility layer. They are intentionally excluded from the Direct Lake semantic model and should not be used for AI-generated reporting.

Byte-saving estimates remain directional discovery evidence, not validated CU savings. CU improvement requires a separate controlled before/after validation lifecycle.
