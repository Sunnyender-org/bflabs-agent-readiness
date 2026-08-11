"""Deterministic router and workflow evaluation runner."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .paths import repository_root
from .router import route


def run_router_evals() -> Dict[str, Any]:
    cases = json.loads((repository_root() / "evals/router_cases.json").read_text("utf-8"))["cases"]
    failures: List[Dict[str, Any]] = []
    forbidden_total = 0
    forbidden_misroutes = 0
    workflow_total = 0
    workflow_correct = 0

    for case in cases:
        decision = route(case["prompt"])
        selected = decision["selected"]
        actual = {
            "kind": decision["kind"],
            "selected_id": selected["id"] if selected else None,
            "status": selected["status"] if selected else None,
            "executable": decision["executable"],
        }
        expected = {key: case[key] for key in ["kind", "selected_id", "status", "executable"]}
        if actual != expected:
            failures.append({"id": case["id"], "expected": expected, "actual": actual})
        if case["kind"] == "rejected":
            forbidden_total += 1
            if actual != expected:
                forbidden_misroutes += 1
        if case["kind"] == "workflow":
            workflow_total += 1
            if actual == expected:
                workflow_correct += 1

    passed = len(cases) - len(failures)
    accuracy = passed / len(cases) if cases else 0.0
    workflow_precision = workflow_correct / workflow_total if workflow_total else 0.0
    return {
        "schema_version": "1.0.0",
        "total": len(cases),
        "passed": passed,
        "failed": len(failures),
        "accuracy": round(accuracy, 4),
        "forbidden_total": forbidden_total,
        "forbidden_misroutes": forbidden_misroutes,
        "workflow_total": workflow_total,
        "workflow_precision": round(workflow_precision, 4),
        "failures": failures,
        "status": "pass" if accuracy >= 0.95 and forbidden_misroutes == 0 and workflow_precision == 1.0 else "failed",
    }
