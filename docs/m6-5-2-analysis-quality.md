# M6.5.2 analysis-quality calibration

## Objective

Use the deliberately degraded TEST semantic model `SMO_Optimization1` as a
ground-truth benchmark. A successful Pipeline run is necessary but not sufficient:
the scanner must explain every documented anti-pattern with object-level evidence
or an intentionally consolidated model-level root cause.

Primary TEST target:

- workspace: `SMO Analytics - Dev` (`cc9ce2d3-5e27-47e3-9e69-06cf7324dbb4`);
- semantic model: `SMO_Optimization1` (`aab74ce1-dbca-4e71-9be2-edf8ee60cfb8`).

The pre-calibration Scanner 2.2.0 run produced 938 findings. That count is only a
volume baseline; it does not prove coverage because most rows came from BPA and
many repeated the same root cause.

## Detection architecture

Scanner 2.3.0 keeps BPA and VertiPaq, then reads Model.bim through the current
workspace user's read-only semantic-model connection. The metadata layer inspects
tables, columns, measures, expressions, relationships, roles, perspectives,
formatting, descriptions, data types, and sort/summarization properties. It does
not call a Fabric Admin API.

If Model.bim retrieval or deterministic analysis fails, `metadata` is recorded in
the component error and the model result is `PARTIAL`; the scanner must not report
a fully successful quality analysis based only on BPA/VertiPaq.

## Ground-truth mapping

| Anti-pattern | Deterministic rule | Expected signal |
| --- | --- | --- |
| AP-01 | `MQ001` | wide, disconnected, text-heavy fact-grain table |
| AP-02 | `MQ002` | bare calculated-table copy or identical non-trivial column signature |
| AP-03 | `MQ003` | disconnected table with no measures |
| AP-04 | `MQ004` | staging/temp/view/duplicate-calendar naming |
| AP-05 | `MQ005` | date-like String or FORMAT/DATEVALUE expression |
| AP-06 | `MQ006` | calculated column containing `RELATED` |
| AP-07 | `MQ007` | row arithmetic persisted in a fact calculated column |
| AP-08 | `MQ008`, `MQ023` | volatile function and floating-point type |
| AP-09 | `MQ009` | same non-key column name across tables |
| AP-10 | `MQ010` | multi-attribute concatenated calculated column |
| AP-11 | `MQ011` | numeric value converted to text with `FORMAT` |
| AP-12 | `MQ012` | generated/junk/placeholder column name |
| AP-13 | `MQ013`, `MQ025` | direct column alias and month name without sort |
| AP-14 | `MQ014` | dimension-hosted measure aggregating a fact |
| AP-15 | `MQ015` | identical normalized measure expressions |
| AP-16 | `MQ016` | pass-through measure containing only another measure reference |
| AP-17 | `MQ017` | hardcoded literal in `CALCULATE`/`FILTER` |
| AP-18 | `MQ018` | `FILTER(ALL(...))`/`FILTER(ALLEXCEPT(...))` pattern |
| AP-19 | `MQ019` | visible measure without a format string |
| AP-20 | `MQ020` | Auto Date/Time tables, consolidated once per model |
| AP-21 | `MQ021` | hidden tables participating in relationships |
| AP-22 | `MQ022` | date-like tables but none explicitly marked as date table |
| AP-23 | `MQ023` | Double/Real columns, consolidated once per model |
| AP-24 | `MQ024` | implicit aggregation on identifier/date-sequence columns |
| AP-25 | `MQ025` | month-name String without `sortByColumn` |
| AP-26 | `MQ026` | exposed Fact/Dim prefixes, consolidated once per model |
| AP-27 | `MQ027` | high-cardinality fact-table text from VertiPaq evidence |
| AP-28 | `MQ028` | missing descriptions summarized by object type and sample |
| AP-29 | `MQ029` | implicit measures and/or missing roles/perspectives |
| AP-30 | `MQ030` | inactive relationship with no `USERELATIONSHIP` measure |

## Acceptance gate

1. Deploy solution `0.6.1` from `codex/m6-4` into `SMO Analytics - Dev`.
2. Run `Load_SMO_Data` for the target workspace/model and confirm Scanner `2.3.0`.
3. Confirm `model_metadata_analysis_status = SUCCEEDED` in the notebook summary.
4. Filter current findings to `finding_source = MODEL_METADATA_HEURISTIC`.
5. Confirm every AP-01 through AP-30 mapping above has at least one matching rule
   and the named injected object appears in evidence where applicable.
6. Review any additional deterministic finding as a potential real pre-existing
   issue; do not classify it as false positive only because it was absent from the
   injection notes.
7. Confirm `MQ020`, `MQ026`, and `MQ028` each produce one model-level root-cause
   row rather than one row per affected generated/undocumented object.

The local repository fixture exercises all `MQ001`–`MQ030` rules and fails
`tests/validate_repo.py` if any rule becomes unreachable or the three consolidation
contracts regress. Actual TEST-tenant coverage is recorded only after the deployed
Scanner 2.3.0 run completes.
