# M6.7.1 — PROD SMO Data Agent Configuration and Acceptance

**Date:** 2026-09-10  
**Branch:** `codex/m6-4`  
**Data Agent:** `Fabric Optimization Assistant v2`  
**Runtime:** Standard  
**Status:** V1 accepted for publication with one documented evidence-lineage limitation

## Purpose

This document records the PROD Data Agent work completed after the advanced SMO Analytics solution was successfully redeployed and scanned in PROD. It is intended to preserve the implementation history, configuration decisions, test evidence, known limitations, and the handoff point for the next phase: Copilot Studio packaging and Microsoft Teams publication.

## Starting point

The earlier UC1a Agent Consumption Layer had been completed against the enhanced UC1a v0.x solution. After the advanced SMO Analytics solution became deployable and usable in PROD, a new Data Agent was created specifically for SMO Analytics.

A previous PROD deployment had scanned 11 semantic models, with 10 succeeding and one failing because the running user did not have access to the Lakehouse used by that model. That whole solution instance was later removed. A fresh SMO deployment was then created in a new workspace and only the five predefined validation models were scanned. The current Data Agent therefore intentionally works against the new five-model dataset; the earlier failed scan is not expected to exist in the current Lakehouse.

Current validation models:

- Bank Customer Churn
- Maven Fuzzy Factory
- SMO_Optimization1_copy
- US Candy Distributor
- Video Game Sales

The five current model scans completed successfully with scanner version `2.6.6`.

## Data Agent architecture

```text
SMO Analytics PROD
       │
       ▼
SMO_Analytics_Lakehouse
       │
       ├─ Business consumption schemas/tables
       │
       ▼
Fabric Optimization Assistant v2
       │
       ├─ Agent instructions
       ├─ Data source description
       ├─ Data source instructions
       └─ Example queries / few-shots
       │
       ▼
Fabric Data Agent test & acceptance
       │
       ▼
Publish Data Agent                    ← current handoff point
       │
       ▼
Copilot Studio
       │
       ▼
Microsoft Teams
```

## Selected Lakehouse scope

The Data Agent exposes the SMO business consumption layer and intentionally excludes the raw/legacy `smopt` tables.

Selected business schemas and tables:

| Schema | Table |
|---|---|
| `semantic_model_metadata` | `semantic_models` |
| `analysis_control` | `semantic_model_analysis_runs` |
| `semantic_model_best_practice` | `semantic_model_best_practice_rule_findings` |
| `semantic_model_vertipaq` | `semantic_model_column_storage` |
| `semantic_model_vertipaq` | `semantic_model_table_storage` |
| `semantic_model_optimization` | `semantic_model_optimization_overview` |
| `semantic_model_optimization` | `semantic_model_optimization_opportunities` |
| `semantic_model_optimization` | `semantic_model_optimization_recommendations` |
| `semantic_model_optimization` | `semantic_model_optimization_findings` |
| `semantic_model_optimization` | `semantic_model_optimization_opportunity_recommendation_links` |
| `semantic_model_optimization` | `semantic_model_optimization_opportunity_finding_links` |

All `smopt.*` tables are excluded from the Data Agent selection.

## Configuration artifacts

The exact Data Agent configuration used for V1 is recorded separately:

- [`data-agent/agent-instructions.md`](data-agent/agent-instructions.md)
- [`data-agent/data-source-instructions.md`](data-agent/data-source-instructions.md)
- [`data-agent/example-queries.json`](data-agent/example-queries.json)

The Data Source Instructions were deliberately compacted after the first version reached the Fabric 15,000-character limit. The compact version keeps NL2SQL-critical semantics while avoiding duplicated schema descriptions already supplied by the Data Agent runtime.

## Important instruction semantics

The final V1 configuration explicitly teaches the agent to distinguish:

- current optimization state vs historical scan execution;
- model inventory vs remembered model names;
- opportunity priority vs recommendation priority vs finding priority;
- `ACTIONABLE`, `REVIEW_REQUIRED`, `INFORMATIONAL`, and `SUPPRESSED` at the entity level;
- current model comparison using `semantic_model_optimization_overview` rather than inventing a model-level score;
- directional byte-saving estimates vs validated CU/performance/financial savings;
- business consumption tables vs legacy/raw `smopt` tables.

## Example-query configuration

The Data Agent initially used 10 few-shot examples. Four additional hardening examples were added after the advanced acceptance test exposed NL2SQL failure modes. The final V1 configuration contains **14 example queries**.

The four hardening examples specifically cover:

1. strict `REVIEW_REQUIRED` recommendation filtering;
2. BPA aggregation across the current dynamic semantic-model inventory;
3. current-state cross-model comparison without unnecessary joins or invented scoring;
4. recommendation queries paired with evidence at the broader optimization-opportunity scope.

## Acceptance testing

### Round 1 — Core tests

Five core tests were executed against PROD:

| Test | Result |
|---|---|
| Model inventory | PASS |
| Latest scan execution per semantic model | PASS |
| Failed scan query | PASS — expected empty result in the fresh five-model deployment |
| Current optimization overview | PASS |
| Highest-priority remediation / "what should I fix first" | PASS |

This validated the basic routing distinction between current-state business tables and historical analysis-run data.

### Round 2 — Advanced tests

Ten advanced tests were executed to validate opportunity/recommendation relationships, evidence, actionability, BPA, VertiPaq, cross-model comparison, savings semantics, and complex joins.

Initial results:

| Test | Initial result | Finding |
|---|---|---|
| A1 Opportunity → Recommendation | PASS | Correct routing |
| A2 Highest-priority issue → Evidence | PASS | Correct model filtering and finding evidence |
| A3 Human-review recommendations | FAIL | Parent opportunity actionability leaked into recommendation filtering |
| A4 Suppressed findings | PASS / harden | Correct output, unnecessary broader query behavior |
| A5 VertiPaq columns | PASS | Correct column-storage routing |
| A6 VertiPaq tables | PASS | Correct table-storage routing |
| A7 BPA across current models | FAIL | Agent guessed a stale model list |
| A8 Cross-model comparison | FAIL | Unnecessary joins created duplicates and an unsupported "overall optimization score" |
| A9 Estimated savings | PASS | Correctly avoided unsupported CU/performance claims |
| A10 Recommendation → supporting findings | FAIL / critical | False evidence associations caused by insufficient lineage granularity |

### Hardening iteration

The Data Source Instructions were rewritten into a compact SQL-guidance version and four corrective few-shot examples were added.

Retest results:

| Test | Retest result |
|---|---|
| A3 Human-review recommendations | PASS |
| A7 BPA across current models | PASS |
| A8 Cross-model comparison | PASS |
| A10 Recommendation → supporting findings | STILL FAILS for exact one-to-one evidence mapping |

The A3/A7/A8 fixes confirmed that the instruction and few-shot layers are effective for query semantics. A10 demonstrated a deeper limitation in the current consumption data contract.

## A10 finding — recommendation-to-finding lineage gap

The Data Agent can deterministically identify:

```text
Opportunity
   ├─ Recommendations
   └─ Findings
```

However, the current consumption contract does not provide a deterministic one-to-one or one-to-many mapping from a **specific recommendation** to its **specific supporting findings**.

Even after tightening the join to include:

```text
semantic_model_id
+ analysis_id
+ analysis_scope_key
+ issue_scope_key
+ opportunity_id
```

multiple findings can still be associated with a recommendation simply because they belong to the same broader issue/opportunity scope. This can produce misleading statements such as presenting one rule's finding as direct evidence for another rule's recommendation.

This is not treated as an NL2SQL prompt defect after the retest; it is a data-contract lineage limitation.

## Decision — publish V1 using Option A

Two options were evaluated.

### Option A — safe V1 publication — SELECTED

Publish the Data Agent now, while explicitly limiting the evidence semantics:

- recommendations can be presented as remediation actions;
- findings can be presented as evidence associated with the broader optimization opportunity;
- the agent must **not claim that an individual finding specifically supports an individual recommendation unless deterministic lineage exists**.

The final example-query wording was therefore changed from exact "supporting findings" to broader-opportunity evidence:

> `For Video Game Sales, show the top actionable recommendations and the evidence associated with their broader optimization opportunities.`

This allows the Data Agent to ship without misrepresenting the current relationship model.

### Option B — exact recommendation-to-finding lineage — BACKLOG

A future SMO iteration should consider adding a deterministic bridge such as:

```text
semantic_model_optimization_recommendation_finding_links
    analysis_id
    semantic_model_id
    recommendation_id
    finding_id
```

Target relationship:

```text
Recommendation
      │ recommendation_id
      ▼
recommendation_finding_links
      │ finding_id
      ▼
Finding
```

This would enable exact recommendation → finding → technical-evidence navigation and remove ambiguity from complex evidence queries.

**Backlog classification:** architectural/data-contract enhancement; not required for V1 publication under Option A.

## Additional response-quality observations

The SQL layer for the cross-model comparison passed after hardening, but future response tuning should continue to avoid over-interpreting returned counts. For example:

- `analysis_status = SUCCEEDED` means the analysis succeeded; it does not mean the model itself is already "optimized";
- `suppressed_finding_count > 0` does not by itself explain why findings were suppressed; `suppression_reason` must be queried before assigning a reason;
- a high number of findings is not itself a model-level health score;
- SMO currently has no single overall optimization/quality/maturity score.

These are wording-quality hardening items rather than publication blockers for V1.

## Publication status at this handoff

After selecting Option A, the Fabric Data Agent publication flow was initiated for `Fabric Optimization Assistant v2`.

At the time of this record, the Publish dialog has been opened and the next UI action is to provide the publication description and confirm Publish. Do not infer completion until Fabric confirms that the published version is active.

The Microsoft 365 Copilot Agent Store toggle is not required for the planned Copilot Studio → Teams packaging path unless a separate Agent Store distribution decision is made.

## Next phase — Copilot Studio and Teams

After the Fabric Data Agent publish operation completes:

```text
Publish Fabric Data Agent
          │
          ▼
Create / configure Copilot Studio agent
          │
          ├─ Connect published SMO Data Agent
          ├─ Configure agent instructions
          ├─ Configure starter/suggested prompts
          ├─ Validate orchestration and SMO answers
          └─ Apply Option A evidence-language guardrail
          │
          ▼
Publish Copilot Studio agent
          │
          ▼
Add Microsoft Teams channel
          │
          ▼
Teams end-to-end acceptance
```

The next acceptance target is not just "agent opens in Teams". It should confirm that Teams → Copilot Studio → Fabric Data Agent returns the same trusted current-state, priority, BPA, VertiPaq, and broader-opportunity evidence semantics validated here.

## Current project checkpoint

```text
PROD SMO deployment                 DONE
Five-model PROD scan                DONE
SMO Data Agent configuration        DONE
Core Data Agent validation          PASS
Advanced Data Agent hardening       DONE
Known A10 lineage limitation        DOCUMENTED
V1 publication strategy             OPTION A SELECTED
Fabric Data Agent publish           IN PROGRESS
Copilot Studio packaging            NEXT
Microsoft Teams publication         NEXT
Option B exact evidence lineage      BACKLOG
```
