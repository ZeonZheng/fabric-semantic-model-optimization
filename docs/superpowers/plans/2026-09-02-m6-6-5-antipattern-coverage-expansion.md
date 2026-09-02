# M6.6.5 Anti-pattern Coverage Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the two newly scanned adverse models into a repeatable acceptance corpus, eliminate confirmed rule misclassification, and extend the scanner so every valid documented anti-pattern produces either a specific deterministic finding or an explicitly review-required finding.

**Architecture:** Keep `scripts/model_quality_rules.py` as the dependency-free Model.bim/VPA analyzer and add small parsing helpers around it rather than creating a second rule engine. Store the acceptance contract as JSON, exercise each new behavior through local tests, then embed the same tested source into the Fabric scanner notebook with the existing notebook upgrader. Live Lakehouse validation remains the final gate and is not replaced by fixture tests.

**Tech Stack:** Python 3, dependency-free Model.bim metadata analysis, JSON fixtures, Fabric Notebook JSON, sempy/Fabric runtime, Lakehouse SQL.

**Spec:** `docs/m6-6-5-antipattern-coverage-expansion.md`

## Global Constraints

- The valid benchmark contains 51 anti-patterns: 27 Bank Customer Churn items plus 24 Video Game Sales items.
- Bank `AP-E02` is excluded because the injected `Fake_Calendar` table contradicts the statement that the final model has no date column or date table.
- `AgeGroup` and `AgeGroupOrder` are not special-case negative controls and receive no object-name suppression.
- Existing `MQ001` through `MQ030` identifiers remain stable.
- Deterministic findings use technical metadata evidence; usage-dependent claims require successful object-usage evidence.
- The development deployment branch remains `codex/m6-4`.
- Every production behavior change follows RED-GREEN-REFACTOR.

---

### Task 1: Freeze the acceptance corpus

**Files:**
- Create: `docs/m6-6-5-antipattern-coverage-expansion.md`
- Create: `tests/fixtures/m6_6_5_antipattern_acceptance.json`
- Modify: `tests/validate_repo.py`

**Interfaces:**
- Consumes: the two supplied anti-pattern design documents and the 2026-09-02 Lakehouse review.
- Produces: `load_m665_acceptance()` returning the validated acceptance dictionary.

- [ ] **Step 1: Write the acceptance fixture and failing contract test**

```python
fixture = json.loads((ROOT / "tests/fixtures/m6_6_5_antipattern_acceptance.json").read_text())
assert fixture["valid_item_count"] == 51
assert fixture["excluded_items"] == [{"model": "Bank Customer Churn", "id": "AP-E02", "reason": "conflicts with injected Fake_Calendar"}]
assert "AgeGroup" not in fixture.get("negative_control_objects", [])
```

- [ ] **Step 2: Run the repository validator and confirm the new contract fails before the loader exists**

Run: `python tests/validate_repo.py`

Expected: FAIL because `load_m665_acceptance` or the fixture contract is absent.

- [ ] **Step 3: Add the fixture loader and exact count/ID validation**

```python
def load_m665_acceptance():
    return json.loads((ROOT / "tests/fixtures/m6_6_5_antipattern_acceptance.json").read_text(encoding="utf-8"))
```

- [ ] **Step 4: Run the validator and confirm the corpus contract passes**

Run: `python tests/validate_repo.py`

Expected: PASS with 51 valid items and one documented exclusion.

- [ ] **Step 5: Commit**

```bash
git add docs/m6-6-5-antipattern-coverage-expansion.md docs/superpowers/plans/2026-09-02-m6-6-5-antipattern-coverage-expansion.md tests/fixtures/m6_6_5_antipattern_acceptance.json tests/validate_repo.py
git commit -m "test(scanner): freeze M6.6.5 anti-pattern corpus"
```

### Task 2: Correct current classification defects

**Files:**
- Modify: `scripts/model_quality_rules.py`
- Modify: `tests/validate_repo.py`

**Interfaces:**
- Consumes: `analyze_model_bim(bim, vpa_columns, vpa_tables)`.
- Produces: corrected MQ010 concatenation matching and ratio-format semantic evidence.

- [ ] **Step 1: Add tests proving logical `&&` is not text concatenation and text concatenation still is**

```python
assert not findings_for("MQ010", expression="FILTER(Bank_Churn, [A] > 0 && [B] > 0)")
assert findings_for("MQ010", expression='FORMAT([CustomerId], "0") & "-" & [Surname]')
```

- [ ] **Step 2: Run the focused validator and observe the MQ010 test fail**

Run: `python tests/validate_repo.py`

Expected: FAIL because the current `canon_expr.count("&") >= 2` treats `&&` as concatenation.

- [ ] **Step 3: Strip DAX logical operators before counting concatenation operators**

```python
concatenation_expression = canon_expr.replace("&&", "")
has_concatenation = "concatenate(" in canon_expr or concatenation_expression.count("&") >= 1
```

- [ ] **Step 4: Add and satisfy a ratio-format test**

```python
ratio = measure("Exited Ratio Raw", "DIVIDE([Exited Customers], [Customers])", formatString="0.00")
assert one_finding("MQ039", ratio)["severity"] == "ERROR"
```

- [ ] **Step 5: Run all tests and commit**

Run: `python tests/validate_repo.py`

Expected: PASS.

```bash
git add scripts/model_quality_rules.py tests/validate_repo.py
git commit -m "fix(scanner): correct DAX and ratio classifications"
```

### Task 3: Add relationship and model-structure coverage

**Files:**
- Modify: `scripts/model_quality_rules.py`
- Modify: `tests/validate_repo.py`

**Interfaces:**
- Produces: findings for bidirectional relationships, repeated active date roles, flat models, and visible disconnected calculated/helper tables without asserting that an object is unused.

- [ ] **Step 1: Add failing tests for Bank AP-R01 and Video AP-03/AP-04/AP-21/AP-22**

```python
assert rule_objects(findings, "MQ031") == {"Bank_Churn -> Dim_Geography"}
assert "MQ032" in detected_codes
assert "MQ001" in detected_codes
assert disconnected_table_findings_do_not_say_unused(findings)
```

- [ ] **Step 2: Run tests and confirm the new rule codes are missing**

Run: `python tests/validate_repo.py`

Expected: FAIL listing MQ031/MQ032 and the flat-model fixture.

- [ ] **Step 3: Implement metadata-only relationship and table rules**

```python
if _text(_key(rel, "crossFilteringBehavior")).lower() in {"both", "bothdirections"}:
    findings.append(_issue("MQ031", ...))
```

- [ ] **Step 4: Run tests and commit**

Run: `python tests/validate_repo.py`

Expected: PASS.

```bash
git add scripts/model_quality_rules.py tests/validate_repo.py
git commit -m "feat(scanner): detect relationship and flat-model anti-patterns"
```

### Task 4: Add DAX maintainability and performance coverage

**Files:**
- Modify: `scripts/model_quality_rules.py`
- Modify: `tests/validate_repo.py`

**Interfaces:**
- Produces: MQ035 through MQ047 measure findings using balanced-parenthesis and token-aware helpers.

- [ ] **Step 1: Add separate failing tests for volatile functions, nested IF, trivial iterators, unused VAR, magic numbers, repeated expressions, whole-table FILTER, and high-cardinality DISTINCTCOUNT**

```python
expected = {"MQ035", "MQ036", "MQ037", "MQ038", "MQ040", "MQ045", "MQ046", "MQ047"}
assert expected <= detected_codes
```

- [ ] **Step 2: Run tests and confirm failures are caused by absent behaviors**

Run: `python tests/validate_repo.py`

Expected: FAIL with the listed new codes absent.

- [ ] **Step 3: Implement the smallest token-aware helpers and rules**

```python
def _function_calls(expression, function_name):
    return re.finditer(rf"\b{re.escape(function_name)}\s*\(", _text(expression), re.I)
```

- [ ] **Step 4: Add negative tests for `DIVIDE`, date-part functions without volatility, used variables, and non-trivial iterators**

```python
assert "MQ035" not in codes_for("DAY([Order Date])")
assert "MQ038" not in codes_for("VAR Total = [Sales] RETURN Total")
```

- [ ] **Step 5: Run tests and commit**

Run: `python tests/validate_repo.py`

Expected: PASS.

```bash
git add scripts/model_quality_rules.py tests/validate_repo.py
git commit -m "feat(scanner): add DAX anti-pattern analysis"
```

### Task 5: Add calculated-column, metadata, and organization coverage

**Files:**
- Modify: `scripts/model_quality_rules.py`
- Modify: `tests/validate_repo.py`

**Interfaces:**
- Produces: specific findings for calculated-column aggregation, EARLIER, text flags, generic ordered categories, exposed technical names/PII, measure placement, and missing display folders.

- [ ] **Step 1: Add failing Bank and Video fixtures for the intended objects**

```python
expected_objects = {
    "MQ041": {("Bank_Churn", "ExitedText")},
    "MQ042": {("Bank_Churn", "TenureBand")},
    "MQ043": {("Bank_Churn", "AvgBalanceByGeo"), ("vgchartz-2024", "sales_vs_avg")},
    "MQ044": {("Bank_Churn", "GeoRankLegacy")},
    "MQ048": {("Bank_Churn", "Surname")},
}
```

- [ ] **Step 2: Run tests and observe the object-specific failures**

Run: `python tests/validate_repo.py`

Expected: FAIL for each missing object/rule pair.

- [ ] **Step 3: Implement the metadata rules without object-name allowlists or AgeGroup suppression**

```python
if re.search(r"\bEARLIER\s*\(", expression, re.I):
    findings.append(_issue("MQ044", ...))
```

- [ ] **Step 4: Broaden MQ024/MQ027 using evidence rather than `Fact` name prefixes**

```python
if is_visible_text and cardinality >= 10000:
    findings.append(_issue("MQ027", ...))
```

- [ ] **Step 5: Run tests and commit**

Run: `python tests/validate_repo.py`

Expected: PASS.

```bash
git add scripts/model_quality_rules.py tests/validate_repo.py
git commit -m "feat(scanner): cover column and semantic hygiene anti-patterns"
```

### Task 6: Embed the tested analyzer and version the scanner

**Files:**
- Modify: `scripts/upgrade_notebook_v2.py`
- Modify: `src/SMO_Optimization_Scanner.Notebook/notebook-content.ipynb`
- Modify: `config/deployment_config.yaml`
- Modify: `README.md`
- Modify: `docs/m6-6-5-antipattern-coverage-expansion.md`
- Test: `tests/validate_repo.py`

**Interfaces:**
- Consumes: tested `model_quality_rules.py` source.
- Produces: deployable Fabric scanner notebook containing byte-equivalent rule logic and an incremented scanner version.

- [ ] **Step 1: Add failing version and embedded-source parity assertions**

```python
assert notebook["metadata"]["scanner_version"] == "2.6.4"
assert embedded_analyzer_source == (ROOT / "scripts/model_quality_rules.py").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run the validator and observe the version/parity failure**

Run: `python tests/validate_repo.py`

Expected: FAIL until the notebook is rebuilt.

- [ ] **Step 3: Update the builder/version and regenerate the notebook**

Run: `python scripts/upgrade_notebook_v2.py`

Expected: notebook metadata and executable source report scanner `2.6.4`.

- [ ] **Step 4: Run the full local verification suite and commit**

Run: `python tests/validate_repo.py`

Expected: PASS with every JSON/notebook/platform file valid.

```bash
git add README.md config/deployment_config.yaml docs/m6-6-5-antipattern-coverage-expansion.md scripts/upgrade_notebook_v2.py src/SMO_Optimization_Scanner.Notebook/notebook-content.ipynb tests/validate_repo.py
git commit -m "build(scanner): publish M6.6.5 analyzer version"
```

### Task 7: Deploy and validate against Lakehouse evidence

**Files:**
- Modify: `docs/m6-6-5-antipattern-coverage-expansion.md`

**Interfaces:**
- Consumes: scanner 2.6.4, the two model IDs, and Lakehouse curated finding tables.
- Produces: a 51-row final comparison with exact, review-required, missed, and conflicting counts.

- [ ] **Step 1: Push the verified commits to `codex/m6-4` and deploy from that exact commit SHA**

```text
Repository: ZeonZheng/fabric-semantic-model-optimization
Branch: codex/m6-4
```

- [ ] **Step 2: Run the scanner for both target semantic models**

```text
Bank Customer Churn: 1ce4e502-a22b-4164-b9cc-0173e6056226
Video Game Sales: fad077bd-c277-43d3-8ca1-8532fd0b14fd
```

- [ ] **Step 3: Query the Lakehouse using the new analysis IDs**

```sql
SELECT semantic_model_name, rule_name, affected_table_name,
       affected_object_name, technical_evidence, actionability_status
FROM smopt.semantic_model_optimization_findings
WHERE analysis_id = '<new-analysis-id>'
ORDER BY semantic_model_name, rule_name, affected_table_name, affected_object_name;
```

- [ ] **Step 4: Validate the live acceptance gates**

```text
Valid benchmark items: 51
Silent misses: 0
Conflicting item: Bank AP-E02 excluded and documented
Usage-dependent "unused" assertions: 0 unless object_usage_analysis_status = SUCCEEDED
Legacy MQ001-MQ030 regression: pass
```

- [ ] **Step 5: Record actual scan IDs/counts and commit the acceptance evidence**

```bash
git add docs/m6-6-5-antipattern-coverage-expansion.md
git commit -m "docs(scanner): record M6.6.5 live acceptance"
```
