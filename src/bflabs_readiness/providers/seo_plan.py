"""Evidence-bounded technical SEO planning without live platform mutation."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from ..evidence import stable_claim_id
from ..paths import repository_root


CATEGORIES = [
    "robots",
    "meta-robots",
    "canonical",
    "redirects",
    "sitemap",
    "indexnow",
    "structured-data",
    "cwv-lab",
    "cwv-field",
    "ai-crawlers",
    "hreflang",
]

SOURCE_MAP = {
    "robots": ["google-robots-meta"],
    "meta-robots": ["google-robots-meta"],
    "canonical": ["google-canonical"],
    "redirects": ["google-canonical"],
    "sitemap": ["google-sitemap"],
    "indexnow": ["indexnow-protocol"],
    "structured-data": ["google-structured-data"],
    "cwv-lab": ["google-cwv"],
    "cwv-field": ["google-cwv"],
    "ai-crawlers": ["openai-crawlers", "bing-crawlers"],
    "hreflang": ["google-hreflang"],
}

CHECK_ACTIONS = {
    "robots": "Inspect robots.txt directives separately from page-level indexing controls.",
    "meta-robots": "Inspect meta robots and X-Robots-Tag on representative old and new URLs.",
    "canonical": "Compare rendered canonical targets with the migration URL map.",
    "redirects": "Verify one-hop redirects, status codes, destinations, and redirect loops.",
    "sitemap": "Validate sitemap URLs, canonical alignment, last modification signals, and discoverability.",
    "indexnow": "Determine whether IndexNow is applicable and verify submitted URL scope without assuming indexing.",
    "structured-data": "Validate structured data against visible page facts and applicable official feature rules.",
    "cwv-lab": "Record reproducible lab measurements separately from field evidence.",
    "cwv-field": "Acquire current field evidence without substituting lab results for user data.",
    "ai-crawlers": "Inspect search and AI crawler directives by named user agent and purpose.",
    "hreflang": "Validate reciprocal hreflang clusters, canonical compatibility, and language-region targets.",
}


def _priority(category: str, change_type: str) -> str:
    if change_type == "migration" and category in {"robots", "meta-robots", "canonical", "redirects", "sitemap"}:
        return "P0"
    if category in {"canonical", "robots", "meta-robots", "sitemap", "ai-crawlers", "hreflang"}:
        return "P1"
    return "P2"


def _registry() -> Dict[str, Any]:
    return json.loads((repository_root() / "registry/seo-official-sources.json").read_text("utf-8"))


def _age_days(newer: str, older: str) -> int:
    newer_value = datetime.fromisoformat(newer.replace("Z", "+00:00"))
    older_value = datetime.fromisoformat(older.replace("Z", "+00:00"))
    return max(0, (newer_value - older_value).days)


def run_seo_plan(brief: Dict[str, Any]) -> Dict[str, Any]:
    registry = _registry()
    official_by_id = {source["id"]: source for source in registry["sources"]}
    evidence_by_id = {item["id"]: item for item in brief["evidence_sources"]}
    observation_by_category = {item["category"]: item for item in brief["observations"]}

    findings = []
    evidence_gaps = []
    checks = []
    implementation_actions = []
    for category in CATEGORIES:
        observation = observation_by_category.get(category)
        if observation is None or observation["state"] == "unknown":
            evidence_gaps.append(
                {
                    "category": category,
                    "reason": "No confirmed site evidence was supplied for this category.",
                    "acquisition": CHECK_ACTIONS[category],
                }
            )
        if observation is not None and observation["state"] == "fail":
            findings.append(
                {
                    "id": "finding-" + observation["id"],
                    "category": category,
                    "state": "failed",
                    "summary": observation["summary"],
                    "evidence_ids": observation["evidence_ids"],
                }
            )
            implementation_actions.append(
                {
                    "id": "implement-" + category,
                    "category": category,
                    "priority": _priority(category, brief["change_type"]),
                    "action": "Prepare and test a bounded correction for the confirmed {} failure.".format(category),
                    "preconditions": [
                        "owner approves the exact target files or platform change",
                        "current configuration and representative responses are captured",
                        "a non-production or reversible verification route is available",
                    ],
                    "authorization": "owner-approval-required",
                    "rollback": [
                        "restore the captured previous configuration",
                        "re-run the same representative URL checks",
                        "stop rollout if response, canonical, crawl, or rendering behavior regresses",
                    ],
                }
            )
        checks.append(
            {
                "id": "check-" + category,
                "category": category,
                "priority": _priority(category, brief["change_type"]),
                "action": CHECK_ACTIONS[category],
                "expected_evidence": "timestamped request/response, repository path, or user-supplied platform export",
                "official_source_ids": SOURCE_MAP[category],
                "authorization": "read-only",
            }
        )
    checks.sort(key=lambda item: (item["priority"], CATEGORIES.index(item["category"])))

    used_source_ids = sorted({source_id for item in checks for source_id in item["official_source_ids"]})
    plan = {
        "schema_version": "1.0.0",
        "scope": {
            "target": brief["target"],
            "change_type": brief["change_type"],
            "symptoms": brief["symptoms"],
            "constraints": brief["constraints"],
        },
        "findings": findings,
        "evidence_gaps": evidence_gaps,
        "checks": checks,
        "implementation_actions": implementation_actions,
        "official_sources": used_source_ids,
        "live_actions_not_performed": [
            "No Search Console or Bing Webmaster Tools access was requested or used.",
            "No CMS, server, DNS, redirect, robots, sitemap, IndexNow, or structured-data mutation was performed.",
            "No live ranking query was performed or represented as evidence.",
        ],
        "outcome_boundaries": [
            "A technically correct plan does not guarantee crawling, indexing, ranking, traffic, conversion, or revenue.",
            "AI crawler controls remain distinct from search indexing and external AI answer visibility.",
        ],
    }

    blockers: List[str] = []
    warnings: List[str] = []
    quality_checks: List[Dict[str, str]] = []
    observation_ids = [item["id"] for item in brief["observations"]]
    observation_categories = [item["category"] for item in brief["observations"]]
    evidence_ids = [item["id"] for item in brief["evidence_sources"]]
    official_evidence_ids = {
        "ev_official_" + source_id.replace("-", "_") for source_id in used_source_ids
    }
    if (
        len(observation_ids) != len(set(observation_ids))
        or len(observation_categories) != len(set(observation_categories))
        or len(evidence_ids) != len(set(evidence_ids))
        or bool(set(evidence_ids) & official_evidence_ids)
    ):
        blockers.append("duplicate observation ids, categories, or evidence ids")
        quality_checks.append({"id": "seo-input-uniqueness", "status": "blocked", "message": blockers[-1]})
    else:
        quality_checks.append({"id": "seo-input-uniqueness", "status": "pass", "message": "observation and evidence identities are unique"})

    ungrounded = [
        observation["id"]
        for observation in brief["observations"]
        if observation["state"] != "unknown"
        and (
            not observation["evidence_ids"]
            or any(evidence_id not in evidence_by_id for evidence_id in observation["evidence_ids"])
        )
    ]
    if ungrounded:
        blockers.append("SEO findings lack supplied site evidence: {}".format(ungrounded))
        quality_checks.append({"id": "finding-evidence-coverage", "status": "blocked", "message": blockers[-1]})
    else:
        quality_checks.append({"id": "finding-evidence-coverage", "status": "pass", "message": "all findings are evidence-linked; unknown categories remain gaps"})

    unversioned_dynamic = [
        item["id"]
        for item in brief["evidence_sources"]
        if item["dynamic_fact"] and not item["fact_version"]
    ]
    if unversioned_dynamic:
        blockers.append("dynamic site evidence lacks fact_version: {}".format(unversioned_dynamic))
        quality_checks.append({"id": "dynamic-site-evidence", "status": "blocked", "message": blockers[-1]})
    else:
        quality_checks.append({"id": "dynamic-site-evidence", "status": "pass", "message": "dynamic site evidence is versioned or not present"})

    stale_sources = [
        source_id
        for source_id in used_source_ids
        if source_id not in official_by_id
        or _age_days(brief["captured_at"], official_by_id[source_id]["captured_at"])
        > official_by_id[source_id]["freshness_days"]
    ]
    if stale_sources:
        blockers.append("official guidance sources are missing or stale: {}".format(stale_sources))
        quality_checks.append({"id": "official-source-freshness", "status": "blocked", "message": blockers[-1]})
    else:
        quality_checks.append({"id": "official-source-freshness", "status": "pass", "message": "all technical checks link to current captured official sources"})

    bad_gates = [
        action["id"]
        for action in implementation_actions
        if action["authorization"] != "owner-approval-required"
        or not action["preconditions"]
        or not action["rollback"]
    ]
    if bad_gates:
        blockers.append("implementation actions lack authorization or rollback gates: {}".format(bad_gates))
        quality_checks.append({"id": "implementation-gates", "status": "blocked", "message": blockers[-1]})
    else:
        quality_checks.append({"id": "implementation-gates", "status": "pass", "message": "all implementation actions are owner-gated and reversible"})

    if not brief["evidence_sources"]:
        warnings.append("no site evidence supplied; output contains scope, checks, and evidence gaps only")
        quality_checks.append({"id": "site-evidence-scope", "status": "warning", "message": warnings[-1]})
    else:
        quality_checks.append({"id": "site-evidence-scope", "status": "pass", "message": "supplied site evidence remains separate from official guidance"})

    official_items = [
        {
            "id": "ev_official_" + source["id"].replace("-", "_"),
            "summary": "Official {} guidance for {}".format(source["organization"], source["topic"]),
            "source_type": "public-url",
            "locator": source["url"],
            "captured_at": source["captured_at"],
            "content_hash": source["content_hash"],
            "support_scope": "technical planning guidance only",
            "limitations": source["limitations"],
            "dynamic_fact": False,
            "fact_version": None,
            "license": "official public documentation",
        }
        for source in registry["sources"]
        if source["id"] in used_source_ids
    ]
    claims = []
    for finding in findings:
        claims.append(
            {
                "id": stable_claim_id(finding["summary"]),
                "text": finding["summary"],
                "evidence_ids": finding["evidence_ids"],
                "support_level": "direct",
            }
        )
    for check in checks:
        text = check["action"]
        claims.append(
            {
                "id": stable_claim_id(text),
                "text": text,
                "evidence_ids": ["ev_official_" + source_id.replace("-", "_") for source_id in check["official_source_ids"]],
                "support_level": "context-only",
            }
        )
    return {
        "outputs": {
            "outputs/seo-plan.json": (plan, "seo-plan.schema.json"),
            "outputs/official-sources.json": (registry, "seo-official-sources.schema.json"),
        },
        "evidence_ledger": {
            "schema_version": "1.0.0",
            "items": [dict(item) for item in brief["evidence_sources"]] + official_items,
            "claims": claims,
        },
        "quality_report": {
            "schema_version": "1.0.0",
            "status": "blocked" if blockers else ("pass_with_warnings" if warnings else "pass"),
            "checks": quality_checks,
            "warnings": warnings,
            "blockers": blockers,
        },
    }
