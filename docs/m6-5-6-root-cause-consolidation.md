# M6.5.6 Cross-source root-cause consolidation

## Purpose

M6.5.6 removes duplicated work items without hiding scanner evidence. The first
calibration target is Auto Date/Time, where BPA and deterministic model-metadata
analysis describe different symptoms of the same model-level design decision.
Report redesign remains outside this release.

## Scanner 2.6.0 TEST baseline

The live TEST scans showed the following duplicate rollups:

| Model | BPA rollups | Metadata rollups | Total Auto Date recommendations |
| --- | --- | --- | ---: |
| `Getting Started in Power BI` | Performance and Maintenance | MQ020 and MQ022 | 4 |
| `SMO_Optimization1` | Performance | MQ020 and MQ022 | 3 |

The control model contains four generated-object BPA findings spanning two BPA
categories. The adverse model contains twelve generated-object BPA findings. Both
models also contain MQ020 and MQ022. These findings are valid evidence and must not
be deleted merely because they share a root cause.

## Scanner 2.6.1 behavior

1. Generated `LocalDateTable_*` and `DateTableTemplate_*` object findings and MQ020
   are direct Auto Date/Time root-cause evidence.
2. MQ022 joins that root cause only when direct Auto Date/Time evidence exists in the
   same model analysis. Without direct evidence, MQ022 remains independent.
3. All matching findings use the canonical rollup key `AUTO_DATE_TIME`, source
   `ROOT_CAUSE_CONSOLIDATION`, domain `Date handling`, and recommendation title
   `Replace Auto Date/Time with an explicit date dimension`.
4. Finding rows retain their original source, optimization domain, rule name, object
   identity, description, action, and technical evidence.
5. The canonical recommendation remains `REVIEW_REQUIRED`, score 72 (`P2_HIGH`), and
   `MANUAL_REVIEW`; it is not a generated script candidate.

## Dual-model acceptance gate

1. Both scans complete as `SUCCEEDED` with scanner `2.6.1`.
2. Adverse-model findings remain 1,021 with MQ001-MQ030 coverage intact; control-model
   findings remain 138 with 9 detected MQ rule codes.
3. Each model has exactly one Auto Date/Time opportunity and one recommendation.
4. The consolidated recommendation links every generated-object, MQ020, and eligible
   MQ022 finding; raw finding sources remain BPA or `MODEL_METADATA_HEURISTIC`.
5. Recommendation totals fall only by the removed duplicate rollups, and all existing
   business-layer referential-integrity gates continue to pass.

## TEST acceptance

Pending deployment and dual-model rescan.
