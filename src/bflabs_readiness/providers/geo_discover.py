"""Deterministic query and opportunity discovery from a bounded brief."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Tuple

from ..evidence import stable_claim_id
from ..quality import evaluate_discovery


DIMENSIONS = ["audience", "scenario", "comparison", "decision", "price-cost", "integration", "limitation"]


def _id(prefix: str, value: str) -> str:
    return "{}_{}".format(prefix, hashlib.sha256(value.encode("utf-8")).hexdigest()[:10])


def _templates(brief: Dict[str, Any]) -> Dict[str, str]:
    subject = brief["subject"]
    audience = brief["audiences"][0]
    scenario = brief["scenarios"][0]
    comparison = brief["comparison_targets"][0] if brief["comparison_targets"] else "其他替代方案"
    if brief["language"] == "zh-CN":
        return {
            "audience": "{}选择{}时最关心什么？".format(audience, subject),
            "scenario": "{}在{}场景下怎么选？".format(subject, scenario),
            "comparison": "{}和{}有什么区别？".format(subject, comparison),
            "decision": "什么时候应该选择{}，什么时候不应该？".format(subject),
            "price-cost": "{}现在多少钱，计费单位和成本怎么算？".format(subject),
            "integration": "{}如何接入，有哪些接口和前置条件？".format(subject),
            "limitation": "{}有哪些限制、不可用场景和风险？".format(subject),
        }
    comparison_en = brief["comparison_targets"][0] if brief["comparison_targets"] else "other alternatives"
    return {
        "audience": "What matters most to {} when choosing {}?".format(audience, subject),
        "scenario": "How should teams choose {} for {}?".format(subject, scenario),
        "comparison": "How does {} compare with {}?".format(subject, comparison_en),
        "decision": "When should a buyer choose {}, and when should they not?".format(subject),
        "price-cost": "What does {} cost now, and how are units and total cost calculated?".format(subject),
        "integration": "How do teams integrate {}, and what APIs or prerequisites apply?".format(subject),
        "limitation": "What limitations, unavailable scenarios, and risks apply to {}?".format(subject),
    }


def _trace_for_dimension(brief: Dict[str, Any], dimension: str, evidence_id: str) -> Tuple[str, str, Optional[str], List[str]]:
    if dimension == "audience":
        return "input", brief["audiences"][0], evidence_id, []
    if dimension == "scenario":
        return "input", brief["scenarios"][0], evidence_id, []
    if dimension == "comparison" and brief["comparison_targets"]:
        return "input", brief["comparison_targets"][0], evidence_id, []
    if dimension in {"decision", "price-cost", "integration"}:
        return "seed", brief["seed_queries"][0], evidence_id, []
    assumption = "{} is a relevant decision dimension for the bounded discovery brief".format(dimension)
    return "assumption", dimension, None, [assumption]


def run_geo_discover(brief: Dict[str, Any]) -> Dict[str, Any]:
    templates = _templates(brief)
    first_evidence_id = brief["evidence_sources"][0]["id"]
    queries = []
    claims = []
    for dimension in DIMENSIONS:
        text = templates[dimension]
        source_type, source_value, evidence_id, assumptions = _trace_for_dimension(brief, dimension, first_evidence_id)
        query_id = _id("qry", dimension + ":" + text)
        queries.append(
            {
                "id": query_id,
                "text": text,
                "dimension": dimension,
                "trace": {
                    "source_type": source_type,
                    "source_value": source_value,
                    "evidence_id": evidence_id,
                },
                "assumptions": assumptions,
            }
        )
        claims.append(
            {
                "id": stable_claim_id(text),
                "text": text,
                "evidence_ids": [evidence_id] if evidence_id else [],
                "support_level": "context-only",
            }
        )

    query_map = {
        "schema_version": "1.0.0",
        "subject": brief["subject"],
        "language": brief["language"],
        "queries": queries,
    }

    covered = set(brief["covered_dimensions"])
    priorities = set(brief["priority_dimensions"])
    opportunities = []
    for query in queries:
        dimension = query["dimension"]
        coverage_state = "covered" if dimension in covered else "missing"
        coverage_gap = 0 if coverage_state == "covered" else 2
        evidence_gap = 0 if query["trace"]["evidence_id"] else 1
        business_relevance = 3 if dimension in priorities else 1
        score = coverage_gap + evidence_gap + business_relevance
        opportunities.append(
            {
                "id": _id("opp", dimension + ":" + query["id"]),
                "dimension": dimension,
                "query_ids": [query["id"]],
                "coverage_state": coverage_state,
                "coverage_gap": coverage_gap,
                "evidence_gap": evidence_gap,
                "business_relevance": business_relevance,
                "priority_score": score,
                "search_volume": {"status": "not_measured", "value": None},
                "trace": {
                    "source_query_ids": [query["id"]],
                    "basis": [
                        "coverage_state={}".format(coverage_state),
                        "evidence_gap={}".format(evidence_gap),
                        "business_relevance={}".format(business_relevance),
                    ],
                },
            }
        )
    opportunities.sort(key=lambda item: (-item["priority_score"], item["dimension"]))
    opportunity_map = {
        "schema_version": "1.0.0",
        "subject": brief["subject"],
        "scoring_method": "coverage_gap(0-2) + evidence_gap(0-1) + business_relevance(1-3)",
        "opportunities": opportunities,
    }

    items = []
    for source in brief["evidence_sources"]:
        item = dict(source)
        item.setdefault("fact_version", None)
        items.append(item)
    ledger = {"schema_version": "1.0.0", "items": items, "claims": claims}
    quality = evaluate_discovery(query_map, opportunity_map, ledger)
    return {
        "outputs": {
            "outputs/query-map.json": (query_map, "query-map.schema.json"),
            "outputs/opportunity-map.json": (opportunity_map, "opportunity-map.schema.json"),
        },
        "evidence_ledger": ledger,
        "quality_report": quality,
    }
