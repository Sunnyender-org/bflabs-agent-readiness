"""Offline aggregation of user-supplied AI answer observations."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
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

OPTIONAL_CSV_SCALARS = (
    "experiment_id",
    "round_id",
    "phase",
    "question_version",
    "facts_version",
    "rubric_version",
    "observation_line",
    "intent_tag",
    "language",
    "region",
    "visible_model",
    "personalization_status",
    "sample_slot_id",
    "execution_status",
    "replacement_of",
    "collection_method",
    "answer_verdict",
)
OPTIONAL_CSV_JSON = ("fact_judgement", "compared_action_ids", "evidence_refs")
COMPARE_KNOWN_FIELDS = (
    "question_version",
    "facts_version",
    "rubric_version",
    "language",
    "region",
)
JUDGED_VERDICTS = {"correct", "partially_correct", "wrong", "no_answer"}
KNOWN_PERSONALIZATION = {"off", "on"}
LINE_LABELS = {
    "A": "A 品牌识别",
    "B": "B 给网址后解释",
    "C": "C 自主找到官网",
    "D": "D 无品牌选型",
}
TERMINAL_LABELS = {"web": "网页", "app": "应用", "api": "接口"}
VERDICT_LABELS = {
    "improved": "改善",
    "unchanged": "持平",
    "regressed": "回退",
    "insufficient": "样本不足",
    "not_comparable": "不可比",
}
STAGE_VERSION_NAMES = (
    ("question_version", "题目版本"),
    ("facts_version", "事实版本"),
    ("rubric_version", "判读版本"),
)
EMPTY_PAIR_SIDE = {"correct": 0, "valid_answers": 0, "valid_slots": 0, "planned_slots": 0}
AMBIGUOUS_BASELINE_WARNING = "multiple baseline rounds without baseline_round_id"
THREE_REP_LIMITATION = (
    "Three repetitions support process trial and direction only; they do not support statistical significance claims."
)
FIXTURE_ONLY_LIMITATION = "fixture-only: does not demonstrate live platform visibility"
DEFAULT_LIMITATIONS = [
    "Results describe only the supplied observations and do not establish causality.",
    "AI visibility observations do not establish traffic, conversion, or revenue outcomes.",
]


def _answer_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_prompt(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split()).strip().casefold()


def _prompt_fingerprint(text: str) -> str:
    return hashlib.sha256(_normalize_prompt(text).encode("utf-8")).hexdigest()


def _is_judged(observation: Dict[str, Any]) -> bool:
    return observation.get("answer_verdict") in JUDGED_VERDICTS


def _has_release_evidence(action: Dict[str, Any]) -> bool:
    evidence = action.get("release_evidence")
    return evidence is not None and str(evidence).strip() != ""


def _planned_slot_ids(request: Dict[str, Any]) -> List[str]:
    specified = request.get("sample_slot_ids")
    if specified:
        return list(specified)
    planned = request.get("planned_slots_per_question", 3)
    return ["slot_{}".format(index) for index in range(1, planned + 1)]


def _empty_counts(planned_slots: int) -> Dict[str, int]:
    return {
        "planned_slots": planned_slots,
        "valid_slots": 0,
        "attempts": 0,
        "technical_failures": 0,
        "valid_answers": 0,
        "judged_answers": 0,
        "unjudged_answers": 0,
        "exploratory_answers": 0,
        "correct": 0,
        "partially_correct": 0,
        "no_answer": 0,
        "brand_mentioned": 0,
        "recommended": 0,
        "site_cited": 0,
    }


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


def _csv_present(row: Dict[str, str], key: str) -> bool:
    if key not in row:
        return False
    value = row[key]
    return value is not None and str(value).strip() != ""


def _parse_optional_csv_scalar(key: str, raw: str) -> Any:
    text = raw.strip()
    if key == "replacement_of" and text.lower() == "null":
        return None
    if key == "attempt_index":
        return int(text)
    return text


def _csv_observation(row: Dict[str, str]) -> Dict[str, Any]:
    cited_urls = json.loads(row.get("cited_urls") or "[]")
    if not isinstance(cited_urls, list):
        raise ValueError("cited_urls must be a JSON array")
    observation: Dict[str, Any] = {
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
    if _csv_present(row, "attempt_index"):
        observation["attempt_index"] = int(str(row["attempt_index"]).strip())
    for key in OPTIONAL_CSV_SCALARS:
        if _csv_present(row, key):
            observation[key] = _parse_optional_csv_scalar(key, row[key])
    for key in OPTIONAL_CSV_JSON:
        if not _csv_present(row, key):
            continue
        parsed = json.loads(row[key])
        if not isinstance(parsed, list):
            raise ValueError("{} must be a JSON array".format(key))
        observation[key] = parsed
    return observation


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


def _execution_status(observation: Dict[str, Any]) -> str:
    return observation.get("execution_status") or "valid"


def _is_technical_failure(observation: Dict[str, Any]) -> bool:
    return _execution_status(observation) != "valid"


def _is_valid(observation: Dict[str, Any]) -> bool:
    if observation["source_kind"] != "model-answer":
        return False
    if not observation["evidence_complete"] or observation["exclusion_reason"]:
        return False
    if observation["network_status"] == "verified" and not observation["network_evidence"]:
        return False
    if _is_technical_failure(observation):
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


def _parse_dt(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _unique(values: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _slot_key(observation: Dict[str, Any]) -> Optional[Tuple[str, str, str, str, str]]:
    slot = observation.get("sample_slot_id")
    round_id = observation.get("round_id")
    if not slot or not round_id:
        return None
    return (round_id, observation["prompt_id"], observation["platform"], observation["terminal"], slot)


def _apply_duplicate_imports(observations: List[Dict[str, Any]]) -> None:
    seen: Dict[Tuple[str, str, str, str, str], str] = {}
    for item in observations:
        key = (
            item["answer_hash"],
            item["prompt_id"],
            item["platform"],
            item["terminal"],
            item["captured_at"],
        )
        if key in seen:
            if not item.get("exclusion_reason"):
                item["exclusion_reason"] = "duplicate_import"
            continue
        seen[key] = item["id"]


def _check_replacements(observations: List[Dict[str, Any]]) -> List[str]:
    by_id = {item["id"]: item for item in observations}
    replacements = [item for item in observations if item.get("replacement_of")]
    blockers: List[str] = []
    per_slot: Dict[Tuple[str, str, str, str, str], List[str]] = {}
    for item in replacements:
        target_id = item["replacement_of"]
        target = by_id.get(target_id)
        if target is None:
            blockers.append("replacement {} references unknown observation {}".format(item["id"], target_id))
            continue
        if not _is_technical_failure(target):
            blockers.append(
                "replacement {} cannot replace valid observation {}".format(item["id"], target_id)
            )
        source_slot = _slot_key(item)
        target_slot = _slot_key(target)
        if source_slot is None or target_slot is None or source_slot != target_slot:
            blockers.append(
                "replacement {} changes slot; it must stay in the same round, question, platform, terminal, and sample slot as {}".format(
                    item["id"], target_id
                )
            )
            continue
        per_slot.setdefault(source_slot, []).append(item["id"])
    for slot, ids in per_slot.items():
        if len(ids) > 1:
            blockers.append(
                "slot {} in round {} has more than one replacement: {}".format(slot[4], slot[0], ", ".join(ids))
            )
    return blockers


def _apply_duplicate_slots(observations: List[Dict[str, Any]]) -> None:
    first_valid: Dict[Tuple[str, str, str, str, str], str] = {}
    ordered = sorted(observations, key=lambda item: (_parse_dt(item["captured_at"]), item["id"]))
    for item in ordered:
        key = _slot_key(item)
        if key is None or not _is_valid(item):
            continue
        if key in first_valid:
            item["exclusion_reason"] = "duplicate_slot_answer"
            continue
        first_valid[key] = item["id"]


def _apply_slot_plan(observations: List[Dict[str, Any]], planned_slot_ids: Sequence[str]) -> None:
    planned = set(planned_slot_ids)
    for item in observations:
        if not item.get("round_id") or item.get("exclusion_reason"):
            continue
        slot = item.get("sample_slot_id")
        if not slot:
            if _is_valid(item):
                item["exclusion_reason"] = "missing_slot"
            continue
        if slot not in planned:
            item["exclusion_reason"] = "unplanned_slot"


def _apply_shared_sessions(observations: List[Dict[str, Any]]) -> None:
    seen: Set[Tuple[str, str, str]] = set()
    ordered = sorted(observations, key=lambda item: (_parse_dt(item["captured_at"]), item["id"]))
    for item in ordered:
        if not item.get("round_id") or not _is_valid(item):
            continue
        key = (item["platform"], item["terminal"], item["session_id"])
        if key in seen:
            item["exclusion_reason"] = "shared_session"
            continue
        seen.add(key)


def _prompt_consistency_blockers(observations: List[Dict[str, Any]]) -> List[str]:
    grouped: Dict[Tuple[str, str, str, str, str, str, str], List[Dict[str, Any]]] = {}
    for item in observations:
        key = _group_identity(item)
        if key is None or not _is_valid(item):
            continue
        grouped.setdefault(key, []).append(item)
    blockers: List[str] = []
    for members in grouped.values():
        fingerprints = {_prompt_fingerprint(item["prompt_text"]) for item in members}
        if len(fingerprints) > 1:
            ids = ", ".join(item["id"] for item in members)
            blockers.append("prompt text differs within round group {}".format(ids))
    return blockers


def _group_fingerprint(members: Sequence[Dict[str, Any]]) -> Optional[str]:
    preferred = [item for item in members if _is_valid(item)] or list(members)
    fingerprints = _unique(_prompt_fingerprint(item["prompt_text"]) for item in preferred if item.get("prompt_text"))
    if len(fingerprints) == 1:
        return fingerprints[0]
    return None


def _valid_field_states(members: Sequence[Dict[str, Any]], field: str) -> Tuple[bool, List[Any]]:
    valid = [item for item in members if _is_valid(item)]
    missing = any(item.get(field) in (None, "") for item in valid)
    values = _unique(item.get(field) for item in valid if item.get(field) not in (None, ""))
    return missing, values


def _baseline_round_ids(observations: Sequence[Dict[str, Any]]) -> List[str]:
    return _unique(
        item["round_id"]
        for item in observations
        if item.get("phase") == "baseline" and item.get("round_id")
    )


def _resolve_bound_baseline(
    request: Dict[str, Any],
    observations: Sequence[Dict[str, Any]],
) -> Tuple[Optional[str], bool]:
    specified = request.get("baseline_round_id")
    if specified:
        return specified, False
    ids = _baseline_round_ids(observations)
    if len(ids) == 1:
        return ids[0], False
    if len(ids) > 1:
        return None, True
    return None, False


def _search_interface(observation: Dict[str, Any]) -> str:
    value = observation.get("search_interface")
    return str(value) if value else ""


def _group_identity(observation: Dict[str, Any]) -> Optional[Tuple[str, str, str, str, str, str, str]]:
    required = ("round_id", "phase", "observation_line", "prompt_id", "platform", "terminal")
    if any(not observation.get(field) for field in required):
        return None
    return (
        observation["round_id"],
        observation["phase"],
        observation["observation_line"],
        observation["prompt_id"],
        observation["platform"],
        observation["terminal"],
        _search_interface(observation),
    )


def _pair_side(counts: Dict[str, int]) -> Dict[str, int]:
    return {
        "correct": counts["correct"],
        "valid_answers": counts["valid_answers"],
        "valid_slots": counts["valid_slots"],
        "planned_slots": counts["planned_slots"],
    }


def _round_counts(
    members: Sequence[Dict[str, Any]],
    site_domain: str,
    planned_slots: int,
) -> Dict[str, int]:
    attempt_members = [item for item in members if item.get("exclusion_reason") != "duplicate_import"]
    valid = [item for item in attempt_members if _is_valid(item)]
    judged = [item for item in valid if _is_judged(item)]
    valid_slots = {item["sample_slot_id"] for item in valid if item.get("sample_slot_id")}
    return {
        "planned_slots": planned_slots,
        "valid_slots": min(len(valid_slots), planned_slots),
        "attempts": len(attempt_members),
        "technical_failures": sum(_is_technical_failure(item) for item in attempt_members),
        "valid_answers": len(valid),
        "judged_answers": len(judged),
        "unjudged_answers": len(valid) - len(judged),
        "exploratory_answers": sum(item.get("exclusion_reason") == "unplanned_slot" for item in attempt_members),
        "correct": sum(item.get("answer_verdict") == "correct" for item in judged),
        "partially_correct": sum(item.get("answer_verdict") == "partially_correct" for item in judged),
        "no_answer": sum(item.get("answer_verdict") == "no_answer" for item in judged),
        "brand_mentioned": sum(item.get("brand_mentioned") is True for item in valid),
        "recommended": sum(item.get("recommended") is True for item in valid),
        "site_cited": sum(_site_cited(item, site_domain) for item in valid),
    }


def _field_value(members: Sequence[Dict[str, Any]], field: str) -> Any:
    preferred = [item for item in members if _is_valid(item)] or list(members)
    if not preferred:
        return None
    values = [item.get(field) for item in preferred]
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    if len(unique) == 1:
        return unique[0]
    return unique


def _visible_model(members: Sequence[Dict[str, Any]]) -> Any:
    value = _field_value(members, "visible_model")
    if value in (None, "unknown"):
        return "unknown"
    return value


def _comparability_reasons(
    baseline_members: Sequence[Dict[str, Any]],
    after_members: Sequence[Dict[str, Any]],
    after_phase: str,
    actions: Dict[str, Dict[str, Any]],
    observation_line: str,
) -> List[str]:
    reasons: List[str] = []
    for field in COMPARE_KNOWN_FIELDS:
        left_missing, left_values = _valid_field_states(baseline_members, field)
        right_missing, right_values = _valid_field_states(after_members, field)
        if left_missing or right_missing:
            reasons.append("{}_missing".format(field))
        elif len(left_values) > 1 or len(right_values) > 1:
            reasons.append("{}_mixed".format(field))
        elif left_values != right_values:
            reasons.append("{}_mismatch".format(field))

    baseline_personalization = [item.get("personalization_status") for item in baseline_members if _is_valid(item)]
    after_personalization = [item.get("personalization_status") for item in after_members if _is_valid(item)]
    personalization = baseline_personalization + after_personalization
    if personalization and any(value not in KNOWN_PERSONALIZATION for value in personalization):
        reasons.append("personalization_unknown")
    elif baseline_personalization and after_personalization:
        left = _unique(baseline_personalization)
        right = _unique(after_personalization)
        if len(left) > 1 or len(right) > 1:
            reasons.append("personalization_status_mixed")
        elif left != right:
            reasons.append("personalization_status_mismatch")

    baseline_model = _visible_model(baseline_members)
    after_model = _visible_model(after_members)
    if baseline_model == "unknown" or after_model == "unknown":
        reasons.append("visible_model_unknown")
    elif isinstance(baseline_model, list) or isinstance(after_model, list):
        reasons.append("visible_model_mixed")
    elif baseline_model != after_model:
        reasons.append("visible_model_mismatch")

    baseline_valid = [item for item in baseline_members if _is_valid(item)]
    after_valid = [item for item in after_members if _is_valid(item)]
    checked = baseline_valid + after_valid
    if checked:
        if any(item.get("network_status") == "unknown" for item in checked):
            reasons.append("network_mode_unverified")
        elif observation_line == "A":
            if any(item["network_status"] != "not-used" for item in checked):
                reasons.append("network_mode_unverified")
        elif any(item["network_status"] != "verified" for item in checked):
            reasons.append("network_mode_unverified")

    left_fp = _unique(_prompt_fingerprint(item["prompt_text"]) for item in baseline_valid)
    right_fp = _unique(_prompt_fingerprint(item["prompt_text"]) for item in after_valid)
    if len(left_fp) > 1 or len(right_fp) > 1 or (left_fp and right_fp and left_fp != right_fp):
        reasons.append("prompt_text_mismatch")

    baseline_sessions = {item["session_id"] for item in baseline_valid}
    after_sessions = {item["session_id"] for item in after_valid}
    if baseline_sessions & after_sessions or any(
        item.get("exclusion_reason") == "shared_session"
        for item in list(baseline_members) + list(after_members)
    ):
        reasons.append("session_reused")

    if baseline_members and after_members:
        baseline_latest = max(_parse_dt(item["captured_at"]) for item in baseline_members)
        after_earliest = min(_parse_dt(item["captured_at"]) for item in after_members)
        if after_earliest <= baseline_latest:
            reasons.append("after_not_later_than_baseline")

    if after_phase == "after_release":
        for item in after_valid:
            action_ids = item.get("compared_action_ids") or []
            if not action_ids:
                reasons.append("release_evidence_missing")
                continue
            matched_after_release = False
            saw_known_action = False
            sampled_before = False
            evidence_missing = False
            for action_id in action_ids:
                action = actions.get(action_id)
                if action is None:
                    continue
                saw_known_action = True
                released_earlier = _parse_dt(action["released_at"]) < _parse_dt(item["captured_at"])
                if released_earlier and _has_release_evidence(action):
                    matched_after_release = True
                elif released_earlier:
                    evidence_missing = True
                else:
                    sampled_before = True
            if matched_after_release:
                continue
            if evidence_missing or not saw_known_action:
                reasons.append("release_evidence_missing")
            elif sampled_before:
                reasons.append("sampled_before_release")
    return _unique(reasons)


def _insufficiency_reasons(baseline_counts: Dict[str, int], after_counts: Dict[str, int]) -> List[str]:
    if (
        baseline_counts.get("unjudged_answers", 0) > 0
        or after_counts.get("unjudged_answers", 0) > 0
        or baseline_counts.get("judged_answers", 0) == 0
        or after_counts.get("judged_answers", 0) == 0
    ):
        return ["unjudged_answers"]
    return []


def _verdict(
    comparable: bool,
    baseline_counts: Dict[str, int],
    after_counts: Dict[str, int],
    insufficiency: Sequence[str],
) -> str:
    if not comparable:
        return "not_comparable"
    if insufficiency:
        return "insufficient"
    baseline_rate = baseline_counts["correct"] / baseline_counts["judged_answers"]
    after_rate = after_counts["correct"] / after_counts["judged_answers"]
    if after_rate > baseline_rate:
        return "improved"
    if after_rate < baseline_rate:
        return "regressed"
    return "unchanged"


def format_stage_side(counts: Optional[Dict[str, int]]) -> str:
    if counts is None:
        return "未测"
    return "正确 {}/{} · 已判读 {}/{} · 有效样本位 {}/{} · 尝试 {} 次 · 技术失败 {} 次".format(
        counts["correct"],
        counts["judged_answers"],
        counts["judged_answers"],
        counts["valid_answers"],
        counts["valid_slots"],
        counts["planned_slots"],
        counts["attempts"],
        counts["technical_failures"],
    )


def _version_label(value: Any) -> str:
    if value in (None, []):
        return "未记录"
    if isinstance(value, list):
        return "/".join(str(item) for item in value)
    return str(value)


def _stage_basis(baseline_members: Sequence[Dict[str, Any]], after_members: Sequence[Dict[str, Any]]) -> str:
    parts = []
    for field, name in STAGE_VERSION_NAMES:
        left = _field_value(baseline_members, field)
        right = _field_value(after_members, field)
        if left == right:
            parts.append("{} {}".format(name, _version_label(left)))
        else:
            parts.append("{} {} → {}".format(name, _version_label(left), _version_label(right)))
    return " · ".join(parts)


def _stage_question(pair: Dict[str, Any]) -> str:
    members = list(pair["_after_members"]) + list(pair["_baseline_members"])
    text = next((item.get("prompt_text") for item in members if item.get("prompt_text")), None)
    if not text:
        return pair["prompt_id"]
    text = " ".join(str(text).split())
    return text if len(text) <= 60 else text[:57] + "…"


def _build_rounds(
    observations: List[Dict[str, Any]],
    site_domain: str,
    planned_slots: int,
) -> Tuple[List[Dict[str, Any]], Dict[Tuple[str, str, str, str, str, str, str], Dict[str, Any]]]:
    grouped: Dict[Tuple[str, str, str, str, str, str, str], List[Dict[str, Any]]] = {}
    for item in observations:
        key = _group_identity(item)
        if key is None:
            continue
        grouped.setdefault(key, []).append(item)
    rounds: List[Dict[str, Any]] = []
    details: Dict[Tuple[str, str, str, str, str, str, str], Dict[str, Any]] = {}
    for key in sorted(grouped):
        members = grouped[key]
        counts = _round_counts(members, site_domain, planned_slots)
        record = {
            "round_id": key[0],
            "phase": key[1],
            "observation_line": key[2],
            "prompt_id": key[3],
            "platform": key[4],
            "terminal": key[5],
            "counts": counts,
            "prompt_fingerprint": _group_fingerprint(members),
        }
        rounds.append(record)
        details[key] = {"record": record, "members": members, "counts": counts}
    return rounds, details


def _match_baseline(
    after_key: Tuple[str, str, str, str, str, str, str],
    details: Dict[Tuple[str, str, str, str, str, str, str], Dict[str, Any]],
    bound_round_id: Optional[str],
) -> Optional[Tuple[str, str, str, str, str, str, str]]:
    if not bound_round_id:
        return None
    for key in details:
        if key[0] == bound_round_id and key[1] == "baseline" and key[2:] == after_key[2:]:
            return key
    return None


def _build_pairs(
    details: Dict[Tuple[str, str, str, str, str, str, str], Dict[str, Any]],
    actions: Dict[str, Dict[str, Any]],
    bound_round_id: Optional[str],
    ambiguous: bool,
    planned_slots: int,
) -> List[Dict[str, Any]]:
    pairs: List[Dict[str, Any]] = []
    after_keys = [key for key in details if key[1] in {"after_release", "follow_up"}]
    empty_counts = _empty_counts(planned_slots)
    for after_key in sorted(after_keys):
        after = details[after_key]
        reasons: List[str] = []
        baseline_key = None
        baseline = None
        if ambiguous:
            reasons.append("baseline_ambiguous")
        else:
            baseline_key = _match_baseline(after_key, details, bound_round_id)
            baseline = details.get(baseline_key) if baseline_key else None
            if baseline is None:
                reasons.append("baseline_missing")
            else:
                reasons = _comparability_reasons(
                    baseline["members"],
                    after["members"],
                    after_key[1],
                    actions,
                    after_key[2],
                )
        comparable = not reasons
        baseline_members = baseline["members"] if baseline else []
        baseline_counts = baseline["counts"] if baseline else empty_counts
        insufficiency = _insufficiency_reasons(baseline_counts, after["counts"])
        verdict = _verdict(comparable, baseline_counts, after["counts"], insufficiency)
        pairs.append(
            {
                "baseline_round_id": baseline_key[0] if baseline_key else None,
                "after_round_id": after_key[0],
                "phase": after_key[1],
                "prompt_id": after_key[3],
                "observation_line": after_key[2],
                "platform": after_key[4],
                "terminal": after_key[5],
                "comparable": comparable,
                "incomparable_reasons": reasons,
                "insufficiency_reasons": insufficiency,
                "baseline": _pair_side(baseline_counts) if baseline else dict(EMPTY_PAIR_SIDE),
                "after": _pair_side(after["counts"]),
                "verdict": verdict,
                "_baseline_members": baseline_members,
                "_after_members": after["members"],
                "_baseline_counts": baseline["counts"] if baseline else None,
                "_after_counts": after["counts"],
            }
        )
    return pairs


def _build_stage_table(pairs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    rows = []
    for pair in pairs:
        label = "{} · {} {} · {}".format(
            LINE_LABELS.get(pair["observation_line"], pair["observation_line"]),
            pair["platform"],
            TERMINAL_LABELS.get(pair["terminal"], pair["terminal"]),
            _stage_question(pair),
        )
        rows.append(
            {
                "label": label,
                "baseline": format_stage_side(pair["_baseline_counts"]),
                "after": format_stage_side(pair["_after_counts"]),
                "basis": _stage_basis(pair["_baseline_members"], pair["_after_members"]),
                "result": VERDICT_LABELS[pair["verdict"]],
            }
        )
    return rows


def _public_pairs(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned = []
    for pair in pairs:
        cleaned.append({key: value for key, value in pair.items() if not key.startswith("_")})
    return cleaned


def run_geo_measure(request: Dict[str, Any]) -> Dict[str, Any]:
    observations = [dict(item) for item in request["observations"]]
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

    _apply_duplicate_imports(observations)
    replacement_blockers = _check_replacements(observations)
    if replacement_blockers:
        blockers.extend(replacement_blockers)
        checks.append({"id": "replacement-discipline", "status": "blocked", "message": "; ".join(replacement_blockers)})
    else:
        checks.append({"id": "replacement-discipline", "status": "pass", "message": "replacements stay in-slot and replace technical failures only"})
    has_rounds = any(item.get("round_id") for item in observations)
    planned_slot_ids = _planned_slot_ids(request) if has_rounds else []
    if has_rounds:
        _apply_slot_plan(observations, planned_slot_ids)
        _apply_shared_sessions(observations)
    _apply_duplicate_slots(observations)
    if has_rounds:
        prompt_blockers = _prompt_consistency_blockers(observations)
        if prompt_blockers:
            blockers.extend(prompt_blockers)
            checks.append({"id": "prompt-fingerprint", "status": "blocked", "message": "; ".join(prompt_blockers)})
        else:
            checks.append({"id": "prompt-fingerprint", "status": "pass", "message": "prompt text is consistent within each round group"})

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

    planned_slots = len(planned_slot_ids) if planned_slot_ids else request.get("planned_slots_per_question", 3)
    actions = {item["action_id"]: item for item in request.get("actions") or []}
    bound_baseline_id = None
    if has_rounds:
        bound_baseline_id, ambiguous = _resolve_bound_baseline(request, observations)
        if ambiguous:
            warnings.append(AMBIGUOUS_BASELINE_WARNING)
            checks.append({"id": "baseline-binding", "status": "warning", "message": warnings[-1]})
        else:
            checks.append(
                {
                    "id": "baseline-binding",
                    "status": "pass",
                    "message": "baseline round {}".format(bound_baseline_id) if bound_baseline_id else "no baseline round in input",
                }
            )
        rounds, details = _build_rounds(observations, request["site_domain"], planned_slots)
        pairs = _build_pairs(details, actions, bound_baseline_id, ambiguous, planned_slots)
        stage_table = _build_stage_table(pairs)
        pairs = _public_pairs(pairs)
    else:
        rounds, pairs, stage_table = [], [], []

    research = _research_context()
    limitations = list(DEFAULT_LIMITATIONS)
    if has_rounds:
        limitations.append(THREE_REP_LIMITATION)
        if valid and all(item.get("collection_method") == "recorded_fixture" for item in valid):
            limitations.append(FIXTURE_ONLY_LIMITATION)
    report = {
        "schema_version": "1.0.0",
        "site_domain": request["site_domain"],
        "captured_at": request["captured_at"],
        "counts": _counts(observations),
        "metrics": metrics,
        "strata": strata,
        "research_rule_ids": sorted({rule for principle in research["principles"] for rule in principle["runtime_rule_ids"]}),
        "limitations": limitations,
        "rounds": rounds,
        "pairs": pairs,
        "stage_table": stage_table,
    }
    if has_rounds:
        report["experiment_id"] = request.get("experiment_id")
        report["questions_version"] = request.get("questions_version")
        report["baseline_round_id"] = bound_baseline_id
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
