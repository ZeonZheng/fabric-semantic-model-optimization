# Lakehouse V1 data contract

The scanner owns the `smopt` schema. Writes are idempotent Delta merges using stable business keys.

| Table | Grain / key | Purpose |
| --- | --- | --- |
| `smopt.smopt_scan_run` | one row per `scan_id` | Run status, timing, package versions, and target counts |
| `smopt.smopt_model_scan` | `scan_id` + `model_id` | Per-model execution status and component outcomes |
| `smopt.smopt_finding` | one row per `finding_id` | Normalized recommendations and technical evidence |
| `smopt.smopt_vpa_column` | one row per column observation | VertiPaq size and cardinality evidence |
| `smopt.smopt_vpa_table` | one row per table observation | VertiPaq table-size evidence |
| `smopt.smopt_object_usage` | one row per observed object | Optional usage evidence |
| `smopt.smopt_refresh` | one row per refresh observation | Refresh status and duration evidence |
| `smopt.smopt_direct_lake` | one row per Direct Lake check | Direct Lake configuration findings |
| `smopt.smopt_item_access_snapshot` | one row per principal snapshot | Observed item access for governed visibility |
| `smopt.smopt_model_access` | one row per model/principal grant | Explicit analytical access contract |
| `smopt.smopt_dim_model` | one row per model | Latest model state for reporting |

## Contract rules

- Additive columns are allowed within V1.
- Renaming, deleting, or changing the meaning/type of an existing column requires V2.
- `scan_id` groups all output from one execution.
- `finding_id` and evidence IDs are stable hashes where source data allows it.
- Byte-saving estimates are not claimed as validated CU savings.
- Raw provider payloads are retained only in designated JSON evidence columns.

