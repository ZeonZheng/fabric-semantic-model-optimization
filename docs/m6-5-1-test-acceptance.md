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

