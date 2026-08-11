"""Offline aggregation of user-supplied AI answer observations."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from ..evidence import stable_claim_id
from ..paths import repository_root


METRICS = [
    "network_rate",
    "site_citation_rate",
    "content_absorption_rate",
    "brand_mention_rate",
    "recommendation_rate",
    "dynamic_fact_accuracy",
]


def _answer_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_tri_state(value: Any) -> Any:
    if value in (True, False, "unknown"):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    if normalized in {"unknown", "", "null", "none"}:
        return "unknown"
    raise ValueError("invalid tri-state value: {}".format(value))


def _parse_bool(value: Any) -> bool:
    parsed = _parse_tri_state(value)
    if parsed == "unknown":
        raise ValueError("boolean value cannot be unknown")
    return parsed


def _csv_observation(row: Dict[str, str]) -> Dict[str, Any]:
    cited_urls = json.loads(row.get("cited_urls") or "[]")
    if not isinstance(cited_urls, list):
        raise ValueError("cited_urls must be a JSON array")
    return {
        "id": row["id"],
        "captured_at": row["captured_at"],
        "platform": row["platform"],
        "terminal": row["terminal"],
        "prompt_id": row["prompt_id"],
        "prompt_text": row["prompt_text"],
        "session_id": row["session_id"],
        "answer_text": row["answer_text"],
        "answer_hash": row["answer_hash"],
        "source_kind": row["source_kind"],
        "network_status": row["network_status"],
        "network_evidence": row.get("network_evidence") or None,
        "cited_urls": cited_urls,
        "content_absorbed": _parse_tri_state(row.get("content_absorbed")),
        "brand_mentioned": _parse_tri_state(row.get("brand_mentioned")),
        "recommended": _parse_tri_state(row.get("recommended")),
        "dynamic_fact_correct": _parse_tri_state(row.get("dynamic_fact_correct")),
        "evidence_complete": _parse_bool(row.get("evidence_complete")),
        "exclusion_reason": row.get("exclusion_reason") or None,
    }


def load_measurement_input(path: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        value = json.loads(path.read_text("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("measurement JSON input must be an object")
        return value
    if suffix == ".jsonl":
        records = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]
        if not records:
            raise ValueError("measurement JSONL input is empty")
        site_domains = {record["site_domain"] for record in records}
        captured = {record["batch_captured_at"] for record in records}
        if len(site_domains) != 1 or len(captured) != 1:
            raise ValueError("JSONL rows must share site_domain and batch_captured_at")
        return {
            "schema_version": "1.0.0",
            "capability": "geo-measure",
            "captured_at": captured.pop(),
            "site_domain": site_domains.pop(),
            "observations": [record["observation"] for record in records],
        }
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError("measurement CSV input is empty")
        site_domains = {row["site_domain"] for row in rows}
        captured = {row["batch_captured_at"] for row in rows}
        if len(site_domains) != 1 or len(captured) != 1:
            raise ValueError("CSV rows must share site_domain and batch_captured_at")
        return {
            "schema_version": "1.0.0",
            "capability": "geo-measure",
            "captured_at": captured.pop(),
            "site_domain": site_domains.pop(),
            "observations": [_csv_observation(row) for row in rows],
        }
    raise ValueError("geo-measure input must be .json, .jsonl, or .csv")


def _is_valid(observation: Dict[str, Any]) -> bool:
    if observation["source_kind"] != "model-answer":
        return False
    if not observation["evidence_complete"] or observation["exclusion_reason"]:
        return False
    if observation["network_status"] == "verified" and not observation["network_evidence"]:
        return False
    return True


def _site_cited(observation: Dict[str, Any], site_domain: str) -> bool:
    target = site_domain.lower().rstrip(".")
    for value in observation["cited_urls"]:
        hostname = (urlparse(value).hostname or "").lower().rstrip(".")
        if hostname == target or hostname.endswith("." + target):
            return True
    return False


def _wilson(numerator: int, denominator: int) -> Optional[Dict[str, float]]:
    if denominator == 0:
        return None
    z = 1.959963984540054
    proportion = numerator / denominator
    denominator_adjusted = 1 + z * z / denominator
    center = (proportion + z * z / (2 * denominator)) / denominator_adjusted
    margin = z * math.sqrt((proportion * (1 - proportion) + z * z / (4 * denominator)) / denominator) / denominator_adjusted
    return {"lower": round(max(0.0, center - margin), 6), "upper": round(min(1.0, center + margin), 6)}


def _metric(
    metric_id: str,
    valid: List[Dict[str, Any]],
    site_domain: str,
    base_excluded: int,
) -> Dict[str, Any]:
    if metric_id == "network_rate":
        known = [item for item in valid if item["network_status"] != "unknown"]
        numerator = sum(item["network_status"] == "verified" for item in known)
        missing = len(valid) - len(known)
        excluded = base_excluded
        rule = "valid model answers with known network_status"
    elif metric_id == "site_citation_rate":
        known = [item for item in valid if item["network_status"] == "verified"]
        numerator = sum(_site_cited(item, site_domain) for item in known)
        missing = 0
        excluded = base_excluded + len(valid) - len(known)
        rule = "valid model answers with verified network use"
    else:
        field = {
            "content_absorption_rate": "content_absorbed",
            "brand_mention_rate": "brand_mentioned",
            "recommendation_rate": "recommended",
            "dynamic_fact_accuracy": "dynamic_fact_correct",
        }[metric_id]
        known = [item for item in valid if item[field] != "unknown"]
        numerator = sum(item[field] is True for item in known)
        missing = len(valid) - len(known)
        excluded = base_excluded
        rule = "valid model answers with known {}".format(field)
    denominator = len(known)
    return {
        "id": metric_id,
        "numerator": numerator,
        "denominator": denominator,
        "excluded": excluded,
        "missing": missing,
        "rate": round(numerator / denominator, 6) if denominator else None,
        "wilson_95": _wilson(numerator, denominator),
        "denominator_rule": rule,
    }


def _counts(observations: List[Dict[str, Any]]) -> Dict[str, int]:
    valid = [item for item in observations if _is_valid(item)]
    return {
        "input": len(observations),
        "valid": len(valid),
        "excluded": len(observations) - len(valid),
        "ordinary_web_search_results": sum(item["source_kind"] == "ordinary-web-search-result" for item in observations),
        "incomplete_evidence": sum(
            not item["evidence_complete"]
            or (item["network_status"] == "verified" and not item["network_evidence"])
            for item in observations
        ),
    }


def _research_context() -> Dict[str, Any]:
    value = json.loads((repository_root() / "registry/research-evidence.json").read_text("utf-8"))
    return {"schema_version": "1.0.0", "principles": value["principles"]}


def run_geo_measure(request: Dict[str, Any]) -> Dict[str, Any]:
    observations = request["observations"]
    ids = [item["id"] for item in observations]
    blockers: List[str] = []
    warnings: List[str] = []
    checks: List[Dict[str, str]] = []
    if len(ids) != len(set(ids)):
        blockers.append("duplicate observation ids")
        checks.append({"id": "observation-id-uniqueness", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "observation-id-uniqueness", "status": "pass", "message": "observation ids are unique"})
    bad_hashes = [item["id"] for item in observations if item["answer_hash"] != _answer_hash(item["answer_text"])]
    if bad_hashes:
        blockers.append("observation answer hashes do not match: {}".format(bad_hashes))
        checks.append({"id": "observation-hash-integrity", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "observation-hash-integrity", "status": "pass", "message": "all answer hashes match supplied text"})

    valid = [item for item in observations if _is_valid(item)]
    search_results = [item for item in observations if item["source_kind"] == "ordinary-web-search-result"]
    if any(item in valid for item in search_results):
        blockers.append("ordinary web search result counted as a model answer")
        checks.append({"id": "model-answer-boundary", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "model-answer-boundary", "status": "pass", "message": "ordinary web search results are excluded"})
    if not valid:
        warnings.append("no valid model-answer observations; rates remain null, not 0%")
        checks.append({"id": "valid-sample-count", "status": "warning", "message": warnings[-1]})
    else:
        checks.append({"id": "valid-sample-count", "status": "pass", "message": "{} valid observations".format(len(valid))})

    base_excluded = len(observations) - len(valid)
    metrics = [
        _metric(metric_id, valid, request["site_domain"], base_excluded)
        for metric_id in METRICS
    ]
    strata = []
    keys = sorted({(item["platform"], item["terminal"]) for item in observations})
    for platform, terminal in keys:
        subset = [item for item in observations if item["platform"] == platform and item["terminal"] == terminal]
        subset_valid = [item for item in subset if _is_valid(item)]
        counts = _counts(subset)
        strata.append(
            {
                "platform": platform,
                "terminal": terminal,
                "counts": {key: counts[key] for key in ["input", "valid", "excluded"]},
                "metrics": [
                    _metric(
                        metric_id,
                        subset_valid,
                        request["site_domain"],
                        len(subset) - len(subset_valid),
                    )
                    for metric_id in METRICS
                ],
            }
        )
    research = _research_context()
    report = {
        "schema_version": "1.0.0",
        "site_domain": request["site_domain"],
        "captured_at": request["captured_at"],
        "counts": _counts(observations),
        "metrics": metrics,
        "strata": strata,
        "research_rule_ids": sorted({rule for principle in research["principles"] for rule in principle["runtime_rule_ids"]}),
        "limitations": [
            "Results describe only the supplied observations and do not establish causality.",
            "AI visibility observations do not establish traffic, conversion, or revenue outcomes.",
        ],
    }
    items = [
        {
            "id": "ev_" + item["id"][4:],
            "summary": "Supplied {} {} observation {}".format(item["platform"], item["terminal"], item["id"]),
            "source_type": "user-supplied-observation",
            "locator": "observation:{}/{}".format(item["platform"], item["session_id"]),
            "captured_at": item["captured_at"],
            "content_hash": item["answer_hash"],
            "support_scope": "external answer observation only",
            "limitations": [item["exclusion_reason"] or "non-random supplied sample"],
            "dynamic_fact": False,
            "fact_version": None,
            "license": "user-supplied observation",
        }
        for item in observations
    ]
    valid_evidence_ids = ["ev_" + item["id"][4:] for item in valid]
    claims = []
    for metric in metrics:
        if metric["denominator"] == 0:
            continue
        text = "{} = {}/{} for the supplied valid observation scope".format(
            metric["id"], metric["numerator"], metric["denominator"]
        )
        claims.append(
            {"id": stable_claim_id(text), "text": text, "evidence_ids": valid_evidence_ids, "support_level": "derived"}
        )
    quality = {
        "schema_version": "1.0.0",
        "status": "blocked" if blockers else ("pass_with_warnings" if warnings else "pass"),
        "checks": checks,
        "warnings": warnings,
        "blockers": blockers,
    }
    return {
        "outputs": {
            "outputs/measurement-report.json": (report, "measurement-report.schema.json"),
            "outputs/research-context.json": (research, "research-context.schema.json"),
        },
        "evidence_ledger": {"schema_version": "1.0.0", "items": items, "claims": claims},
        "quality_report": quality,
    }
