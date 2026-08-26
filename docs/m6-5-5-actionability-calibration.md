# M6.5.5 Actionability and priority calibration

## Purpose

M6.5.5 turns technically valid findings into an operationally credible work queue.
It does not change rule recall or redesign the report. The gate checks whether the
priority band, review boundary, and future automation label match the strength and
completeness of the evidence.

## Scanner 2.5.0 TEST baseline

| Model | Recommendations | Actionable | Review required | Informational | P1 | P2 | Script candidates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Getting Started in Power BI` | 28 | 19 | 7 | 2 | 7 | 17 | 8 |
| `SMO_Optimization1` | 56 | 33 | 15 | 8 | 23 | 20 | 11 |

The distribution is not operationally credible. Finding volume promoted maintenance
hygiene into P1, while every recommendation in the broad `Formatting` domain could
become a script candidate. This included data-category selection and relationship
data-type redesign even though neither recommendation contains a deterministic target
state suitable for generated remediation.

## Scanner 2.6.0 calibration

1. Finding count remains visible as breadth evidence but no longer increases the
   priority score or moves a recommendation/opportunity into a higher band.
2. P1 requires an explicitly `CRITICAL` finding or quantified impact evidence.
3. High-risk, unquantified structural changes remain `REVIEW_REQUIRED` and cannot
   enter P1 solely because their source severity is `ERROR`.
4. Scoring continues to consider severity, confidence, evidence, action, impact area,
   implementation risk, and quantified/reclaimable bytes.
5. `SCRIPT_CANDIDATE` uses an explicit deterministic-operation allowlist:
   - disable implicit summarization for numeric columns;
   - hide foreign-key columns;
   - mark identified primary-key columns;
   - apply the BPA-defined whole-number format;
   - apply the BPA-defined Yes/No flag format.
6. Recommendations that require a business decision, inferred data category,
   data-type redesign, or unspecified format remain `MANUAL_REVIEW`.

## Dual-model acceptance gate

1. Both models complete with status `SUCCEEDED` and the adverse model retains all
   MQ001-MQ030 rule codes.
2. The control model has no P1 recommendation unless the scan provides critical or
   quantified evidence.
3. Repeated description/naming/formatting hygiene cannot become P1 solely because
   many objects are affected.
4. Script candidates are a strict subset of the deterministic allowlist; all other
   actionable recommendations remain manual-review candidates.
5. Finding, recommendation, and opportunity counts and their link-table integrity
   continue to pass the existing business-layer quality gate.

## TEST acceptance (2026-08-26)

Solution `0.6.4` was deployed to `SMO Analytics - Dev`; scanner initialization job
`fd53f519-fcca-4b6f-8e84-ea3fc893e78b` completed and the SQL endpoint reported all
eleven model-source tables ready.

| Gate | Adverse model | Control model |
| --- | --- | --- |
| Pipeline run | `7c597e35-5252-4c30-82ac-675a183bae5f` | `f0110213-be3d-4812-b96d-226ca622290c` |
| Analysis ID | `7b935671-ae75-4442-a3b9-c737a2778183` | `688aae34-1897-42d1-8d00-da5bd4cdcf01` |
| Scanner / status | `2.6.0` / `SUCCEEDED` | `2.6.0` / `SUCCEEDED` |
| Findings / metadata MQ coverage | 1,021 / 30 of 30 | 138 / 9 of 30 |
| Recommendations | 56 | 28 |
| Actionable / review / informational | 33 / 15 / 8 | 19 / 7 / 2 |
| P1 / P2 / P3 / P4 | 0 / 13 / 35 / 8 | 0 / 5 / 21 / 2 |
| Script candidates | 5 | 4 |

The actionability states and rule recall remained stable; the change affected only
priority and automation classification. In both models, P1 fell to zero because no
scan evidence was explicitly critical or quantified. The adverse model retained its
core structural and DAX issues in P2 rather than being flattened into low priority.

The control script queue contains only `Do not summarize numeric columns`, `Hide
foreign keys`, `Mark primary keys`, and the deterministic whole-number format rule.
The adverse queue adds the deterministic Yes/No flag format rule. Data-category
selection, relationship data-type redesign, unspecified measure/date formats, and
object renaming are no longer script candidates.

The M6.5.5 dual-model gate passes. A separate follow-up remains: Auto Date/Time can
still appear as overlapping BPA and MQ recommendations. Cross-source root-cause
consolidation should merge those recommendation rows without discarding their
original finding evidence.
