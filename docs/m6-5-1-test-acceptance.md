# M6.5.1 TEST acceptance

## Scope

M6.5.1 is accepted against the TEST tenant. Use:

- `SMO Analytics - Dev` for development and primary validation;
- TEST `ANG_FabricPOC` for clean deployment and upgrade regression;
- PROD `ANG_FabricPOC` only after the external Private Link/XMLA network dependency is resolved.

Report redesign is outside this acceptance. Existing report bindings must continue
to work, but the gate focuses on scanner output, business-table integrity, and
recommendation quality.

## Deployment gate

1. Import and run `scripts/Deploy_SMO_Analytics.ipynb` from `codex/m6-4`.
2. Confirm that deployment completes without a failed Environment publish, SQL
   endpoint table sync, semantic-model refresh, or report binding.
3. Confirm lineage is:

   `SMO_Analytics_Lakehouse` → SQL analytics endpoint → `SMO_Analytics_SM` → `SMO_Analytics_Report`.

4. Confirm all five reserved business schemas exist and all eleven business tables
   are present before the first scan.

## Scan gate

1. Run `Load_SMO_Data` as a normal workspace user for an explicitly approved
   workspace/model scope.
2. Confirm the Pipeline and notebook both succeed and report Scanner `2.2.0`.
3. Confirm the three core tables contain the successfully analyzed model:

   - `analysis_control.semantic_model_analysis_runs`;
   - `semantic_model_metadata.semantic_models`;
   - `semantic_model_optimization.semantic_model_optimization_overview`.

4. Confirm the overview `analysis_id` and `analysis_status` match the model
   dimension's latest analysis and the current scan result.
5. Confirm the default profile is `workspace_user` and item-access status is
   `NOT_APPLICABLE_WORKSPACE_USER_PROFILE`, not a failed Admin API call.

## Valid empty evidence

An evidence table may contain zero rows only when the overview explains why:

| Evidence | Valid empty example |
| --- | --- |
| Best-practice findings | BPA completed with no rule violations |
| Column/table storage | Storage analysis completed with no returned records, was not requested, or failed visibly |
| Opportunities/recommendations/findings | No qualifying evidence was produced |
| Refresh history | No records in the selected history window or collector not requested |
| Object usage | Standard profile did not run usage analysis or no observations were returned |
| Direct Lake checks | Not applicable to the model storage mode or no fallback observations |
| Item access | Not applicable to `workspace_user`; available only through the explicit governance profile |

A reserved business schema with no tables, a missing core row, or a blank
`data_availability_explanation` is not a valid empty result.

## Recommendation-quality gate

The Scanner rejects the run when any of the following is inconsistent:

- overview counts do not match opportunity, recommendation, or finding detail rows;
- opportunity rollups do not match their related findings/recommendations;
- a finding or recommendation has an invalid actionability state;
- a priority score is outside 0–100 or does not match its priority band;
- an actionable/review-required recommendation lacks an action, reason, impact,
  validation method, or rollback guidance;
- informational or suppressed content is marked as automation eligible;
- recommendation/finding link rows are missing, duplicated, or orphaned;
- a description-only finding without technical evidence is promoted directly to
  `ACTIONABLE`.

## Acceptance result

M6.5.1 passes when deployment and scanning succeed in both TEST workspaces, the
notebook's business-layer quality gate passes, valid empty evidence is explicitly
explained, and no normal-user run invokes a Fabric Admin API.

## Recorded TEST result — 2026-08-25

| Check | `SMO Analytics - Dev` | TEST `ANG_FabricPOC` |
| --- | --- | --- |
| Deployment | `SUCCEEDED`, solution `0.6.0` | upgraded `0.5.5` → `0.6.0`, `SUCCEEDED` |
| Semantic-model source | `DirectLakeOnSqlEndpoint` | `DirectLakeOnSqlEndpoint` |
| SQL endpoint readiness | 11/11 source tables ready | 11/11 source tables ready |
| Pipeline run ID | `17d1af66-e22f-49dc-ada8-6915edbd32e2` | `aed4493d-4058-4d08-899c-b8007b3ed43b` |
| Scanner run ID | `59dd33e3-5c08-486c-b6ee-4e403f156d98` | `080e6b90-68d4-4a50-8d31-76af7346a66a` |
| Result | 1 succeeded, 0 partial/failed/skipped | 1 succeeded, 0 partial/failed/skipped |
| Findings | 938 | 938 |
| Runtime | Semantic Link `0.11.2`; Labs `0.17.0` | Semantic Link `0.11.2`; Labs `0.17.0` |
| Profile | `workspace_user` | `workspace_user` |

Both runs completed after `validate_curated_scan_output`, so overview/detail
counts, latest-analysis consistency, opportunity rollups, link integrity,
actionability, priority, guidance, automation eligibility, and orphan checks all
passed. Both runs reported `NOT_CHECKED_USER_MODE`, no component errors, and did
not enter the `governance_admin` branch.

The TEST login identity used for these runs is also a tenant administrator. The
evidence therefore proves that the default code path is workspace-scoped and does
not invoke Fabric Admin APIs; it does not by itself prove identity-role parity with
a non-admin user. The existing PROD non-admin validation remains blocked by the
tenant Private Link/XMLA network dependency and is intentionally outside this
release gate.
