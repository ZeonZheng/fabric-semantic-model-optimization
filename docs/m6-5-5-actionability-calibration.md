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

Live Scanner 2.6.0 TEST results will be added after deployment and dual-model rerun.
