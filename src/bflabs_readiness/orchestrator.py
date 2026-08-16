"""Bounded workflow orchestration over schema-validated provider outputs."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from .artifacts import publish_run
from .providers.geo_discover import run_geo_discover
from .providers.geo_content import run_geo_content
from .providers.geo_optimize import run_geo_optimize
from .registry import CapabilityRegistry
from .schemas import validate_instance


def _canonical_hash(value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _merge_ledgers(*ledgers: Dict[str, Any]) -> Dict[str, Any]:
    items_by_id: Dict[str, Dict[str, Any]] = {}
    claims_by_id: Dict[str, Dict[str, Any]] = {}
    for ledger in ledgers:
        for item in ledger["items"]:
            existing = items_by_id.get(item["id"])
            if existing is not None and existing != item:
                raise ValueError("conflicting evidence id across workflow stages: {}".format(item["id"]))
            items_by_id[item["id"]] = item
        for claim in ledger["claims"]:
            existing = claims_by_id.get(claim["id"])
            if existing is not None and existing != claim:
                raise ValueError("conflicting claim id across workflow stages: {}".format(claim["id"]))
            claims_by_id[claim["id"]] = claim
    return {
        "schema_version": "1.0.0",
        "items": sorted(items_by_id.values(), key=lambda item: item["id"]),
        "claims": sorted(claims_by_id.values(), key=lambda claim: claim["id"]),
    }


def _merge_quality(*stage_reports: Any) -> Dict[str, Any]:
    checks: List[Dict[str, str]] = []
    warnings: List[str] = []
    blockers: List[str] = []
    for stage, report in stage_reports:
        for check in report["checks"]:
            checks.append({**check, "id": stage + ":" + check["id"]})
        warnings.extend(stage + ": " + warning for warning in report["warnings"])
        blockers.extend(stage + ": " + blocker for blocker in report["blockers"])
    status = "blocked" if blockers else ("pass_with_warnings" if warnings else "pass")
    return {
        "schema_version": "1.0.0",
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "blockers": blockers,
    }


def run_discover_diagnose(request: Dict[str, Any], output_root: Path) -> Path:
    validate_instance(request, "discover-diagnose-input.schema.json")
    registry = CapabilityRegistry()
    workflow = registry.resolve_workflow("discover-diagnose", executable=True)

    discovery_result = run_geo_discover(request["discovery"])
    if discovery_result["quality_report"]["status"] not in {"pass", "pass_with_warnings"}:
        raise ValueError("geo-discover blocked workflow publication")
    opportunity_map = discovery_result["outputs"]["outputs/opportunity-map.json"][0]

    diagnosis_request = copy.deepcopy(request["diagnosis"])
    opportunity_count = len(opportunity_map["opportunities"])
    discovery_summary = "Discovery produced {} traceable opportunities for diagnosis coverage review.".format(opportunity_count)
    diagnosis_request["evidence_sources"].append(
        {
            "id": "ev_discovery_opportunity_map",
            "summary": discovery_summary,
            "source_type": "fixture" if all(item["source_type"] == "fixture" for item in request["discovery"]["evidence_sources"]) else "repository",
            "locator": "artifact:outputs/geo-discover/opportunity-map.json",
            "captured_at": request["discovery"]["captured_at"],
            "content_hash": _canonical_hash(opportunity_map),
            "support_scope": "opportunity coverage diagnosis only",
            "limitations": ["does not establish search volume, AI visibility, or business outcome"],
            "dynamic_fact": False,
            "fact_version": None,
            "license": "MIT",
        }
    )
    diagnosis_request["receipt"]["scope"].setdefault("inspected_paths", []).append(
        "outputs/geo-discover/opportunity-map.json"
    )
    diagnosis_request["receipt"]["findings"].append(
        {
            "id": "discovery-opportunity-coverage",
            "priority": "P1",
            "state": "unknown",
            "evidence": [discovery_summary],
            "repair": "Review missing high-priority dimensions against current public pages.",
            "recheck": "rerun discover-diagnose after the relevant public pages or facts change",
        }
    )
    validate_instance(diagnosis_request, "geo-optimize-run-input.schema.json")
    diagnosis_result = run_geo_optimize(diagnosis_request)

    combined_quality = _merge_quality(
        ("geo-discover", discovery_result["quality_report"]),
        ("geo-optimize", diagnosis_result["quality_report"]),
    )
    combined_ledger = _merge_ledgers(
        discovery_result["evidence_ledger"], diagnosis_result["evidence_ledger"]
    )
    workflow_receipt = {
        "schema_version": "1.0.0",
        "workflow_id": workflow.id,
        "status": combined_quality["status"],
        "steps": workflow.steps,
        "data_flow": {
            "producer_artifact": "outputs/geo-discover/opportunity-map.json",
            "consumer_evidence_id": "ev_discovery_opportunity_map",
            "consumer_finding_id": "discovery-opportunity-coverage",
        },
    }

    outputs: Dict[str, Any] = {
        "outputs/geo-discover/query-map.json": discovery_result["outputs"]["outputs/query-map.json"],
        "outputs/geo-discover/opportunity-map.json": discovery_result["outputs"]["outputs/opportunity-map.json"],
        "outputs/geo-optimize/readiness-report.json": diagnosis_result["outputs"]["outputs/readiness-report.json"],
        "outputs/workflow-receipt.json": (workflow_receipt, "workflow-receipt.schema.json"),
    }
    provider_result = {
        "outputs": outputs,
        "evidence_ledger": combined_ledger,
        "quality_report": combined_quality,
    }
    return publish_run(
        registry.resolve("bflabs-agent-readiness", executable=True),
        request,
        provider_result,
        output_root,
        workflow_id=workflow.id,
        input_schema_name="discover-diagnose-input.schema.json",
    )


def run_discover_content(request: Dict[str, Any], output_root: Path) -> Path:
    validate_instance(request, "discover-content-input.schema.json")
    registry = CapabilityRegistry()
    workflow = registry.resolve_workflow("discover-content", executable=True)

    discovery_result = run_geo_discover(request["discovery"])
    if discovery_result["quality_report"]["status"] not in {"pass", "pass_with_warnings"}:
        raise ValueError("geo-discover blocked workflow publication")
    query_map = discovery_result["outputs"]["outputs/query-map.json"][0]
    opportunity_map = discovery_result["outputs"]["outputs/opportunity-map.json"][0]

    content_request = copy.deepcopy(request["content"])
    selected = opportunity_map["opportunities"][:3]
    opportunity_ids = [item["id"] for item in selected]
    selected_query_ids = sorted({query_id for item in selected for query_id in item["query_ids"]})
    discovery_summary = "Discovery supplied {} prioritized opportunities as content context.".format(len(selected))
    content_request["evidence_sources"].append(
        {
            "id": "ev_discovery_opportunity_map",
            "summary": discovery_summary,
            "source_type": "fixture" if all(item["source_type"] == "fixture" for item in request["discovery"]["evidence_sources"]) else "repository",
            "locator": "artifact:outputs/geo-discover/opportunity-map.json",
            "captured_at": request["discovery"]["captured_at"],
            "content_hash": _canonical_hash(opportunity_map),
            "support_scope": "content opportunity selection only",
            "limitations": ["does not establish search volume, factual product claims, AI visibility, or business outcome"],
            "dynamic_fact": False,
            "fact_version": None,
            "license": "MIT",
        }
    )
    content_request["discovery_context"] = {
        "evidence_id": "ev_discovery_opportunity_map",
        "opportunity_ids": opportunity_ids,
        "query_ids": selected_query_ids,
    }
    validate_instance(content_request, "content-brief.schema.json")
    content_result = run_geo_content(content_request)

    combined_quality = _merge_quality(
        ("geo-discover", discovery_result["quality_report"]),
        ("geo-content", content_result["quality_report"]),
    )
    combined_ledger = _merge_ledgers(
        discovery_result["evidence_ledger"], content_result["evidence_ledger"]
    )
    workflow_receipt = {
        "schema_version": "1.0.0",
        "workflow_id": workflow.id,
        "status": combined_quality["status"],
        "steps": workflow.steps,
        "data_flow": {
            "producer_artifact": "outputs/geo-discover/opportunity-map.json",
            "consumer_evidence_id": "ev_discovery_opportunity_map",
            "consumer_artifact": "outputs/geo-content/content-spec.json",
            "consumer_field": "discovery_context",
        },
    }

    outputs: Dict[str, Any] = {
        "outputs/geo-discover/query-map.json": discovery_result["outputs"]["outputs/query-map.json"],
        "outputs/geo-discover/opportunity-map.json": discovery_result["outputs"]["outputs/opportunity-map.json"],
        "outputs/workflow-receipt.json": (workflow_receipt, "workflow-receipt.schema.json"),
    }
    for relative, artifact in content_result["outputs"].items():
        outputs["outputs/geo-content/" + relative.removeprefix("outputs/")] = artifact
    provider_result = {
        "outputs": outputs,
        "evidence_ledger": combined_ledger,
        "quality_report": combined_quality,
    }
    return publish_run(
        registry.resolve("bflabs-agent-readiness", executable=True),
        request,
        provider_result,
        output_root,
        workflow_id=workflow.id,
        input_schema_name="discover-content-input.schema.json",
    )
