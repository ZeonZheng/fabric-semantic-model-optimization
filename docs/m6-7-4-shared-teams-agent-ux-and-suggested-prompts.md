# M6.7.4 — Shared Teams Agent UX and Suggested Prompts

**Date:** 2026-09-11  
**Branch:** `codex/m6-4`  
**Teams agent:** `Fabric Optimization_Agent_V2`  
**Connected Fabric Data Agent:** `Fabric Optimization Assistant v2`  
**Status:** Shared-user starter UX configured after successful Teams E2E validation

## Context

The SMO Agent Consumption Layer has already been validated end-to-end through the classic Copilot Studio connected-agent path and Microsoft Teams.

The next UX concern is shared use by multiple members. In a shared environment, the SMO Analytics Lakehouse may contain:

- data scanned by different members;
- multiple scans of the same semantic model;
- older historical scan executions;
- current optimization state from the latest usable analysis;
- semantic models from multiple workspaces.

Because of this, generic starter prompts such as only `What should I fix first?` are not sufficient for production/pilot use. Users need prompts that establish execution/model/workspace scope explicitly.

## Design decision

The Teams **Suggested Prompts** are intentionally different from the Fabric Data Agent's 14 NL-to-SQL few-shot examples.

```text
Fabric Data Agent
14 Example Queries
        ↓
NL2SQL grounding / query-generation behavior

Teams Suggested Prompts
        ↓
User onboarding / scope selection / common shared-use workflows
```

The 14 example queries remain unchanged and continue to support Data Agent query generation.

Ten user-facing Suggested Prompts were added to the classic Copilot Studio Teams agent.

## Configured Suggested Prompts

1. **Latest scan**
   - `Show me the latest semantic model scan execution across all available scan records.`

2. **Latest scan for a model**
   - `Show me the latest scan execution for a semantic model. Ask me for the model name if I haven't specified it.`

3. **Latest scans in a workspace**
   - `Show me the latest scan execution for each semantic model in a workspace. Ask me for the workspace name first.`

4. **Model scan history**
   - `Show me the recent scan history for a semantic model. Ask me for the model name and how many recent scans I want to see.`

5. **Current model status**
   - `Show me the current optimization status for a semantic model. Ask me for the model name if needed.`

6. **What should I fix?**
   - `Show me what I should fix first for a semantic model. Ask me which model to analyze.`

7. **Failed recent scans**
   - `Show me recent failed or incomplete semantic model scans and explain why they failed.`

8. **BPA issues for a model**
   - `Show me the most frequent Best Practice Analyzer issues for a semantic model. Ask me which model to analyze.`

9. **Storage hotspots**
   - `Show me the largest VertiPaq tables and columns for a semantic model. Ask me which model to analyze.`

10. **Compare models**
    - `Compare the current optimization status of two semantic models. Ask me for both model names.`

The detailed prompt catalog is maintained in [`data-agent/suggested-prompts.md`](data-agent/suggested-prompts.md).

## Key semantic distinction reinforced by the UX

The agent must keep these concepts separate:

```text
Latest / recent scan execution
        ↓
analysis_control.semantic_model_analysis_runs

Current optimization state
        ↓
current-state business tables
(e.g. semantic_model_optimization_overview)
```

A failed newest execution can coexist with older usable current-state optimization data. User-facing prompts should therefore not imply that `latest execution` and `current state` are interchangeable.

## Parameterization pattern

Instead of requiring users to manually edit placeholders such as `<model_name>`, starter prompts ask the agent to request missing scope interactively.

Examples:

```text
User clicks: Latest scan for a model
Agent: Which semantic model would you like me to check?
User: Maven Fuzzy Factory
```

```text
User clicks: Latest scans in a workspace
Agent: Which workspace should I use?
User: Fabric AI Hackathon
```

This approach is preferred for Teams because it works better for non-technical users and reduces accidental cross-model or cross-workspace interpretation.

## Deferred limitation: scan initiator identity

A shared multi-user environment naturally creates potential questions such as:

- `Show me my latest scans.`
- `Who scanned this model last?`
- `Show scans initiated by <user>.`

These are **not advertised in V1** because the current documented business consumption contract does not expose a reliable scan-initiator identity field.

Potential future fields:

- `requested_by_upn`
- `requested_by_display_name`
- `execution_identity_type`
- `scan_trigger_source`

This is now recorded as a future multi-user auditability enhancement rather than being inferred from unsupported data.

## Updated Agent Consumption Layer state

```text
SMO PROD deployment                         ✅
5-model PROD validation                     ✅
Fabric Data Agent                           ✅
14 Data Agent few-shot examples             ✅
Data Agent acceptance                       ✅
Classic Copilot Studio connected-agent path ✅
Teams publication                           ✅
Teams end-user authentication               ✅
Teams E2E validation                        ✅
10 shared-user Suggested Prompts            ✅

Known/deferred items:
Exact Recommendation → Finding lineage      ⚠️ Option A retained
New Copilot Studio tool-based Teams path    ⚠️ MCS-4031 compatibility issue
Scan initiator identity / per-user history  🔵 Backlog
```

## Current recommended V1 delivery path

```text
SMO Analytics
   ↓
Fabric Optimization Assistant v2
   ↓
Classic Copilot Studio connected agent
Fabric Optimization_Agent_V2
   ↓
Microsoft Teams
   ↓
Shared-member usage with scoped Suggested Prompts
```

At this point, the SMO **Agent Consumption Layer V1 is operational and user-onboarding UX is configured**. Remaining work should shift toward pilot feedback, measurable business impact, cost-vs-savings evidence, final documentation, and leadership/DevOps closure rather than additional core agent plumbing.
