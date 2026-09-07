# Source References

This page records the primary repository sources used by the UC1a project documentation.

## 1. Microsoft Fabric AI Hackathon UC1a

Repository:

- https://github.com/SeanCowburnMSFT/Fabric-AI-Hackathon

Relevant folder:

- https://github.com/SeanCowburnMSFT/Fabric-AI-Hackathon/tree/main/Use%20Case%201a

Reference README:

- https://github.com/SeanCowburnMSFT/Fabric-AI-Hackathon/blob/main/Use%20Case%201a/readme.md

Reference notebook:

- https://github.com/SeanCowburnMSFT/Fabric-AI-Hackathon/blob/main/Use%20Case%201a/uc1a-semantic-model-optimization.ipynb

### Key source-verified notebook behaviors

The notebook title states:

```text
UC1 v02 - Semantic Model Optimisation (All Workspaces, No Input)
```

Tenant discovery uses:

```python
import sempy.fabric.admin as admin

ws_df = admin.list_workspaces(workspace_state="Active")
sm_df = admin.list_items(item_type="SemanticModel", state="Active")
```

The Stage 2 markdown says:

```text
Run BPA + VPA for every semantic model
```

The analysis loop uses:

```python
labs.run_model_bpa(
    dataset=model_name,
    workspace=ws_id,
    return_dataframe=True
)

labs.vertipaq_analyzer(
    dataset=model_name,
    workspace=ws_id
)
```

The notebook explicitly warns that broad execution can take a long time and recommends considering a subset of workspaces and semantic models.

### BPA normalization excerpt

Conceptually, the notebook maps BPA rows into:

```text
source
severity
object_type
object_name
rule
finding
recommended_fix
workspace_name
workspace_id
model_name
model_id
```

`finding` and `recommended_fix` may both be populated from the BPA description.

### VertiPaq normalization behavior

The notebook:

1. prefers a result object named `Columns`;
2. otherwise selects the first DataFrame-like object;
3. searches for a size field, otherwise a cardinality field;
4. sorts descending;
5. retains the top 15 rows;
6. emits generic values such as:

```text
severity        = Warning
object_type     = Column
rule            = High size / cardinality
finding         = Large contributor to model size
recommended_fix = Reduce cardinality (Date vs DateTime), remove unused columns, or aggregate.
```

Persistence uses:

```text
optimization_findings
optimization_runlog
```

The final optional quick-check cell refers to `_v02` table names even though the write cell uses the non-suffixed names. This is retained as a minor reference-code hardening observation rather than a core architectural argument.

---

## 2. Semantic Link Labs

Repository:

- https://github.com/microsoft/semantic-link-labs

Documentation:

- https://semantic-link-labs.readthedocs.io/

Key capabilities used by UC1a:

- Best Practice Analyzer;
- VertiPaq Analyzer;
- semantic-model metadata / XMLA-oriented analysis functions.

The project principle is to reuse this deterministic engine rather than replacing it with LLM-generated optimization guesses.

---

## 3. Internal Advanced Solution

Repository:

- https://github.com/ZeonZheng/fabric-semantic-model-optimization

Working branch for this documentation:

- `codex/m6-4`

Branch URL:

- https://github.com/ZeonZheng/fabric-semantic-model-optimization/tree/codex/m6-4

### Repository README

- https://github.com/ZeonZheng/fabric-semantic-model-optimization/blob/codex/m6-4/README.md

The branch README currently describes the following deployed solution items:

- `SMO_Analytics_Lakehouse`;
- `SMO_Scanner_Environment`;
- `SMO_Optimization_Scanner`;
- `Load_SMO_Data`;
- `SMO_Analytics_SM`;
- `SMO_Analytics_Report`.

The operational pipeline parameters are:

```text
workspace_ids
model_ids_optional
```

The README also states that the current `workspace_user` profile does not enumerate tenant workspaces, workspace members, or items through Fabric Admin APIs.

### Architecture document

- https://github.com/ZeonZheng/fabric-semantic-model-optimization/blob/codex/m6-4/docs/architecture.md

The architecture document records:

- deployment separated from recurring data collection;
- a published Fabric Environment for Semantic Link Labs;
- explicit workspace/model scope;
- technical history plus latest business state;
- deterministic quality grading;
- post-scan contract validation;
- Direct Lake analytics;
- Power BI reporting;
- controlled before/after CU validation;
- `workspace_user` as the default non-admin scan profile;
- optional isolated `governance_admin` enrichment.

---

## 4. Project Observations

The following evidence comes from internal project implementation and should be presented as project-specific observation rather than universal Fabric benchmarks.

### TEST broad-scan observation

A test execution involving approximately 70+ semantic models required substantial runtime. The test supported the decision to avoid making broad tenant-style analysis the default operating model.

### PROD Private Link observation

The project PROD environment has Private Link enabled. Notebook/Spark node startup overhead can consume a significant portion of the execution window before semantic-model analysis begins.

These observations are intentionally not assigned fixed timing or CU numbers until a controlled benchmark is captured.

---

## 5. Related Internal Validation Documentation

Existing project documentation on branch `codex/m6-4` includes milestone-specific validation such as:

- `docs/m6-5-1-test-acceptance.md`
- `docs/m6-5-2-analysis-quality.md`
- `docs/m6-5-3-precision-calibration.md`
- `docs/m6-5-4-control-model-calibration.md`
- `docs/m6-5-5-actionability-calibration.md`
- `docs/m6-5-6-root-cause-consolidation.md`
- `docs/m6-6-report-consumption-review.md`
- `docs/m6-6-1-viewer-ux-redesign.md`
- `docs/m6-6-2-insight-correctness.md`
- `docs/m6-6-3-report-review-workbench.md`
- `docs/m6-6-4-report-and-antipattern-revalidation.md`
- `docs/m6-6-5-antipattern-coverage-expansion.md`

These files are part of the existing project and are referenced only as evidence. This new `uc1a-project-documentation/` folder does not modify them.
