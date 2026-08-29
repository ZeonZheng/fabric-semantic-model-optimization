# M6.6.3 Report review workbench

## Why this gate was reopened

M6.6.2 proved that the report could locate findings by object and preserve the raw evidence. Viewer review then exposed five usability and correctness gaps:

1. Start here had no drillthrough path.
2. The affected-table locator displayed visually duplicated names caused by quoting and invisible-character variants.
3. Issues, Actions, Evidence, and Issue detail repeated the same control columns and forced unnecessary page changes.
4. The detail summary mixed a stored root-cause total with filter-aware visible rows.
5. Conditional formatting was not applied consistently to the same semantic fields.

M6.6.3 therefore reopens the report acceptance gate. Scanner findings and technical evidence remain immutable; only display normalization, report information architecture, and interaction semantics change.

## Design decisions

- Keep three visible pages: **Start here**, **Review issues**, and **Storage**.
- Merge Issues, Actions, Evidence, and Issue detail into one 1280 × 1080 analytical workbench.
- Treat the Issues table as the root-cause navigator. Selecting one issue filters Actions and Evidence.
- Put implementation rationale, recommended action, validation, and rollback directly in Actions.
- Put finding text and technical evidence directly in Evidence.
- Keep the unique issue key only in Issues as a technical row-grain control.
- Drill from Start here to Review issues by Priority and Decision, then refine with object locators.
- Remove the stored summary text from the report. All displayed counts are filter-aware measures.
- Normalize display-only table names by trimming wrapping quotes, non-breaking spaces, zero-width characters, and repeated whitespace. Raw finding fields are unchanged.
- Apply the same restrained semantic color rules everywhere: Priority, Decision, Severity, Risk, and Automation retain their labels and use color only as a secondary cue.

```yaml
Design Brief:
  generated_by: powerbi-report-design
  contract_version: 1
  mode: brownfield
  current_tone: dense multi-page inspection report
  target_tone: calm evidence-first remediation workbench
  signature: root-cause selection drives inline action and evidence
  canvas:
    standard_width: 1280
    workbench_height: 1080
  pages:
    - name: Start here
      purpose: triage severity and workload before detailed review
      primary_question: What should I fix first?
      interaction: drill through Priority and Decision to Review issues
    - name: Review issues
      purpose: locate a root cause, decide an action, and verify preserved evidence
      primary_question: Which issue should I fix, and what proves it?
      sections:
        - shared object and severity locators
        - issue/root-cause selector
        - inline implementation actions
        - preserved raw evidence
    - name: Storage
      purpose: inspect model storage independently from quality findings
  accessibility:
    - color is never the only semantic cue
    - visual titles describe the required interaction
    - visual tab order follows top-to-bottom reading order
    - no visual overlaps or clipped card labels
```

## Acceptance contract

- Start here exposes a working drillthrough entry to Review issues.
- Review issues has exactly one shared locator area and three tables with distinct jobs.
- Selecting an Issues row filters both Actions and Evidence; Actions and Evidence do not cross-filter each other.
- Actions contains Why it matters, Recommended action, Validation method, and Rollback guidance.
- Evidence contains Finding and Technical evidence.
- The issue key is absent from Actions and Evidence.
- No report visual uses `opportunity_summary`.
- Affected-table display values are canonical while raw evidence fields remain unchanged.
- Priority, Decision, Severity, Risk, and Automation conditional formatting is consistent wherever each field is shown.
- PBIR schema validation, repository validation, TEST deployment, and Fabric Viewer acceptance all pass.
