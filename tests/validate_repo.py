#!/usr/bin/env python3
"""Static validation for the repository's Fabric item definitions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def validate_json() -> int:
    count = 0
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and (path.suffix in {".json", ".ipynb"} or path.name == ".platform"):
            json.loads(path.read_text(encoding="utf-8"))
            count += 1
    return count


def validate_manifest() -> None:
    config = yaml.safe_load((ROOT / "config/deployment_config.yaml").read_text())
    order = json.loads((ROOT / "config/deployment_order.json").read_text())
    ordered_names = [item["name"] for item in order]
    expected = list(config["items"].values())
    if ordered_names != expected:
        fail(f"Deployment order differs from configured items: {ordered_names} != {expected}")
    if config["lakehouse"]["enable_schemas"] is not True:
        fail("The V1 contract requires a schema-enabled Lakehouse.")
    for item in ordered_names:
        if item.endswith(".Lakehouse"):
            continue
        if not (ROOT / "src" / item).is_dir():
            fail(f"Missing source directory for {item}")


def validate_scanner() -> None:
    path = ROOT / "src/SMO_Optimization_Scanner.Notebook/notebook-content.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    for required in (
        'output_schema = "smopt"',
        "workspace_ids = \"\"",
        "model_ids_optional = \"\"",
        "initialize_only = False",
        "def ensure_tables()",
    ):
        if required not in source:
            fail(f"Scanner is missing required text: {required}")
    dependency = notebook["metadata"]["dependencies"]["lakehouse"]
    if dependency["default_lakehouse"] != "11111111-1111-1111-1111-111111111111":
        fail("Scanner Lakehouse placeholder does not match the deployment manifest.")


def validate_model() -> None:
    model_root = ROOT / "src/SMO_Analytics_SM.SemanticModel/definition"
    model = (model_root / "model.tmdl").read_text(encoding="utf-8")
    refs = re.findall(r"^ref table (.+)$", model, flags=re.MULTILINE)
    for table in refs:
        if not (model_root / "tables" / f"{table}.tmdl").exists():
            fail(f"Missing TMDL table file for {table}")
    expressions = (model_root / "expressions.tmdl").read_text(encoding="utf-8")
    if "Sql.Database" not in expressions:
        fail("Direct Lake connection expression is missing.")


def validate_report() -> None:
    report_root = ROOT / "src/SMO_Analytics_Report.Report"
    binding = json.loads((report_root / "definition.pbir").read_text())
    connection = binding["datasetReference"]["byConnection"]["connectionString"]
    if "44444444-4444-4444-4444-444444444444" not in connection:
        fail("Report semantic-model placeholder is missing.")
    pages = json.loads((report_root / "definition/pages/pages.json").read_text())
    for page in pages["pageOrder"]:
        page_root = report_root / "definition/pages" / page
        if not (page_root / "page.json").exists():
            fail(f"Missing report page: {page}")
        visuals = list((page_root / "visuals").glob("*/visual.json"))
        if not visuals:
            fail(f"Report page {page} has no visuals.")


def validate_no_secrets() -> None:
    suspicious = re.compile(r"(?i)(client_secret|github_token)\s*=\s*[\"'][^\"']{8,}[\"']")
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if suspicious.search(content):
            fail(f"Possible committed secret in {path.relative_to(ROOT)}")


def main() -> int:
    json_count = validate_json()
    validate_manifest()
    validate_scanner()
    validate_model()
    validate_report()
    validate_no_secrets()
    print(f"Validation passed: {json_count} JSON/notebook/platform files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

