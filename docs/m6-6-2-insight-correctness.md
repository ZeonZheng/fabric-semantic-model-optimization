# M6.6.2 Insight Correctness and Information Hierarchy

## Why M6.6.1 was reopened

M6.6.1 fixed the missing report path, clipped cards, object navigation, and Back
action. A second Viewer review then identified correctness and hierarchy gaps:

1. Start here repeated the full Issues root-cause inventory.
2. Issues displayed stored opportunity totals, so table/object filters changed
   the visible issue rows but not the Evidence or Actions numbers.
3. Evidence exposed raw `affected_table_name`; table-level and Auto Date/Time
   records could therefore show a blank Table while the technical table name
   appeared in Object.
4. Object and Table slicers had ambiguous names and inconsistent membership.
5. Area/domain and root-cause navigation were missing.
6. Shared fields appeared in different orders, and drillthrough did not make its
   additional implementation details visually obvious.

M6.6.2 corrects these consumption semantics without rescanning either TEST model
or changing any accepted finding description, technical evidence, source, rule,
opportunity, or recommendation row.

The TEST deployment candidate is solution `0.6.15`. Existing semantic models and
reports are updated through the Fabric public-definition REST APIs so the complete
TMDL/PBIR contract is validated directly; the CLI import path remains available
for first creation only.

## Corrected page contract

| Page | One job | Main content |
| --- | --- | --- |
| Start here | Choose which priority queue to inspect | Four KPIs plus an aggregate Priority × Decision summary |
| Issues | Locate grouped root causes | Full issue inventory with filter-aware visible Evidence and Actions |
| Actions | Plan work items | Root cause → Action queue with evidence visible in the current object scope |
| Evidence | Locate preserved records | Canonically ordered raw finding table with normalized locator fields |
| Issue detail | Explain and control implementation | Filter-aware summary, rationale, validation, rollback, and preserved technical evidence |

The shared locator uses six full-height controls in the left rail and two
full-height controls above the table. This preserves eight dimensions without
reintroducing clipped dropdowns:

- Object category
- Object type
- Affected table
- Affected object
- Area / domain
- Root cause
- page-specific state 1: Severity or Decision
- page-specific state 2: Decision, Priority, or Source

## Semantic corrections

### Filter-aware counts

`opportunities.finding_count` and `recommendation_count` remain valid stored
all-issue totals, but they are no longer labeled as if they respond to object
filters. The report uses three explicit measures:

- `Visible evidence`: finding rows remaining in the current model, issue, and
  affected-object filter context.
- `Visible action evidence`: current evidence mapped to an action through the
  existing recommendation-title/rule-title contract; consolidated recommendations
  map through their root-cause title.
- `Visible actions`: recommendations with at least one visible supporting finding.

This fixes the former case where selecting `DimCustomerCopy` and `vw_AllSales`
left Model structure at 13 Evidence / 6 Actions even though the selected scope
contained only a subset of those records.

### Object and table taxonomy

Three semantic display columns are added to the curated Findings table. They are
derived during curated projection and deterministically backfilled for accepted
rows; they do not replace or mutate raw evidence columns:

- `object_scope`: `Auto Date/Time (system)`, `Authored / imported object`, or
  `Model-level`.
- `display_table_name`: raw table name when present; otherwise the table-level or
  Auto Date/Time technical object name; otherwise `Not applicable`.
- `display_object_name`: raw object name or `Not applicable`.

Auto Date/Time classification recognizes the engine names
`DateTableTemplate_*` and `LocalDateTable_*`. The technical names remain visible
in Evidence and drillthrough for traceability.

## Canonical field order

| Surface | Order |
| --- | --- |
| Issues | Priority → Decision → Root cause → Area/domain → Severity → Risk → Visible evidence → Visible actions |
| Actions | Priority → Decision → Root cause → Action → Risk → Automation → Visible evidence |
| Evidence | Priority → Decision → Root cause → Area/domain → Severity → Object category → Object type → Affected table → Affected object → Source → Rule |
| Detail actions | Action → Why it matters → Recommended action → Validation → Rollback → Risk → Automation → Visible evidence |
| Detail evidence | Severity → Source → Rule → Object category → Object type → Affected table → Affected object → Finding → Technical evidence |

## Why Evidence remains a table

A Matrix is useful for a count hierarchy, but it is not a better primary surface
for preserved finding records: collapsed groups hide individual rule text,
descriptions, and technical evidence, and repeated object names are meaningful
at the raw finding grain. M6.6.2 therefore keeps the evidence table and fixes its
locator taxonomy. A future optional summary matrix can sit beside the table only
if it answers a distinct aggregation question.

## Acceptance gates

1. The accepted adverse and control analysis IDs and counts remain unchanged;
   no scanner run occurs.
2. Start here has no full root-cause inventory and does not duplicate Issues.
3. Selecting an affected table/object recalculates Visible evidence and Visible
   actions on Issues.
4. Auto Date/Time system objects can be isolated from authored/imported objects.
5. Affected table no longer renders blank for table-level and recognized Auto
   Date/Time records.
6. Eight locator/state slicers are available on Issues, Actions, and Evidence;
   all dropdowns render at least 76 px high.
7. Shared field order matches the canonical contract.
8. Drillthrough retains a working Back action and makes rationale, validation,
   rollback, finding description, and technical evidence explicit.

## Candidate validation

- Repository validation: passed, 88 JSON/notebook/platform files.
- Python compile and `git diff --check`: passed.
- Microsoft `powerbi-report-author` `0.1.4`: 0 errors. The only warnings were
  schema-fetch warnings caused by the execution network; no PBIR diagnostic
  remained.
- Report inventory: five visible pages, one hidden drillthrough page, 70 visuals,
  no overlap or out-of-canvas bounds.
- TEST deployment and Viewer acceptance: pending.
