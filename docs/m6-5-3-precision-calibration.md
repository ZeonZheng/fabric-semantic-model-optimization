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

## TEST acceptance result

Scanner `2.4.0` / solution `0.6.2` passed the acceptance gate in
`SMO Analytics - Dev` against the same `SMO_Optimization1` semantic model.

- deployment initialization job: `6960e4bf-74b5-4534-b8e3-529eef704e20`;
- pipeline run: `20668881-7913-43e3-982c-ff2f72d0848f`;
- notebook run: `f206d17c-64be-497d-99a7-a05c40babf59`;
- scan ID: `a2e08de7-66b0-4c5a-8502-52a5e4a0467a`;
- result: `SUCCEEDED`, with best-practice, storage, and model-metadata analysis
  all `SUCCEEDED`;
- total findings: 1,022, down from 1,063;
- metadata-heuristic findings: 84, down from 125 (41 fewer, 32.8%);
- rule coverage: 30/30 (`MQ001` through `MQ030`).

The three precision targets changed as follows:

| Rule | Scanner 2.3.0 | Scanner 2.4.0 | Result |
|---|---:|---:|---|
| `MQ009` | 59 | 32 | Root-cause and generated/copy-column repetitions removed |
| `MQ011` | 13 | 1 | Only the exposed injected `YearlyIncomeText` issue remains |
| `MQ030` | 7 | 5 | Seven inactive relationships retained in five table-pair groups |

The `MQ009` evidence for the injected `Name` conflict is now exactly
`DimCustomer[Name], DimProduct[Name]`; `DimCustomerCopy[Name]` is no longer
repeated. `MQ030` retains all seven intentionally inactive relationships from
AP-30 in grouped technical evidence, which is expected because the benchmark
model deliberately contains no matching `USERELATIONSHIP` measures.

The acceptance result establishes M6.5.3 as complete. A clean-model/control
benchmark is still required before treating the heuristic set as generally
calibrated beyond this deliberately adverse model.

Report redesign and PROD Private Link remediation remain deferred.
