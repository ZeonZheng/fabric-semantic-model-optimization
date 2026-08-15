# Semantic Model Optimization Analytics

An FUAM-style Microsoft Fabric solution for read-only semantic-model analysis. One deployment notebook creates or updates the complete solution in a Fabric workspace:

- schema-enabled Lakehouse
- semantic-model scanner notebook
- parameterized ingestion pipeline
- Direct Lake semantic model
- Power BI report

After deployment, normal operations run only the `Load_SMO_Data` pipeline.

## Solution items

| Item | Fabric name | Purpose |
| --- | --- | --- |
| Lakehouse | `SMO_Analytics_Lakehouse` | Technical history plus seven AI-friendly business tables across meaningful schemas |
| Notebook | `SMO_Optimization_Scanner` | Read-only metadata, BPA, VertiPaq, refresh, and Direct Lake checks |
| Pipeline | `Load_SMO_Data` | Member-facing entry point with two simple parameters |
| Semantic model | `SMO_Analytics_SM` | Direct Lake model over the seven-table current-state contract |
| Report | `SMO_Analytics_Report` | Five pages and 15 visuals for overview, opportunities, recommendations, findings, and storage |

## Deploy

1. Download [`scripts/Deploy_SMO_Analytics.ipynb`](scripts/Deploy_SMO_Analytics.ipynb).
2. Create or open a Fabric workspace backed by Fabric capacity.
3. Import the notebook into that workspace.
4. Run all cells.

The notebook is idempotent by item name. Re-running it updates the deployed code while preserving Lakehouse data.

> The default bootstrap downloads this repository without credentials. If the repository is private, pass a short-lived GitHub token at runtime in `github_token_optional`; never save the token in the notebook.

## Run data collection

Open `Load_SMO_Data`, select **Run**, and enter:

| Parameter | Required | Example |
| --- | --- | --- |
| `workspace_ids` | Yes | `id1,id2` or one workspace ID per line |
| `model_ids_optional` | No | Blank scans all eligible models in the listed workspaces |

The pipeline runs under the identity of its last modifying user. During the user-authentication POC, that identity must be allowed to open the target semantic models through XMLA.

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

## Current stage

Version `0.2.4` restores the approved V2 business contract: five meaningful schemas, seven AI-friendly Direct Lake tables, per-model latest-state replacement, explicit empty-data explanations, and the five-page/15-visual report.
