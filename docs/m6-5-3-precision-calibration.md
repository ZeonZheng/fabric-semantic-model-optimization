# M6.5.3 precision and root-cause calibration

## Baseline

The accepted Scanner 2.3.0 TEST run against `SMO_Optimization1` completed with:

- scan ID `9fa32e22-31e9-4012-b6d7-3f7f97f33fc6`;
- 1,063 total findings;
- 125 `MODEL_METADATA_HEURISTIC` findings;
- all `MQ001` through `MQ030` rules detected;
- `MQ020`, `MQ026`, and `MQ028` each consolidated to one model-level row.

The largest deterministic groups were `MQ009` (59), `MQ011` (13), and `MQ030`
(7). Coverage was correct, but these groups repeated stronger root causes or did
not match relationship usage precisely enough.

## Precision changes

### MQ009 — ambiguous exposed names

Only visible business-facing columns participate in ambiguity detection. Columns
from hidden/generated Auto Date/Time tables are excluded. Columns copied into a
wide disconnected table (`MQ001`) or a direct calculated-table copy (`MQ002`) are
also excluded so the same structural defect is not repeated once per column.

The injected `DimCustomer[Name]` / `DimProduct[Name]` conflict remains detectable.

### MQ011 — numeric values formatted as text

The rule now applies only to exposed columns. Hidden system date-table FORMAT
expressions are explained by the consolidated `MQ020` Auto Date/Time root cause.
The injected `DimCustomer[YearlyIncomeText]` issue remains detectable.

### MQ030 — inactive relationship intent

`USERELATIONSHIP` is matched to the exact from/to column references instead of
treating one occurrence anywhere in the model as coverage for every inactive
relationship. Remaining unresolved relationships are grouped by table pair, with
all column-level relationship references retained in technical evidence.

## Acceptance gate

1. Local fixture still reaches all `MQ001`–`MQ030` rules.
2. Hidden/generated objects do not inflate `MQ009` or `MQ011`.
3. A relationship invoked by a matching `USERELATIONSHIP` expression is excluded.
4. Multiple unresolved inactive relationships for one table pair produce one
   `MQ030` finding with a relationship count and complete evidence.
5. Deploy Scanner `2.4.0` to TEST and rerun the same target model.
6. Confirm 30/30 rule coverage and compare deterministic counts against the
   Scanner 2.3.0 baseline above.

Report redesign and PROD Private Link remediation remain deferred.
