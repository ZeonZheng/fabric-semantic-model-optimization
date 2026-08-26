"""Deterministic quality grading for scanner findings and recommendations.

This dependency-free source is embedded into the Fabric scanner notebook by
``upgrade_notebook_v2.py`` and is also importable for local contract tests.
"""

ACTIONABLE = "ACTIONABLE"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
INFORMATIONAL = "INFORMATIONAL"
SUPPRESSED = "SUPPRESSED"


# Only recommendations with a deterministic metadata operation belong in the
# approval-controlled script queue.  A broad domain such as "Formatting" is not
# sufficient: it also contains semantic decisions (data category, data type,
# business format selection) that cannot be generated safely without user input.
SCRIPT_CANDIDATE_RULE_FRAGMENTS = (
    "DO NOT SUMMARIZE NUMERIC COLUMNS",
    "HIDE FOREIGN KEYS",
    "MARK PRIMARY KEYS",
    "WHOLE NUMBERS SHOULD BE FORMATTED WITH THOUSANDS SEPARATORS AND NO DECIMALS",
    "FORMAT FLAG COLUMNS AS YES/NO VALUE STRINGS",
)

AUTO_DATE_ROOT_CAUSE_KEY = "AUTO_DATE_TIME"
AUTO_DATE_ROOT_CAUSE_SOURCE = "ROOT_CAUSE_CONSOLIDATION"
AUTO_DATE_ROOT_CAUSE_DOMAIN = "Date handling"
AUTO_DATE_ROOT_CAUSE_TITLE = "Replace Auto Date/Time with an explicit date dimension"
AUTO_DATE_ROOT_CAUSE_ACTION = (
    "Disable Auto Date/Time, create and mark an explicit date dimension, update relationships and calculations, "
    "then refresh and regression-test dependent reports."
)


def _normalized(value):
    return str(value or "").strip().upper()


def is_system_generated_date_object(finding):
    """Return True for Power BI Auto Date/Time implementation objects."""
    prefixes = ("LOCALDATETABLE_", "DATETABLETEMPLATE_")
    return any(
        _normalized(name).startswith(prefixes)
        for name in (finding.get("table_name"), finding.get("object_name"))
    )


def is_auto_date_root_cause_finding(finding):
    """Identify direct evidence that the model uses Auto Date/Time."""
    rule_name = _normalized(finding.get("rule_name"))
    return (
        is_system_generated_date_object(finding)
        or rule_name.startswith("MQ020:")
        or "AUTO DATE/TIME" in rule_name
    )


def is_date_table_companion_finding(finding):
    """Identify the missing-explicit-date-table finding that can share this root cause."""
    return _normalized(finding.get("rule_name")).startswith("MQ022:")


def root_cause_grouping(finding, auto_date_present):
    """Return a canonical rollup key while leaving the raw finding unchanged."""
    belongs_to_auto_date_root_cause = is_auto_date_root_cause_finding(finding) or (
        auto_date_present and is_date_table_companion_finding(finding)
    )
    if not belongs_to_auto_date_root_cause:
        return None
    return {
        "key": AUTO_DATE_ROOT_CAUSE_KEY,
        "source": AUTO_DATE_ROOT_CAUSE_SOURCE,
        "domain": AUTO_DATE_ROOT_CAUSE_DOMAIN,
        "title": AUTO_DATE_ROOT_CAUSE_TITLE,
        "action": AUTO_DATE_ROOT_CAUSE_ACTION,
    }


def _is_auto_date_root_cause_group(findings, title=None):
    """Confirm that a grouped recommendation/opportunity is one Auto Date root cause."""
    if not findings:
        return False
    if _normalized(title) == _normalized(AUTO_DATE_ROOT_CAUSE_TITLE):
        return True
    has_direct_evidence = any(is_auto_date_root_cause_finding(row) for row in findings)
    return has_direct_evidence and all(
        is_auto_date_root_cause_finding(row) or is_date_table_companion_finding(row)
        for row in findings
    )


def priority_band(score):
    """Map a stable 0-100 score to an explicit operational priority band."""
    if score >= 80:
        return "P1_CRITICAL"
    if score >= 65:
        return "P2_HIGH"
    if score >= 40:
        return "P3_MEDIUM"
    return "P4_LOW"


def _is_script_candidate(title):
    normalized = _normalized(title)
    return any(fragment in normalized for fragment in SCRIPT_CANDIDATE_RULE_FRAGMENTS)


def grade_finding(finding):
    """Grade one raw finding without discarding its original evidence."""
    description = str(finding.get("finding_text") or "").strip()
    evidence = str(finding.get("technical_evidence") or "").strip()
    action = str(finding.get("recommended_action") or "").strip()
    severity = _normalized(finding.get("severity"))
    confidence = _normalized(finding.get("confidence"))
    risk = _normalized(finding.get("change_risk"))

    suppression_reason = None
    if not description and not evidence:
        status = SUPPRESSED
        reason = "No description or technical evidence was supplied; retain for audit but exclude from the action queue."
        suppression_reason = reason
    elif is_system_generated_date_object(finding):
        status = SUPPRESSED
        reason = "System-generated Auto Date/Time object; remediate the model-level root cause instead of editing the generated object."
        suppression_reason = reason
    elif not evidence:
        status = REVIEW_REQUIRED
        reason = "A description is available, but technical evidence is missing; confirm the condition before implementation."
    elif not action:
        status = INFORMATIONAL
        reason = "Evidence is retained, but the scanner did not supply a concrete remediation action."
    elif severity in {"INFO", "LOW"}:
        status = INFORMATIONAL
        reason = "Low-severity evidence is useful context but does not belong in the immediate action queue."
    elif confidence in {"LOW", "UNKNOWN"}:
        status = REVIEW_REQUIRED
        reason = "The finding requires human confirmation because confidence is low or unavailable."
    elif risk == "HIGH":
        status = REVIEW_REQUIRED
        reason = "The proposed change has high implementation risk and requires design review before execution."
    else:
        status = ACTIONABLE
        reason = "The finding has evidence, a concrete action, sufficient confidence, and acceptable change risk."

    severity_points = {
        "CRITICAL": 70, "ERROR": 50, "HIGH": 45, "WARNING": 30,
        "MEDIUM": 25, "INFO": 10, "LOW": 5,
    }.get(severity, 0)
    # Treat absent confidence as neutral/medium rather than silently emptying
    # the actionable queue for collectors that do not publish this attribute.
    confidence_points = {"HIGH": 10, "MEDIUM": 5, "LOW": 0, "UNKNOWN": 0}.get(confidence, 5)
    risk_points = {"LOW": 5, "MEDIUM": 0, "HIGH": -10}.get(risk, 0)
    saving = max(
        int(finding.get("estimated_saving_bytes_low") or 0),
        int(finding.get("estimated_saving_bytes_high") or 0),
        int(finding.get("reclaimable_upper_bound_bytes") or 0),
    )
    score = severity_points + confidence_points + risk_points
    score += 5 if evidence else 0
    score += 10 if action else 0
    score += 5 if any(token in _normalized(finding.get("impact_area")) for token in (
        "PERFORMANCE", "MODEL_SIZE", "REFRESH", "QUERY", "CAPACITY",
    )) else 0
    score += 15 if saving > 0 else 0
    if status == SUPPRESSED:
        score = 0
    elif status == INFORMATIONAL:
        score = min(score, 39)
    elif severity != "CRITICAL" and saving <= 0:
        # P1 is reserved for explicitly critical evidence or quantified impact.
        # Finding volume is exposed separately and must not manufacture urgency.
        score = min(score, 79)
    score = max(0, min(100, score))

    return {
        "actionability_status": status,
        "actionability_reason": reason,
        "suppression_reason": suppression_reason,
        "finding_priority_score": score,
        "finding_priority_band": priority_band(score),
    }


def _why_it_matters(domain):
    text = _normalized(domain)
    if "DAX" in text or "EXPRESSION" in text:
        return "Improves calculation correctness, maintainability, and representative query performance."
    if any(token in text for token in ("PERFORMANCE", "STORAGE", "VERTIPAQ")):
        return "Reduces model size, refresh cost, memory pressure, and interactive query latency."
    if "FORMAT" in text:
        return "Improves semantic consistency and makes the model easier for users and AI agents to interpret."
    if any(token in text for token in ("MAINTENANCE", "GOVERNANCE", "BEST PRACTICE")):
        return "Reduces support cost and makes future model changes safer and easier to review."
    return "Addresses model quality or operational risk while preserving traceable evidence for validation."


def _validation_method(domain):
    text = _normalized(domain)
    if "DAX" in text or "EXPRESSION" in text:
        return "Compare representative query results and duration before and after the change, then rerun BPA."
    if any(token in text for token in ("PERFORMANCE", "STORAGE", "VERTIPAQ")):
        return "Compare model size, refresh duration, and representative query duration; rerun storage analysis."
    return "Rerun BPA and the scanner, then complete model refresh and report smoke tests."


def grade_recommendation(findings, domain, title, action):
    """Aggregate finding grades into an implementation-oriented recommendation."""
    grades = [grade_finding(row) for row in findings]
    statuses = [grade["actionability_status"] for grade in grades]
    auto_date_root_cause = _is_auto_date_root_cause_group(findings, title)

    if auto_date_root_cause:
        status = REVIEW_REQUIRED
        reason = (
            "BPA generated-date-object evidence and model-metadata date findings were consolidated into one "
            "model-level remediation that requires relationship and calculation review."
        )
        title = AUTO_DATE_ROOT_CAUSE_TITLE
        action = AUTO_DATE_ROOT_CAUSE_ACTION
        score = 72
    else:
        if ACTIONABLE in statuses:
            status = ACTIONABLE
            reason = "At least one linked finding meets the evidence, confidence, action, and risk thresholds for execution."
        elif REVIEW_REQUIRED in statuses:
            status = REVIEW_REQUIRED
            reason = "Linked findings require human confirmation or design review before implementation."
        elif INFORMATIONAL in statuses:
            status = INFORMATIONAL
            reason = "Linked findings are valid context but do not yet form an executable change."
        else:
            status = SUPPRESSED
            reason = "All linked findings are suppressed from the action queue while remaining available for audit."
        # Finding count is an impact/breadth dimension, not evidence of criticality.
        # Keep it in affected_finding_count instead of allowing volume to promote a
        # recommendation into a higher operational priority band.
        score = max((grade["finding_priority_score"] for grade in grades), default=0)

    highest_risk = max(
        (_normalized(row.get("change_risk")) for row in findings),
        key=lambda value: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(value, 0),
        default="",
    )
    if status in {INFORMATIONAL, SUPPRESSED}:
        automation = "NOT_ELIGIBLE"
    elif status == REVIEW_REQUIRED:
        automation = "MANUAL_REVIEW"
    elif highest_risk == "HIGH":
        automation = "MANUAL_ONLY"
    elif _is_script_candidate(title) and highest_risk in {"LOW", "MEDIUM"}:
        automation = "SCRIPT_CANDIDATE"
    else:
        automation = "MANUAL_REVIEW"

    return {
        "recommendation_title": title,
        "recommended_action": action,
        "actionability_status": status,
        "actionability_reason": reason,
        "recommendation_priority_score": score,
        "recommendation_priority_band": priority_band(score),
        "automation_eligibility": automation,
        "why_it_matters": _why_it_matters(domain),
        "validation_method": _validation_method(domain),
        "rollback_guidance": "Capture the original PBIP/TMDL state in source control and restore it if validation thresholds fail.",
        "actionable_finding_count": statuses.count(ACTIONABLE),
        "suppressed_finding_count": statuses.count(SUPPRESSED),
    }


def summarize_opportunity(findings, source, domain):
    """Build an explicit, AI-readable summary of an opportunity's finding mix."""
    grades = [grade_finding(row) for row in findings]
    counts = {
        ACTIONABLE: 0,
        REVIEW_REQUIRED: 0,
        INFORMATIONAL: 0,
        SUPPRESSED: 0,
    }
    for grade in grades:
        counts[grade["actionability_status"]] += 1
    return (
        f"{len(findings)} finding(s) from {source} in {domain}: "
        f"{counts[ACTIONABLE]} actionable, "
        f"{counts[REVIEW_REQUIRED]} review required, "
        f"{counts[INFORMATIONAL]} informational, and "
        f"{counts[SUPPRESSED]} suppressed."
    )


def grade_opportunity(findings):
    """Aggregate actionability and priority for an opportunity summary."""
    grades = [grade_finding(row) for row in findings]
    statuses = [grade["actionability_status"] for grade in grades]
    auto_date_root_cause = _is_auto_date_root_cause_group(findings)
    if auto_date_root_cause:
        status, score = REVIEW_REQUIRED, 72
    elif ACTIONABLE in statuses:
        status, score = ACTIONABLE, max(grade["finding_priority_score"] for grade in grades)
    elif REVIEW_REQUIRED in statuses:
        status, score = REVIEW_REQUIRED, max(grade["finding_priority_score"] for grade in grades)
    elif INFORMATIONAL in statuses:
        status, score = INFORMATIONAL, max(grade["finding_priority_score"] for grade in grades)
    else:
        status, score = SUPPRESSED, 0
    # Breadth remains available as actionable_finding_count and does not inflate
    # the opportunity's evidence-based priority.
    score = max(0, min(100, score))
    return {
        "actionability_status": status,
        "actionable_finding_count": statuses.count(ACTIONABLE),
        "review_required_finding_count": statuses.count(REVIEW_REQUIRED),
        "suppressed_finding_count": statuses.count(SUPPRESSED),
        "priority_score": score,
        "priority_band": priority_band(score),
    }
