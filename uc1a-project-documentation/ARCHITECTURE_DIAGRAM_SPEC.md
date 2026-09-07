# Architecture Diagram Specifications

These diagrams are intended to be recreated as modern Draw.io assets and reused in both the canonical project document and the presentation deck.

## Visual language

Use one consistent ownership/evolution palette across all diagrams:

- **Blue** — Microsoft UC1a baseline / reused capability.
- **Green / teal** — UC1a V0.x adaptation or modified execution behavior.
- **Purple** — advanced SMO Analytics capability.
- **Neutral grey** — shared platform or infrastructure.
- **Amber / red accents** — risk, cost, timeout, or privileged-scope callouts only.

Design guidance:

- rounded rectangles;
- modern Microsoft/Fabric iconography where appropriate;
- minimal text inside nodes;
- strong left-to-right or top-to-bottom flow;
- use grouped layers rather than dense connector webs;
- preserve whitespace;
- no screenshots of ASCII diagrams in the final deck;
- keep editable `.drawio` source files.

---

# Diagram 01 - Microsoft UC1a End-to-End Architecture

## Purpose

Explain the original reference pattern before discussing its implementation limitations.

## Layers

### Execution

- Fabric Notebook
- Semantic Link / Semantic Link Labs

### Deterministic analysis

- Best Practice Analyzer
- VertiPaq Analyzer
- conceptual Direct Lake/storage-mode advice from README

### Persistence

- Lakehouse
- `optimization_findings`
- `optimization_runlog`

### Conversational consumption

- Fabric Data Agent
- Copilot Studio
- Microsoft Teams

## Suggested layout

```text
Semantic Models
      |
      v
+--------------------+
| Fabric Notebook    |
| SemPy / SLL        |
+----------+---------+
           |
     +-----+-----+
     |           |
     v           v
+---------+   +---------+
|   BPA   |   | VertiPaq|
+----+----+   +----+----+
     |             |
     +------+------+
            v
+--------------------+
| Fabric Lakehouse   |
| findings + run log |
+----------+---------+
           v
+--------------------+
| Fabric Data Agent  |
+----------+---------+
           v
+--------------------+
| Copilot Studio     |
+----------+---------+
           v
+--------------------+
| Microsoft Teams    |
+--------------------+
```

## Callout

> Deterministic facts first; conversational AI second.

---

# Diagram 02 - Microsoft UC1a Two-Stage Execution

## Purpose

Clarify the important permission distinction between tenant inventory discovery and per-model analysis.

## Stage 1 - Tenant Discovery

Blue container:

- `sempy.fabric.admin`
- `list_workspaces()`
- `list_items(SemanticModel)`
- tenant-wide inventory
- privileged/admin identity callout

## Stage 2 - Model Analysis

Blue container:

- iterate through inventory
- `run_model_bpa()`
- `vertipaq_analyzer()`
- model read/XMLA access

## Stage 3 - Persistence

Neutral container:

- normalized findings
- run log
- Lakehouse

## Critical message

Use a connector label between Stage 1 and Stage 2:

> **The discovered inventory becomes the default analysis workload.**

Use a footer callout:

> Admin privileges enable discovery; Semantic Link Labs performs the actual analysis per model.

---

# Diagram 03 - Rich Analysis In, Simplified Findings Out

## Purpose

Visually demonstrate the information loss in the original normalization layer.

## Left side - rich evidence

Blue evidence cards:

### BPA

- category
- rule
- severity
- object
- description
- contextual fields

### VertiPaq

- tables
- columns
- size metrics
- cardinality
- dictionary/storage metrics
- encoding / physical evidence
- other analyzer outputs

## Center - normalization funnel

Amber funnel:

```text
UC1a Normalization

BPA selected fields
VertiPaq Columns preferred
sort by size/cardinality
Top 15
hard-coded VPA classification
```

## Right side - persisted contract

Single simple findings table:

- source
- severity
- object_type
- object_name
- rule
- finding
- recommended_fix
- workspace/model

## Strong callout

> Easy for an Agent to consume — but much of the diagnostic evidence is discarded.

## Optional concrete example

Left:

```text
CustomerID
Cardinality: 8.2M
Total Size: 598 MB
Dictionary: 387 MB
Encoding: Hash
```

Right:

```text
Object: CustomerID
Severity: Warning
Rule: High size / cardinality
Finding: Large contributor to model size
Fix: Reduce cardinality / remove unused / aggregate
```

Cross out the metric values that do not survive the projection.

---

# Diagram 04 - Why Tenant-Wide Analysis Does Not Scale Operationally

## Purpose

Show why the V0.x scope change is driven by cost/reliability as well as permission.

## Left flow

```text
Tenant Inventory
      |
      v
70 / 100 / 500+ Models
      |
      v
BPA + VertiPaq per model
      |
      v
Long-running Notebook
```

## Risk branches

From the long-running notebook, branch into:

- Higher CU consumption
- Longer runtime
- Timeout exposure
- Partial/incomplete run risk
- repeated inaccessible-model failures

## PROD environment callout

Separate amber container:

```text
PROD
Private Link enabled
      |
      v
Notebook / Spark startup overhead
      |
      v
Less effective analysis window
```

## Project observation badge

> TEST observation: a run involving approximately 70+ models already required substantial runtime. This is project evidence, not a formal benchmark.

## Final green decision

```text
ON-DEMAND SCOPED SCAN
Workspace IDs required
Model IDs optional
```

---

# Diagram 05 - UC1a V0.x Functional Architecture

## Purpose

Present the adapted operating model as an architecture redesign, not merely a parameter change.

## Layer 1 - Parameters and identity

Green container:

- `workspace_ids` — required
- `model_ids_optional` — optional
- signed-in user / pipeline identity
- optional SPN

## Layer 2 - Target resolution

Green container:

- validate requested workspace scope
- if model IDs supplied: validate requested workspace/model pairs
- if model IDs blank: list eligible models only inside supplied workspaces
- **No tenant-wide discovery**

## Layer 3 - Analysis engine

Blue container:

- Semantic Link Labs
- BPA
- VertiPaq

Use a label:

> Reused deterministic engine

## Layer 4 - Output

Neutral/green container:

- normalized results
- Lakehouse
- run history

## Key callout

> **Discovery no longer defines workload. User intent defines workload.**

---

# Diagram 06 - Identity / Permission Before and After

## Purpose

Create a direct visual comparison between the Microsoft reference and V0.x.

## Left - Microsoft reference

Blue:

```text
Privileged identity
      |
      v
Tenant inventory
      |
      v
Discovered models
      |
      v
Per-model BPA/VPA
```

Label:

> Admin dependency introduced at discovery.

## Right - V0.x

Green:

```text
Current user / optional SPN
      |
      v
Explicit workspace scope
      |
      v
Authorized target resolution
      |
      v
Per-model BPA/VPA
```

Label:

> Core analysis needs effective target access, not tenant-wide visibility.

---

# Diagram 07 - Solution Evolution

## Purpose

Connect the three generations into one engineering story.

## Three horizontal cards

### Microsoft UC1a - blue

Headline:

> **PROVE THE PATTERN**

Content:

- deterministic analysis
- Lakehouse findings
- Data Agent
- Copilot Studio
- Teams

### UC1a V0.x - green

Headline:

> **CONTROL THE SCOPE**

Content:

- current-user-first
- explicit workspace scope
- optional model scope
- optional SPN
- on-demand execution

### SMO Analytics - purple

Headline:

> **PRODUCTIZE THE WORKFLOW**

Content:

- deployment notebook
- Fabric Environment
- scanner
- pipeline
- technical history
- business contracts
- quality gates
- Direct Lake
- Power BI report

Connector labels between cards:

Microsoft → V0.x:

> Reverse engineering, permissions, enterprise-fit analysis

V0.x → SMO:

> Evidence preservation, operationalization, validation, analytics

---

# Diagram 08 - Advanced SMO Analytics Architecture

## Purpose

Show that the advanced solution is a complete operating model, not merely a larger notebook.

## Deployment lane

Purple:

```text
Deploy_SMO_Analytics
      |
      +--> Schema-enabled Lakehouse
      +--> SMO_Scanner_Environment
      +--> Scanner Notebook
      +--> Load_SMO_Data Pipeline
      +--> Direct Lake Semantic Model
      +--> Power BI Report
```

## Runtime lane

```text
Pipeline Parameters
      |
      v
Read-only Scanner
      |
      +--> Technical Evidence / History
      |
      +--> Latest Business State
                |
                v
          Quality Grading
                |
                v
        Contract Validation
                |
                v
          Direct Lake Model
                |
                v
          Power BI Report
```

## Governance lane

- `workspace_user` — default core scan profile, no tenant Admin enumeration.
- optional `governance_admin` — isolated enrichment path only.

## Callout

> Deployment, collection, technical evidence, business interpretation, consumption, and benefit validation are separate responsibilities.

---

# Recommended output files

When the Draw.io stage starts, create the following under this documentation folder without modifying existing repository assets:

```text
uc1a-project-documentation/
  diagrams/
    01-microsoft-uc1a-reference.drawio
    02-microsoft-uc1a-two-stage.drawio
    03-lossy-normalization.drawio
    04-tenant-scan-scalability.drawio
    05-uc1a-v0x-architecture.drawio
    06-identity-before-after.drawio
    07-solution-evolution.drawio
    08-smo-analytics-architecture.drawio
```

PNG/SVG exports can be added beside the source files for Word/PPT consumption while retaining `.drawio` as the editable master.
