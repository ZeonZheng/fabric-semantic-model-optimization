# M6.7.3 — Teams E2E Acceptance and Copilot Studio Compatibility Finding

**Date:** 2026-09-11  
**Branch:** `codex/m6-4`  
**Classic Copilot Studio agent:** `Fabric Optimization_Agent_V2`  
**Connected Fabric Data Agent:** `Fabric Optimization Assistant v2`  
**Teams status:** Published and validated  
**Status:** E2E accepted on the classic/connected-agent path

## Purpose

Record the final end-to-end validation of the SMO Agent Consumption Layer through Microsoft Teams, and document the compatibility difference observed between the new Copilot Studio tool-based experience and the classic connected-agent experience.

## Architecture validated

```text
Microsoft Teams
      │
      ▼
Classic Copilot Studio agent
Fabric Optimization_Agent_V2
      │
      ▼
Connected Fabric Data Agent / MCP
Fabric Optimization Assistant v2
      │
      ▼
SMO_Analytics_Lakehouse
```

## Classic Copilot Studio configuration

The connected Fabric Data Agent was configured under the classic Copilot Studio **Agents** section.

Key settings:

- Connected agent: `Fabric Optimization Assistant v2`
- Fabric Data Agent MCP server enabled
- Credentials to use: **End user credentials**
- Ask end user before running: **No**
- Data Agent ID and Workspace ID populated from the published Fabric Data Agent
- Web Search disabled for the SMO validation path
- Main agent instructions retained the SMO routing, actionability, evidence, and savings guardrails

This preserves user-level authorization through Fabric rather than replacing it with a shared service identity.

## Classic Copilot Studio test-pane validation

Two core tests were re-run in the classic Copilot Studio test pane.

### Test 1 — Current semantic-model inventory

Prompt:

`Which semantic models are available in SMO Analytics?`

Result: **PASS**

Observed behavior:

- The connected Fabric Data Agent was invoked through MCP.
- The current five-model scope was returned correctly:
  - Bank Customer Churn
  - Maven Fuzzy Factory
  - SMO_Optimization1_copy
  - US Candy Distributor
  - Video Game Sales
- Latest scans were reported as successful.
- Scanner version `2.6.6` was preserved.

### Test 2 — Fix-first prioritization

Prompt:

`What should I fix first?`

Result: **PASS with wording note**

Observed behavior:

- The connected Fabric Data Agent was invoked successfully.
- The highest-priority item for Maven Fuzzy Factory was identified as `P1_CRITICAL`, `REVIEW_REQUIRED`, with high change risk.
- The response also surfaced immediately actionable P2 recommendations.
- Directional savings semantics were preserved.

Wording note:

The heading can still say “Fix first” for a `REVIEW_REQUIRED` P1 item. The explanatory text correctly states that the item must be investigated and validated before implementation, so this is a presentation issue rather than a routing/data defect.

## Microsoft Teams validation

The classic Copilot Studio agent was published to Microsoft Teams and tested in a personal 1:1 chat.

### First-use authentication

On the first SMO query, Teams displayed a **Connect to continue** prompt for the Fabric Data Agent MCP server.

The user selected **Allow**.

Unlike the new Copilot Studio experience, the classic connected-agent path successfully completed the connection and returned data.

### Teams Test 1 — Current semantic-model inventory

Prompt:

`Which semantic models are available in SMO Analytics?`

Result: **PASS**

Observed behavior:

- The Fabric Data Agent connection succeeded after the one-time user consent.
- Teams returned the same five-model inventory and current scan status as the Fabric/Copilot Studio validation layers.
- Workspace, storage mode, latest scan status, latest scan time, and scanner version were surfaced successfully.

### Teams Test 2 — Fix-first prioritization

Prompt:

`What should I fix first?`

Result: **PASS with wording note**

Observed behavior:

- Teams returned the P1 `REVIEW_REQUIRED` high-cardinality-column case for Maven Fuzzy Factory.
- The response explicitly explained that the item requires review/validation before implementation.
- It then surfaced the strongest immediately actionable recommendation separately.
- SMO priority, actionability, risk, and object-level evidence survived the full Teams path.

## Compatibility finding: new vs classic Copilot Studio experience

A meaningful A/B difference was observed.

### New Copilot Studio experience

The newer experience configured the published Fabric Data Agent as a **Tool**.

Observed behavior:

- Fabric Data Agent direct tests: PASS
- New Copilot Studio Preview: PASS (5/5 routing tests)
- Agent published to Teams: successful
- Teams showed a permission/allow prompt
- After allowing, Teams returned `MCS-4031` / `SystemError`

### Classic Copilot Studio experience

The classic experience configured the Fabric Data Agent as a **connected agent / MCP server**.

Observed behavior:

- Classic Copilot Studio test pane: PASS
- Agent published to Teams: successful
- Teams showed a one-time `Connect to continue` prompt
- After allowing, Fabric Data Agent access succeeded
- SMO queries returned grounded results successfully

### Engineering conclusion

The evidence strongly suggests that the SMO solution, Fabric Data Agent, and user permissions are fundamentally valid, because the same published Fabric Data Agent works end-to-end through the classic connected-agent path.

The failure in the newer Copilot Studio experience is therefore most likely isolated to the newer Teams ↔ Copilot Studio tool/MCP permission handoff or compatibility path rather than the SMO scanner, Lakehouse contract, Fabric Data Agent, or underlying Fabric permissions.

This is an evidence-based compatibility finding, not a confirmed Microsoft product root cause.

## Final E2E acceptance state

```text
SMO PROD deployment                         ✅
5-model PROD scan                           ✅
Fabric Data Agent                           ✅
Data Agent NL2SQL / acceptance              ✅
Copilot Studio classic connected-agent path ✅
Microsoft Teams personal 1:1 chat           ✅
End-user Fabric authentication              ✅
Grounded SMO responses in Teams             ✅

Known V1 limitation:
Exact Recommendation → Finding lineage      ⚠️ Option A guardrail retained

New Copilot Studio tool-based Teams path     ⚠️ MCS-4031 compatibility issue
```

## Project interpretation

The SMO **Agent Consumption Layer can now be considered end-to-end complete for V1** using the classic Copilot Studio connected-agent path.

The preferred production/pilot path for the current iteration is:

```text
SMO Analytics
   ↓
Fabric Optimization Assistant v2
   ↓
Classic Copilot Studio connected agent
Fabric Optimization_Agent_V2
   ↓
Microsoft Teams
```

The newer Copilot Studio tool-based experience should remain a follow-up compatibility investigation rather than a blocker for the current V1 delivery.

## Recommended next steps

1. Keep the classic connected-agent Teams deployment as the accepted V1 path.
2. Run a small pilot with additional users to validate end-user permissions and usability.
3. Retain the V1 Option A evidence guardrail for broader opportunity-level evidence.
4. Track the new Copilot Studio `MCS-4031` behavior separately as a product compatibility issue.
5. Later iterate the SMO data contract with deterministic Recommendation → Finding lineage if Option B is prioritized.
6. Continue with remaining DevOps DoD items such as measured business impact, cost-vs-savings evidence, final documentation, and leadership presentation.
