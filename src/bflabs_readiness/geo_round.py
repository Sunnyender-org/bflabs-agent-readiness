"""Local portable GEO round record: validate, resume status, business windows, stage report."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlparse

from .paths import repository_root
from .schemas import SchemaValidationError, load_schema, validate_instance


ERR_EXPERIMENT_REQUIRED = "experiment.json is required"
ERR_BASELINE_ROUND_ID = "baseline.round_id not found in rounds"
ERR_FACTS_VERSION = "facts_version does not match experiment"
ERR_QUESTIONS_VERSION = "questions_version does not match experiment"
ERR_UNKNOWN_FACT_ID = "unknown fact_id"
ERR_UNKNOWN_QUESTION_ID = "unknown question_id"
ERR_UNKNOWN_ACTION_ID = "unknown action_id in compared_action_ids"
ERR_RELEASED_REQUIRES_RELEASED_AT = "released status requires released_at"
ERR_RELEASED_REQUIRES_RELEASE_EVIDENCE = "released status requires non-empty release_evidence"
ERR_RELEASED_REQUIRES_DELIVERABLE = "released status requires deliverable"
ERR_VERIFIED_PUBLIC_REQUIRES_RELEASED_AT = "verified_public requires released_at"
ERR_VERIFIED_PUBLIC_REQUIRES_RELEASE_EVIDENCE = "verified_public requires non-empty release_evidence"
ERR_VERIFIED_PUBLIC_REQUIRES_DELIVERABLE = "verified_public requires deliverable"
ERR_VERIFIED_PUBLIC_REQUIRES_RECHECK = "verified_public requires public_recheck"
ERR_VERIFIED_PUBLIC_REQUIRES_PASS = "verified_public requires public_recheck.result == pass"
ERR_VERIFIED_PUBLIC_REQUIRES_NOTE = "verified_public requires non-empty public_recheck.note"
ERR_VERIFIED_PUBLIC_RECHECK_NOT_AFTER_RELEASE = "verified_public requires checked_at after released_at"
ERR_AI_EVENT_EVIDENCE = "ai event requires source_evidence_url and known attribution_method"
ERR_MONEY_ONLY_ON_PURCHASE = "money is only allowed on purchase events"
ERR_DUPLICATE_EVENT_ID = "duplicate event id within import"
ERR_BASELINE_OBSERVATION_MISSING = "baseline observation file is missing"
ERR_BASELINE_OBSERVATION_OUTSIDE_PROJECT = "baseline observation_file must stay inside the project directory"
ERR_BASELINE_OBSERVATION_UNREADABLE = "baseline observation file could not be read"
ERR_BASELINE_OBSERVATION_FORMAT = "baseline observations must be JSONL or JSON with observations"
ERR_BASELINE_OBSERVATION_PARSE = "baseline observation row could not be parsed"
ERR_BASELINE_OBSERVATION_ROUND_ID = "baseline observation round_id does not match experiment baseline"
ERR_BASELINE_OBSERVATION_PHASE = "baseline observation phase must be baseline"
ERR_BASELINE_OBSERVATION_QUESTION_VERSION = "baseline observation question_version does not match experiment"
ERR_BASELINE_OBSERVATION_EXPERIMENT_ID = "baseline observation experiment_id does not match experiment"
ERR_MEASUREMENT_NO_EXPERIMENT_ID = "measurement report has no experiment_id"
ERR_MEASUREMENT_NO_QUESTIONS_VERSION = "measurement report has no questions_version"
ERR_MEASUREMENT_NO_BASELINE_ROUND_ID = "measurement report has no baseline_round_id"
ERR_MEASUREMENT_SITE_DOMAIN = "measurement report site_domain does not match experiment"
ERR_MEASUREMENT_EXPERIMENT_ID = "measurement report experiment_id does not match experiment"
ERR_MEASUREMENT_QUESTIONS_VERSION = "measurement report questions_version does not match experiment"
ERR_MEASUREMENT_BASELINE_ROUND = "measurement report pair baseline_round_id does not match experiment baseline"
ERR_MEASUREMENT_NULL_BASELINE = "measurement report has comparisons but experiment baseline is null"
ERR_MEASUREMENT_AFTER_ROUND = "measurement report pair after_round_id is not in experiment rounds"
ERR_MEASUREMENT_STAGE_LENGTH = "measurement report stage_table length does not match pairs"
ERR_MEASUREMENT_STAGE_RESULT = "measurement report stage_table result does not match pair verdict"
ERR_MEASUREMENT_INSUFFICIENCY_REASONS = "measurement report pair is missing insufficiency_reasons"
MISSING_BASELINE_BEFORE_CHANGE = "baseline observations missing before change phase"
MISSING_BASELINE_QUESTIONS_PREFIX = "baseline observations missing for questions:"

RECORD_SPECS = (
    ("experiment", "experiment.json", "round-experiment.schema.json", True),
    ("facts", "facts.json", "round-facts.schema.json", False),
    ("questions", "questions.json", "round-questions.schema.json", False),
    ("actions", "actions.json", "round-actions.schema.json", False),
    ("business_events", "business-events.json", "round-business-events.schema.json", False),
)
ACTION_STATUSES = ("planned", "changed_local", "released", "verified_public", "reverted")
EVENT_TYPES = ("visit", "signup", "lead", "activation", "purchase")
SOURCE_TYPES = ("ai", "search", "social", "direct", "unknown")
EXCLUDED_EVENT_REASONS = ("outside_window", "other_site", "duplicate_event")
BASELINE_REQUIRED_PHASES = ("change", "release", "retest", "business_review", "report", "next_round")
VERDICT_LABELS = {
    "improved": "改善",
    "regressed": "回退",
    "unchanged": "持平",
    "insufficient": "样本不足",
    "not_comparable": "不可比",
}
FUTURE_MEASUREMENT_FIELDS = ("experiment_id", "questions_version", "baseline_round_id")
FUTURE_PAIR_FIELDS = ("insufficiency_reasons",)
CURRENCY_LABELS = {
    "USD": "美元",
    "EUR": "欧元",
    "GBP": "英镑",
    "CNY": "人民币",
    "JPY": "日元",
}
# amount_minor is stored in the currency's minor unit; most ISO 4217 currencies use two decimals.
ZERO_DECIMAL_CURRENCIES = {"JPY": 0, "KRW": 0, "VND": 0}


class MeasurementReportError(ValueError):
    """Raised when a supplied measurement report cannot be associated with this experiment."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = [str(item) for item in errors]
        super().__init__("; ".join(self.errors))


def _as_dir(project_dir: Any) -> Path:
    return Path(project_dir).expanduser().resolve()


def _read_json_object(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("{} must be a JSON object".format(path.name))
    return value


def _optional_record(root: Path, filename: str) -> Optional[Dict[str, Any]]:
    path = root / filename
    if not path.is_file():
        return None
    return _read_json_object(path)


def load_project(project_dir: Any) -> Dict[str, Optional[Dict[str, Any]]]:
    root = _as_dir(project_dir)
    experiment_path = root / "experiment.json"
    if not experiment_path.is_file():
        raise FileNotFoundError(ERR_EXPERIMENT_REQUIRED)
    return {
        "experiment": _read_json_object(experiment_path),
        "facts": _optional_record(root, "facts.json"),
        "questions": _optional_record(root, "questions.json"),
        "actions": _optional_record(root, "actions.json"),
        "business_events": _optional_record(root, "business-events.json"),
    }


def _load_record_for_validation(root: Path, filename: str, required: bool) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    path = root / filename
    if not path.is_file():
        if required:
            return None, [ERR_EXPERIMENT_REQUIRED if filename == "experiment.json" else "{} is required".format(filename)]
        return None, []
    try:
        return _read_json_object(path), []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, ["{}: {}".format(filename, exc)]


def _schema_errors(filename: str, schema_name: str, instance: Dict[str, Any]) -> List[str]:
    try:
        validate_instance(instance, schema_name)
    except SchemaValidationError as exc:
        return ["{}: {}".format(filename, exc)]
    return []


def _fact_ids(facts: Optional[Dict[str, Any]]) -> set:
    if not facts:
        return set()
    return {item["fact_id"] for item in facts.get("facts", []) if "fact_id" in item}


def _question_ids(questions: Optional[Dict[str, Any]]) -> set:
    if not questions:
        return set()
    return {item["question_id"] for item in questions.get("questions", []) if "question_id" in item}


def _action_ids(actions: Optional[Dict[str, Any]]) -> set:
    if not actions:
        return set()
    return {item["action_id"] for item in actions.get("actions", []) if "action_id" in item}


def _nonempty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _has_release_fields(action: Dict[str, Any]) -> bool:
    return _nonempty(action.get("released_at")) and _nonempty(action.get("release_evidence")) and _nonempty(action.get("deliverable"))


def _recheck_is_pass(action: Dict[str, Any]) -> bool:
    recheck = action.get("public_recheck")
    if not isinstance(recheck, dict):
        return False
    if recheck.get("result") != "pass":
        return False
    if not _nonempty(recheck.get("note")):
        return False
    checked_at = recheck.get("checked_at")
    released_at = action.get("released_at")
    if not checked_at or not released_at:
        return False
    try:
        return parse_datetime(str(checked_at)) > parse_datetime(str(released_at))
    except (TypeError, ValueError):
        return False


def _is_released(action: Dict[str, Any]) -> bool:
    return action.get("status") in {"released", "verified_public"} and _has_release_fields(action)


def _is_verified_public(action: Dict[str, Any]) -> bool:
    return action.get("status") == "verified_public" and _has_release_fields(action) and _recheck_is_pass(action)


def _action_status_errors(action: Dict[str, Any]) -> List[str]:
    action_id = action.get("action_id", "?")
    status = action.get("status")
    errors: List[str] = []
    if status == "reverted":
        return errors
    if status == "released":
        if not action.get("released_at"):
            errors.append("{}: {}".format(ERR_RELEASED_REQUIRES_RELEASED_AT, action_id))
        if not _nonempty(action.get("release_evidence")):
            errors.append("{}: {}".format(ERR_RELEASED_REQUIRES_RELEASE_EVIDENCE, action_id))
        if not _nonempty(action.get("deliverable")):
            errors.append("{}: {}".format(ERR_RELEASED_REQUIRES_DELIVERABLE, action_id))
        return errors
    if status != "verified_public":
        return errors
    if not action.get("released_at"):
        errors.append("{}: {}".format(ERR_VERIFIED_PUBLIC_REQUIRES_RELEASED_AT, action_id))
    if not _nonempty(action.get("release_evidence")):
        errors.append("{}: {}".format(ERR_VERIFIED_PUBLIC_REQUIRES_RELEASE_EVIDENCE, action_id))
    if not _nonempty(action.get("deliverable")):
        errors.append("{}: {}".format(ERR_VERIFIED_PUBLIC_REQUIRES_DELIVERABLE, action_id))
    recheck = action.get("public_recheck")
    if not isinstance(recheck, dict):
        errors.append("{}: {}".format(ERR_VERIFIED_PUBLIC_REQUIRES_RECHECK, action_id))
        return errors
    if recheck.get("result") != "pass":
        errors.append("{}: {}".format(ERR_VERIFIED_PUBLIC_REQUIRES_PASS, action_id))
    if not _nonempty(recheck.get("note")):
        errors.append("{}: {}".format(ERR_VERIFIED_PUBLIC_REQUIRES_NOTE, action_id))
    checked_at = recheck.get("checked_at")
    released_at = action.get("released_at")
    if checked_at and released_at:
        try:
            if parse_datetime(str(checked_at)) <= parse_datetime(str(released_at)):
                errors.append("{}: {}".format(ERR_VERIFIED_PUBLIC_RECHECK_NOT_AFTER_RELEASE, action_id))
        except (TypeError, ValueError):
            errors.append("{}: {}".format(ERR_VERIFIED_PUBLIC_RECHECK_NOT_AFTER_RELEASE, action_id))
    elif _has_release_fields(action):
        errors.append("{}: {}".format(ERR_VERIFIED_PUBLIC_RECHECK_NOT_AFTER_RELEASE, action_id))
    return errors


def _cross_file_errors(records: Dict[str, Optional[Dict[str, Any]]]) -> List[str]:
    errors: List[str] = []
    experiment = records.get("experiment") or {}
    facts = records.get("facts")
    questions = records.get("questions")
    actions = records.get("actions")
    business_events = records.get("business_events")
    known_facts = _fact_ids(facts)
    known_questions = _question_ids(questions)
    known_actions = _action_ids(actions)

    baseline = experiment.get("baseline")
    rounds = experiment.get("rounds") or []
    round_ids = {item.get("round_id") for item in rounds}
    if isinstance(baseline, dict):
        round_id = baseline.get("round_id")
        if round_id not in round_ids:
            errors.append("{}: {}".format(ERR_BASELINE_ROUND_ID, round_id))

    if facts is not None and facts.get("facts_version") != experiment.get("facts_version"):
        errors.append(ERR_FACTS_VERSION)
    if questions is not None and questions.get("questions_version") != experiment.get("questions_version"):
        errors.append(ERR_QUESTIONS_VERSION)

    for action in (actions or {}).get("actions") or []:
        action_id = action.get("action_id", "?")
        for fact_id in action.get("fact_ids") or []:
            if fact_id not in known_facts:
                errors.append("{}: {} -> {}".format(ERR_UNKNOWN_FACT_ID, action_id, fact_id))
        for question_id in action.get("question_ids") or []:
            if question_id not in known_questions:
                errors.append("{}: {} -> {}".format(ERR_UNKNOWN_QUESTION_ID, action_id, question_id))
        errors.extend(_action_status_errors(action))

    for item in rounds:
        round_id = item.get("round_id", "?")
        for action_id in item.get("compared_action_ids") or []:
            if action_id not in known_actions:
                errors.append("{}: {} -> {}".format(ERR_UNKNOWN_ACTION_ID, round_id, action_id))

    for batch in (business_events or {}).get("imports") or []:
        import_id = batch.get("import_id", "?")
        seen_ids: Set[Tuple[Any, Any]] = set()
        for event in batch.get("events") or []:
            external_id = event.get("external_id", "?")
            key = (batch.get("source"), external_id)
            if key in seen_ids:
                errors.append("{}: {} / {}".format(ERR_DUPLICATE_EVENT_ID, import_id, external_id))
            else:
                seen_ids.add(key)
            if event.get("source_type") == "ai" and (
                not event.get("source_evidence_url") or event.get("attribution_method") == "unknown"
            ):
                errors.append("{}: {} / {}".format(ERR_AI_EVENT_EVIDENCE, import_id, external_id))
            if event.get("type") != "purchase" and (
                event.get("amount_minor") is not None or event.get("currency") is not None
            ):
                errors.append("{}: {} / {}".format(ERR_MONEY_ONLY_ON_PURCHASE, import_id, external_id))
    return errors


def _project_file(root: Path, relative: Any) -> Optional[Path]:
    text = str(relative or "")
    if not text.strip():
        return None
    rel = Path(text)
    if not rel.parts or ".." in rel.parts:
        return None
    resolved_root = root.resolve()
    path = rel.resolve() if rel.is_absolute() else (resolved_root / rel).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError:
        return None
    return path


def _row_observation(row: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(row, dict):
        return None
    inner = row.get("observation")
    if isinstance(inner, dict):
        return inner
    if "prompt_id" in row:
        return row
    return None


def _load_observation_rows(path: Path) -> Tuple[Optional[List[Any]], Optional[str]]:
    try:
        text = path.read_text("utf-8")
    except OSError:
        return None, "{}: {}".format(ERR_BASELINE_OBSERVATION_UNREADABLE, path.name)
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return None, "{}: {}".format(ERR_BASELINE_OBSERVATION_PARSE, path.name)
        if not isinstance(value, dict) or not isinstance(value.get("observations"), list):
            return None, ERR_BASELINE_OBSERVATION_FORMAT
        return value["observations"], None
    rows: List[Any] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            return None, "{}: {}".format(ERR_BASELINE_OBSERVATION_PARSE, path.name)
        if not isinstance(row, dict):
            return None, "{}: {}".format(ERR_BASELINE_OBSERVATION_PARSE, path.name)
        rows.append(row)
    if not rows:
        return None, ERR_BASELINE_OBSERVATION_FORMAT
    return rows, None


def baseline_evidence_errors(root: Path, experiment: Optional[Dict[str, Any]], questions: Optional[Dict[str, Any]]) -> List[str]:
    baseline = (experiment or {}).get("baseline")
    if not isinstance(baseline, dict):
        return [MISSING_BASELINE_BEFORE_CHANGE]
    label = str(baseline.get("observation_file") or "")
    path = _project_file(root, label)
    if path is None:
        return ["{}: {}".format(ERR_BASELINE_OBSERVATION_OUTSIDE_PROJECT, label or "(empty)")]
    if not path.is_file():
        return ["{}: {}".format(ERR_BASELINE_OBSERVATION_MISSING, label)]
    rows, read_error = _load_observation_rows(path)
    if read_error:
        return [read_error]
    errors: List[str] = []
    seen_prompts = set()
    expected_round = baseline.get("round_id")
    expected_version = (experiment or {}).get("questions_version")
    expected_experiment = (experiment or {}).get("experiment_id")
    for row in rows or []:
        observation = _row_observation(row)
        if observation is None:
            errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_PARSE, label))
            continue
        prompt_id = observation.get("prompt_id")
        if prompt_id:
            seen_prompts.add(prompt_id)
        if observation.get("round_id") != expected_round:
            errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_ROUND_ID, prompt_id or "?"))
        if observation.get("phase") != "baseline":
            errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_PHASE, prompt_id or "?"))
        if observation.get("question_version") != expected_version:
            errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_QUESTION_VERSION, prompt_id or "?"))
        if observation.get("experiment_id") is not None and observation.get("experiment_id") != expected_experiment:
            errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_EXPERIMENT_ID, prompt_id or "?"))
    missing_questions = sorted(_question_ids(questions) - seen_prompts)
    if missing_questions:
        errors.append("{} {}".format(MISSING_BASELINE_QUESTIONS_PREFIX, ", ".join(missing_questions)))
    return errors


def validate_project(project_dir: Any) -> List[str]:
    root = _as_dir(project_dir)
    records: Dict[str, Optional[Dict[str, Any]]] = {}
    errors: List[str] = []
    for key, filename, schema_name, required in RECORD_SPECS:
        instance, read_errors = _load_record_for_validation(root, filename, required)
        errors.extend(read_errors)
        records[key] = instance
        if instance is not None:
            errors.extend(_schema_errors(filename, schema_name, instance))
    experiment = records.get("experiment")
    if experiment is not None:
        errors.extend(_cross_file_errors(records))
        if isinstance(experiment.get("baseline"), dict):
            errors.extend(baseline_evidence_errors(root, experiment, records.get("questions")))
    return errors


def project_status(project_dir: Any) -> Dict[str, Any]:
    root = _as_dir(project_dir)
    records = load_project(root)
    experiment = records["experiment"] or {}
    actions = (records["actions"] or {}).get("actions") or []
    counts = {status: 0 for status in ACTION_STATUSES}
    for action in actions:
        status = action.get("status")
        if status in counts:
            counts[status] += 1
    evidence_errors = baseline_evidence_errors(root, experiment, records.get("questions"))
    missing: List[str] = []
    if experiment.get("current_phase") in BASELINE_REQUIRED_PHASES:
        missing.extend(evidence_errors)
    return {
        "current_phase": experiment.get("current_phase"),
        "next_step": experiment.get("next_step"),
        "actions_by_status": counts,
        "baseline_present": not evidence_errors,
        "missing_preconditions": missing,
        "last_updated": experiment.get("updated_at"),
    }


def parse_datetime(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def window_days(window: Dict[str, Any]) -> float:
    return (parse_datetime(window["end"]) - parse_datetime(window["start"])).total_seconds() / 86400.0


def window_whole_days(window: Dict[str, Any]) -> int:
    start = parse_datetime(window["start"]).date()
    end = parse_datetime(window["end"]).date()
    return (end - start).days


def windows_equal_to_the_day(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    return parse_datetime(left["start"]).date() == parse_datetime(right["start"]).date() and parse_datetime(
        left["end"]
    ).date() == parse_datetime(right["end"]).date()


def windows_overlap(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    return parse_datetime(left["start"]) <= parse_datetime(right["end"]) and parse_datetime(right["start"]) <= parse_datetime(
        left["end"]
    )


def _zero_counts() -> Dict[str, int]:
    return {key: 0 for key in EVENT_TYPES}


def _zero_sources() -> Dict[str, int]:
    return {key: 0 for key in SOURCE_TYPES}


def _zero_excluded() -> Dict[str, int]:
    return {key: 0 for key in EXCLUDED_EVENT_REASONS}


def _page_host_allowed(page_url: Optional[str], site_domain: Optional[str]) -> bool:
    if not page_url:
        return True
    if not site_domain:
        return True
    host = (urlparse(str(page_url)).hostname or "").lower().rstrip(".")
    target = str(site_domain).lower().rstrip(".")
    if not host or not target:
        return False
    return host == target or host.endswith("." + target)


def _event_in_window(event: Dict[str, Any], window: Dict[str, Any]) -> bool:
    if "start" not in window or "end" not in window or not event.get("occurred_at"):
        return False
    occurred = parse_datetime(str(event["occurred_at"]))
    return parse_datetime(window["start"]) <= occurred <= parse_datetime(window["end"])


def _summarize_events(events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    real_counts = _zero_counts()
    test_counts = _zero_counts()
    source_type_counts = _zero_sources()
    revenue_by_currency: Dict[str, int] = {}
    test_total = 0
    for event in events:
        bucket = test_counts if event.get("is_test") else real_counts
        event_type = event.get("type")
        if event_type in bucket:
            bucket[event_type] += 1
        if event.get("is_test"):
            test_total += 1
            continue
        source_type = event.get("source_type")
        if source_type in source_type_counts:
            source_type_counts[source_type] += 1
        if event_type == "purchase" and event.get("amount_minor") is not None and event.get("currency"):
            currency = event["currency"]
            revenue_by_currency[currency] = revenue_by_currency.get(currency, 0) + int(event["amount_minor"])
    visits = real_counts["visit"]
    signups = real_counts["signup"]
    purchases = real_counts["purchase"]
    if visits > 0:
        signup_rate: Optional[float] = signups / visits
        signup_rate_reason: Optional[str] = None
    else:
        signup_rate = None
        signup_rate_reason = "missing visits"
    if signups > 0:
        purchase_rate: Optional[float] = purchases / signups
        purchase_rate_reason: Optional[str] = None
    else:
        purchase_rate = None
        purchase_rate_reason = "missing signups"
    return {
        "counts": real_counts,
        "test_counts": test_counts,
        "test_event_count": test_total,
        "revenue_by_currency": revenue_by_currency,
        "source_type_counts": source_type_counts,
        "signup_rate": signup_rate,
        "signup_rate_reason": signup_rate_reason,
        "purchase_rate": purchase_rate,
        "purchase_rate_reason": purchase_rate_reason,
    }


def _import_status(coverage: str, real_counts: Dict[str, int]) -> str:
    if coverage == "unknown":
        return "data_incomplete"
    if coverage == "complete" and sum(real_counts.values()) == 0:
        return "measured_zero"
    if coverage == "complete":
        return "measured"
    return "partial"


def _analyze_import(
    batch: Dict[str, Any],
    site_domain: Optional[str],
    seen_keys: Set[Tuple[Any, Any]],
) -> Dict[str, Any]:
    window = batch.get("window") or {}
    excluded_events: List[Dict[str, str]] = []
    excluded_counts = _zero_excluded()
    included: List[Dict[str, Any]] = []
    local_ids: Set[Any] = set()
    source = batch.get("source")
    for event in batch.get("events") or []:
        external_id = event.get("external_id", "?")
        if external_id in local_ids:
            continue
        local_ids.add(external_id)
        if not _event_in_window(event, window):
            excluded_events.append({"external_id": str(external_id), "reason": "outside_window"})
            excluded_counts["outside_window"] += 1
            continue
        if not _page_host_allowed(event.get("page_url"), site_domain):
            excluded_events.append({"external_id": str(external_id), "reason": "other_site"})
            excluded_counts["other_site"] += 1
            continue
        key = (source, external_id)
        if key in seen_keys:
            excluded_events.append({"external_id": str(external_id), "reason": "duplicate_event"})
            excluded_counts["duplicate_event"] += 1
            continue
        seen_keys.add(key)
        included.append(event)
    summary = _summarize_events(included)
    coverage = batch.get("coverage")
    return {
        "import_id": batch.get("import_id"),
        "coverage": coverage,
        "status": _import_status(coverage, summary["counts"]),
        "window": window,
        "window_days": window_days(window) if "start" in window and "end" in window else None,
        "excluded_events": excluded_events,
        "excluded_counts": excluded_counts,
        **summary,
    }


def _overlapping_pairs(imports: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    pairs: List[Dict[str, str]] = []
    for index, left in enumerate(imports):
        for right in imports[index + 1 :]:
            if windows_overlap(left["window"], right["window"]):
                pairs.append({"left": left["import_id"], "right": right["import_id"]})
    return pairs


def _comparison(experiment: Optional[Dict[str, Any]], analyzed: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    baseline = (experiment or {}).get("baseline")
    if not isinstance(baseline, dict) or not analyzed:
        return None
    before_window = baseline.get("captured_window")
    if not before_window:
        return None
    later = [
        item
        for item in analyzed
        if item.get("window") and "start" in item["window"] and parse_datetime(item["window"]["start"]) >= parse_datetime(before_window["end"])
    ]
    if not later:
        return None
    after = sorted(later, key=lambda item: item["window"]["start"])[0]
    before_match = next(
        (
            item
            for item in analyzed
            if item.get("window") and "start" in item["window"] and windows_equal_to_the_day(item["window"], before_window)
        ),
        None,
    )
    if before_match is None:
        return {
            "comparable": False,
            "reason": "no business baseline import",
            "before": None,
            "after": after,
        }
    before = before_match
    overlap = windows_overlap(before_window, after["window"])
    equal_length = window_whole_days(before_window) == window_whole_days(after["window"])
    if before.get("coverage") == "partial":
        reason: Optional[str] = "baseline import coverage partial"
    elif before.get("coverage") == "unknown":
        reason = "baseline import coverage unknown"
    elif after.get("coverage") == "unknown":
        reason = "after import coverage unknown"
    elif overlap:
        reason = "windows overlap"
    elif not equal_length:
        reason = "unequal window length"
    else:
        reason = None
    return {
        "comparable": reason is None,
        "reason": reason,
        "before": before,
        "after": after,
    }


def analyze_business(records: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Any]:
    business_events = records.get("business_events")
    imports = list((business_events or {}).get("imports") or [])
    if business_events is None or not imports:
        return {
            "status": "not_measured",
            "imports": [],
            "flags": {"overlapping_windows": []},
            "comparison": None,
        }
    experiment = records.get("experiment") or {}
    site_domain = experiment.get("site_domain")
    seen_keys: Set[Tuple[Any, Any]] = set()
    analyzed = [_analyze_import(batch, site_domain, seen_keys) for batch in imports]
    overlap = _overlapping_pairs(imports)
    return {
        "status": "analyzed",
        "imports": analyzed,
        "flags": {"overlapping_windows": overlap},
        "comparison": _comparison(experiment, analyzed),
    }


def _fact_statement(facts: Optional[Dict[str, Any]], fact_id: str) -> str:
    for item in (facts or {}).get("facts") or []:
        if item.get("fact_id") == fact_id:
            return item.get("statement") or fact_id
    return "一条尚未登记说明的事实"


def _pages_and_facts(records: Dict[str, Optional[Dict[str, Any]]]) -> str:
    actions = (records.get("actions") or {}).get("actions") or []
    facts = records.get("facts")
    changed = [item for item in actions if item.get("status") in {"changed_local", "released", "verified_public", "reverted"}]
    if not changed:
        return "这一轮还没有改页面，也还没有改对外事实。"
    pages = []
    seen_pages = set()
    for item in changed:
        url = item.get("page_url")
        if url and url not in seen_pages:
            seen_pages.add(url)
            pages.append(url)
    statements = []
    seen_facts = set()
    for item in changed:
        for fact_id in item.get("fact_ids") or []:
            if fact_id in seen_facts:
                continue
            seen_facts.add(fact_id)
            statements.append(_fact_statement(facts, fact_id))
    page_text = "、".join(pages) if pages else "尚未记下具体页面"
    if statements:
        fact_text = "更新的事实：" + "；".join(statement.rstrip("。.！!？?") for statement in statements) + "。"
    else:
        fact_text = "没有记下对应的对外事实。"
    local_only = any(item.get("status") == "changed_local" for item in changed)
    public = any(_is_released(item) or _is_verified_public(item) for item in changed)
    reverted = any(item.get("status") == "reverted" for item in changed)
    visibility = []
    if public:
        visibility.append("其中已有改动出现在公开页")
    if local_only:
        visibility.append("另有改动还只在本地")
    if reverted:
        visibility.append("还有改动后来撤回了")
    extra = "，".join(visibility)
    if extra:
        return "改过这些页面：{}。{}{}".format(page_text, fact_text, extra + "。")
    return "改过这些页面：{}。{}".format(page_text, fact_text)


def _stage_rows(measurement_report: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not measurement_report:
        return []
    rows = measurement_report.get("stage_table")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _ai_changes(measurement_report: Optional[Dict[str, Any]]) -> str:
    rows = _stage_rows(measurement_report)
    if not rows:
        return "未测。还没有可核对的 AI 回答前后对比。"
    sentences = []
    for row in rows:
        label = row.get("label") or "一项对比"
        baseline = row.get("baseline")
        after = row.get("after")
        basis = row.get("basis")
        result = row.get("result")
        sentence = "{}：改前 {}，改后 {}。".format(label, baseline, after)
        if basis:
            sentence += "依据：{}。".format(basis)
        if result:
            sentence += "{}。".format(result)
        sentences.append(sentence)
    return "\n".join(sentences)


def _not_yet(records: Dict[str, Optional[Dict[str, Any]]]) -> str:
    actions = (records.get("actions") or {}).get("actions") or []
    if not actions:
        return "还没有登记要改的内容。"
    lines: List[str] = []
    for item in actions:
        summary = item.get("summary") or "一项改动"
        url = item.get("page_url") or "未记下的页面"
        status = item.get("status")
        if status == "planned":
            lines.append("还没开始改：{}（{}）。".format(summary, url))
        elif status == "changed_local":
            lines.append("本地已改、公开页还看不到：{}（{}）。".format(summary, url))
        elif status == "released":
            if not _has_release_fields(item):
                lines.append("已经写了发布，但还缺发布凭据：{}（{}）。".format(summary, url))
            else:
                lines.append("已经发布，还没有核对公开结果是否符合预期：{}（{}）。".format(summary, url))
        elif status == "verified_public":
            if not _is_verified_public(item):
                lines.append("公开页核对尚未通过：{}（{}）。".format(summary, url))
        elif status == "reverted":
            lines.append("曾经改过，后来撤回了：{}（{}）。".format(summary, url))
    if not lines:
        return "计划中的改动都已经出现在公开页，并完成核对。"
    return "\n".join(lines)


def _zh_counts(counts: Dict[str, int]) -> str:
    return "访问 {} 次，注册 {} 次，线索 {} 条，开通 {} 次，成交 {} 笔。".format(
        counts.get("visit", 0),
        counts.get("signup", 0),
        counts.get("lead", 0),
        counts.get("activation", 0),
        counts.get("purchase", 0),
    )


def _zh_amount(code: str, amount_minor: int) -> str:
    decimals = ZERO_DECIMAL_CURRENCIES.get(code, 2)
    if decimals == 0:
        return "{:,}".format(amount_minor)
    major, minor = divmod(amount_minor, 10 ** decimals)
    return "{:,}.{:0{width}d}".format(major, minor, width=decimals)


def _zh_revenue(revenue: Dict[str, int]) -> str:
    if not revenue:
        return "没有计入真实收入的成交金额。"
    parts = [
        "{} {}".format(_zh_amount(code, amount), CURRENCY_LABELS.get(code, code))
        for code, amount in sorted(revenue.items())
    ]
    return "成交金额按币种分开（未换算）：" + "；".join(parts) + "。"


def _zh_rate(name: str, rate: Optional[float], reason: Optional[str], numerator: int, denominator: int) -> str:
    if rate is None:
        if reason == "missing visits":
            return "没有访问次数，不能计算{}，只报注册 {} 次。".format(name, numerator)
        if reason == "missing signups":
            return "没有注册次数，不能计算{}，只报成交 {} 笔。".format(name, numerator)
        return "{}未计算。".format(name)
    return "{}为 {:.1%}（{} / {}）。".format(name, rate, numerator, denominator)


def _excluded_text(item: Dict[str, Any]) -> Optional[str]:
    counts = item.get("excluded_counts") or {}
    outside = counts.get("outside_window") or 0
    other = counts.get("other_site") or 0
    duplicate = counts.get("duplicate_event") or 0
    if not (outside or other or duplicate):
        return None
    return "未计入：窗口外 {} 条，其他站点 {} 条，重复事件 {} 条。".format(outside, other, duplicate)


def _business_import_lines(item: Dict[str, Any]) -> List[str]:
    status = item.get("status")
    if status == "data_incomplete":
        head = "这段窗口的数据不完整，不能当成零。"
    elif status == "measured_zero":
        head = "这段完整窗口里，可统计的访问、注册和购买都是 0。"
    elif status == "partial":
        head = "这段窗口只覆盖了部分数据，下面的数字不能当成全量。"
    else:
        head = "这段窗口按已导入的真实事件统计。"
    lines = [head, "次数：" + _zh_counts(item.get("counts") or {})]
    excluded = _excluded_text(item)
    if excluded:
        lines.append(excluded)
    test_total = item.get("test_event_count") or 0
    if test_total:
        lines.append("另有 {} 条测试事件，不计入真实收入。".format(test_total))
        lines.append("测试事件次数：" + _zh_counts(item.get("test_counts") or {}))
    lines.append(_zh_revenue(item.get("revenue_by_currency") or {}))
    sources = item.get("source_type_counts") or {}
    if sources.get("social"):
        lines.append("来自社交渠道的记录仍记为社交，不会改记成 AI。")
    if sources.get("unknown"):
        lines.append("来源不明的记录保持来源不明，不会记成 AI。")
    return lines


def _before_is_missing(before: Any) -> bool:
    return before is None or (isinstance(before, dict) and before.get("status") == "not_measured")


def _comparison_text(comparison: Optional[Dict[str, Any]]) -> List[str]:
    if not comparison:
        return []
    before = comparison.get("before")
    after = comparison.get("after") or {}
    reason = comparison.get("reason")
    if comparison.get("comparable"):
        lines = ["有两段等长且不重叠的窗口，数字可以并排看，但不能据此判断是这次改动导致了业务变化。"]
    elif reason == "no business baseline import":
        lines = ["改前窗口没有导入数据，只列改后窗口的数字，不做前后增减。"]
    elif reason == "baseline import coverage partial":
        lines = ["改前窗口的导入不完整，不能做前后对比。"]
    elif reason == "baseline import coverage unknown":
        lines = ["改前窗口的覆盖范围不明，不能做前后对比。"]
    elif reason == "after import coverage unknown":
        lines = ["改后窗口的覆盖范围不明，不能做前后对比。"]
    elif reason == "windows overlap":
        lines = ["两段窗口不能对比，因为两端窗口有重叠。"]
    elif reason == "unequal window length":
        lines = ["两段窗口不能对比，因为两端窗口长度不同。"]
    else:
        lines = ["两段窗口不能对比，因为两端窗口不能对齐。"]
    if _before_is_missing(before):
        if reason != "no business baseline import":
            lines.append("改前窗口没有导入数据，只列改后窗口的数字，不做前后增减。")
        lines.append("改后窗口：" + _zh_counts(after.get("counts") or {}))
        return lines
    lines.append("改前窗口：" + _zh_counts((before or {}).get("counts") or {}))
    lines.append("改后窗口：" + _zh_counts(after.get("counts") or {}))
    return lines


def _business_section(analysis: Dict[str, Any]) -> str:
    if analysis.get("status") == "not_measured":
        return "没有业务数据。没有业务数据时，这一阶段的报告仍然完整。"
    lines: List[str] = []
    for item in analysis.get("imports") or []:
        lines.extend(_business_import_lines(item))
    if analysis.get("flags", {}).get("overlapping_windows"):
        lines.append("有两段导入窗口重叠，重叠时段的数字不能当成互不干扰的两段。")
    lines.extend(_comparison_text(analysis.get("comparison")))
    return "\n".join(lines)


def _denominators(analysis: Dict[str, Any]) -> str:
    if analysis.get("status") == "not_measured":
        return "没有业务数据，因此没有转化率。"
    lines: List[str] = []
    for item in analysis.get("imports") or []:
        counts = item.get("counts") or {}
        lines.append(
            _zh_rate(
                "注册率",
                item.get("signup_rate"),
                item.get("signup_rate_reason"),
                counts.get("signup", 0),
                counts.get("visit", 0),
            )
        )
        lines.append(
            _zh_rate(
                "成交率",
                item.get("purchase_rate"),
                item.get("purchase_rate_reason"),
                counts.get("purchase", 0),
                counts.get("signup", 0),
            )
        )
        if item.get("status") == "data_incomplete":
            lines.append("覆盖范围不明，这些次数不能当成完整窗口里的零。")
        if item.get("status") == "measured_zero":
            lines.append("这是一段完整窗口，统计结果就是零。")
    return "\n".join(lines) if lines else "没有可计算的转化率。"


def _business_limits() -> str:
    return "\n".join(
        [
            "覆盖范围不明时写未测或数据不完整，不当成零。",
            "完整窗口里的零就是零。",
            "注册率需要访问次数，成交率需要注册次数；缺了这些次数时只报个数。",
            "测试事件不计入真实收入。",
            "不同币种分开统计。",
            "业务改前数字必须来自一段已导入、覆盖完整、且和改前观察同一起止日期的窗口，不能把缺数据当成零。",
            "窗口长度按整天计算，两端必须一样长且不重叠，才能并排对比。",
            "窗口外、其他站点或重复导入的事件不计入次数和收入。",
            "这些数字不能证明是这次改动带来了业务变化。",
            "只看这一站点、这一市场，不把其他语言或其他地区的结果加进来。",
        ]
    )


def _stage_table(measurement_report: Optional[Dict[str, Any]]) -> str:
    rows = _stage_rows(measurement_report)
    if not rows:
        return "未测"
    lines = [
        "| 对比项 | 改前 | 改后 | 依据 | 结果 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {} | {} | {} | {} | {} |".format(
                row.get("label") or "—",
                row.get("baseline") if row.get("baseline") not in (None, "") else "—",
                row.get("after") if row.get("after") not in (None, "") else "—",
                row.get("basis") if row.get("basis") not in (None, "") else "—",
                row.get("result") if row.get("result") not in (None, "") else "—",
            )
        )
    return "\n".join(lines)


def _sources_footer(records: Dict[str, Optional[Dict[str, Any]]], measurement_report: Optional[Dict[str, Any]]) -> str:
    names = ["experiment.json"]
    if records.get("facts") is not None:
        names.append("facts.json")
    if records.get("questions") is not None:
        names.append("questions.json")
    if records.get("actions") is not None:
        names.append("actions.json")
    if records.get("business_events") is not None:
        names.append("business-events.json")
    names.append("report.md")
    lines = [
        "本报告根据同目录下的实验、事实、问题、改动和业务事件记录生成。",
        "记录文件：" + "、".join(names) + "。",
    ]
    if measurement_report is not None:
        lines.append("如附带了测量结果，前后对比表来自这次提供的测量。本报告没有另外计算回答变化。")
    return "\n".join(lines)


def _fill_template(values: Dict[str, str]) -> str:
    text = (repository_root() / "templates" / "round-report.md").read_text("utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _schema_instance_for_measurement(report: Dict[str, Any]) -> Dict[str, Any]:
    schema = load_schema("measurement-report.schema.json")
    properties = schema.get("properties") or {}
    instance: Dict[str, Any] = report
    if schema.get("additionalProperties") is False:
        extra = [key for key in FUTURE_MEASUREMENT_FIELDS if key in report and key not in properties]
        if extra:
            instance = {key: value for key, value in report.items() if key not in extra}
    pair_schema = (schema.get("$defs") or {}).get("pair") or {}
    pair_properties = pair_schema.get("properties") or {}
    strip_pair = []
    if pair_schema.get("additionalProperties") is False:
        strip_pair = [key for key in FUTURE_PAIR_FIELDS if key not in pair_properties]
    pairs = instance.get("pairs")
    if strip_pair and isinstance(pairs, list):
        if instance is report:
            instance = dict(report)
        instance["pairs"] = [
            {key: value for key, value in pair.items() if key not in strip_pair} if isinstance(pair, dict) else pair
            for pair in pairs
        ]
    return instance


def _measurement_association_errors(report: Dict[str, Any], experiment: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    schema = load_schema("measurement-report.schema.json")
    properties = schema.get("properties") or {}
    pair_schema = (schema.get("$defs") or {}).get("pair") or {}
    pair_properties = pair_schema.get("properties") or {}
    if not report.get("experiment_id"):
        errors.append(ERR_MEASUREMENT_NO_EXPERIMENT_ID)
    elif report.get("experiment_id") != experiment.get("experiment_id"):
        errors.append(ERR_MEASUREMENT_EXPERIMENT_ID)
    if not report.get("questions_version"):
        errors.append(ERR_MEASUREMENT_NO_QUESTIONS_VERSION)
    elif report.get("questions_version") != experiment.get("questions_version"):
        errors.append(ERR_MEASUREMENT_QUESTIONS_VERSION)
    if report.get("site_domain") != experiment.get("site_domain"):
        errors.append(ERR_MEASUREMENT_SITE_DOMAIN)
    if "baseline_round_id" in properties and not report.get("baseline_round_id"):
        errors.append(ERR_MEASUREMENT_NO_BASELINE_ROUND_ID)
    pairs = report.get("pairs") if isinstance(report.get("pairs"), list) else []
    stage_table = report.get("stage_table") if isinstance(report.get("stage_table"), list) else []
    baseline = experiment.get("baseline")
    if pairs and not isinstance(baseline, dict):
        errors.append(ERR_MEASUREMENT_NULL_BASELINE)
    expected_baseline = baseline.get("round_id") if isinstance(baseline, dict) else None
    if "baseline_round_id" in properties and report.get("baseline_round_id") and expected_baseline and report.get("baseline_round_id") != expected_baseline:
        errors.append(ERR_MEASUREMENT_BASELINE_ROUND)
    round_ids = {item.get("round_id") for item in experiment.get("rounds") or []}
    if len(stage_table) != len(pairs):
        errors.append(ERR_MEASUREMENT_STAGE_LENGTH)
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            errors.append(ERR_MEASUREMENT_STAGE_RESULT)
            continue
        if isinstance(baseline, dict) and pair.get("baseline_round_id") != expected_baseline:
            errors.append(ERR_MEASUREMENT_BASELINE_ROUND)
        if pair.get("after_round_id") not in round_ids:
            errors.append("{}: {}".format(ERR_MEASUREMENT_AFTER_ROUND, pair.get("after_round_id")))
        if "insufficiency_reasons" in pair_properties and "insufficiency_reasons" not in pair:
            errors.append(ERR_MEASUREMENT_INSUFFICIENCY_REASONS)
        if index < len(stage_table) and isinstance(stage_table[index], dict):
            expected_result = VERDICT_LABELS.get(str(pair.get("verdict")))
            if stage_table[index].get("result") != expected_result:
                errors.append(ERR_MEASUREMENT_STAGE_RESULT)
    return list(dict.fromkeys(errors))


def accept_measurement_report(report: Dict[str, Any], experiment: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(report, dict):
        raise MeasurementReportError(["measurement report must be a JSON object"])
    try:
        validate_instance(_schema_instance_for_measurement(report), "measurement-report.schema.json")
    except SchemaValidationError as exc:
        raise MeasurementReportError([str(exc)]) from exc
    errors = _measurement_association_errors(report, experiment or {})
    if errors:
        raise MeasurementReportError(errors)
    return report


def render_report(project_dir: Any, measurement_report: Optional[Dict[str, Any]] = None) -> str:
    records = load_project(project_dir)
    experiment = records["experiment"] or {}
    accepted = None
    if measurement_report is not None:
        accepted = accept_measurement_report(measurement_report, experiment)
    analysis = analyze_business(records)
    next_step = experiment.get("next_step") or "先查看当前进度，再决定下一件要改的事。"
    return _fill_template(
        {
            "pages_and_facts": _pages_and_facts(records),
            "ai_changes": _ai_changes(accepted),
            "not_yet": _not_yet(records),
            "business": _business_section(analysis),
            "next_item": next_step,
            "stage_table": _stage_table(accepted),
            "denominators": _denominators(analysis),
            "business_limits": _business_limits(),
            "next_step": next_step,
            "sources_footer": _sources_footer(records, accepted),
        }
    )


def _load_measurement_report(path: Optional[Any]) -> Optional[Dict[str, Any]]:
    if path is None:
        return None
    value = _read_json_object(Path(path))
    return value


def write_report(project_dir: Any, measurement_report_path: Optional[Any] = None) -> Path:
    dest = _as_dir(project_dir) / "report.md"
    text = render_report(project_dir, _load_measurement_report(measurement_report_path))
    if not text.endswith("\n"):
        text += "\n"
    dest.write_text(text, "utf-8")
    return dest
