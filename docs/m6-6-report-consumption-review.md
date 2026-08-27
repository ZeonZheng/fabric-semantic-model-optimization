# M6.6 Report / Consumption Experience

## Purpose

M6.6 makes the existing scan results decision-ready without changing scanner rule
recall or rescanning the TEST models. It distinguishes three user-facing grains:

- **Finding**: preserved raw scanner evidence for an affected object.
- **Opportunity**: a grouped root cause that can link many findings and work items.
- **Recommendation**: a user work item with priority, risk, validation, rollback,
  and automation guidance.

Auto-fix execution, tenant-wide scanning, PROD network remediation, and realized
benefit claims remain outside this release.

## P0 report contract

1. The visible page order is Overview → Recommendations → Opportunities → Findings
   → Storage, followed by one hidden Opportunity detail drillthrough page.
2. Workspace, semantic-model, and latest-analysis-ID slicers are synchronized across
   all five visible pages and the hidden detail page.
3. The current analysis context identifies workspace, model, latest analysis ID,
   status, completion time, and scanner version.
4. Overview surfaces top root causes sorted by deterministic opportunity priority,
   alongside scan freshness and explicit data-availability explanations.
5. The Recommendation queue defaults to `P2_HIGH`, `ACTIONABLE`, and
   `REVIEW_REQUIRED`. Users can clear those saved slicer selections to inspect the
   complete queue.
6. Recommendation rows include the related visible Opportunity title so right-click
   drillthrough opens the matching root cause.
7. The detail page exposes recommendation action, reason, risk, automation label,
   validation method, rollback guidance, and preserved finding source, confidence,
   description, and technical evidence.
8. Conditional formatting is limited to actionability and evidence severity so color
   supports prioritization without replacing the textual status.

## TEST acceptance scope

Use the existing current-state data in workspace `SMO Analytics - Dev`
(`cc9ce2d3-5e27-47e3-9e69-06cf7324dbb4`). Do not run the scanner again.

| Model | Latest analysis ID | Accepted M6.5.6 baseline |
| --- | --- | --- |
| `SMO_Optimization1` adverse model | `7b935671-ae75-4442-a3b9-c737a2778183` | `SUCCEEDED`; 1,021 findings; 30/30 MQ; 54 recommendations |
| `Getting Started in Power BI` control model | `688aae34-1897-42d1-8d00-da5bd4cdcf01` | `SUCCEEDED`; 138 findings; 9 MQ; 25 recommendations |

## Acceptance gates

1. Static repository validation and the Microsoft PBIR authoring validator pass.
2. The three global slicers remain synchronized when navigating all visible pages.
3. Selecting either accepted analysis ID shows the matching workspace, model,
   status, completion time, scanner version, and analysis ID in the context card.
4. The Recommendation page initially shows only P2 actionable/review work items;
   clearing the saved selections restores all priorities and actionability states.
5. A recommendation can drill through by its Opportunity field, and the detail page
   displays the related work item plus raw findings and technical evidence.
6. Overview counts and the two accepted analysis IDs remain unchanged because M6.6
   is a report-only consumption release.

## Current result

Local implementation and static validation are complete. TEST deployment and the
visual/filter/drillthrough acceptance checks are pending.
