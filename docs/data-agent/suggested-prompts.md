# Teams Suggested Prompts — Shared / Multi-user SMO Usage

**Date:** 2026-09-11  
**Target surface:** Microsoft Teams via `Fabric Optimization_Agent_V2`  
**Status:** V1 configured

## Why these prompts exist

The published Teams agent is expected to be used by multiple members. The shared SMO Analytics Lakehouse can therefore contain:

- scans initiated by different users;
- multiple scans of the same semantic model;
- historical scan executions;
- current-state optimization results;
- multiple workspaces and semantic models.

The suggested prompts are intentionally designed to help users constrain scope before interpreting results.

A critical distinction is:

- **scan execution history** -> `analysis_control.semantic_model_analysis_runs`
- **current optimization state** -> current-state SMO business tables such as `semantic_model_optimization_overview`

`Latest scan execution` and `current optimization state` must not be treated as the same concept.

## V1 Suggested Prompts

### 1. Latest scan

**Title:** `Latest scan`

**Prompt:**

> Show me the latest semantic model scan execution across all available scan records.

Purpose: identify the newest scan execution in the shared environment regardless of model/workspace.

---

### 2. Latest scan for a model

**Title:** `Latest scan for a model`

**Prompt:**

> Show me the latest scan execution for a semantic model. Ask me for the model name if I haven't specified it.

Purpose: parameterized model-level execution lookup.

---

### 3. Latest scans in a workspace

**Title:** `Latest scans in a workspace`

**Prompt:**

> Show me the latest scan execution for each semantic model in a workspace. Ask me for the workspace name first.

Purpose: parameterized workspace-level execution lookup.

---

### 4. Model scan history

**Title:** `Model scan history`

**Prompt:**

> Show me the recent scan history for a semantic model. Ask me for the model name and how many recent scans I want to see.

Purpose: inspect multiple historical executions for one semantic model.

---

### 5. Current model status

**Title:** `Current model status`

**Prompt:**

> Show me the current optimization status for a semantic model. Ask me for the model name if needed.

Purpose: query the current optimization state rather than historical execution records.

---

### 6. What should I fix?

**Title:** `What should I fix?`

**Prompt:**

> Show me what I should fix first for a semantic model. Ask me which model to analyze.

Purpose: return prioritized recommendations for a specified semantic model while preserving ACTIONABLE vs REVIEW_REQUIRED semantics.

---

### 7. Failed recent scans

**Title:** `Failed recent scans`

**Prompt:**

> Show me recent failed or incomplete semantic model scans and explain why they failed.

Purpose: operational troubleshooting in a shared scan environment.

---

### 8. BPA issues for a model

**Title:** `BPA issues for a model`

**Prompt:**

> Show me the most frequent Best Practice Analyzer issues for a semantic model. Ask me which model to analyze.

Purpose: parameterized BPA analysis.

---

### 9. Storage hotspots

**Title:** `Storage hotspots`

**Prompt:**

> Show me the largest VertiPaq tables and columns for a semantic model. Ask me which model to analyze.

Purpose: parameterized storage optimization analysis.

---

### 10. Compare models

**Title:** `Compare models`

**Prompt:**

> Compare the current optimization status of two semantic models. Ask me for both model names.

Purpose: parameterized cross-model comparison using current-state metrics rather than inventing a model-level health/quality score.

## UX / orchestration rules

When a request for `latest`, `current`, or `recent` is ambiguous, the agent should not silently guess the intended scope when that scope materially changes the result.

Preferred behavior:

1. ask for `semantic_model_name` when a model must be specified;
2. ask for `workspace_name` when workspace scope is needed;
3. use workspace + model ID/name to disambiguate duplicate/similar model names;
4. distinguish historical scan execution from current optimization state;
5. keep different semantic models separate unless the user explicitly asks for aggregation/comparison.

## Useful free-form patterns

Users can also ask questions such as:

- `Show me the latest scan for [model name].`
- `Show me the latest scan for [model name] in [workspace name].`
- `Show me the last 5 scans for [model name].`
- `Show me all failed scans from the last 7 days.`
- `Show me the current optimization status for [model name].`
- `What should I fix first for [model name]?`
- `Show me P1 and P2 recommendations for [model name].`
- `Show me REVIEW_REQUIRED recommendations for [model name].`
- `Show me the top storage-consuming columns for [model name].`
- `Compare [model A] with [model B].`

## Deferred multi-user enhancement

The current V1 consumption contract does not expose a reliable scan-initiator identity field such as `requested_by`, `run_by`, or user UPN in the documented business contract.

Therefore prompts such as these should not be advertised yet:

- `Show me my latest scans.`
- `Show scans run by John.`
- `Who scanned this model last?`

A future multi-user auditability enhancement could add fields such as:

- `requested_by_upn`
- `requested_by_display_name`
- `execution_identity_type`
- `scan_trigger_source`

Once such lineage is available, user-scoped scan-history prompts can be added safely.
