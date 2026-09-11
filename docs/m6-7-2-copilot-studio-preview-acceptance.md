# M6.7.2 — Copilot Studio Preview Acceptance

**Date:** 2026-09-11  
**Branch:** `codex/m6-4`  
**Copilot Studio agent:** `Fabric Optimization_Pre_V2`  
**Model:** GPT-5.6 Reasoning  
**Fabric tool:** `Fabric Optimization Assistant v2`  
**Knowledge:** none  
**Memory:** Off  
**Status:** Preview routing accepted and Copilot Studio agent published; Teams channel configuration is next

## Purpose

Validate the Copilot Studio orchestration layer on top of the published SMO Fabric Data Agent before publishing to Teams.

The acceptance goal is not to re-test NL2SQL itself. That was validated at the Fabric Data Agent layer. This phase verifies:

1. Copilot Studio invokes the Fabric Data Agent for SMO-data questions;
2. returned answers remain grounded in the SMO data;
3. Copilot Studio does not reintroduce unsafe or unsupported interpretations;
4. the V1 evidence-lineage limitation is preserved.

## Architecture under test

```text
Teams / end user
      │
      ▼
Copilot Studio
Fabric Optimization_Pre_V2
      │
      ▼
Fabric Data Agent tool
Fabric Optimization Assistant v2
      │
      ▼
SMO_Analytics_Lakehouse
```

## Preview test results

### Test 1 — Current semantic-model inventory

Prompt:

`Which semantic models are available in SMO Analytics?`

Result: **PASS**

Observed behavior:

- Copilot Studio invoked `DataAgent_Fabric_Optimization_Assistant_v2`.
- The answer returned exactly five current semantic models:
  - Bank Customer Churn
  - Maven Fuzzy Factory
  - SMO_Optimization1_copy
  - US Candy Distributor
  - Video Game Sales
- Workspace was correctly shown as `Fabric AI Hackathon`.
- The response did not invent old or unavailable model names.

### Test 2 — What should I fix first?

Prompt:

`What should I fix first?`

Result: **PASS with wording hardening**

Observed behavior:

- Copilot Studio invoked the Fabric Data Agent.
- It identified `Large high-cardinality column` for Maven Fuzzy Factory as the only `P1_CRITICAL` item, but correctly stated that it is `REVIEW_REQUIRED` with `HIGH` change risk and should be investigated/validated rather than automatically implemented.
- It separately identified an immediately implementable `ACTIONABLE` P2 item for `SMO_Optimization1_copy`.
- Directional storage-savings semantics were preserved.

Hardening note:

For future wording, distinguish clearly between:

- **highest-priority item to review**, and
- **highest-priority item to implement**.

A `REVIEW_REQUIRED` item should not be presented as the first item to implement.

### Test 3 — Cross-model current-state comparison

Prompt:

`Compare the current optimization status of Bank Customer Churn and US Candy Distributor.`

Result: **PASS with wording hardening**

Observed behavior:

- Copilot Studio invoked the Fabric Data Agent.
- Current-state metrics were returned for both models without the previous duplicated-row problem.
- The answer explicitly noted that no separate overall optimization score was returned.
- Actionability, priority, BPA, model-size, recommendation and finding metrics were surfaced successfully.

Hardening note:

The answer described Bank Customer Churn as having the "stronger current optimization posture". SMO V1 does not define a model-level optimization/health/quality score, so future responses should avoid declaring one model globally "better", "healthier", or "stronger" unless the user explicitly asks for a judgment and the comparison criteria are clearly stated.

### Test 4 — BPA rule frequency across current models

Prompt:

`Which Best Practice Analyzer rules are triggered most frequently across all currently available semantic models?`

Result: **PASS**

Observed behavior:

- Copilot Studio invoked the Fabric Data Agent.
- The answer scoped the result to five currently available models.
- It returned ranked BPA rule frequencies, including:
  - Visible objects with no description — 702 findings / 5 models
  - Do not summarize numeric columns — 226 / 5
  - Avoid using calculated columns — 191 / 5
  - Column references should be fully qualified — 160 / 4
- Current-model scoping remained correct; the prior stale-model-list issue did not reappear.

### Test 5 — Actionable recommendations with broader evidence

Prompt:

`For Video Game Sales, what are the top actionable recommendations and what broader evidence supports them?`

Result: **PASS**

Observed behavior:

- Copilot Studio invoked the Fabric Data Agent.
- It returned 7 actionable recommendations for Video Game Sales, including two P2 items and five P3 items.
- The answer surfaced broader supporting evidence for each optimization area.
- Most importantly, it explicitly stated that the findings are evidence associated with broader optimization opportunities and **must not be interpreted as deterministic one-to-one mappings to individual recommendations unless explicitly linked in SMO data**.

This confirms that the selected V1 **Option A** evidence semantics survived the Copilot Studio orchestration layer.

## Acceptance summary

| Test | Result |
|---|---|
| Current model inventory | PASS |
| Fix-first routing/actionability | PASS with wording hardening |
| Cross-model current-state comparison | PASS with wording hardening |
| BPA across current models | PASS |
| Broader evidence semantics | PASS |

### Routing gate

**5/5 Copilot Studio Preview tests invoked the Fabric Data Agent successfully.**

No evidence was observed of Copilot Studio bypassing the Fabric tool and answering SMO-data questions from generic web or model knowledge.

## Publish decision

Copilot Studio Preview was considered **functionally accepted for publication**.

The following response guardrails were added before publication:

1. For "what should I fix first?", distinguish the highest-priority item requiring review from the highest-priority item that is immediately actionable. `REVIEW_REQUIRED` must be reviewed and validated before implementation even when its priority score is higher than an `ACTIONABLE` recommendation.
2. When comparing semantic models, do not describe one model as globally better, healthier, or having a stronger optimization posture unless the user explicitly requests a judgment and the comparison criteria are stated. SMO V1 does not provide a model-level optimization, health, quality, or maturity score.

The Copilot Studio agent `Fabric Optimization_Pre_V2` was then successfully **published on 2026-09-11**. The Monitor view became available after publication, confirming that a live version exists. No production Teams traffic has been generated yet.

## Current handoff point

```text
Fabric Data Agent                      ✅ Published
Copilot Studio Preview acceptance     ✅ 5/5 routing tests passed
Final response guardrails             ✅ Added
Copilot Studio agent                  ✅ Published
        │
        ▼
Teams + Microsoft 365 channel         ← NEXT
        │
        ▼
Install agent in Teams
        │
        ▼
Final Teams E2E acceptance
```

## Next phase

Configure the **Teams + Microsoft 365** channel. For the initial V1 validation, Teams-only availability is preferred unless Microsoft 365 Copilot exposure is explicitly required. After connecting the channel, install the agent for the maker first and run a small Teams E2E regression set before wider sharing or organization catalog submission.
