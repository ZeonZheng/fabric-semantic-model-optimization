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


def _is_generated_table_name(table_name):
    return _text(table_name).lower().startswith(("localdatetable_", "datetabletemplate_"))


def _is_date_like_table(table):
    table_name = _name(table).lower()
    if "date" in table_name or "calendar" in table_name:
        return True
    return any(
        "date" in _text(_key(column, "dataType")).lower()
        for column in _list(table, "columns")
    )


def _is_numeric_data_type(data_type):
    normalized = re.sub(r"[^a-z0-9]", "", _text(data_type).lower())
    return normalized in {
        "byte", "currency", "decimal", "decimal128", "double", "fixeddecimal",
        "float", "int", "int16", "int32", "int64", "integer", "long",
        "number", "real", "single", "uint16", "uint32", "uint64", "whole",
        "wholenumber",
    }


def _format_references_numeric_column(expression, columns):
    """Return True when FORMAT's value expression references a known numeric column."""
    numeric_names = {
        _name(column)
        for column in columns
        if _name(column) and _is_numeric_data_type(_key(column, "dataType"))
    }
    if not numeric_names:
        return False
    format_arguments = re.findall(r"\bFORMAT\s*\(\s*([^,\r\n]+)", _text(expression), re.I)
    for argument in format_arguments:
        for column_name in numeric_names:
            if re.search(rf"\[\s*{re.escape(column_name)}\s*\]", argument, re.I):
                return True
    return False


def _measure_is_text_like(measure, expression):
    """Identify measures whose result is intentionally text and needs no format string."""
    if "string" in _text(_key(measure, "dataType")).lower():
        return True
    if re.search(r"(?:label|name|title|text|description|message|caption)\s*$", _name(measure), re.I):
        return True
    canonical = _canon_expression(expression)
    return "format(" in canonical or "concatenate(" in canonical or "&" in canonical


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


def _function_calls(expression, function_name):
    """Return balanced DAX function calls as full text plus their argument text."""
    source = _text(expression)
    calls = []
    pattern = re.compile(rf"\b{re.escape(function_name)}\s*\(", re.I)
    for match in pattern.finditer(source):
        opening = source.find("(", match.start())
        depth = 0
        quote = None
        index = opening
        while index < len(source):
            char = source[index]
            if quote:
                if char == quote:
                    if index + 1 < len(source) and source[index + 1] == quote:
                        index += 1
                    else:
                        quote = None
            elif char in {'"', "'"}:
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    calls.append((source[match.start():index + 1], source[opening + 1:index]))
                    break
            index += 1
    return calls


def _split_dax_arguments(arguments):
    """Split a balanced DAX argument list on top-level commas."""
    parts = []
    start = 0
    depth = 0
    quote = None
    for index, char in enumerate(arguments):
        if quote:
            if char == quote:
                quote = None
        elif char in {'"', "'"}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            parts.append(arguments[start:index].strip())
            start = index + 1
    parts.append(arguments[start:].strip())
    return parts


def _max_function_depth(expression, function_name):
    """Return the maximum nested depth of one DAX function."""
    source = _text(expression)
    token = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    stack = []
    wanted = function_name.upper()
    maximum = 0
    index = 0
    quote = None
    while index < len(source):
        char = source[index]
        if quote:
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {'"', "'"}:
            quote = char
            index += 1
            continue
        match = token.match(source, index)
        if match:
            stack.append(match.group(1).upper())
            maximum = max(maximum, sum(name == wanted for name in stack))
            index = match.end()
            continue
        if char == ")" and stack:
            stack.pop()
        index += 1
    return maximum


def _magic_numbers(expression):
    """Return non-trivial numeric literals from executable DAX text."""
    without_strings = re.sub(r'"(?:""|[^"])*"', "", _text(expression))
    values = re.findall(r"(?<![A-Za-z0-9_.])(?:\d+\.\d+|\d{2,})(?![A-Za-z0-9_.])", without_strings)
    return sorted(set(values), key=lambda value: (float(value), value))


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
    business_relationship_tables = defaultdict(int)
    active_date_relationships = defaultdict(list)
    for rel in relationships:
        from_table = _text(_key(rel, "fromTable"))
        to_table = _text(_key(rel, "toTable"))
        for field in ("fromTable", "toTable"):
            table_name = _text(_key(rel, field))
            if table_name:
                relationship_tables[table_name] += 1
        if from_table and to_table:
            if not _is_generated_table_name(to_table):
                business_relationship_tables[from_table] += 1
            if not _is_generated_table_name(from_table):
                business_relationship_tables[to_table] += 1
        if (
            _bool(rel, "isActive", True)
            and from_table
            and to_table in table_by_name
            and _is_date_like_table(table_by_name[to_table])
        ):
            active_date_relationships[from_table].append(
                f"{from_table}[{_text(_key(rel, 'fromColumn'))}] -> "
                f"{to_table}[{_text(_key(rel, 'toColumn'))}]"
            )

        cross_filtering = re.sub(
            r"[^a-z]", "", _text(_key(rel, "crossFilteringBehavior")).lower()
        )
        if cross_filtering in {"both", "bothdirections", "bidirectional"}:
            findings.append(_issue(
                "MQ031", "Bidirectional relationship filtering", "Relationships", "ERROR", "Relationship",
                from_table, f"{from_table} -> {to_table}",
                "An active model relationship permits filters to propagate in both directions.",
                "Use single-direction dimension-to-fact filtering unless a reviewed many-to-many design requires both directions.",
                (
                    f"relationship={from_table}[{_text(_key(rel, 'fromColumn'))}] -> "
                    f"{to_table}[{_text(_key(rel, 'toColumn'))}]; "
                    f"cross_filtering_behavior={_text(_key(rel, 'crossFilteringBehavior'))}"
                ),
                risk="HIGH", impact="PERFORMANCE",
            ))

    for table_name, relationship_refs in sorted(active_date_relationships.items()):
        if len(relationship_refs) >= 2:
            findings.append(_issue(
                "MQ032", "Multiple active date-role relationships", "Relationships", "WARNING", "Relationship group",
                table_name, table_name,
                "A table uses multiple active relationships for separate date roles, which can fragment time intelligence.",
                "Use one conformed date dimension and make secondary date roles inactive with explicit USERELATIONSHIP measures.",
                f"count={len(relationship_refs)}; relationships=" + "; ".join(sorted(relationship_refs)),
                risk="HIGH",
            ))

    all_measure_expressions = []
    measure_records = []
    for table in tables:
        table_name = _name(table)
        for measure in _list(table, "measures"):
            expression = _expression(measure)
            all_measure_expressions.append(expression)
            measure_records.append((table_name, measure, expression))

    vpa_cardinality = {}
    for row in vpa_columns or []:
        key = (_text(row.get("table_name")).lower(), _text(row.get("column_name")).lower())
        vpa_cardinality[key] = int(row.get("cardinality") or 0)
    vpa_row_counts = {
        _text(row.get("table_name")).lower(): int(row.get("row_count") or 0)
        for row in vpa_tables or []
    }
    known_table_names = {name.lower() for name in table_by_name}

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
        if _is_generated_table_name(table_name):
            auto_date_names.append(table_name)

        visible_string_columns = [
            column for column in columns
            if "string" in _text(_key(column, "dataType")).lower() and not _bool(column, "isHidden")
        ]
        strong_wide_signal = (
            len(columns) >= 25
            and len(visible_string_columns) >= 5
            and relationship_tables[table_name] == 0
        )
        flat_model_signal = (
            len(columns) >= 12
            and len(visible_string_columns) >= 4
            and business_relationship_tables[table_name] <= 1
        )
        if strong_wide_signal or flat_model_signal:
            wide_root_cause_tables.add(table_name)
            findings.append(_issue(
                "MQ001", "Wide denormalized fact-grain table", "Model structure",
                "ERROR" if strong_wide_signal else "WARNING", "Table",
                table_name, table_name,
                "A wide or weakly related table mixes descriptive text attributes with fact-grain data.",
                "Restore a star schema: keep additive events in facts and descriptive attributes in related dimensions.",
                (
                    f"columns={len(columns)}; visible_string_columns={len(visible_string_columns)}; "
                    f"relationships={relationship_tables[table_name]}; "
                    f"business_relationships={business_relationship_tables[table_name]}"
                ),
                confidence="HIGH" if strong_wide_signal else "MEDIUM", risk="HIGH", impact="PERFORMANCE",
            ))

        if relationship_tables[table_name] == 0 and not measures and 0 < len(columns) <= 5 and not _bool(table, "isHidden"):
            findings.append(_issue(
                "MQ003", "Disconnected table without measures", "Model structure", "WARNING", "Table",
                table_name, table_name,
                "The table has no model relationships and contains no measures.",
                "Confirm the table has an intentional disconnected-table use case; otherwise relate or remove it.",
                f"columns={len(columns)}; relationships=0; measures=0", risk="HIGH",
            ))
        table_expression = _expression(table)
        if (
            relationship_tables[table_name] == 0
            and not measures
            and table_expression
            and re.search(r"\b(DISTINCT|VALUES|SUMMARIZE|SELECTCOLUMNS|FILTER)\s*\(", table_expression, re.I)
        ):
            findings.append(_issue(
                "MQ052", "Disconnected calculated projection table", "Model structure", "WARNING", "Table",
                table_name, table_name,
                "A calculated table projects values from model data but has no relationships or measures.",
                "Confirm the disconnected-table interaction design; otherwise relate it or remove the redundant projection after dependency review.",
                f"relationships=0; measures=0; expression={table_expression}",
                confidence="MEDIUM", risk="HIGH", impact="MODEL_SIZE",
            ))

    for table_name in sorted(technical_names):
        findings.append(_issue(
            "MQ004", "Technical or temporary table names", "Naming", "WARNING", "Table",
            table_name, table_name,
            "A published table exposes a technical, staging, temporary, or non-business name.",
            "Rename the semantic object with a clear business term and keep staging objects outside the published model.",
            f"table={table_name}; matched_pattern=STG_/STAGE_/TEMP_/TMP_/VW_/Dim_*<number>", risk="LOW",
        ))
    for table_name in sorted(prefix_names):
        findings.append(_issue(
            "MQ026", "Fact/Dim table prefixes exposed to users", "Naming", "INFO", "Table",
            table_name, table_name,
            "A business-facing table exposes a technical Fact/Dim prefix.",
            "Use a concise business-facing table name while retaining technical lineage in its description.",
            f"table={table_name}; matched_prefix=Fact/Dim", risk="MEDIUM",
        ))

    # Duplicate table definitions: exact column signatures or a bare calculated-table reference.
    signatures = defaultdict(list)
    duplicate_copy_tables = set()
    for table in tables:
        if _is_generated_table_name(_name(table)):
            continue
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
        columns = _list(table, "columns")
        table_is_generated = _is_generated_table_name(table_name)
        table_is_exposed = not _bool(table, "isHidden") and not table_is_generated
        if table_is_exposed and not _text(_key(table, "description")):
            missing_descriptions["tables"].append(table_name)
        for column in columns:
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
            dax_without_logical_and = canon_expr.replace("&&", "")
            if "concatenate(" in canon_expr or "&" in dax_without_logical_and:
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
                and _format_references_numeric_column(expression, columns)
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
        distinct_tables = {ref.split("[")[0] for ref in refs}
        if len(distinct_tables) > 1:
            evidence = "objects=" + ", ".join(sorted(refs))
            for object_ref in sorted(refs):
                table_name, object_name = object_ref.split("[", 1)
                findings.append(_issue(
                    "MQ009", "Ambiguous column name across tables", "Naming", "WARNING", "Column",
                    table_name, object_name.rstrip("]"),
                    "The same non-key column name is exposed by multiple tables.",
                    "Use specific business names and descriptions so users and AI can distinguish the fields.",
                    evidence, risk="LOW",
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
        if re.search(r"\b(TODAY|NOW|UTCNOW|RAND|RANDBETWEEN)\s*\(", expression, re.I):
            volatile_functions = sorted(set(
                match.upper()
                for match in re.findall(
                    r"\b(TODAY|NOW|UTCNOW|RAND|RANDBETWEEN)\s*\(", expression, re.I
                )
            ))
            findings.append(_issue(
                "MQ035", "Volatile function in a measure", "DAX", "WARNING", "Measure",
                table_name, measure_name,
                "The measure uses a volatile or non-deterministic function that can reduce cache reuse.",
                "Replace query-time volatility with a controlled refresh-time value or explicit as-of parameter where possible.",
                f"functions={','.join(volatile_functions)}; expression={expression}", risk="MEDIUM",
                impact="PERFORMANCE",
            ))
        nested_if_depth = _max_function_depth(expression, "IF")
        if nested_if_depth >= 3:
            findings.append(_issue(
                "MQ036", "Deeply nested IF expression", "DAX", "INFO", "Measure",
                table_name, measure_name,
                "The measure contains at least three nested IF levels and is difficult to review and maintain.",
                "Use SWITCH or variables to express mutually exclusive branches and avoid repeated evaluation.",
                f"nested_if_depth={nested_if_depth}; expression={expression}", confidence="HIGH", risk="MEDIUM",
            ))
        for iterator_name in ("SUMX", "AVERAGEX"):
            trivial_calls = []
            for full_call, arguments in _function_calls(expression, iterator_name):
                parts = _split_dax_arguments(arguments)
                if len(parts) != 2:
                    continue
                iterator_table = parts[0].strip().strip("'").lower()
                row_expression = _canon_expression(parts[1])
                simple_column = re.fullmatch(
                    r"(?:'?[a-z0-9_\- ]+'?)?\[[^\]]+\](?:\*1)?", row_expression
                )
                if iterator_table in known_table_names and simple_column:
                    trivial_calls.append(full_call)
            if trivial_calls:
                findings.append(_issue(
                    "MQ037", "Trivial whole-table iterator", "DAX performance", "WARNING", "Measure",
                    table_name, measure_name,
                    "A whole-table iterator performs a simple column aggregation that the storage engine can evaluate directly.",
                    f"Replace {iterator_name} with the equivalent direct aggregation and compare query results and duration.",
                    "calls=" + " | ".join(trivial_calls), risk="MEDIUM", impact="PERFORMANCE",
                ))
        variable_names = re.findall(r"\bVAR\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", expression, re.I)
        unused_variables = sorted({
            name for name in variable_names
            if len(re.findall(rf"\b{re.escape(name)}\b", expression, re.I)) == 1
        })
        if unused_variables:
            findings.append(_issue(
                "MQ038", "Unused DAX variables", "DAX", "INFO", "Measure",
                table_name, measure_name,
                "The measure declares variables that are never referenced after their declaration.",
                "Remove dead variables or use them in the intended expression, then regression-test the result.",
                f"variables={','.join(unused_variables)}; expression={expression}", risk="LOW",
            ))
        expensive_distinct_counts = []
        for full_call, arguments in _function_calls(expression, "DISTINCTCOUNT"):
            ref_match = re.fullmatch(
                r"\s*(?:'([^']+)'|([^\[\]]+))?\s*\[\s*([^\]]+)\s*\]\s*", arguments
            )
            if not ref_match:
                continue
            ref_table = _text(ref_match.group(1) or ref_match.group(2) or table_name)
            ref_column = _text(ref_match.group(3))
            cardinality = vpa_cardinality.get((ref_table.lower(), ref_column.lower()), 0)
            row_count = vpa_row_counts.get(ref_table.lower(), 0)
            if cardinality >= 5000 or (row_count and cardinality / row_count >= 0.5):
                expensive_distinct_counts.append(
                    f"{full_call}:cardinality={cardinality}:row_count={row_count}"
                )
        if expensive_distinct_counts:
            findings.append(_issue(
                "MQ040", "DISTINCTCOUNT over a high-cardinality column", "DAX performance", "WARNING", "Measure",
                table_name, measure_name,
                "The measure performs DISTINCTCOUNT over a column with high observed cardinality.",
                "Confirm the business grain and query frequency; consider a pre-aggregated count or lower-cardinality key where equivalent.",
                "calls=" + " | ".join(expensive_distinct_counts), confidence="HIGH", risk="HIGH",
                impact="PERFORMANCE",
            ))
        magic_numbers = _magic_numbers(expression)
        if magic_numbers:
            findings.append(_issue(
                "MQ045", "Undocumented numeric constants in a measure", "DAX", "INFO", "Measure",
                table_name, measure_name,
                "The measure embeds non-trivial numeric constants whose business meaning is not represented in model metadata.",
                "Replace business constants with documented parameters or named variables and validate the calculation intent.",
                f"numeric_literals={','.join(magic_numbers)}; expression={expression}",
                confidence="MEDIUM", risk="HIGH",
            ))
        repeated_calls = defaultdict(list)
        for aggregate_name in ("SUM", "AVERAGE", "COUNT", "COUNTROWS", "MIN", "MAX"):
            for full_call, _ in _function_calls(expression, aggregate_name):
                repeated_calls[_canon_expression(full_call)].append(full_call)
        repeated_evidence = [
            f"count={len(calls)}:{calls[0]}"
            for calls in repeated_calls.values() if len(calls) >= 2
        ]
        if repeated_evidence and not variable_names:
            findings.append(_issue(
                "MQ046", "Repeated DAX subexpression without variables", "DAX", "WARNING", "Measure",
                table_name, measure_name,
                "The measure repeats the same aggregate expression without assigning it to a variable.",
                "Evaluate the aggregate once in a named VAR and reuse it in RETURN; verify identical results and query plans.",
                "repeated_calls=" + " | ".join(repeated_evidence) + f"; expression={expression}",
                risk="LOW", impact="PERFORMANCE",
            ))
        whole_table_filters = []
        for full_call, arguments in _function_calls(expression, "FILTER"):
            parts = _split_dax_arguments(arguments)
            if len(parts) < 2:
                continue
            filter_source = parts[0].strip().strip("'").lower()
            if filter_source in known_table_names:
                whole_table_filters.append(full_call)
        if whole_table_filters:
            findings.append(_issue(
                "MQ047", "FILTER iterates a whole model table", "DAX performance", "ERROR", "Measure",
                table_name, measure_name,
                "FILTER iterates an entire model table instead of applying a narrow Boolean or column filter.",
                "Use a direct CALCULATE Boolean filter or KEEPFILTERS over the required column when semantics are equivalent.",
                "calls=" + " | ".join(whole_table_filters), risk="HIGH", impact="PERFORMANCE",
            ))
        if (
            not _bool(measure, "isHidden")
            and not _text(_key(measure, "formatString"))
            and not _measure_is_text_like(measure, expression)
        ):
            findings.append(_issue(
                "MQ019", "Visible measure without format string", "Formatting", "WARNING", "Measure",
                table_name, measure_name, "A visible measure has no explicit format string.",
                "Apply a business-appropriate numeric, currency, percentage, or date format.",
                f"measure={object_ref}", risk="LOW",
            ))
        format_string = _text(_key(measure, "formatString"))
        if (
            re.search(r"\bDIVIDE\s*\(", expression, re.I)
            and re.search(r"(?:ratio|rate|share|percent|percentage|pct|margin)", measure_name, re.I)
            and format_string
            and "%" not in format_string
        ):
            findings.append(_issue(
                "MQ039", "Ratio measure without percentage format", "Formatting", "ERROR", "Measure",
                table_name, measure_name,
                "A ratio-like DIVIDE measure uses a numeric format that displays the fractional value without a percentage sign.",
                "Apply a percentage format string with the business-required decimal precision and validate report labels.",
                f"format_string={format_string}; expression={expression}", risk="LOW",
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
