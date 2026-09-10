# SMO Data Agent Configuration

This folder preserves the configuration used for the PROD SMO Analytics Data Agent (`Fabric Optimization Assistant v2`) as of 2026-09-10.

## Configuration files

- [`agent-instructions.md`](agent-instructions.md) — Fabric Data Agent behavior and response guardrails.
- [`data-source-description.md`](data-source-description.md) — description of the SMO Analytics Lakehouse and supported question domains.
- [`data-source-instructions.md`](data-source-instructions.md) — compact NL2SQL/table-routing/join/actionability guidance.
- [`example-queries.json`](example-queries.json) — 14 natural-language/T-SQL few-shot examples used for V1.

## Implementation and acceptance history

See [`../m6-7-1-prod-data-agent-configuration-and-acceptance.md`](../m6-7-1-prod-data-agent-configuration-and-acceptance.md) for:

- PROD deployment context;
- selected Lakehouse schemas/tables;
- core and advanced acceptance tests;
- A10 recommendation-to-finding lineage limitation;
- selected V1 Option A publication strategy;
- deferred Option B exact lineage enhancement;
- Copilot Studio and Microsoft Teams handoff plan.

## V1 evidence semantics

V1 may present findings as evidence associated with the broader optimization opportunity. It must not claim a deterministic one-to-one mapping from an individual recommendation to an individual finding unless such lineage is explicitly available in the data contract.
