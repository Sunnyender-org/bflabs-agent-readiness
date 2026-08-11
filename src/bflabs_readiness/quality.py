"""Evidence-bounded quality gates."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List


FORBIDDEN_CLAIMS = [
    re.compile(r"guarantee(?:d)?\s+(?:ranking|citation|revenue)", re.I),
    re.compile(r"保证.{0,8}(?:排名|收录|引用|推荐|收入)"),
]


def evaluate(readiness_report: Dict[str, Any], ledger: Dict[str, Any]) -> Dict[str, Any]:
    checks: List[Dict[str, str]] = []
    warnings: List[str] = []
    blockers: List[str] = []
    item_ids = [item["id"] for item in ledger["items"]]
    evidence_ids = set(item_ids)

    if len(item_ids) != len(evidence_ids):
        blockers.append("duplicate evidence ids")
        checks.append({"id": "evidence-id-uniqueness", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "evidence-id-uniqueness", "status": "pass", "message": "evidence ids are unique"})

    unsupported = [claim["id"] for claim in ledger["claims"] if claim["support_level"] == "unsupported"]
    dangling = [
        claim["id"]
        for claim in ledger["claims"]
        if any(evidence_id not in evidence_ids for evidence_id in claim["evidence_ids"])
    ]
    if unsupported or dangling:
        blockers.append("unsupported or dangling claims: {}".format(sorted(set(unsupported + dangling))))
        checks.append({"id": "claim-evidence-coverage", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "claim-evidence-coverage", "status": "pass", "message": "all claims link to evidence"})

    stale_dynamic = [item["id"] for item in ledger["items"] if item["dynamic_fact"] and not item.get("fact_version")]
    if stale_dynamic:
        blockers.append("dynamic evidence lacks fact_version: {}".format(stale_dynamic))
        checks.append({"id": "dynamic-fact-freshness", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "dynamic-fact-freshness", "status": "pass", "message": "dynamic evidence is versioned"})

    if readiness_report["ai_visibility"] != "not_measured" or readiness_report["business_outcome"] != "not_measured":
        blockers.append("visibility or business outcome was promoted without a separate measurement provider")
        checks.append({"id": "measurement-boundary", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "measurement-boundary", "status": "pass", "message": "visibility and outcome remain not_measured"})

    serialized = json.dumps(
        {"report": readiness_report, "claims": [claim["text"] for claim in ledger["claims"]]},
        ensure_ascii=False,
    )
    forbidden = [pattern.pattern for pattern in FORBIDDEN_CLAIMS if pattern.search(serialized)]
    if forbidden:
        blockers.append("forbidden outcome guarantee detected")
        checks.append({"id": "forbidden-claims", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "forbidden-claims", "status": "pass", "message": "no forbidden outcome guarantee"})

    status = "blocked" if blockers else ("pass_with_warnings" if warnings else "pass")
    return {
        "schema_version": "1.0.0",
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "blockers": blockers,
    }


def evaluate_discovery(
    query_map: Dict[str, Any],
    opportunity_map: Dict[str, Any],
    ledger: Dict[str, Any],
) -> Dict[str, Any]:
    checks: List[Dict[str, str]] = []
    warnings: List[str] = []
    blockers: List[str] = []
    item_ids = [item["id"] for item in ledger["items"]]
    evidence_ids = set(item_ids)

    if len(item_ids) != len(evidence_ids):
        blockers.append("duplicate evidence ids")
        checks.append({"id": "evidence-id-uniqueness", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "evidence-id-uniqueness", "status": "pass", "message": "evidence ids are unique"})

    untraced = []
    for query in query_map["queries"]:
        trace = query["trace"]
        if trace["source_type"] == "assumption":
            if not query["assumptions"]:
                untraced.append(query["id"])
        elif not trace["evidence_id"] or trace["evidence_id"] not in evidence_ids:
            untraced.append(query["id"])
    if untraced:
        blockers.append("queries lack input, seed, or explicit assumption trace: {}".format(untraced))
        checks.append({"id": "query-traceability", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "query-traceability", "status": "pass", "message": "every query traces to input, seed, or explicit assumption"})

    query_ids = {query["id"] for query in query_map["queries"]}
    untraced_opportunities = [
        opportunity["id"]
        for opportunity in opportunity_map["opportunities"]
        if not opportunity["query_ids"]
        or set(opportunity["query_ids"]) != set(opportunity["trace"]["source_query_ids"])
        or any(query_id not in query_ids for query_id in opportunity["query_ids"])
    ]
    if untraced_opportunities:
        blockers.append("opportunities lack a valid source-query trace: {}".format(untraced_opportunities))
        checks.append({"id": "opportunity-traceability", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "opportunity-traceability", "status": "pass", "message": "every opportunity traces to a discovered query"})

    measured_volume = [
        opportunity["id"]
        for opportunity in opportunity_map["opportunities"]
        if opportunity["search_volume"] != {"status": "not_measured", "value": None}
    ]
    if measured_volume:
        blockers.append("search volume was invented or imported without an approved connector")
        checks.append({"id": "search-volume-boundary", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "search-volume-boundary", "status": "pass", "message": "search volume remains not_measured"})

    bad_scores = []
    for opportunity in opportunity_map["opportunities"]:
        expected = opportunity["coverage_gap"] + opportunity["evidence_gap"] + opportunity["business_relevance"]
        if opportunity["priority_score"] != expected:
            bad_scores.append(opportunity["id"])
    if bad_scores:
        blockers.append("opportunity scores are not explainable: {}".format(bad_scores))
        checks.append({"id": "opportunity-scoring", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "opportunity-scoring", "status": "pass", "message": "all scores match the declared formula"})

    status = "blocked" if blockers else ("pass_with_warnings" if warnings else "pass")
    return {
        "schema_version": "1.0.0",
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "blockers": blockers,
    }


def evaluate_content(
    brief: Dict[str, Any],
    content_spec: Dict[str, Any],
    markdown: str,
    ledger: Dict[str, Any],
) -> Dict[str, Any]:
    checks: List[Dict[str, str]] = []
    warnings: List[str] = []
    blockers: List[str] = []
    item_ids = [item["id"] for item in ledger["items"]]
    evidence_by_id = {item["id"]: item for item in ledger["items"]}

    if len(item_ids) != len(evidence_by_id):
        blockers.append("duplicate evidence ids")
        checks.append({"id": "evidence-id-uniqueness", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "evidence-id-uniqueness", "status": "pass", "message": "evidence ids are unique"})

    unsupported = []
    stale = []
    for fact in brief["facts"]:
        sources = [evidence_by_id.get(evidence_id) for evidence_id in fact["evidence_ids"]]
        if any(source is None for source in sources) or fact["support_level"] not in {"direct", "derived"}:
            unsupported.append(fact["id"])
            continue
        primary = sources[0]
        if fact["evidence_hash"] != primary["content_hash"]:
            stale.append(fact["id"])
        if fact["dynamic_fact"] and (
            not fact["fact_version"]
            or not primary["dynamic_fact"]
            or fact["fact_version"] != primary["fact_version"]
        ):
            stale.append(fact["id"])
    if unsupported:
        blockers.append("content facts lack direct or derived evidence: {}".format(sorted(unsupported)))
        checks.append({"id": "claim-evidence-coverage", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "claim-evidence-coverage", "status": "pass", "message": "all content facts have direct or derived evidence"})
    if stale:
        blockers.append("content facts are stale against canonical evidence: {}".format(sorted(set(stale))))
        checks.append({"id": "dynamic-fact-freshness", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "dynamic-fact-freshness", "status": "pass", "message": "fact hashes and dynamic versions match canonical evidence"})

    if brief["mode"] == "comparison" and (
        len(brief["comparison_targets"]) < 2 or not brief["comparison_dimensions"]
    ):
        blockers.append("comparison requires at least two targets and explicit symmetric dimensions")
        checks.append({"id": "comparison-symmetry", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "comparison-symmetry", "status": "pass", "message": "comparison symmetry requirements are satisfied or not applicable"})

    if brief["mode"] == "ranking" and brief["ranking_method"] is None:
        blockers.append("ranking requires a disclosed method and dataset scope")
        checks.append({"id": "ranking-method", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "ranking-method", "status": "pass", "message": "ranking method is disclosed or not applicable"})

    if brief["mode"] in {"refine", "article-friendly"} and not brief["source_markdown"]:
        blockers.append("{} requires source_markdown".format(brief["mode"]))
        checks.append({"id": "source-preservation", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "source-preservation", "status": "pass", "message": "source content requirement is satisfied or not applicable"})

    claim_ids = {claim["id"] for claim in ledger["claims"]}
    markdown_markers = set(re.findall(r"\[\^(claim_[a-z0-9_-]+)\]", markdown))
    unknown_markers = sorted(markdown_markers - claim_ids)
    spec_claim_ids = set(content_spec["claim_ids"])
    if unknown_markers or spec_claim_ids != claim_ids or not claim_ids.issubset(markdown_markers):
        blockers.append("content contains missing or untraceable evidence markers")
        checks.append({"id": "citation-integrity", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "citation-integrity", "status": "pass", "message": "all content claims use traceable internal evidence markers"})

    serialized = json.dumps({"spec": content_spec, "markdown": markdown}, ensure_ascii=False)
    if any(pattern.search(serialized) for pattern in FORBIDDEN_CLAIMS):
        blockers.append("forbidden outcome guarantee detected")
        checks.append({"id": "forbidden-claims", "status": "blocked", "message": blockers[-1]})
    else:
        checks.append({"id": "forbidden-claims", "status": "pass", "message": "no forbidden outcome guarantee"})

    status = "blocked" if blockers else ("pass_with_warnings" if warnings else "pass")
    return {
        "schema_version": "1.0.0",
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "blockers": blockers,
    }
