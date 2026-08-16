"""Compatibility adapter from the geo-optimize receipt to Artifact Protocol 1.0."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from ..evidence import build_ledger
from ..quality import evaluate


def _all_evidence_text(receipt: Dict[str, Any]) -> Iterable[str]:
    for truth in receipt["confirmed_product_truth"]:
        yield truth
    for axis in receipt["readiness_axes"].values():
        for evidence in axis.get("evidence", []):
            yield evidence
    for finding in receipt["findings"]:
        for evidence in finding.get("evidence", []):
            yield evidence


def run_geo_optimize(request: Dict[str, Any]) -> Dict[str, Any]:
    receipt = request["receipt"]
    evidence_by_summary = {item["summary"]: item["id"] for item in request["evidence_sources"]}

    axes: Dict[str, Any] = {}
    for axis_id in ["discoverable", "understandable", "actionable"]:
        source = receipt["readiness_axes"][axis_id]
        axis = {
            "status": source["status"],
            "evidence_ids": [
                evidence_by_summary[evidence]
                for evidence in source.get("evidence", [])
                if evidence in evidence_by_summary
            ],
            "limitations": source.get("limitations", []),
        }
        if axis_id == "actionable":
            axis["webmcp_status"] = source.get("webmcp_status", "not_present")
        axes[axis_id] = axis

    target = {"repo_root": receipt["scope"].get("repo_root", "UNRESOLVED")}
    readiness_report = {
        "schema_version": "1.0.0",
        "target": target,
        "mode": receipt["mode"],
        "axes": axes,
        "findings": receipt["findings"],
        "verification": receipt["verification"],
        "ai_visibility": receipt["ai_visibility"]["status"],
        "business_outcome": receipt["business_outcome"]["status"],
        "external_gates": list(receipt.get("service_escalations", [])),
    }

    claims: List[Tuple[str, str]] = [(text, "direct") for text in _all_evidence_text(receipt)]
    ledger = build_ledger(request["evidence_sources"], claims)
    quality_report = evaluate(readiness_report, ledger)
    return {
        "outputs": {
            "outputs/readiness-report.json": (readiness_report, "readiness-report.schema.json"),
        },
        "evidence_ledger": ledger,
        "quality_report": quality_report,
    }
