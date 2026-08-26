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
