# UC1a Evidence Matrix

This matrix maps the main project claims to their evidence source and evidence class.

## Evidence classes

- **Source verified** — confirmed directly in repository code or repository documentation.
- **Project observation** — observed during implementation/validation in TEST or PROD.
- **Engineering assessment** — a design conclusion derived from source evidence and project observations.

| ID | Claim | Evidence | Class | Confidence / note |
|---|---|---|---|---|
| E-01 | Microsoft UC1a uses deterministic Semantic Link Labs analysis instead of asking an LLM to guess optimizations. | Microsoft `Use Case 1a/readme.md` | Source verified | High |
| E-02 | Original notebook is designed as "All Workspaces, No Input". | Original notebook title and markdown | Source verified | High |
| E-03 | Stage 1 enumerates active workspaces and semantic models through `sempy.fabric.admin`. | `admin.list_workspaces()` and `admin.list_items()` in original notebook | Source verified | High |
| E-04 | Stage 2 analyzes each inventory record with `run_model_bpa()` and `vertipaq_analyzer()`. | Original notebook model loop | Source verified | High |
| E-05 | Admin APIs are used for inventory discovery, while BPA/VPA are executed per semantic model. | Original notebook imports and execution flow | Source verified | High |
| E-06 | The discovered inventory becomes the default analysis workload. | `for ... in inventory.iterrows()` in original notebook | Source verified | High |
| E-07 | The original notebook warns that broad execution can take a long time and suggests using a subset. | Original notebook Stage 2 markdown note | Source verified | High |
| E-08 | Microsoft documentation warns that VertiPaq analysis of a very large model consumes meaningful CUs and memory. | Microsoft UC1a README Step 2 risk note | Source verified | High |
| E-09 | BPA output is normalized into a small generic findings contract. | `_append_bpa_rows()` in original notebook | Source verified | High |
| E-10 | BPA `finding` and `recommended_fix` can both derive from the description. | `_append_bpa_rows()` mapping | Source verified | High |
| E-11 | VertiPaq normalization prefers `Columns`, falls back to the first DataFrame-like object, and retains top 15 rows. | `_extract_vpa_columns_frame()` and `_append_vpa_rows(..., top_n=15)` | Source verified | High |
| E-12 | VertiPaq normalized findings use generic severity/rule/finding/recommendation values. | `_append_vpa_rows()` | Source verified | High |
| E-13 | Rich VertiPaq metrics used for ranking are not fully retained in the final generic finding record. | `_append_vpa_rows()` output schema | Source verified | High |
| E-14 | The simplified one-row-per-finding design is intentionally optimized for Data Agent top-N queries. | Microsoft UC1a README Step 3 | Source verified | High |
| E-15 | A TEST execution involving approximately 70+ semantic models required substantial runtime. | Internal project test | Project observation | Medium/High; not a formal benchmark |
| E-16 | PROD Private Link increases practical notebook/Spark startup overhead in the project environment. | Internal PROD investigation | Project observation | High for project environment; not a universal Fabric benchmark |
| E-17 | Tenant-wide recurring analysis is not an efficient default operating model for this environment. | E-07, E-08, E-15, E-16 | Engineering assessment | High |
| E-18 | V0.x should separate user intent from tenant discovery. | Internal V0.x design | Engineering assessment / design evidence | High |
| E-19 | V0.x uses `workspace_ids` plus optional model targeting rather than tenant-wide no-input execution. | V0.x design and later `Load_SMO_Data` operating contract | Design/source evidence | High |
| E-20 | Current-user-first execution reduces unnecessary admin dependency for core scanning. | V0.x design and later `workspace_user` profile | Design/source evidence | High |
| E-21 | Later SMO solution uses `Load_SMO_Data` as the normal operational entry point. | Repository README on `codex/m6-4` | Source verified | High |
| E-22 | Later SMO solution includes Lakehouse, Fabric Environment, scanner, pipeline, Direct Lake model, and Power BI report. | Repository README on `codex/m6-4` | Source verified | High |
| E-23 | `workspace_user` does not enumerate tenant workspaces/members/items through Fabric Admin APIs. | `docs/architecture.md` and README on `codex/m6-4` | Source verified | High |
| E-24 | Optional governance-admin enrichment is isolated from core optimization status. | `docs/architecture.md` on `codex/m6-4` | Source verified | High |
| E-25 | Advanced solution preserves technical history and publishes structured business-facing tables. | README and `docs/architecture.md` on `codex/m6-4` | Source verified | High |
| E-26 | Advanced solution validates business-contract quality before Pipeline success. | `docs/architecture.md` on `codex/m6-4` | Source verified | High |
| E-27 | Estimated savings remain directional until controlled before/after measurement. | Repository guardrails / architecture | Source verified | High |

## Claims that should not be overstated

### 70+ model test

Use wording such as:

> During project testing, a run involving approximately 70+ semantic models required substantial runtime.

Do **not** convert this into a universal statement such as "70 models always take X minutes" unless a controlled benchmark is later captured.

### Private Link startup overhead

Use wording such as:

> In the project PROD environment, Private Link and Fabric runtime startup overhead reduced the effective execution window available for analysis.

Do **not** claim that Private Link always causes a fixed startup penalty across all Fabric environments.

### Reference implementation maturity

Preferred wording:

> The reference implementation successfully demonstrates the intended end-to-end pattern, while several implementation choices are optimized for hackathon simplicity rather than enterprise operational requirements.

Avoid wording such as:

> The Microsoft implementation is bad / broken / production-unusable.

The project assessment concerns fitness for the target enterprise operating model, not the validity of the reference architecture.
