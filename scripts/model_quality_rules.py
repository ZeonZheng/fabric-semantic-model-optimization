"""Deterministic semantic-model metadata heuristics.

The scanner feeds this module a standard Model.bim dictionary plus optional
VertiPaq column/table records.  The rules intentionally return a compact,
root-cause-oriented set of issues instead of one row for every generated or
missing-description object.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict


SOURCE = "MODEL_METADATA_HEURISTIC"


def _text(value):
    return str(value or "").strip()


def _key(mapping, name, default=None):
    if not isinstance(mapping, dict):
        return default
    wanted = re.sub(r"[^a-z0-9]", "", name.lower())
    for key, value in mapping.items():
        if re.sub(r"[^a-z0-9]", "", str(key).lower()) == wanted:
            return value
    return default


def _list(mapping, name):
    value = _key(mapping, name, [])
    return value if isinstance(value, list) else []


def _model(bim):
    if not isinstance(bim, dict):
        return {}
    model = _key(bim, "model")
    if isinstance(model, dict):
        return model
    database = _key(bim, "database")
    nested = _key(database, "model") if isinstance(database, dict) else None
    return nested if isinstance(nested, dict) else bim


def _name(obj):
    return _text(_key(obj, "name"))


def _bool(obj, name, default=False):
    value = _key(obj, name, default)
    if isinstance(value, bool):
        return value
    return _text(value).lower() in {"true", "1", "yes"}


def _expression(obj):
    direct = _key(obj, "expression")
    if isinstance(direct, list):
        direct = "\n".join(map(str, direct))
    if direct is not None:
        return _text(direct)
    for partition in _list(obj, "partitions"):
        source = _key(partition, "source", {})
        value = _key(source, "expression") if isinstance(source, dict) else None
        if isinstance(value, list):
            value = "\n".join(map(str, value))
        if value:
            return _text(value)
    return ""


def _canon_expression(value):
    value = re.sub(r"//.*?$|/\*.*?\*/", "", _text(value), flags=re.M | re.S)
    return re.sub(r"\s+", "", value).lower()


def _column_ref_variants(table_name, column_name):
    """Return normalized DAX reference forms for one model column."""
    table_name = _text(table_name)
    column_name = _text(column_name)
    if not table_name or not column_name:
        return set()
    return {
        _canon_expression(f"{table_name}[{column_name}]"),
        _canon_expression(f"'{table_name}'[{column_name}]"),
    }


def _relationship_is_invoked(relationship, measure_expressions):
    """Match USERELATIONSHIP to the specific inactive relationship it invokes."""
    from_refs = _column_ref_variants(
        _key(relationship, "fromTable"), _key(relationship, "fromColumn")
    )
    to_refs = _column_ref_variants(
        _key(relationship, "toTable"), _key(relationship, "toColumn")
    )
    for expression in measure_expressions:
        canonical = _canon_expression(expression)
        if "userelationship(" not in canonical:
            continue
        if any(ref in canonical for ref in from_refs) and any(ref in canonical for ref in to_refs):
            return True
    return False


def _issue(code, rule_name, category, severity, object_type, table_name, object_name,
           description, action, evidence, confidence="HIGH", risk="MEDIUM",
           impact="MODEL_QUALITY"):
    return {
        "rule_code": code,
        "source": SOURCE,
        "rule_name": rule_name,
        "category": category,
        "severity": severity,
        "confidence": confidence,
        "impact_area": impact,
        "object_type": object_type,
        "table_name": table_name,
        "object_name": object_name,
        "finding_text": description,
        "recommended_action": action,
        "technical_evidence": evidence,
        "evidence_json": json.dumps({"rule_code": code, "evidence": evidence}, ensure_ascii=False),
        "change_risk": risk,
    }


def analyze_model_bim(bim, vpa_columns=None, vpa_tables=None):
    """Return compact deterministic findings for one semantic model."""
    model = _model(bim)
    tables = _list(model, "tables")
    relationships = _list(model, "relationships")
    roles = _list(model, "roles")
    perspectives = _list(model, "perspectives")
    findings = []

    table_by_name = {_name(table): table for table in tables if _name(table)}
    relationship_tables = defaultdict(int)
    for rel in relationships:
        for field in ("fromTable", "toTable"):
            table_name = _text(_key(rel, field))
            if table_name:
                relationship_tables[table_name] += 1

    all_measure_expressions = []
    measure_records = []
    for table in tables:
        table_name = _name(table)
        for measure in _list(table, "measures"):
            expression = _expression(measure)
            all_measure_expressions.append(expression)
            measure_records.append((table_name, measure, expression))

    # Star-schema structure and table naming.
    technical_names = []
    prefix_names = []
    auto_date_names = []
    wide_root_cause_tables = set()
    for table in tables:
        table_name = _name(table)
        columns = _list(table, "columns")
        measures = _list(table, "measures")
        lower_name = table_name.lower()
        if re.match(r"^(stg|stage|temp|tmp|vw)[_ ]", lower_name) or re.match(r"^dim_.*\d+$", lower_name):
            technical_names.append(table_name)
        if re.match(r"^(fact|dim)[A-Z_]", table_name) or lower_name.startswith(("fact", "dim")):
            prefix_names.append(table_name)
        if lower_name.startswith(("localdatetable_", "datetabletemplate_")):
            auto_date_names.append(table_name)

        visible_string_columns = [
            column for column in columns
            if "string" in _text(_key(column, "dataType")).lower() and not _bool(column, "isHidden")
        ]
        if len(columns) >= 25 and len(visible_string_columns) >= 5 and relationship_tables[table_name] == 0:
            wide_root_cause_tables.add(table_name)
            findings.append(_issue(
                "MQ001", "Wide denormalized fact-grain table", "Model structure", "ERROR", "Table",
                table_name, table_name,
                "A wide disconnected table mixes many descriptive text attributes with fact-grain data.",
                "Restore a star schema: keep additive events in facts and descriptive attributes in related dimensions.",
                f"columns={len(columns)}; visible_string_columns={len(visible_string_columns)}; relationships=0",
                risk="HIGH", impact="PERFORMANCE",
            ))

        if relationship_tables[table_name] == 0 and not measures and 0 < len(columns) <= 5 and not _bool(table, "isHidden"):
            findings.append(_issue(
                "MQ003", "Disconnected table without measures", "Model structure", "WARNING", "Table",
                table_name, table_name,
                "The table has no model relationships and contains no measures.",
                "Confirm the table has an intentional disconnected-table use case; otherwise relate or remove it.",
                f"columns={len(columns)}; relationships=0; measures=0", risk="HIGH",
            ))

    if technical_names:
        findings.append(_issue(
            "MQ004", "Technical or temporary table names", "Naming", "WARNING", "Model", None, None,
            "Technical/staging names reduce business readability and AI discoverability.",
            "Rename published semantic objects with clear business terms and keep staging objects outside the model.",
            "tables=" + ", ".join(sorted(technical_names)), risk="LOW",
        ))
    if prefix_names:
        findings.append(_issue(
            "MQ026", "Fact/Dim table prefixes exposed to users", "Naming", "INFO", "Model", None, None,
            "Technical Fact/Dim prefixes are exposed in the business layer.",
            "Use concise business-facing table names while retaining technical lineage in descriptions.",
            "tables=" + ", ".join(sorted(prefix_names)), risk="MEDIUM",
        ))

    # Duplicate table definitions: exact column signatures or a bare calculated-table reference.
    signatures = defaultdict(list)
    duplicate_copy_tables = set()
    for table in tables:
        names = tuple(sorted(_name(c).lower() for c in _list(table, "columns") if _name(c)))
        if len(names) >= 3:
            signatures[names].append(_name(table))
        expression = _canon_expression(_expression(table)).strip("'")
        if expression in {name.lower() for name in table_by_name if name.lower() != _name(table).lower()}:
            duplicate_copy_tables.add(_name(table))
            findings.append(_issue(
                "MQ002", "Duplicate calculated table", "Model structure", "ERROR", "Table", _name(table), _name(table),
                "The calculated table is a direct copy of another model table.",
                "Remove the duplicate and reuse the original dimension; validate dependencies before deletion.",
                f"expression={_expression(table)}", risk="HIGH", impact="MODEL_SIZE",
            ))
    for signature, names in signatures.items():
        if len(names) > 1:
            findings.append(_issue(
                "MQ002", "Duplicate table column signature", "Model structure", "ERROR", "Model", None, None,
                "Multiple tables expose the same non-trivial column set.",
                "Confirm whether the tables are true role-playing dimensions; otherwise consolidate duplicate copies.",
                f"tables={', '.join(sorted(names))}; shared_columns={len(signature)}", risk="HIGH", impact="MODEL_SIZE",
            ))

    duplicate_columns = defaultdict(list)
    missing_descriptions = defaultdict(list)
    double_columns = []
    invalid_summarize = []
    for table in tables:
        table_name = _name(table)
        table_lower = table_name.lower()
        table_is_generated = table_lower.startswith(("localdatetable_", "datetabletemplate_"))
        table_is_exposed = not _bool(table, "isHidden") and not table_is_generated
        if table_is_exposed and not _text(_key(table, "description")):
            missing_descriptions["tables"].append(table_name)
        for column in _list(table, "columns"):
            column_name = _name(column)
            data_type = _text(_key(column, "dataType")).lower()
            expression = _expression(column)
            canon_expr = _canon_expression(expression)
            object_ref = f"{table_name}[{column_name}]"
            column_is_exposed = table_is_exposed and not _bool(column, "isHidden")
            if column_is_exposed and not _text(_key(column, "description")):
                missing_descriptions["columns"].append(object_ref)
            if (
                column_is_exposed
                and table_name not in wide_root_cause_tables
                and table_name not in duplicate_copy_tables
                and column_name
                and not re.search(r"(?:key|id)$", column_name, re.I)
            ):
                duplicate_columns[column_name.lower()].append(object_ref)

            if "string" in data_type and ("date" in column_name.lower() or ("format(" in canon_expr and "datevalue(" in canon_expr)):
                findings.append(_issue(
                    "MQ005", "Date stored or calculated as text", "Date handling", "ERROR", "Column",
                    table_name, column_name, "A date-like column uses text storage or FORMAT-based text output.",
                    "Use a Date/DateTime typed column and apply display formatting separately.",
                    f"data_type={data_type}; expression={expression}", risk="MEDIUM",
                ))
            if "related(" in canon_expr:
                findings.append(_issue(
                    "MQ006", "Dimension attribute copied into fact with RELATED", "Model structure", "ERROR", "Column",
                    table_name, column_name, "A calculated column copies a related attribute into another table.",
                    "Keep the attribute in its dimension and use the relationship/filter context.",
                    f"expression={expression}", risk="MEDIUM", impact="MODEL_SIZE",
                ))
            if table_name.lower().startswith("fact") and expression and re.search(r"[+*/-]", expression) and not re.search(r"RELATED|FORMAT|CONCATENATE|RAND", expression, re.I):
                findings.append(_issue(
                    "MQ007", "Row arithmetic implemented as a calculated fact column", "DAX", "ERROR", "Column",
                    table_name, column_name, "Row-level arithmetic is persisted in a fact calculated column.",
                    "Prefer a measure when the result is an aggregation and validate filter-context behavior.",
                    f"expression={expression}", risk="HIGH", impact="MODEL_SIZE",
                ))
            if re.search(r"\b(RAND|RANDBETWEEN|NOW|TODAY)\s*\(", expression, re.I):
                findings.append(_issue(
                    "MQ008", "Volatile or non-deterministic calculated column", "DAX", "WARNING", "Column",
                    table_name, column_name, "The expression uses a volatile/non-deterministic function.",
                    "Replace it with deterministic source data or a controlled refresh-time value.",
                    f"expression={expression}", risk="MEDIUM",
                ))
            if "concatenate(" in canon_expr or canon_expr.count("&") >= 2:
                findings.append(_issue(
                    "MQ010", "Multi-attribute concatenated column", "Model structure", "WARNING", "Column",
                    table_name, column_name, "The column combines multiple independent attributes into one text value.",
                    "Keep attributes separate for filtering/grouping; add a display label only when required.",
                    f"expression={expression}", risk="MEDIUM",
                ))
            if (
                column_is_exposed
                and "format(" in canon_expr
                and "string" in data_type
                and "date" not in column_name.lower()
            ):
                findings.append(_issue(
                    "MQ011", "Numeric value formatted into a text column", "Data types", "WARNING", "Column",
                    table_name, column_name, "FORMAT converts a numeric value into text, preventing correct aggregation and sorting.",
                    "Keep the column numeric and use format metadata for presentation.",
                    f"data_type={data_type}; expression={expression}", risk="MEDIUM",
                ))
            if re.search(r"^(column\d+|zz_|junk|placeholder)", column_name, re.I):
                findings.append(_issue(
                    "MQ012", "Meaningless or junk column name", "Naming", "INFO", "Column",
                    table_name, column_name, "The column name signals a placeholder, generated field, or unused artifact.",
                    "Confirm usage, then rename with business meaning or remove it after dependency validation.",
                    f"column={object_ref}", risk="HIGH",
                ))
            if re.search(r"month.*name|name.*month", column_name, re.I) and "string" in data_type and not _text(_key(column, "sortByColumn")):
                findings.append(_issue(
                    "MQ025", "Month-name column without chronological sort", "Date handling", "INFO", "Column",
                    table_name, column_name, "A text month attribute has no sort-by column and can sort alphabetically.",
                    "Set Sort by column to the numeric month sequence.",
                    f"sortByColumn={_key(column, 'sortByColumn')}", risk="LOW",
                ))
            if re.fullmatch(r"\[?[^\[\]]+\]?", _text(expression)) and expression and column_name.lower() not in expression.lower():
                findings.append(_issue(
                    "MQ013", "Redundant calculated column alias", "Maintainability", "INFO", "Column",
                    table_name, column_name, "The calculated column directly aliases another column.",
                    "Reuse the source column or rename it at the semantic layer instead of persisting a clone.",
                    f"expression={expression}", risk="MEDIUM", impact="MODEL_SIZE",
                ))
            if data_type in {"double", "real"}:
                double_columns.append(object_ref)
            summarize = _text(_key(column, "summarizeBy")).lower()
            if summarize not in {"", "none", "donotsummarize"} and re.search(r"key|id|numberof|linenumber|year", column_name, re.I):
                invalid_summarize.append(f"{object_ref}={summarize}")

    for column_name, refs in duplicate_columns.items():
        if len({ref.split("[")[0] for ref in refs}) > 1:
            findings.append(_issue(
                "MQ009", "Ambiguous column name across tables", "Naming", "WARNING", "Model", None, column_name,
                "The same non-key column name is exposed by multiple tables.",
                "Use specific business names and descriptions so users and AI can distinguish the fields.",
                "objects=" + ", ".join(sorted(refs)), risk="LOW",
            ))
    if double_columns:
        findings.append(_issue(
            "MQ023", "Floating-point columns", "Data types", "WARNING", "Model", None, None,
            "Double/Real columns can introduce rounding ambiguity and weaker compression.",
            "Use fixed decimal, whole number, or scaled integer types where business precision permits.",
            "columns=" + ", ".join(sorted(double_columns)), risk="HIGH", impact="MODEL_SIZE",
        ))
    if invalid_summarize:
        findings.append(_issue(
            "MQ024", "Implicit aggregation enabled on identifiers", "Usability", "INFO", "Model", None, None,
            "Identifier/date-sequence columns allow implicit aggregation.",
            "Set Summarize by to None/Do not summarize for non-additive attributes.",
            "columns=" + ", ".join(sorted(invalid_summarize)), risk="LOW",
        ))

    # Measure expression rules.
    expression_groups = defaultdict(list)
    for table_name, measure, expression in measure_records:
        measure_name = _name(measure)
        canon_expr = _canon_expression(expression)
        object_ref = f"{table_name}[{measure_name}]"
        if canon_expr:
            expression_groups[canon_expr].append(object_ref)
        if not _bool(measure, "isHidden") and not _text(_key(measure, "description")):
            missing_descriptions["measures"].append(object_ref)
        if table_name.lower().startswith("dim") and re.search(r"\b(SUM|SUMX|COUNT|COUNTROWS|AVERAGE)\s*\(\s*Fact", expression, re.I):
            findings.append(_issue(
                "MQ014", "Fact aggregation measure stored in a dimension", "Measure organization", "ERROR", "Measure",
                table_name, measure_name, "A measure in a dimension table aggregates a fact-table value.",
                "Move the measure to a dedicated measure table or the relevant business subject area.",
                f"expression={expression}", risk="MEDIUM",
            ))
        if re.fullmatch(r"\s*\[[^\]]+\]\s*", expression or ""):
            findings.append(_issue(
                "MQ016", "Pass-through measure alias", "DAX", "INFO", "Measure",
                table_name, measure_name, "The measure is only a direct reference to another measure.",
                "Remove the alias or give it distinct business logic and documentation.",
                f"expression={expression}", risk="MEDIUM",
            ))
        if re.search(r"CALCULATE|FILTER", expression, re.I) and re.search(r"(?:=|<>|>=|<=|>|<)\s*(?:\d{4}|\"[^\"]+\")", expression):
            findings.append(_issue(
                "MQ017", "Hardcoded filter literal in measure", "DAX", "ERROR", "Measure",
                table_name, measure_name, "The measure embeds a fixed filter literal that can silently age or return blank results.",
                "Use model attributes, parameters, or relative logic and regression-test across the supported data range.",
                f"expression={expression}", risk="HIGH",
            ))
        if re.search(r"FILTER\s*\(\s*ALL(?:EXCEPT)?\s*\(", expression, re.I):
            findings.append(_issue(
                "MQ018", "FILTER over ALL table scan", "DAX performance", "ERROR", "Measure",
                table_name, measure_name, "FILTER(ALL(...)) can force unnecessary full-table iteration.",
                "Rewrite with a direct Boolean filter or narrower filter-removal semantics where equivalent.",
                f"expression={expression}", risk="HIGH", impact="PERFORMANCE",
            ))
        if not _bool(measure, "isHidden") and not _text(_key(measure, "formatString")):
            findings.append(_issue(
                "MQ019", "Visible measure without format string", "Formatting", "WARNING", "Measure",
                table_name, measure_name, "A visible measure has no explicit format string.",
                "Apply a business-appropriate numeric, currency, percentage, or date format.",
                f"measure={object_ref}", risk="LOW",
            ))
    for expression, refs in expression_groups.items():
        if len(refs) > 1:
            findings.append(_issue(
                "MQ015", "Duplicate measure expression", "DAX", "ERROR", "Model", None, None,
                "Multiple measures have the same normalized DAX expression.",
                "Consolidate the measures and preserve aliases only when they carry documented business semantics.",
                "measures=" + ", ".join(sorted(refs)), risk="HIGH",
            ))

    if auto_date_names:
        findings.append(_issue(
            "MQ020", "Auto Date/Time tables present", "Date handling", "ERROR", "Model", None, None,
            "System-generated local date tables coexist with the published semantic model.",
            "Disable Auto Date/Time and migrate calculations/relationships to a marked explicit date dimension.",
            "tables=" + ", ".join(sorted(auto_date_names)), risk="HIGH", impact="MODEL_SIZE",
        ))
    hidden_related = sorted(
        name for name, table in table_by_name.items()
        if _bool(table, "isHidden") and relationship_tables[name] > 0
    )
    if hidden_related:
        findings.append(_issue(
            "MQ021", "Hidden tables participate in relationships", "Maintainability", "WARNING", "Model", None, None,
            "Hidden tables remain active in model relationships and obscure lineage.",
            "Document the role or replace generated/technical tables with an explicit maintained design.",
            "tables=" + ", ".join(hidden_related), risk="HIGH",
        ))
    date_candidates = [
        table for table in tables
        if "date" in _name(table).lower() or any("date" in _name(c).lower() for c in _list(table, "columns"))
    ]
    marked_dates = [
        _name(table) for table in tables
        if _bool(table, "isDateTable") or _text(_key(table, "dataCategory")).lower() == "time"
    ]
    if date_candidates and not marked_dates:
        findings.append(_issue(
            "MQ022", "No explicit table marked as the date table", "Date handling", "ERROR", "Model", None, None,
            "Date-like tables exist but none is explicitly marked as the model date table.",
            "Mark the conformed date dimension and validate time-intelligence calculations.",
            "date_candidates=" + ", ".join(sorted(_name(t) for t in date_candidates)), risk="HIGH",
        ))

    # Storage-aware high-cardinality text rule.
    for row in vpa_columns or []:
        table_name = _text(row.get("table_name"))
        column_name = _text(row.get("column_name"))
        data_type = _text(row.get("data_type")).lower()
        cardinality = int(row.get("cardinality") or 0)
        if table_name.lower().startswith("fact") and any(x in data_type for x in ("string", "text")) and cardinality >= 10000:
            findings.append(_issue(
                "MQ027", "High-cardinality text in a fact table", "Storage", "WARNING", "Column",
                table_name, column_name, "A fact-grain text column has high cardinality and can create a large dictionary.",
                "Validate report/export usage, then remove, normalize, or move it to an appropriate degenerate dimension.",
                f"cardinality={cardinality}; total_size_bytes={row.get('total_size_bytes')}", risk="HIGH", impact="MODEL_SIZE",
            ))

    description_counts = {kind: len(values) for kind, values in missing_descriptions.items() if values}
    if description_counts:
        sample = []
        for kind in sorted(missing_descriptions):
            sample.extend(missing_descriptions[kind][:5])
        findings.append(_issue(
            "MQ028", "Visible semantic objects lack descriptions", "AI readiness", "INFO", "Model", None, None,
            "Visible tables, columns, or measures lack business descriptions.",
            "Add concise business meaning, grain, calculation intent, units, and important caveats; prioritize user-facing objects.",
            f"counts={json.dumps(description_counts, sort_keys=True)}; sample={', '.join(sample)}", risk="LOW",
        ))

    implicit = _key(model, "discourageImplicitMeasures", False)
    if not _bool({"value": implicit}, "value") or not roles or not perspectives:
        findings.append(_issue(
            "MQ029", "Model governance features are incomplete", "Governance", "WARNING", "Model", None, None,
            "The model permits implicit measures and/or has no roles or perspectives.",
            "Review explicit-measure policy, data sensitivity, RLS requirements, and audience-specific perspectives.",
            f"discourageImplicitMeasures={implicit}; roles={len(roles)}; perspectives={len(perspectives)}", risk="HIGH",
        ))

    unresolved_relationships = defaultdict(list)
    for relationship in relationships:
        if _bool(relationship, "isActive", True):
            continue
        from_table = _text(_key(relationship, "fromTable"))
        from_column = _text(_key(relationship, "fromColumn"))
        to_table = _text(_key(relationship, "toTable"))
        to_column = _text(_key(relationship, "toColumn"))
        if not _relationship_is_invoked(relationship, all_measure_expressions):
            unresolved_relationships[(from_table, to_table)].append(
                f"{from_table}[{from_column}] -> {to_table}[{to_column}]"
            )
    for (from_table, to_table), relationship_refs in sorted(unresolved_relationships.items()):
        findings.append(_issue(
            "MQ030", "Inactive relationships without USERELATIONSHIP measures", "Relationships", "INFO", "Relationship group",
            from_table, f"{from_table} -> {to_table}",
            "One or more inactive relationships between the same table pair are not invoked by a matching USERELATIONSHIP measure.",
            "Confirm each role-playing relationship is required and add explicit measures or remove incomplete design artifacts.",
            f"count={len(relationship_refs)}; relationships=" + "; ".join(sorted(relationship_refs)), risk="HIGH",
        ))

    # Deterministic de-duplication protects idempotent output and opportunity counts.
    unique = {}
    for finding in findings:
        key = (
            finding["rule_code"], finding.get("table_name"), finding.get("object_name"),
            finding.get("technical_evidence"),
        )
        unique[key] = finding
    return list(unique.values())
