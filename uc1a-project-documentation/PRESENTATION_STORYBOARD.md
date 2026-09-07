# UC1a Project Presentation Storyboard

This storyboard is derived from the canonical technical document. The presentation should tell one engineering-evolution story rather than three disconnected repository stories.

## Core narrative

```text
Microsoft UC1a
Reference / Hackathon pattern
        |
        | reverse engineering
        | permission analysis
        | runtime / CU observations
        v
UC1a V0.x
User-scoped enterprise adaptation
        |
        | evidence preservation
        | operationalization
        | validation
        v
SMO Analytics
FUAM-style reusable Fabric solution
```

Recommended speaking message:

> Microsoft UC1a proved that deterministic semantic-model analysis can power a useful Agent experience. The internal engineering work first adapted identity and scope for our operating environment, then evolved the pattern into a reusable Fabric analytics solution.

---

# Recommended deck structure

## Slide 1 - From UC1a to Semantic Model Optimization Analytics

**Purpose:** Set the theme.

Subtitle:

> Deconstructing Microsoft's UC1a, adapting it for user-scoped execution, and evolving it into a reusable Fabric solution

Visual:

```text
Microsoft UC1a --> UC1a V0.x --> SMO Analytics
```

---

## Slide 2 - The Engineering Journey

**Purpose:** Explain immediately that this is one evolution path.

Use Diagram 07 - Solution Evolution.

Three messages:

- **PROVE THE PATTERN** — Microsoft UC1a.
- **CONTROL THE SCOPE** — UC1a V0.x.
- **PRODUCTIZE THE WORKFLOW** — SMO Analytics.

---

## Slide 3 - What Microsoft UC1a Was Designed to Solve

**Purpose:** Start with the value of the reference solution rather than its limitations.

Key points:

- semantic-model performance and cost optimization;
- deterministic BPA + VertiPaq analysis;
- trusted findings stored as data;
- conversational access through Data Agent / Copilot Studio / Teams.

Callout:

> Deterministic facts first; conversational AI second.

---

## Slide 4 - Microsoft UC1a Reference Architecture

Use Diagram 01.

Explain:

```text
Semantic Models
      |
      v
Notebook / Semantic Link Labs
      |
      v
Lakehouse findings
      |
      v
Data Agent
      |
      v
Copilot Studio
      |
      v
Teams
```

Keep this slide positive and architectural.

---

## Slide 5 - Inside the Original UC1a Notebook: Two Stages

Use Diagram 02.

### Stage 1

Tenant inventory using `sempy.fabric.admin`.

### Stage 2

Per-model BPA + VertiPaq analysis.

Key distinction:

> Admin privileges enable discovery; Semantic Link Labs performs the actual analysis per model.

Critical architecture observation:

> The discovered tenant inventory becomes the default analysis workload.

---

## Slide 6 - Rich Analysis In, Simplified Findings Out

Use Diagram 03.

Show that Semantic Link Labs exposes rich evidence, while the reference normalizer intentionally compresses it.

Highlight:

- BPA selected fields;
- VertiPaq Columns extraction;
- top 15 only;
- generic VPA severity/rule/finding/fix;
- detailed metrics are not fully retained in the final findings contract.

Callout:

> Easy for an Agent to consume — but much of the diagnostic evidence is discarded.

Important speaking nuance:

> This is a valid hackathon simplification, but it limits deeper diagnostics, reporting, trend analysis, and benefit validation.

---

## Slide 7 - Why Tenant-Wide Analysis Does Not Scale Operationally

Use Diagram 04.

Show:

```text
Tenant inventory
      |
      v
N semantic models
      |
      v
BPA + VertiPaq repeated N times
      |
      v
Runtime / CU / timeout exposure
```

Project observation:

> A TEST execution involving approximately 70+ models already required substantial runtime. This is project evidence, not a formal benchmark.

PROD factor:

> Private Link and notebook/Spark startup overhead reduce the effective analysis window in the project environment.

Conclusion:

> Tenant-wide analysis should not be the default recurring operating model.

---

## Slide 8 - Why I Adapted UC1a

Use four driver cards:

### Security

Reduce unnecessary privileged discovery dependency.

### Scope

Let users state what should be analyzed.

### Compute

Avoid unnecessary BPA / VertiPaq executions.

### Reliability

Reduce long-running notebook and timeout exposure.

Callout:

> **Deploy broadly. Scan narrowly.**

---

## Slide 9 - UC1a V0.x Design Principles

Four principles:

1. Current-user-first.
2. Explicit workspace scope.
3. Optional model-level targeting.
4. Reuse the deterministic Semantic Link Labs engine.

Key architecture message:

> **Discovery no longer defines workload. User intent defines workload.**

---

## Slide 10 - UC1a V0.x Functional Architecture

Use Diagram 05.

```text
Pipeline parameters
      |
      v
Identity
      |
      v
Target resolution
      |
      v
Authorization / validation
      |
      v
BPA + VertiPaq
      |
      v
Lakehouse
```

Show two operating modes:

- Workspace Scope Mode.
- Explicit Model Target Mode.

---

## Slide 11 - Microsoft UC1a vs V0.x

Use a REUSED / CHANGED / NEW comparison.

| Capability | Microsoft UC1a | UC1a V0.x |
|---|---|---|
| BPA | Original | Reused |
| VertiPaq | Original | Reused |
| Discovery | Tenant inventory | Explicit workspace scope |
| Model selection | No input | Optional explicit models |
| Identity | Privileged discovery path | Current-user-first + optional SPN |
| Workload definition | Inventory-driven | User-intent-driven |
| Default operation | Broad loop | On-demand scoped scan |
| Lakehouse persistence | Original | Retained / adapted |
| Pipeline usability | Limited | Parameterized entry point |

Visual ownership language:

- Blue = Microsoft/reused.
- Green = V0.x modification.
- Purple = new/advanced capability.

---

## Slide 12 - What I Actually Built / Investigated

**Purpose:** Make the engineering effort explicit.

Use cards:

- Reference repository reverse engineering.
- Permission and identity analysis.
- TEST / PROD behavior comparison.
- Private Link / runtime troubleshooting.
- Scoped target resolution.
- Current-user and SPN path investigation.
- Pipeline parameterization.
- Lakehouse persistence and Agent integration.
- Regression / adverse-model validation.
- Production-oriented architecture evolution.

This slide should make it clear that the work is not simply "editing a Microsoft notebook".

---

## Slide 13 - Beyond UC1a: SMO Analytics

Use Diagram 08.

Explain the transition:

```text
V0.x answers:
Who scans?
What is scanned?
How is it triggered?

SMO Analytics additionally answers:
What evidence is retained?
How is it modeled?
How is it validated?
How is it deployed?
How is it consumed?
```

Show advanced solution items:

- deployment notebook;
- Fabric Environment;
- schema-enabled Lakehouse;
- scanner;
- parameterized pipeline;
- technical evidence and business contracts;
- deterministic quality gates;
- Direct Lake semantic model;
- Power BI report.

---

## Slide 14 - Key Recommendations and Takeaways

Recommended final messages:

### 1. Keep deterministic analysis as source of truth

AI explains and navigates evidence; it should not invent technical findings.

### 2. Keep scan scope explicit

Do not make tenant visibility equal analysis workload.

### 3. Preserve technical evidence

Do not discard raw values before root-cause and validation logic have used them.

### 4. Treat CU benefit as a measured outcome

Use controlled before/after capacity metrics rather than assuming estimated savings are realized.

Closing line:

> The primary engineering contribution was not replacing the optimization engine — it was adapting identity, scope, workload, evidence, validation, and operational architecture for enterprise use.

---

# Appendix candidates

Keep detailed evidence out of the main deck unless asked:

1. Original notebook code walkthrough.
2. BPA field mapping.
3. VertiPaq field-loss mapping.
4. Permission matrix.
5. Pipeline parameter definitions.
6. TEST / PROD observations.
7. Private Link notes.
8. Lakehouse table/data contract.
9. Anti-pattern regression evidence.
10. Advanced repository milestone/version history.

---

# Presentation design notes

## Recommended duration

15-20 minutes for the main 14-slide deck.

## Content weighting

```text
Microsoft UC1a                ~35%
UC1a V0.x                     ~40%
Advanced SMO Analytics        ~15%
Recommendations / summary     ~10%
```

## Tone

Avoid framing the Microsoft reference as defective. Use terms such as:

- reference implementation;
- pattern demonstrator;
- hackathon-oriented simplification;
- enterprise-fit gap;
- operational hardening requirement.

The argument should be evidence-based:

```text
Reference design choice
        +
Observed enterprise constraint
        =
Engineering decision
```
