"""Local portable GEO round record: validate, resume status, business windows, stage report."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlparse

from .paths import repository_root
from .business_attribution import analyze as analyze_attribution
from .business_report import render_business_report
from .providers.geo_measure import LINE_LABELS, TERMINAL_LABELS, format_stage_side
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
ERR_MONEY_ONLY_ON_PURCHASE = "money is only allowed on purchase or refund events"
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
ERR_BASELINE_OBSERVATION_INVALID = "baseline observation is not valid evidence"
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
    ("question_backlog", "question-backlog.json", "question-backlog.schema.json", False),
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
            if event.get("type") not in {"purchase", "refund"} and (
                event.get("amount_minor") is not None or event.get("currency") is not None
            ):
                errors.append("{}: {} / {}".format(ERR_MONEY_ONLY_ON_PURCHASE, import_id, external_id))
    backlog = records.get("question_backlog")
    if backlog is not None:
        if backlog.get("questions_version") != experiment.get("questions_version"):
            errors.append("question backlog does not match the frozen question version")
        if set(backlog.get("frozen_question_ids", [])) != known_questions:
            errors.append("question backlog must reference the unchanged frozen question set")
        for candidate in backlog.get("next_round_pool", []):
            if set(candidate.get("related_question_ids", [])) - known_questions:
                errors.append("question backlog references an unknown frozen question")
            if set(candidate.get("related_fact_ids", [])) - known_facts:
                errors.append("question backlog references an unknown fact")
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
        return [
            {"observation": observation, "site_domain": value.get("site_domain"),
             "experiment_id": value.get("experiment_id")}
            for observation in value["observations"]
        ], None
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
    declared_rounds = {item["round_id"]: item["phase"] for item in (experiment or {}).get("rounds", [])}
    known_questions = {item["question_id"]: item for item in (questions or {}).get("questions", [])}
    for row in rows or []:
        observation = _row_observation(row)
        if observation is None:
            errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_PARSE, label))
            continue
        try:
            validate_instance(observation, "observation.schema.json")
        except SchemaValidationError as exc:
            errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_INVALID, exc))
            continue
        prompt_id = observation.get("prompt_id")
        if row.get("site_domain") is not None and row["site_domain"] != (experiment or {}).get("site_domain"):
            errors.append("{}: site mismatch for {}".format(ERR_BASELINE_OBSERVATION_INVALID, prompt_id))
        for identity in (row.get("experiment_id"), observation.get("experiment_id")):
            if identity is not None and identity != expected_experiment:
                errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_EXPERIMENT_ID, prompt_id))
        round_id = observation.get("round_id")
        if round_id != expected_round:
            if round_id not in declared_rounds or observation.get("phase") != declared_rounds[round_id]:
                errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_ROUND_ID, prompt_id))
            # The append-only observation file also holds declared later rounds.
            # Only the frozen baseline set supplies baseline coverage and evidence.
            continue
        if prompt_id:
            seen_prompts.add(prompt_id)
        question = known_questions.get(prompt_id)
        if question is None:
            errors.append("{}: {}".format(ERR_UNKNOWN_QUESTION_ID, prompt_id))
        elif " ".join(observation["prompt_text"].split()) != " ".join(question["text"].split()):
            errors.append("{}: prompt text changed for {}".format(ERR_BASELINE_OBSERVATION_INVALID, prompt_id))
        elif observation.get("observation_line") != question["observation_line"]:
            errors.append("{}: observation line changed for {}".format(ERR_BASELINE_OBSERVATION_INVALID, prompt_id))
        expected_hash = "sha256:" + hashlib.sha256(observation["answer_text"].encode("utf-8")).hexdigest()
        if observation["answer_hash"] != expected_hash:
            errors.append("{}: answer hash mismatch for {}".format(ERR_BASELINE_OBSERVATION_INVALID, prompt_id))
        excluded = observation.get("exclusion_reason")
        failed = observation.get("execution_status", "valid") != "valid"
        if failed or not observation["evidence_complete"]:
            if not _nonempty(excluded):
                errors.append("{}: missing exclusion reason for {}".format(ERR_BASELINE_OBSERVATION_INVALID, prompt_id))
        elif not _nonempty(excluded) and (
            not observation["answer_text"].strip()
            or observation["source_kind"] != "model-answer"
            or (observation["network_status"] == "verified" and not _nonempty(observation["network_evidence"]))
        ):
            errors.append("{}: missing answer evidence for {}".format(ERR_BASELINE_OBSERVATION_INVALID, prompt_id))
        window = baseline.get("captured_window") or {}
        try:
            captured_at = parse_datetime(observation["captured_at"])
            if not parse_datetime(window["start"]) <= captured_at <= parse_datetime(window["end"]):
                errors.append("{}: captured outside baseline window for {}".format(ERR_BASELINE_OBSERVATION_INVALID, prompt_id))
            if question and captured_at < parse_datetime(question["frozen_at"]):
                errors.append("{}: captured before question freeze for {}".format(ERR_BASELINE_OBSERVATION_INVALID, prompt_id))
        except (KeyError, TypeError, ValueError):
            errors.append("{}: invalid capture window for {}".format(ERR_BASELINE_OBSERVATION_INVALID, prompt_id))
        for field in ("facts_version", "rubric_version"):
            if observation.get(field) != (experiment or {}).get(field):
                errors.append("{}: {} mismatch for {}".format(ERR_BASELINE_OBSERVATION_INVALID, field, prompt_id))
        if observation.get("phase") != "baseline":
            errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_PHASE, prompt_id or "?"))
        if observation.get("question_version") != expected_version:
            errors.append("{}: {}".format(ERR_BASELINE_OBSERVATION_QUESTION_VERSION, prompt_id or "?"))
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


def window_duration(window: Dict[str, Any]) -> timedelta:
    return parse_datetime(window["end"]) - parse_datetime(window["start"])


def windows_equal(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    return parse_datetime(left["start"]) == parse_datetime(right["start"]) and parse_datetime(
        left["end"]
    ) == parse_datetime(right["end"])


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
    """Compatibility projection; the attribution module owns calculations."""
    events = list(events)
    real = [event for event in events if not event.get("is_test")]
    report = analyze_attribution({"imports": [{"events": real, "coverage": "unknown"}]})
    counts = report["event_counts"]
    tests = _zero_counts()
    sources = _zero_sources()
    for event in events:
        if event.get("is_test") and event.get("type") in tests:
            tests[event["type"]] += 1
        elif not event.get("is_test") and event.get("source_type") in sources:
            sources[event["source_type"]] += 1
    return {
        "counts": counts, "test_counts": tests,
        "test_event_count": sum(bool(event.get("is_test")) for event in events),
        "revenue_by_currency": {code: item["amount_minor"] for code, item in report["views"]["order_total"].items()},
        "source_type_counts": sources,
        "signup_rate": None, "signup_rate_reason": "missing visits" if not counts["visit"] else "missing identity",
        "purchase_rate": None, "purchase_rate_reason": "missing identity",
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


def analyze_business(records: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Any]:
    """Read old records, but never infer business windows from AI sampling."""
    document = records.get("business_events") or {"imports": []}
    experiment = records.get("experiment") or {}
    imports = list(document.get("imports") or [])
    seen_keys: Set[Tuple[Any, Any]] = set()
    analyzed = [_analyze_import(batch, experiment.get("site_domain"), seen_keys) for batch in imports]
    # Keep the legacy import diagnostics, using them to exclude invalid rows once.
    cleaned = []
    for batch, summary in zip(imports, analyzed):
        excluded = {row["external_id"] for row in summary["excluded_events"]}
        local_seen = set()
        events = []
        for event in batch.get("events", []):
            key = event.get("external_id")
            if key not in excluded and key not in local_seen:
                events.append(event)
                local_seen.add(key)
        cleaned.append({**batch, "events": events})
    report = analyze_attribution({**document, "imports": cleaned}, experiment_doc=experiment)
    labels = {"outside_window": "窗口外", "other_site": "其他站点", "duplicate_event": "重复记录"}
    exclusions = {key: sum(item["excluded_counts"][key] for item in analyzed) for key in labels}
    if any(exclusions.values()):
        report["limitations"].append("未计入：" + "，".join(
            "{} {} 条".format(labels[key], count) for key, count in exclusions.items() if count))
    return {
        "status": "analyzed" if imports else "not_measured", "imports": analyzed,
        "flags": {"overlapping_windows": _overlapping_pairs(imports)},
        "comparison": report["comparison"], "attribution": report,
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


def _derived_measurement_table(
    report: Dict[str, Any], experiment: Dict[str, Any], questions: Optional[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """Render the associated question and structured counts, never cached display prose."""
    question_map = {item["question_id"]: item for item in (questions or {}).get("questions", [])}
    group_fields = ("round_id", "phase", "prompt_id", "observation_line", "platform", "terminal")
    groups = {}
    for group in report.get("rounds") or []:
        key = tuple(group[field] for field in group_fields)
        if key in groups:
            raise MeasurementReportError(["measurement report has duplicate round groups"])
        groups[key] = group

    def side_text(pair: Dict[str, Any], side: str) -> str:
        counts = pair[side]
        if counts["correct"] > counts["valid_answers"] or counts["valid_slots"] > counts["planned_slots"]:
            raise MeasurementReportError(["measurement pair counts are inconsistent"])
        round_id = pair["baseline_round_id" if side == "baseline" else "after_round_id"]
        if round_id is None:
            return "未测"
        phase = "baseline" if side == "baseline" else pair["phase"]
        key = (round_id, phase, pair["prompt_id"], pair["observation_line"], pair["platform"], pair["terminal"])
        group = groups.get(key)
        if group is not None:
            full = group["counts"]
            if any(full[field] != counts[field] for field in counts):
                raise MeasurementReportError(["measurement round counts do not match pair counts"])
            if (
                full["judged_answers"] + full["unjudged_answers"] != full["valid_answers"]
                or full["correct"] > full["judged_answers"]
                or full["valid_answers"] + full["technical_failures"] > full["attempts"]
            ):
                raise MeasurementReportError(["measurement round counts are inconsistent"])
            return format_stage_side(full)
        if groups:
            raise MeasurementReportError(["measurement pair has no matching round group"])
        # Older reports contain only pair counts: do not invent attempts or judgement coverage.
        return "正确标注 {}/{} 条有效回答 · 有效样本位 {}/{}（未附判读与尝试明细）".format(
            counts["correct"], counts["valid_answers"], counts["valid_slots"], counts["planned_slots"]
        )

    rows = []
    for pair in report.get("pairs") or []:
        question = question_map.get(pair["prompt_id"])
        if questions is not None and (
            question is None or question["observation_line"] != pair["observation_line"]
        ):
            raise MeasurementReportError(["measurement question does not match the frozen project questions"])
        question_text = " ".join(question["text"].split()) if question else "问题内容未关联"
        rows.append({
            "label": "{} · {} {} · {}".format(
                LINE_LABELS[pair["observation_line"]], pair["platform"],
                TERMINAL_LABELS.get(pair["terminal"], pair["terminal"]), question_text,
            ),
            "baseline": side_text(pair, "baseline"),
            "after": side_text(pair, "after"),
            "basis": "本项目题目版本 {}；两轮计数来自已关联的测量记录".format(experiment["questions_version"]),
            "result": VERDICT_LABELS[pair["verdict"]],
        })
    return rows


def accept_measurement_report(
    report: Dict[str, Any], experiment: Dict[str, Any], questions: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if not isinstance(report, dict):
        raise MeasurementReportError(["measurement report must be a JSON object"])
    try:
        validate_instance(_schema_instance_for_measurement(report), "measurement-report.schema.json")
    except SchemaValidationError as exc:
        raise MeasurementReportError([str(exc)]) from exc
    errors = _measurement_association_errors(report, experiment or {})
    if errors:
        raise MeasurementReportError(errors)
    return {**report, "stage_table": _derived_measurement_table(report, experiment, questions)}


def render_report(project_dir: Any, measurement_report: Optional[Dict[str, Any]] = None) -> str:
    records = load_project(project_dir)
    experiment = records["experiment"] or {}
    accepted = None
    if measurement_report is not None:
        accepted = accept_measurement_report(measurement_report, experiment, records.get("questions"))
        if accepted.get("pairs") and records.get("questions") is None:
            raise MeasurementReportError(["project questions are required for a measurement comparison"])
    analysis = analyze_business(records)
    next_step = experiment.get("next_step") or "先查看当前进度，再决定下一件要改的事。"
    return _fill_template(
        {
            "pages_and_facts": _pages_and_facts(records),
            "ai_changes": _ai_changes(accepted),
            "not_yet": _not_yet(records),
            "business": render_business_report(analysis["attribution"]),
            "next_item": next_step,
            "stage_table": _stage_table(accepted),
            "denominators": "",
            "business_limits": "",
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
