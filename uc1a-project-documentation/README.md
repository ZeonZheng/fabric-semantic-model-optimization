# UC1a Project Documentation

This folder is a standalone project record for the UC1a semantic-model optimization work. It is intentionally isolated from the existing solution implementation, `docs/`, `src/`, `scripts/`, `config/`, and `tests/` content in this repository.

## Purpose

This documentation supports the Azure DevOps requirement:

> Document findings, architecture, implementation approach, and recommendations.

It records the engineering journey from the Microsoft Fabric AI Hackathon UC1a reference implementation, through the user-scoped UC1a V0.x adaptation, to the more advanced `fabric-semantic-model-optimization` solution.

## Scope

The documentation focuses on:

1. Microsoft UC1a reference architecture and notebook behavior.
2. Two-stage discovery and model-analysis flow.
3. Permission and identity implications.
4. Runtime, CU, and operational scaling observations.
5. Information loss caused by the original simplified result normalization.
6. UC1a V0.x design decisions: explicit scope, current-user-first execution, optional SPN, and on-demand scanning.
7. Evolution into the FUAM-style Semantic Model Optimization Analytics solution.
8. Architecture decisions, recommendations, evidence, and presentation material.

## Documents

- [UC1A_TECHNICAL_EVALUATION.md](UC1A_TECHNICAL_EVALUATION.md) — canonical project document.
- [EVIDENCE_MATRIX.md](EVIDENCE_MATRIX.md) — claim-to-evidence mapping and confidence level.
- [ARCHITECTURE_DIAGRAM_SPEC.md](ARCHITECTURE_DIAGRAM_SPEC.md) — master diagram specifications for Draw.io and presentation reuse.
- [PRESENTATION_STORYBOARD.md](PRESENTATION_STORYBOARD.md) — presentation storyline derived from the canonical document.
- [SOURCES.md](SOURCES.md) — repository paths and reference sources.

## Documentation principle

The project record separates three evidence classes:

- **Source verified** — confirmed directly from repository code or documentation.
- **Project observation** — observed during TEST/PROD implementation and validation.
- **Engineering assessment** — a design conclusion derived from source evidence and project observations.

This distinction is used to avoid presenting a project-specific observation as a universal benchmark or treating a hackathon reference implementation as a production product specification.

## Working summary

```text
Microsoft UC1a
PROVE THE PATTERN
      |
      v
UC1a V0.x
CONTROL THE SCOPE
      |
      v
SMO Analytics
PRODUCTIZE THE WORKFLOW
```

The central engineering contribution is not replacing the deterministic Semantic Link Labs analysis engine. It is adapting identity, scope, workload, evidence preservation, orchestration, and consumption architecture for enterprise use.
