# Semantic Model Optimization Analytics

An FUAM-style Microsoft Fabric solution for read-only semantic-model analysis. One deployment notebook creates or updates the complete solution in a Fabric workspace:

- schema-enabled Lakehouse
- published Fabric Environment with the scanner extension library
- semantic-model scanner notebook
- parameterized ingestion pipeline
- Direct Lake semantic model
- Power BI report

After deployment, normal operations run only the `Load_SMO_Data` pipeline.

## Solution items

| Item | Fabric name | Purpose |
| --- | --- | --- |
| Lakehouse | `SMO_Analytics_Lakehouse` | Raw technical history plus eleven AI-friendly business tables across meaningful schemas |
| Environment | `SMO_Scanner_Environment` | Publishes Semantic Link Labs; the scanner uses Fabric Runtime SemPy and validates required APIs at runtime |
| Notebook | `SMO_Optimization_Scanner` | Read-only metadata, BPA, VertiPaq, refresh, and Direct Lake checks |
| Pipeline | `Load_SMO_Data` | Member-facing entry point with two simple parameters |
| Semantic model | `SMO_Analytics_SM` | Direct Lake on SQL model centered on the `semantic_models` business dimension |
| Report | `SMO_Analytics_Report` | Five visible pages with synchronized scope filters, drillthrough, actionability/priority filtering, and storage analysis |

## Deploy

1. Download [`scripts/Deploy_SMO_Analytics.ipynb`](scripts/Deploy_SMO_Analytics.ipynb).
2. Create or open a Fabric workspace backed by Fabric capacity.
3. Import the notebook into that workspace.
4. Run all cells.

The notebook is idempotent by item name. Re-running it updates the deployed code while preserving Lakehouse data.

Deployment publishes `SMO_Scanner_Environment` before importing the scanner.
Normal pipeline runs never execute `%pip`; the scanner validates the attached
environment by importing the required modules and checking the APIs needed by the
selected authentication mode and analysis options. Package versions are logged for
diagnostics but are not exact-match deployment gates. This keeps the pipeline
compatible with Fabric High Concurrency sessions and avoids fighting the SemPy
version supplied by the selected Fabric Runtime.

The checked-in bootstrap is pinned to `codex/m6-4`. It also verifies that the
downloaded deployment manifest declares the same branch, so a branch mismatch
fails before any Fabric item is changed.

> The default bootstrap downloads this repository without credentials. If the repository is private, pass a short-lived GitHub token at runtime in `github_token_optional`; never save the token in the notebook.

## Run data collection

Open `Load_SMO_Data`, select **Run**, and enter:

| Parameter | Required | Example |
| --- | --- | --- |
| `workspace_ids` | Yes | `id1,id2` or one workspace ID per line |
| `model_ids_optional` | No | Blank scans all eligible models in the listed workspaces |

The pipeline runs under the identity of its last modifying user. During the user-authentication POC, that identity must be allowed to open the target semantic models through XMLA.

After deployment and before the first scan, the eleven business tables exist but
are empty by design. After a successful scan, the following core tables must
contain rows for every successfully analyzed model:

- `analysis_control.semantic_model_analysis_runs`
- `semantic_model_metadata.semantic_models`
- `semantic_model_optimization.semantic_model_optimization_overview`

Evidence tables can legitimately contain zero rows when their corresponding
collector returns no evidence. For example, a model with no BPA violations has no
best-practice finding rows, and a model without available VertiPaq evidence has no
column/table storage rows. A reserved business schema with no tables is never
expected after a successful deployment; rerun the deployment notebook and inspect
the initialization failure.

## Guardrails

- The scanner does not change scanned semantic models.
- No customer data or credentials belong in Git.
- Estimated savings are directional until a controlled before/after validation is completed.
- `Load_SMO_Data` is the operational entry point; the deployment notebook is only for initial deployment and upgrades.

## Repository structure

```text
config/   deployment manifest and order
docs/     architecture and data contract
scripts/  deployment notebook and deployment engine
src/      Fabric item definitions
tests/    static repository validation
```

## Validate locally

```bash
python tests/validate_repo.py
```

Use [`docs/m6-5-1-test-acceptance.md`](docs/m6-5-1-test-acceptance.md) for the
validated platform baseline and
[`docs/m6-5-2-analysis-quality.md`](docs/m6-5-2-analysis-quality.md) for the
anti-pattern coverage gate. Precision and root-cause grouping are documented in
[`docs/m6-5-3-precision-calibration.md`](docs/m6-5-3-precision-calibration.md).
Normal-model false-positive calibration is documented in
[`docs/m6-5-4-control-model-calibration.md`](docs/m6-5-4-control-model-calibration.md).
Priority and remediation-queue calibration is documented in
[`docs/m6-5-5-actionability-calibration.md`](docs/m6-5-5-actionability-calibration.md).
Cross-source root-cause consolidation is documented in
[`docs/m6-5-6-root-cause-consolidation.md`](docs/m6-5-6-root-cause-consolidation.md).

## Current stage

Version `0.6.5` completes M6.5.6 Cross-source Root-cause Consolidation on the
validated TEST-tenant baseline. Scanner `2.6.1` retains the M6.4 production-stabilization
contract: Lakehouse → SQL analytics endpoint → Direct Lake semantic-model lineage,
an unpinned Semantic Link environment, and a `workspace_user` profile that uses the
current identity and workspace-scoped APIs only. It does not enumerate tenant
workspaces, workspace members, or items through Fabric Admin APIs. SPN validation
is likewise an effective-access check against only the explicitly approved
workspace scope.

Capacity labels, model-size metadata, and the optional governance item-access
snapshot are enrichment evidence. Their absence is recorded as a warning and no
longer changes an otherwise successful core scan to `PARTIAL` or `FAILED`. The
`governance_admin` profile is explicit and is the only path that invokes a Fabric
Admin API.

M6.5.1 added a post-scan business-layer quality gate. It verifies overview/detail
counts, latest-analysis consistency, opportunity rollups, link-table referential
integrity, actionability values, priority scores/bands, recommendation guidance,
and automation eligibility. Empty evidence remains valid when the overview gives
an explicit collector-specific explanation.

M6.5.2 adds read-only Model.bim inspection and 30 deterministic metadata rules for
the 30-item `SMO_Optimization1` anti-pattern benchmark. Generated Auto Date/Time,
technical table prefixes, and missing descriptions are consolidated into model-level
root causes to reduce noise. A metadata-analysis failure makes the scan `PARTIAL`
instead of silently publishing BPA/VertiPaq-only results. Report redesign and PROD
Private Link network remediation remain outside this release.

M6.5.3 preserves the 30/30 TEST coverage gate while removing secondary findings
already explained by a stronger root cause. Ambiguous-name and numeric-to-text
checks ignore hidden/generated date objects; ambiguous-name checks also exclude
wide-table and direct-copy table replicas already covered by `MQ001`/`MQ002`.
Inactive relationships are matched to the specific `USERELATIONSHIP` expression
that invokes them and unresolved relationships are grouped by table pair.

M6.5.4 adds a normal-model control gate. Generated Auto Date/Time tables no longer
create duplicate-signature findings, `FORMAT` is classified as numeric-to-text only
when it references a known numeric column, and intentionally textual label measures
do not require a numeric format string. The adverse-model 30/30 coverage gate remains
mandatory so precision improvements cannot silently reduce anti-pattern recall. The
live TEST gate passed: the adverse model retained 30/30 rules, while the control model
fell from 143 to 138 findings by removing exactly the five targeted false positives.

M6.5.5 calibrates operational priority independently from finding volume. P1 is
reserved for explicitly critical or quantified evidence, high-risk unquantified
changes require review, and broad categories no longer imply automation eligibility.
Only explicitly allowlisted deterministic metadata operations enter the future
approval-controlled script queue. The live TEST gate retained 30/30 adverse-model
MQ coverage, removed volume-generated P1 recommendations from both models, and
reduced script candidates from 11 to 5 on the adverse model and from 8 to 4 on the
control model.

M6.5.6 consolidates overlapping Auto Date/Time evidence across BPA categories and
model-metadata rules into one model-level opportunity and one recommendation. Raw
findings retain their original source, domain, rule, object, and technical evidence;
only their rollup key changes. `MQ022` joins the Auto Date/Time root cause only when
the same model also contains direct Auto Date/Time evidence, preventing an unrelated
missing-date-table finding from being relabeled. The live TEST gate passed on both
models: the control model retained 138 findings and 9 detected MQ rules while its
recommendations fell from 28 to 25; the adverse model retained 1,021 findings and
30/30 MQ coverage while its recommendations fell from 56 to 54. Each model now has
exactly one Auto Date/Time opportunity and one recommendation, so M6.5.6 is complete.
