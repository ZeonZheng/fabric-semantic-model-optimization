# SMO Data Agent Configuration

This folder preserves the configuration used for the PROD SMO Analytics Data Agent (`Fabric Optimization Assistant v2`) and its Microsoft Teams consumption UX as of 2026-09-11.

## Configuration files

- [`agent-instructions.md`](agent-instructions.md) — Fabric Data Agent behavior and response guardrails.
- [`data-source-description.md`](data-source-description.md) — description of the SMO Analytics Lakehouse and supported question domains.
- [`data-source-instructions.md`](data-source-instructions.md) — compact NL2SQL/table-routing/join/actionability guidance.
- [`example-queries.json`](example-queries.json) — 14 natural-language/T-SQL few-shot examples used for V1 NL2SQL grounding.
- [`suggested-prompts.md`](suggested-prompts.md) — 10 Teams starter prompts designed for shared/multi-user scan history, model/workspace scoping, current-state analysis, BPA, VertiPaq, and comparison workflows.

## Implementation and acceptance history

See:

- [`../m6-7-1-prod-data-agent-configuration-and-acceptance.md`](../m6-7-1-prod-data-agent-configuration-and-acceptance.md) — PROD Data Agent configuration, acceptance tests, A10 lineage limitation, V1 Option A, and deferred Option B.
- [`../m6-7-2-copilot-studio-preview-acceptance.md`](../m6-7-2-copilot-studio-preview-acceptance.md) — Copilot Studio preview routing and response acceptance.
- [`../m6-7-3-teams-e2e-acceptance-and-compatibility.md`](../m6-7-3-teams-e2e-acceptance-and-compatibility.md) — Microsoft Teams E2E acceptance and the new-vs-classic Copilot Studio compatibility finding (`MCS-4031`).
- [`../m6-7-4-shared-teams-agent-ux-and-suggested-prompts.md`](../m6-7-4-shared-teams-agent-ux-and-suggested-prompts.md) — shared-user UX design, 10 Suggested Prompts, execution-history/current-state distinction, and deferred scan-initiator identity enhancement.

## V1 evidence semantics

V1 may present findings as evidence associated with the broader optimization opportunity. It must not claim a deterministic one-to-one mapping from an individual recommendation to an individual finding unless such lineage is explicitly available in the data contract.

## V1 shared-user semantics

The shared Teams agent can contain old and new scan executions from multiple models/workspaces. User-facing prompts therefore distinguish:

- latest/recent **scan execution history**;
- **current optimization state**;
- semantic-model scope;
- workspace scope.

Prompts that require scan-initiator identity, such as `Show me my latest scans`, are intentionally deferred until a reliable user/initiator field is exposed in the consumption contract.
