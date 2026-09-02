# M6.6.5 Anti-pattern Coverage Expansion

## Objective

Turn the Bank Customer Churn and Video Game Sales adverse models into a repeatable scanner acceptance corpus. M6.6.5 focuses on analysis correctness: specific root-cause detection, technically accurate evidence, and no silent gaps for the valid documented anti-patterns.

## Evidence baseline

| Item | Bank Customer Churn | Video Game Sales |
| --- | ---: | ---: |
| Documented items | 28 enumerated | 24 |
| Valid benchmark items | 27 | 24 |
| Exact matches in scanner 2.6.3 | 9 | 12 |
| Partial matches in scanner 2.6.3 | 8 | 4 |
| Silent misses in scanner 2.6.3 | 10 | 8 |
| Excluded contradictions | 1 | 0 |

Combined valid baseline: **51 items**. Scanner 2.6.3 produced 21 exact matches, 12 partial matches, and 18 silent misses.

Bank `AP-E02` is excluded. Its claim that the final model has no date column or date table conflicts with the injected `Fake_Calendar` table in the same final model.

## Scope decisions

- `AgeGroup` and `AgeGroupOrder` are not defined as special negative controls. The scanner must evaluate them with the same rule semantics as every other calculated column.
- Object names are never used as allowlists or suppressions.
- “Unused” is a usage-dependent assertion. When `object_usage_analysis_status` is not `SUCCEEDED`, metadata/storage rules may report visibility, cardinality, disconnection, or lack of references in the inspected model metadata, but must not state that a column or table is unused.
- Existing rule identifiers `MQ001` through `MQ030` remain stable. New rule identifiers extend the current catalog.

## Planned rule coverage

| Area | Rules |
| --- | --- |
| Relationships | MQ031 bidirectional filtering; MQ032 repeated active date roles |
| Naming and model semantics | MQ033 technical visible names; MQ034 implicit-measure reliance |
| DAX measures | MQ035 volatile functions; MQ036 nested IF; MQ037 trivial iterator; MQ038 unused VAR; MQ039 ratio format; MQ040 high-cardinality DISTINCTCOUNT; MQ045 magic constants; MQ046 repeated subexpression; MQ047 whole-table FILTER |
| Calculated columns | MQ041 text flag; MQ042 ordered category without Sort By; MQ043 aggregation in a calculated column; MQ044 EARLIER |
| Governance and organization | MQ048 exposed PII; MQ049 measures in fact-grain tables; MQ050 missing display folders; MQ051 exposed unmarked key; MQ052 disconnected redundant calculated table |
| Existing rule enhancements | MQ001 flat-model evidence; MQ010 DAX logical-operator handling; MQ024 non-additive column coverage; MQ025 month/weekday coverage; MQ027 high-cardinality visible text without Fact-name dependency |

## Acceptance gates

1. The machine-readable corpus contains 51 unique valid items and the single explicit `AP-E02` exclusion.
2. Every item declares at least one expected rule or BPA capability.
3. Every deterministic behavior is covered by a local regression fixture before implementation.
4. Existing MQ001-MQ030 test coverage remains green.
5. A live scan of both models produces no silent miss against the acceptance corpus.
6. Heuristic-only conclusions are graded `REVIEW_REQUIRED` and include the observed evidence.
7. Usage-dependent wording is absent unless object-usage analysis succeeded.

## Live acceptance record

Local implementation status:

- Acceptance corpus: 51 valid items plus one documented conflicting exclusion.
- Existing MQ001-MQ030 regression fixture: passing.
- New/enhanced rule fixture: passing for relationship, DAX, calculated-column, storage, naming, governance, and measure-organization behaviors.
- Notebook source parity: the deployable scanner embeds the exact tested analyzer source.
- Initial live release: solution `0.6.20`, scanner `2.6.4`.
- Live validation found two MQ013 misses, quoted table-name digits incorrectly
  classified by MQ045, and a storage-significant DateTime column below MQ027's
  original absolute threshold. Solution `0.6.21` / scanner `2.6.5` contains the
  regression-tested corrections.
- The first `2.6.5` rescan confirmed MQ013 and MQ045, but exposed a production
  evidence-key mismatch: runtime VPA rows provide `model_size_pct`, while the
  analyzer read the curated `percentage_of_semantic_model_size` name. Solution
  `0.6.22` / scanner `2.6.6` accepts both representations and tests the native
  runtime key.

Live TEST deployment, rescan, and Lakehouse item-by-item comparison remain pending and are required before M6.6.5 can be marked accepted.
