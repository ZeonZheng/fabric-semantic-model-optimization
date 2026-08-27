# M6.6.1 Viewer UX Redesign

## Why M6.6 was reopened

The M6.6 PBIR structure, saved filters, synchronized model context, and
drillthrough mechanics passed technical acceptance. Viewer review then exposed
four consumption failures:

1. Overview, Opportunities, Recommendations, and Findings did not communicate
   distinct jobs, so the report had no obvious starting path.
2. A seven-value KPI card and the long context card clipped labels and values in
   Power BI Service.
3. Findings contained object metadata, but users could not use object type,
   table, or object to locate the related grouped issue and action.
4. The hidden drillthrough page had no Back action.

M6.6.1 corrects the consumption experience without rescanning either TEST model
or changing the accepted finding, rule, opportunity, or recommendation rows.

## Canonical design contract

```yaml
Design Brief:
  generated_by: powerbi-report-design
  contract_version: 1
  mode: brownfield
  design_identity:
    current_tone: indistinct dense inventory
    current_signature: repeated full-width result tables
    tone: Minimal Restrained — white surface, slate text, one blue emphasis, compact but legible
    signature: Guided decision path — numbered page names plus a recurring object-locator rail
  archetype: Executive + Drill
  color_map:
    - measure: Metrics[Total opportunities]
      color: "#102A43"
      tint: "#F4F7FA"
    - measure: Metrics[Total recommendations]
      color: "#102A43"
      tint: "#F4F7FA"
    - measure: Metrics[High findings]
      color: "#D13438"
      tint: "#F4CCCC"
    - measure: Metrics[Review required recommendations]
      color: "#F59E0B"
      tint: "#FCE8B2"
  pages:
    - name: What should I fix first?
      role: landing
      archetype: Executive
      layout_variant: B
      variant_rationale: Four decision KPIs and one ranked root-cause queue provide a scan-first landing page.
      layout_contract:
        canvas: { width: 1280, height: 720, margin: 24, gutter: 16, snap: 8 }
        grid:
          columns: 12
          rows: 12
          regions:
            navigation: [1, 1, 13, 2]
            header: [1, 2, 5, 4]
            filters: [5, 2, 13, 4]
            context: [1, 4, 13, 5]
            kpis: [1, 5, 13, 7]
            priority_queue: [1, 7, 13, 13]
        placements:
          - { id: page_title, region: header, kind: textbox, text: "What should I fix first?" }
          - { id: global_scope, region: filters, kind: slicer, field_bindings: "Workspace / Model / Latest analysis" }
          - { id: current_scope, region: context, kind: tableEx, purpose: "Which exact analysis is being viewed?", field_bindings: "semantic_models scope fields" }
          - { id: decision_kpis, region: kpis, kind: cardVisual, purpose: "How much prioritized work exists?", field_bindings: "four decision measures" }
          - { id: top_root_causes, region: priority_queue, kind: tableEx, purpose: "Which root cause should the viewer inspect first?", field_bindings: "opportunity priority fields", sort_policy: value_desc }
        space_audit:
          content_cell_count: 96
          placed_cell_count: 96
          empty_cell_pct: 0
          unplaced_regions: []
          largest_region: { name: priority_queue, pct_of_content: 50 }
          balance_rationale: The ranked queue is the explanatory hero; the KPI strip remains compact.
    - name: Where are the model problems?
      role: detail
      archetype: Analytical
      layout_variant: A
      variant_rationale: Five object/root-cause dimensions justify a persistent filter rail.
      layout_contract:
        canvas: { width: 1280, height: 720, margin: 24, gutter: 16, snap: 8 }
        grid:
          columns: 12
          rows: 12
          regions: { header: [1, 1, 13, 4], rail: [1, 4, 3, 13], issues: [3, 4, 13, 13] }
        placements:
          - { id: page_title, region: header, kind: textbox, text: "Where are the model problems?" }
          - { id: object_locator, region: rail, kind: slicer, field_bindings: "Finding object type / table / object / severity plus issue area" }
          - { id: issues, region: issues, kind: tableEx, purpose: "Which grouped root causes affect the selected objects?", field_bindings: "opportunity decision fields", sort_policy: value_desc }
        space_audit: { content_cell_count: 108, placed_cell_count: 108, empty_cell_pct: 0, unplaced_regions: [], largest_region: { name: issues, pct_of_content: 83 }, balance_rationale: "A single locator table is the analytical workspace; detail moves to drillthrough." }
    - name: What should I do next?
      role: detail
      archetype: Analytical
      layout_variant: A
      variant_rationale: Object and decision-state filters narrow one action queue without repeating issue descriptions.
      layout_contract:
        canvas: { width: 1280, height: 720, margin: 24, gutter: 16, snap: 8 }
        grid:
          columns: 12
          rows: 12
          regions: { header: [1, 1, 13, 4], rail: [1, 4, 3, 13], actions: [3, 4, 13, 13] }
        placements:
          - { id: page_title, region: header, kind: textbox, text: "What should I do next?" }
          - { id: action_filters, region: rail, kind: slicer, field_bindings: "Object type / table / object / decision / priority" }
          - { id: actions, region: actions, kind: tableEx, purpose: "Which work item should be planned next?", field_bindings: "recommendation decision fields", sort_policy: value_desc }
        space_audit: { content_cell_count: 108, placed_cell_count: 108, empty_cell_pct: 0, unplaced_regions: [], largest_region: { name: actions, pct_of_content: 83 }, balance_rationale: "The queue is the sole page question; rationale and controls remain behind drillthrough." }
    - name: Which object proves the problem?
      role: detail
      archetype: Analytical
      layout_variant: A
      variant_rationale: Object, severity, and source are the primary evidence-locator dimensions.
      layout_contract:
        canvas: { width: 1280, height: 720, margin: 24, gutter: 16, snap: 8 }
        grid:
          columns: 12
          rows: 12
          regions: { header: [1, 1, 13, 4], rail: [1, 4, 3, 13], evidence: [3, 4, 13, 13] }
        placements:
          - { id: page_title, region: header, kind: textbox, text: "Which object proves the problem?" }
          - { id: evidence_filters, region: rail, kind: slicer, field_bindings: "Object type / table / object / severity / source" }
          - { id: evidence_locator, region: evidence, kind: tableEx, purpose: "Which finding and rule identify the selected object?", field_bindings: "finding locator fields", sort_policy: value_desc }
        space_audit: { content_cell_count: 108, placed_cell_count: 108, empty_cell_pct: 0, unplaced_regions: [], largest_region: { name: evidence, pct_of_content: 83 }, balance_rationale: "Long descriptions are deferred to detail so the locator remains scannable." }
    - name: Which tables and columns consume model storage?
      role: detail
      archetype: Comparative
      layout_variant: A
      variant_rationale: A table selector, two ranked views, and one evidence table separate storage from design-quality findings.
      layout_contract:
        canvas: { width: 1280, height: 720, margin: 24, gutter: 16, snap: 8 }
        grid:
          columns: 12
          rows: 12
          regions: { header: [1, 1, 13, 4], table_filter: [1, 4, 3, 8], columns: [3, 4, 8, 8], tables: [8, 4, 13, 8], evidence: [1, 8, 13, 13] }
        placements:
          - { id: page_title, region: header, kind: textbox, text: "Which tables and columns consume model storage?" }
          - { id: storage_table_filter, region: table_filter, kind: slicer, field_bindings: "column storage table" }
          - { id: largest_columns, region: columns, kind: clusteredBarChart, purpose: "Which columns are largest?", field_bindings: "column and storage MB", sort_policy: value_desc }
          - { id: largest_tables, region: tables, kind: clusteredBarChart, purpose: "Which tables are largest?", field_bindings: "table and bytes", sort_policy: value_desc }
          - { id: storage_evidence, region: evidence, kind: tableEx, purpose: "What is the exact storage metadata?", field_bindings: "column storage fields", sort_policy: value_desc }
        space_audit: { content_cell_count: 108, placed_cell_count: 108, empty_cell_pct: 0, unplaced_regions: [], largest_region: { name: evidence, pct_of_content: 46 }, balance_rationale: "Rankings answer where; the lower table preserves exact evidence." }
    - name: Issue detail — action and evidence
      role: drillthrough
      archetype: Analytical
      layout_variant: B
      variant_rationale: One root cause needs three stacked levels and a persistent Back action, not another filter rail.
      layout_contract:
        canvas: { width: 1280, height: 720, margin: 24, gutter: 16, snap: 8 }
        grid:
          columns: 12
          rows: 12
          regions: { header: [1, 1, 13, 3], summary: [1, 3, 13, 5], actions: [1, 5, 13, 9], evidence: [1, 9, 13, 13] }
        placements:
          - { id: back_button, region: header, kind: actionButton, purpose: "Return to the source page." }
          - { id: page_title, region: header, kind: textbox, text: "Issue detail — action and evidence" }
          - { id: issue_summary, region: summary, kind: tableEx, purpose: "What is the grouped root cause?", field_bindings: "opportunity summary fields" }
          - { id: action_controls, region: actions, kind: tableEx, purpose: "Why act and how will the change be validated or rolled back?", field_bindings: "recommendation control fields" }
          - { id: raw_evidence, region: evidence, kind: tableEx, purpose: "Which preserved raw records support the issue?", field_bindings: "finding evidence fields" }
        space_audit: { content_cell_count: 120, placed_cell_count: 120, empty_cell_pct: 0, unplaced_regions: [], largest_region: { name: actions, pct_of_content: 40 }, balance_rationale: "The stacked sequence mirrors issue → action → evidence and fits the existing canvas." }
  interaction_pattern:
    drill_targets: [Issue detail]
    cross_filter_rules: "Object type/table/object filter Findings bidirectionally to Issues, then Actions. Global model context remains synchronized."
  accessibility:
    alt_text_strategy: "Question-led page titles and textual status fields; color never replaces Decision or Severity labels."
    contrast_notes: "Slate text on white exceeds body-text contrast requirements; alert fills retain explicit text labels."
  theme:
    base: existing Power BI theme preserved
    user_overrides: "No theme swap; per-visual card padding and compact table formatting prevent clipping."
```

## Acceptance gates

1. Visible page names communicate the guided path: Start here → Issues →
   Actions → Evidence → Storage.
2. The Start here KPI strip contains no more than four metrics and no clipped
   values or labels in Power BI Service.
3. `SMO_Optimization1` is the saved validation preset and remains easy to
   replace with the control model.
4. Object type, table, and object selections synchronize across Issues,
   Actions, and Evidence and filter all three grains.
5. No visible visual overlaps another visual or extends outside the 1280 × 720
   canvas.
6. Drillthrough provides an explicit Back action and retains the selected model,
   root cause, action controls, finding description, and technical evidence.
7. The accepted TEST analysis IDs and result counts remain unchanged because no
   scanner run is performed.

## Current result

Local PBIR redesign is implemented and static validation is in progress. TEST
deployment and Viewer-scenario acceptance are pending.
