# M6.5.4 Control-model calibration

## Purpose

M6.5.4 introduces a normal semantic model as a precision control alongside the
deliberately adverse `SMO_Optimization1` recall benchmark. A control model is not
expected to return zero findings: confirmed technical or semantic-quality issues
remain visible. The gate removes only findings whose evidence does not support the
rule conclusion.

## TEST baseline

| Property | Value |
| --- | --- |
| Workspace | `Fabric` (`aa0ae44c-3492-46f7-9eef-81745a4a06bb`) |
| Semantic model | `Getting Started in Power BI` (`8f9454fc-d4f4-454a-93de-7c3043ee009f`) |
| Pipeline run | `90f305b6-05a8-497c-95f0-8ecf7ded03c0` |
| Scanner run | `a0e8cca6-fd7f-45af-9a2b-863397728cbf` |
| Scan ID | `d44f5f46-5d36-484a-aa57-30d3768c948e` |
| Scanner | `2.4.0` |
| Result | `SUCCEEDED` |

The baseline produced 143 findings: 121 BPA findings and 22 deterministic
model-metadata findings. Twelve of the thirty metadata rules matched. This does not
mean the control model is “bad”; BPA reports individual technical-hygiene violations,
while the metadata layer provides compact semantic-model root causes.

## Confirmed false positives and correction

| Rule | Baseline | Correction |
| --- | ---: | --- |
| MQ002 duplicate table | 1 | Exclude generated `LocalDateTable_*` and `DateTableTemplate_*` signatures. |
| MQ011 numeric-to-text | 2 | Require `FORMAT` to reference a known numeric column; date formatting is not numeric-to-text. |
| MQ019 missing measure format | 2 | Exclude measures that are demonstrably textual by type, name, or expression. |

The expected stable result, if BPA evidence does not change, is 138 total findings:
121 BPA and 17 metadata findings. Nine metadata rule codes should remain represented.

## Dual-model acceptance gate

1. The adverse model must still produce all MQ001–MQ030 rule codes.
2. The control model must no longer produce the five confirmed false-positive rows.
3. Genuine control findings such as hard-coded filter literals, Auto Date/Time,
   missing descriptions, ambiguous exposed names, and invalid implicit aggregation
   remain visible.
4. Both scans must complete with core status `SUCCEEDED` under the normal
   `workspace_user` profile.

## TEST acceptance (2026-08-26)

The `0.6.3` solution was deployed to `SMO Analytics - Dev` from `codex/m6-4`.
The deployment initialization job was
`d6e470ac-0b02-4c41-a8bb-e159dfddc84f`; all eleven Lakehouse tables became
available through the SQL analytics endpoint and the Direct Lake semantic model
refresh completed.

| Gate | Adverse model | Control model |
| --- | --- | --- |
| Semantic model | `SMO_Optimization1` | `Getting Started in Power BI` |
| Pipeline run | `060bcedb-d5e8-4a15-952f-7fb78f27142b` | `6ab4e52a-643e-456c-a850-536d9c7fe747` |
| Analysis ID | `134eb8b7-4024-4e7b-9bdc-3ed2698279f2` | `da6f2cd9-a983-419b-bf18-c42cc73fc696` |
| Scanner | `2.5.0` | `2.5.0` |
| Status | `SUCCEEDED` | `SUCCEEDED` |
| Total findings | 1,021 | 138 |
| BPA findings | 938 | 121 |
| Metadata findings | 83 | 17 |
| Distinct MQ rules | 30/30 | 9/30 |

The adverse model retained all MQ001-MQ030 rule codes (scanner 2.4.0 produced
1,022 total / 84 metadata findings). The one-row reduction is the intended
text-label-measure correction, so recall did not regress.

The control result exactly matched the predicted 138 findings. Compared with its
2.4.0 baseline, the five confirmed false positives were removed and no BPA finding
changed:

| Metric | Scanner 2.4.0 | Scanner 2.5.0 | Change |
| --- | ---: | ---: | ---: |
| Total findings | 143 | 138 | -5 |
| BPA | 121 | 121 | 0 |
| Metadata | 22 | 17 | -5 |
| Distinct MQ rules | 12 | 9 | -3 |
| MQ002 + MQ011 + MQ019 targeted rows | 5 | 0 | -5 |

The remaining control metadata distribution is MQ009=6, MQ010=2, MQ017=3,
MQ020=1, MQ021=1, MQ022=1, MQ024=1, MQ028=1, and MQ029=1. These findings retain
technical evidence and are review candidates rather than calibration false
positives. The dual-model acceptance gate therefore passes.
