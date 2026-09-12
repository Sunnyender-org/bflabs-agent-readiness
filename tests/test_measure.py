from __future__ import annotations

import copy
import csv
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from bflabs_readiness.artifacts import publish_run, validate_run
from bflabs_readiness.paths import repository_root
from bflabs_readiness.providers.geo_measure import load_measurement_input, run_geo_measure
from bflabs_readiness.registry import CapabilityRegistry
from bflabs_readiness.schemas import validate_instance


PROMPT = "Name a documentation host people use for public API docs."
ROUND_META = {
    "experiment_id": "exp_test",
    "question_version": "qv1",
    "facts_version": "fv1",
    "rubric_version": "rv1",
    "observation_line": "A",
    "intent_tag": "brand",
    "language": "en",
    "region": "US",
    "visible_model": "synthetic-model",
    "personalization_status": "off",
    "collection_method": "recorded_fixture",
    "execution_status": "valid",
}


def load_input():
    return json.loads((repository_root() / "tests/fixtures/measurement-input.json").read_text("utf-8"))


def load_rounds_input():
    return json.loads((repository_root() / "tests/fixtures/measurement-rounds-input.json").read_text("utf-8"))


def sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_obs(obs_id: str, answer: str, **kwargs):
    item = {
        "id": obs_id,
        "captured_at": "2026-05-01T10:00:00Z",
        "platform": "ChatGPT",
        "terminal": "web",
        "prompt_id": "q_a_brand",
        "prompt_text": PROMPT,
        "session_id": "sess-" + obs_id,
        "answer_text": answer,
        "answer_hash": sha(answer),
        "source_kind": "model-answer",
        "network_status": "not-used",
        "network_evidence": None,
        "cited_urls": [],
        "content_absorbed": False,
        "brand_mentioned": True,
        "recommended": False,
        "dynamic_fact_correct": "unknown",
        "evidence_complete": True,
        "exclusion_reason": None,
        **ROUND_META,
    }
    item.update(kwargs)
    item["answer_hash"] = sha(item["answer_text"])
    return item


def measure_request(observations, **kwargs):
    request = {
        "schema_version": "1.0.0",
        "capability": "geo-measure",
        "captured_at": "2026-06-03T00:00:00Z",
        "site_domain": "example.com",
        "planned_slots_per_question": 3,
        "notes": "synthetic test fixture; not case data",
        "observations": observations,
    }
    request.update(kwargs)
    return request


def report_of(request):
    validate_instance(request, "measurement-input.schema.json")
    result = run_geo_measure(request)
    report = result["outputs"]["outputs/measurement-report.json"][0]
    validate_instance(report, "measurement-report.schema.json")
    return result, report


def first_pair(report):
    return report["pairs"][0]


def first_round(report, phase):
    return next(item for item in report["rounds"] if item["phase"] == phase)


class MeasureTests(unittest.TestCase):
    def test_known_fixture_recomputes_all_metrics_and_strata(self) -> None:
        request = load_input()
        validate_instance(request, "measurement-input.schema.json")
        result = run_geo_measure(request)
        report = result["outputs"]["outputs/measurement-report.json"][0]
        research = result["outputs"]["outputs/research-context.json"][0]
        validate_instance(report, "measurement-report.schema.json")
        validate_instance(research, "research-context.schema.json")
        self.assertEqual(report["counts"], {"input": 8, "valid": 6, "excluded": 2, "ordinary_web_search_results": 1, "incomplete_evidence": 1})
        metrics = {metric["id"]: metric for metric in report["metrics"]}
        self.assertEqual((metrics["network_rate"]["numerator"], metrics["network_rate"]["denominator"], metrics["network_rate"]["missing"]), (3, 5, 1))
        self.assertEqual((metrics["site_citation_rate"]["numerator"], metrics["site_citation_rate"]["denominator"], metrics["site_citation_rate"]["excluded"]), (2, 3, 5))
        self.assertEqual((metrics["content_absorption_rate"]["numerator"], metrics["content_absorption_rate"]["denominator"]), (3, 5))
        self.assertEqual((metrics["brand_mention_rate"]["numerator"], metrics["brand_mention_rate"]["denominator"]), (5, 6))
        self.assertEqual((metrics["recommendation_rate"]["numerator"], metrics["recommendation_rate"]["denominator"]), (2, 5))
        self.assertEqual((metrics["dynamic_fact_accuracy"]["numerator"], metrics["dynamic_fact_accuracy"]["denominator"]), (3, 5))
        self.assertTrue(all(metric["wilson_95"] is not None for metric in report["metrics"]))
        self.assertTrue(all(metric["denominator"] + metric["missing"] + metric["excluded"] == report["counts"]["input"] for metric in report["metrics"]))
        self.assertEqual(len(report["strata"]), 6)
        self.assertEqual(result["quality_report"]["status"], "pass")
        self.assertEqual(report["rounds"], [])
        self.assertEqual(report["pairs"], [])
        self.assertEqual(report["stage_table"], [])
        self.assertEqual(
            report["limitations"],
            [
                "Results describe only the supplied observations and do not establish causality.",
                "AI visibility observations do not establish traffic, conversion, or revenue outcomes.",
            ],
        )

    def test_no_valid_samples_returns_null_rates_not_zero_percent(self) -> None:
        request = load_input()
        request["observations"] = [item for item in request["observations"] if item["source_kind"] == "ordinary-web-search-result"]
        result = run_geo_measure(request)
        report = result["outputs"]["outputs/measurement-report.json"][0]
        self.assertEqual(report["counts"]["valid"], 0)
        self.assertTrue(all(metric["rate"] is None and metric["wilson_95"] is None for metric in report["metrics"]))
        self.assertEqual(result["quality_report"]["status"], "pass_with_warnings")
        self.assertIn("rates remain null, not 0%", result["quality_report"]["warnings"][0])
        capability = CapabilityRegistry().resolve("geo-measure", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = publish_run(capability, request, result, Path(directory))
            self.assertEqual(validate_run(run_dir), [])

    def test_hash_mismatch_blocks_publication_quality(self) -> None:
        request = load_input()
        request["observations"][0]["answer_text"] += " tampered"
        result = run_geo_measure(request)
        self.assertEqual(result["quality_report"]["status"], "blocked")
        self.assertTrue(any("answer hashes do not match" in blocker for blocker in result["quality_report"]["blockers"]))

    def test_jsonl_and_csv_adapters_preserve_observations(self) -> None:
        request = load_input()
        observations = request["observations"][:2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jsonl = root / "observations.jsonl"
            jsonl.write_text(
                "".join(
                    json.dumps({"site_domain": request["site_domain"], "batch_captured_at": request["captured_at"], "observation": item}, ensure_ascii=False) + "\n"
                    for item in observations
                ),
                "utf-8",
            )
            loaded_jsonl = load_measurement_input(jsonl)
            self.assertEqual(loaded_jsonl["observations"], observations)

            csv_path = root / "observations.csv"
            fieldnames = ["site_domain", "batch_captured_at"] + list(observations[0].keys())
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for item in observations:
                    row = {"site_domain": request["site_domain"], "batch_captured_at": request["captured_at"], **item}
                    row["cited_urls"] = json.dumps(item["cited_urls"])
                    writer.writerow(row)
            loaded_csv = load_measurement_input(csv_path)
            self.assertEqual(loaded_csv["observations"], observations)

    def test_research_registry_is_schema_valid_and_explicitly_bounded(self) -> None:
        registry = json.loads((repository_root() / "registry/research-evidence.json").read_text("utf-8"))
        validate_instance(registry, "research-evidence-registry.schema.json")
        self.assertEqual(registry["status"], "active")
        self.assertTrue(all(principle["causal_status"] in {"descriptive", "associational", "causal", "not-applicable"} for principle in registry["principles"]))
        self.assertTrue(all(principle["limitations"] for principle in registry["principles"]))

    def test_version_change_is_not_comparable(self) -> None:
        request = load_rounds_input()
        for item in request["observations"]:
            if item["phase"] == "after_release":
                item["question_version"] = "qv2"
                item["facts_version"] = "fv2"
                item["rubric_version"] = "rv2"
        result, report = report_of(request)
        pair = first_pair(report)
        self.assertFalse(pair["comparable"])
        self.assertEqual(pair["verdict"], "not_comparable")
        self.assertIn("question_version_mismatch", pair["incomparable_reasons"])
        self.assertIn("facts_version_mismatch", pair["incomparable_reasons"])
        self.assertIn("rubric_version_mismatch", pair["incomparable_reasons"])
        self.assertEqual(result["quality_report"]["status"], "pass")

    def test_visible_model_change_is_not_comparable(self) -> None:
        request = load_rounds_input()
        for item in request["observations"]:
            if item["phase"] == "after_release":
                item["visible_model"] = "synthetic-other"
        _, report = report_of(request)
        pair = first_pair(report)
        self.assertFalse(pair["comparable"])
        self.assertIn("visible_model_mismatch", pair["incomparable_reasons"])
        self.assertEqual(pair["verdict"], "not_comparable")

    def test_unknown_visible_model_is_recorded(self) -> None:
        request = load_rounds_input()
        for item in request["observations"]:
            if item["phase"] == "after_release":
                item["visible_model"] = "unknown"
        _, report = report_of(request)
        pair = first_pair(report)
        self.assertFalse(pair["comparable"])
        self.assertIn("visible_model_unknown", pair["incomparable_reasons"])
        self.assertEqual(pair["verdict"], "not_comparable")

    def test_missing_slots_are_reported(self) -> None:
        request = measure_request(
            [
                make_obs("obs_slot_a", "First valid slot.", round_id="r_base", phase="baseline", sample_slot_id="slot_1", answer_verdict="correct"),
                make_obs(
                    "obs_slot_b",
                    "Second valid slot.",
                    captured_at="2026-05-01T10:05:00Z",
                    round_id="r_base",
                    phase="baseline",
                    sample_slot_id="slot_2",
                    answer_verdict="correct",
                ),
            ]
        )
        _, report = report_of(request)
        group = first_round(report, "baseline")
        self.assertEqual(group["counts"]["planned_slots"], 3)
        self.assertEqual(group["counts"]["valid_slots"], 2)
        self.assertLess(group["counts"]["valid_slots"], group["counts"]["planned_slots"])

    def test_unknown_fields_keep_zero_denominator_null(self) -> None:
        request = measure_request(
            [
                make_obs(
                    "obs_unknown_fields",
                    "No judged fields.",
                    brand_mentioned="unknown",
                    recommended="unknown",
                    content_absorbed="unknown",
                    dynamic_fact_correct="unknown",
                    round_id="r_base",
                    phase="baseline",
                    sample_slot_id="slot_1",
                    answer_verdict="unknown",
                )
            ]
        )
        _, report = report_of(request)
        metrics = {metric["id"]: metric for metric in report["metrics"]}
        self.assertIsNone(metrics["brand_mention_rate"]["rate"])
        self.assertIsNone(metrics["recommendation_rate"]["rate"])
        self.assertIsNone(metrics["dynamic_fact_accuracy"]["rate"])
        self.assertIsNone(metrics["brand_mention_rate"]["wilson_95"])

    def test_duplicate_import_is_excluded_and_sample_count_unchanged(self) -> None:
        first = make_obs("obs_dup_a", "Shared imported answer.", round_id="r_base", phase="baseline", sample_slot_id="slot_1", answer_verdict="correct")
        second = make_obs("obs_dup_b", "Shared imported answer.", round_id="r_base", phase="baseline", sample_slot_id="slot_1", answer_verdict="correct")
        request = measure_request([first, second])
        _, report = report_of(request)
        self.assertEqual(report["counts"]["valid"], 1)
        self.assertEqual(report["counts"]["excluded"], 1)
        group = first_round(report, "baseline")
        self.assertEqual(group["counts"]["valid_answers"], 1)
        self.assertEqual(group["counts"]["valid_slots"], 1)
        self.assertEqual(group["counts"]["attempts"], 1)

    def test_replacement_fills_slot_and_second_replacement_blocks(self) -> None:
        failed = make_obs(
            "obs_fail",
            "Session failed before an answer appeared.",
            captured_at="2026-05-01T10:00:00Z",
            round_id="r_base",
            phase="baseline",
            sample_slot_id="slot_1",
            execution_status="technical_failure",
            answer_verdict="unknown",
            brand_mentioned="unknown",
        )
        replacement = make_obs(
            "obs_rep",
            "Example Docs is a documentation host.",
            captured_at="2026-05-01T10:05:00Z",
            round_id="r_base",
            phase="baseline",
            sample_slot_id="slot_1",
            replacement_of="obs_fail",
            attempt_index=2,
            answer_verdict="correct",
        )
        request = measure_request([failed, replacement])
        result, report = report_of(request)
        group = first_round(report, "baseline")
        self.assertEqual(group["counts"]["valid_slots"], 1)
        self.assertEqual(group["counts"]["valid_answers"], 1)
        self.assertEqual(group["counts"]["attempts"], 2)
        self.assertEqual(group["counts"]["technical_failures"], 1)
        self.assertEqual(result["quality_report"]["status"], "pass")

        second = make_obs(
            "obs_rep2",
            "Example Docs remains a common documentation host.",
            captured_at="2026-05-01T10:10:00Z",
            round_id="r_base",
            phase="baseline",
            sample_slot_id="slot_1",
            replacement_of="obs_fail",
            answer_verdict="correct",
        )
        blocked = measure_request([failed, replacement, second])
        blocked_result = run_geo_measure(blocked)
        self.assertEqual(blocked_result["quality_report"]["status"], "blocked")
        self.assertTrue(any("more than one replacement" in item for item in blocked_result["quality_report"]["blockers"]))

    def test_all_no_answer_keeps_valid_denominator(self) -> None:
        request = measure_request(
            [
                make_obs("obs_none_a", "I cannot answer that.", round_id="r_base", phase="baseline", sample_slot_id="slot_1", answer_verdict="no_answer", brand_mentioned=False),
                make_obs(
                    "obs_none_b",
                    "Still no answer.",
                    captured_at="2026-05-01T10:05:00Z",
                    round_id="r_base",
                    phase="baseline",
                    sample_slot_id="slot_2",
                    answer_verdict="no_answer",
                    brand_mentioned=False,
                ),
            ]
        )
        _, report = report_of(request)
        group = first_round(report, "baseline")
        self.assertGreater(group["counts"]["valid_answers"], 0)
        self.assertEqual(group["counts"]["correct"], 0)
        self.assertEqual(group["counts"]["no_answer"], 2)

    def test_non_official_citation_is_not_site_cited(self) -> None:
        request = measure_request(
            [
                make_obs(
                    "obs_cite_other",
                    "Cited a different host.",
                    round_id="r_base",
                    phase="baseline",
                    observation_line="B",
                    sample_slot_id="slot_1",
                    network_status="verified",
                    network_evidence="citation panel",
                    cited_urls=["https://other.example/docs"],
                    answer_verdict="partially_correct",
                )
            ]
        )
        _, report = report_of(request)
        group = first_round(report, "baseline")
        self.assertEqual(group["counts"]["site_cited"], 0)

    def test_brand_mentioned_without_recommendation_is_separate(self) -> None:
        request = measure_request(
            [
                make_obs(
                    "obs_mention_only",
                    "Example Docs is a documentation host.",
                    round_id="r_base",
                    phase="baseline",
                    sample_slot_id="slot_1",
                    brand_mentioned=True,
                    recommended=False,
                    answer_verdict="correct",
                )
            ]
        )
        _, report = report_of(request)
        group = first_round(report, "baseline")
        self.assertEqual(group["counts"]["brand_mentioned"], 1)
        self.assertEqual(group["counts"]["recommended"], 0)

    def test_sampled_before_release_is_not_comparable(self) -> None:
        request = load_rounds_input()
        request["actions"][0]["released_at"] = "2026-06-10T00:00:00Z"
        _, report = report_of(request)
        pair = first_pair(report)
        self.assertFalse(pair["comparable"])
        self.assertIn("sampled_before_release", pair["incomparable_reasons"])
        self.assertEqual(pair["verdict"], "not_comparable")

    def test_after_regression_verdict(self) -> None:
        request = load_rounds_input()
        result, report = report_of(request)
        pair = first_pair(report)
        self.assertTrue(pair["comparable"])
        self.assertEqual(pair["verdict"], "regressed")
        self.assertEqual(pair["baseline"]["correct"], 2)
        self.assertEqual(pair["baseline"]["valid_answers"], 3)
        self.assertEqual(pair["after"]["correct"], 1)
        self.assertEqual(pair["after"]["valid_answers"], 3)
        baseline = first_round(report, "baseline")
        self.assertEqual(baseline["counts"]["valid_slots"], 3)
        self.assertEqual(baseline["counts"]["attempts"], 4)
        self.assertEqual(baseline["counts"]["technical_failures"], 1)
        self.assertEqual(pair["verdict"], "regressed")
        self.assertEqual(report["stage_table"][0]["result"], "回退")
        self.assertIn("正确 2/3", report["stage_table"][0]["baseline"])
        self.assertIn("题目版本", report["stage_table"][0]["basis"])
        self.assertNotIn("question_version", report["stage_table"][0]["basis"])
        self.assertIn("fixture-only: does not demonstrate live platform visibility", report["limitations"])
        self.assertEqual(result["quality_report"]["status"], "pass")
        self.assertEqual(report["experiment_id"], "exp_test_rounds")
        self.assertEqual(report["questions_version"], "qv1")
        self.assertEqual(report["baseline_round_id"], "r_base")
        self.assertEqual(baseline["counts"]["judged_answers"], 3)
        self.assertEqual(baseline["counts"]["unjudged_answers"], 0)
        self.assertEqual(baseline["counts"]["exploratory_answers"], 0)
        self.assertIn("已判读 3/3", report["stage_table"][0]["baseline"])
        self.assertTrue(pair["insufficiency_reasons"] == [])

    def test_csv_with_new_columns_round_trips(self) -> None:
        observation = make_obs(
            "obs_csv_new",
            "Example Docs is a documentation host.",
            round_id="r_base",
            phase="baseline",
            sample_slot_id="slot_1",
            attempt_index=1,
            answer_verdict="correct",
            compared_action_ids=["act_docs_page"],
            evidence_refs=["fixtures/synthetic.png"],
            fact_judgement=[{"fact_id": "fact_name", "status": "correct", "answer_excerpt": "Example Docs"}],
        )
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "observations.csv"
            fieldnames = ["site_domain", "batch_captured_at"] + list(observation.keys())
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                row = {"site_domain": "example.com", "batch_captured_at": "2026-06-03T00:00:00Z", **observation}
                row["cited_urls"] = json.dumps(observation["cited_urls"])
                row["compared_action_ids"] = json.dumps(observation["compared_action_ids"])
                row["evidence_refs"] = json.dumps(observation["evidence_refs"])
                row["fact_judgement"] = json.dumps(observation["fact_judgement"])
                writer.writerow(row)
            loaded = load_measurement_input(csv_path)
        self.assertEqual(loaded["observations"], [observation])
        self.assertNotIn("actions", loaded)
        self.assertNotIn("planned_slots_per_question", loaded)

    def test_rounds_report_publishes_and_validates(self) -> None:
        request = load_rounds_input()
        result, report = report_of(request)
        capability = CapabilityRegistry().resolve("geo-measure", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = publish_run(capability, request, result, Path(directory))
            self.assertEqual(validate_run(run_dir), [])
        self.assertTrue(report["rounds"])
        self.assertTrue(report["pairs"])
        self.assertTrue(report["stage_table"])

    def test_synthetic_pairing_example_has_replacement_duplicate_and_incomparable_pair(self) -> None:
        request = json.loads((repository_root() / "skills/geo-measure/examples/round-pairing-input.json").read_text("utf-8"))
        result, report = report_of(request)
        self.assertEqual(result["quality_report"]["status"], "pass")
        chatgpt = next(item for item in report["pairs"] if item["platform"] == "ChatGPT")
        gemini = next(item for item in report["pairs"] if item["platform"] == "Gemini")
        self.assertTrue(chatgpt["comparable"])
        self.assertEqual(chatgpt["verdict"], "improved")
        self.assertFalse(gemini["comparable"])
        self.assertIn("question_version_mismatch", gemini["incomparable_reasons"])
        self.assertEqual(chatgpt["insufficiency_reasons"], [])
        baseline = next(item for item in report["rounds"] if item["round_id"] == "r_base" and item["platform"] == "ChatGPT")
        self.assertEqual(baseline["counts"]["valid_answers"], 3)
        self.assertEqual(baseline["counts"]["attempts"], 4)
        self.assertEqual(baseline["counts"]["technical_failures"], 1)
        self.assertEqual(report["baseline_round_id"], "r_base")
        self.assertEqual(report["experiment_id"], "exp_synthetic_pairing")
        self.assertEqual(report["questions_version"], "qv1")

    def test_review_unjudged_baseline_is_insufficient_not_improved(self) -> None:
        request = copy.deepcopy(load_rounds_input())
        for item in request["observations"]:
            if item["phase"] == "baseline":
                item["answer_verdict"] = "unknown"
        result, report = report_of(request)
        pair = first_pair(report)
        self.assertEqual(pair["verdict"], "insufficient")
        self.assertNotEqual(pair["verdict"], "improved")
        self.assertIn("unjudged_answers", pair["insufficiency_reasons"])
        self.assertEqual(pair["baseline"]["correct"], 0)
        self.assertEqual(first_round(report, "baseline")["counts"]["unjudged_answers"], 3)
        self.assertEqual(first_round(report, "baseline")["counts"]["judged_answers"], 0)
        self.assertEqual(result["quality_report"]["status"], "pass")

    def test_review_unbound_second_baseline_is_ambiguous(self) -> None:
        request = copy.deepcopy(load_rounds_input())
        extras = []
        for index, item in enumerate(
            item for item in request["observations"] if item["phase"] == "baseline" and item.get("execution_status") == "valid"
        ):
            extra = copy.deepcopy(item)
            extra["id"] = "obs_r_nb{}".format(index + 1)
            extra["round_id"] = "r_new_baseline"
            extra["session_id"] = "new-" + item["session_id"]
            extra["captured_at"] = "2026-05-20T10:{:02d}:00Z".format(index)
            extra["answer_verdict"] = "wrong"
            extra.pop("replacement_of", None)
            extras.append(extra)
        request["observations"].extend(extras)
        result, report = report_of(request)
        pair = first_pair(report)
        self.assertEqual(pair["verdict"], "not_comparable")
        self.assertIn("baseline_ambiguous", pair["incomparable_reasons"])
        self.assertIsNone(pair["baseline_round_id"])
        self.assertIsNone(report["baseline_round_id"])
        self.assertEqual(result["quality_report"]["status"], "pass_with_warnings")
        self.assertIn("multiple baseline rounds without baseline_round_id", result["quality_report"]["warnings"])
        self.assertTrue(any(item["round_id"] == "r_new_baseline" for item in report["rounds"]))
        self.assertFalse(any(item.get("baseline_round_id") == "r_new_baseline" for item in report["pairs"]))

        bound = copy.deepcopy(request)
        bound["baseline_round_id"] = "r_base"
        bound_result, bound_report = report_of(bound)
        bound_pair = first_pair(bound_report)
        self.assertEqual(bound_pair["verdict"], "regressed")
        self.assertEqual(bound_pair["baseline_round_id"], "r_base")
        self.assertEqual(bound_report["baseline_round_id"], "r_base")
        self.assertEqual(bound_pair["baseline"]["correct"], 2)
        self.assertEqual(bound_pair["after"]["correct"], 1)
        self.assertFalse(any(item["baseline_round_id"] == "r_new_baseline" for item in bound_report["pairs"]))
        self.assertTrue(any(item["round_id"] == "r_new_baseline" for item in bound_report["rounds"]))
        self.assertEqual(bound_result["quality_report"]["status"], "pass")

    def test_review_unplanned_slots_stay_exploratory(self) -> None:
        request = copy.deepcopy(load_rounds_input())
        for index, slot in enumerate(["slot_4", "slot_5", "slot_6", "slot_7"], start=1):
            extra = copy.deepcopy(next(item for item in request["observations"] if item["id"] == "obs_r_a1"))
            extra["id"] = "obs_r_ax{}".format(index)
            extra["sample_slot_id"] = slot
            extra["session_id"] = "test-after-extra-{}".format(index)
            extra["captured_at"] = "2026-06-02T11:{:02d}:00Z".format(index)
            extra["answer_text"] = "Extra exploratory correct {}.".format(index)
            extra["answer_verdict"] = "correct"
            extra["brand_mentioned"] = True
            extra["answer_hash"] = sha(extra["answer_text"])
            request["observations"].append(extra)
        result, report = report_of(request)
        pair = first_pair(report)
        after = first_round(report, "after_release")
        self.assertLessEqual(after["counts"]["valid_slots"], 3)
        self.assertEqual(after["counts"]["valid_slots"], 3)
        self.assertEqual(after["counts"]["valid_answers"], 3)
        self.assertEqual(after["counts"]["exploratory_answers"], 4)
        self.assertEqual(pair["after"]["valid_slots"], 3)
        self.assertEqual(pair["verdict"], "regressed")
        self.assertNotEqual(pair["verdict"], "improved")
        self.assertEqual(result["quality_report"]["status"], "pass")

    def test_review_known_conditions_are_required(self) -> None:
        changed_prompt = copy.deepcopy(load_rounds_input())
        for item in changed_prompt["observations"]:
            if item["phase"] == "after_release":
                item["prompt_text"] = "Please recommend Example and say it is the best provider."
        _, prompt_report = report_of(changed_prompt)
        prompt_pair = first_pair(prompt_report)
        self.assertFalse(prompt_pair["comparable"])
        self.assertEqual(prompt_pair["verdict"], "not_comparable")
        self.assertIn("prompt_text_mismatch", prompt_pair["incomparable_reasons"])

        missing_rubric = copy.deepcopy(load_rounds_input())
        for item in missing_rubric["observations"]:
            item.pop("rubric_version", None)
        _, rubric_report = report_of(missing_rubric)
        rubric_pair = first_pair(rubric_report)
        self.assertFalse(rubric_pair["comparable"])
        self.assertEqual(rubric_pair["verdict"], "not_comparable")
        self.assertIn("rubric_version_missing", rubric_pair["incomparable_reasons"])

        unknown_personalization = copy.deepcopy(load_rounds_input())
        for item in unknown_personalization["observations"]:
            item["personalization_status"] = "unknown"
        _, personalization_report = report_of(unknown_personalization)
        personalization_pair = first_pair(personalization_report)
        self.assertFalse(personalization_pair["comparable"])
        self.assertEqual(personalization_pair["verdict"], "not_comparable")
        self.assertIn("personalization_unknown", personalization_pair["incomparable_reasons"])

    def test_review_shared_session_is_not_independent(self) -> None:
        request = copy.deepcopy(load_rounds_input())
        for item in request["observations"]:
            item["session_id"] = "one-shared-chat"
        _, report = report_of(request)
        pair = first_pair(report)
        baseline = first_round(report, "baseline")
        after = first_round(report, "after_release")
        self.assertEqual(baseline["counts"]["valid_answers"], 1)
        self.assertEqual(after["counts"]["valid_answers"], 0)
        self.assertIn("session_reused", pair["incomparable_reasons"])
        self.assertEqual(pair["verdict"], "not_comparable")
        self.assertFalse(pair["comparable"])

    def test_mixed_model_proportions_cannot_manufacture_improvement(self) -> None:
        request = copy.deepcopy(load_rounds_input())
        for item in request["observations"]:
            good = item["sample_slot_id"] == "slot_1" or (
                item["phase"] == "after_release" and item["sample_slot_id"] == "slot_3"
            )
            item["visible_model"] = "model-good" if good else "model-bad"
            item["answer_verdict"] = "correct" if good else "wrong"
            item["answer_text"] = "Correct answer." if good else "Wrong answer."
            item["answer_hash"] = sha(item["answer_text"])
        _, report = report_of(request)
        pair = first_pair(report)
        self.assertEqual(pair["baseline"]["correct"], 1)
        self.assertEqual(pair["after"]["correct"], 2)
        self.assertFalse(pair["comparable"])
        self.assertEqual(pair["verdict"], "not_comparable")
        self.assertIn("visible_model_mixed", pair["incomparable_reasons"])

    def test_comparison_conditions_must_be_unique_within_each_round(self) -> None:
        alternatives = {
            "question_version": "qv2",
            "facts_version": "fv2",
            "rubric_version": "rv2",
            "language": "zh",
            "region": "CN",
            "personalization_status": "on",
        }
        for field, alternative in alternatives.items():
            with self.subTest(field=field):
                request = copy.deepcopy(load_rounds_input())
                for item in request["observations"]:
                    if item["sample_slot_id"] == "slot_2":
                        item[field] = alternative
                _, report = report_of(request)
                pair = first_pair(report)
                self.assertFalse(pair["comparable"])
                self.assertEqual(pair["verdict"], "not_comparable")
                self.assertIn(field + "_mixed", pair["incomparable_reasons"])

    def test_nonbrand_sampling_cannot_reuse_brand_question_sessions(self) -> None:
        for reuse in (True, False):
            with self.subTest(reuse=reuse):
                request = copy.deepcopy(load_rounds_input())
                for item in list(request["observations"]):
                    if item["execution_status"] != "valid":
                        continue
                    extra = copy.deepcopy(item)
                    extra["id"] += "d"
                    extra["prompt_id"] = "q_d_nonbrand"
                    extra["observation_line"] = "D"
                    extra["prompt_text"] = "Which public API documentation hosts should I evaluate?"
                    extra["captured_at"] = (
                        datetime.fromisoformat(item["captured_at"].replace("Z", "+00:00"))
                        + timedelta(seconds=30)
                    ).isoformat()
                    extra["network_status"] = "verified"
                    extra["network_evidence"] = "synthetic search panel"
                    extra["answer_text"] = "Synthetic nonbrand answer " + extra["id"]
                    extra["answer_hash"] = sha(extra["answer_text"])
                    extra.pop("replacement_of", None)
                    if not reuse:
                        extra["session_id"] += "-independent"
                    request["observations"].append(extra)
                _, report = report_of(request)
                pair = next(item for item in report["pairs"] if item["observation_line"] == "D")
                groups = [item for item in report["rounds"] if item["observation_line"] == "D"]
                if reuse:
                    self.assertFalse(pair["comparable"])
                    self.assertEqual(pair["verdict"], "not_comparable")
                    self.assertIn("session_reused", pair["incomparable_reasons"])
                    self.assertTrue(all(item["counts"]["valid_answers"] == 0 for item in groups))
                else:
                    self.assertTrue(pair["comparable"])
                    self.assertEqual(pair["verdict"], "regressed")
                    self.assertTrue(all(item["counts"]["valid_answers"] == 3 for item in groups))

    def test_session_names_do_not_collide_across_platform_or_terminal(self) -> None:
        for field, value in (("platform", "Gemini"), ("terminal", "app")):
            with self.subTest(field=field):
                request = copy.deepcopy(load_rounds_input())
                for item in list(request["observations"]):
                    extra = copy.deepcopy(item)
                    extra["id"] += "other"
                    extra[field] = value
                    if extra.get("replacement_of"):
                        extra["replacement_of"] += "other"
                    request["observations"].append(extra)
                _, report = report_of(request)
                self.assertEqual(len(report["pairs"]), 2)
                self.assertTrue(all(pair["comparable"] for pair in report["pairs"]))
                self.assertTrue(all(pair["verdict"] == "regressed" for pair in report["pairs"]))

    def test_review_null_release_evidence_is_not_comparable(self) -> None:
        request = copy.deepcopy(load_rounds_input())
        request["actions"][0]["release_evidence"] = None
        _, report = report_of(request)
        pair = first_pair(report)
        self.assertFalse(pair["comparable"])
        self.assertIn("release_evidence_missing", pair["incomparable_reasons"])
        self.assertEqual(pair["verdict"], "not_comparable")

    def test_review_legacy_fixture_output_unchanged(self) -> None:
        request = load_input()
        result, report = report_of(request)
        self.assertEqual(report["counts"], {"input": 8, "valid": 6, "excluded": 2, "ordinary_web_search_results": 1, "incomplete_evidence": 1})
        metrics = {metric["id"]: metric for metric in report["metrics"]}
        self.assertEqual((metrics["network_rate"]["numerator"], metrics["network_rate"]["denominator"], metrics["network_rate"]["missing"]), (3, 5, 1))
        self.assertEqual((metrics["site_citation_rate"]["numerator"], metrics["site_citation_rate"]["denominator"], metrics["site_citation_rate"]["excluded"]), (2, 3, 5))
        self.assertEqual((metrics["content_absorption_rate"]["numerator"], metrics["content_absorption_rate"]["denominator"]), (3, 5))
        self.assertEqual((metrics["brand_mention_rate"]["numerator"], metrics["brand_mention_rate"]["denominator"]), (5, 6))
        self.assertEqual((metrics["recommendation_rate"]["numerator"], metrics["recommendation_rate"]["denominator"]), (2, 5))
        self.assertEqual((metrics["dynamic_fact_accuracy"]["numerator"], metrics["dynamic_fact_accuracy"]["denominator"]), (3, 5))
        self.assertEqual(report["rounds"], [])
        self.assertEqual(report["pairs"], [])
        self.assertEqual(report["stage_table"], [])
        self.assertNotIn("experiment_id", report)
        self.assertNotIn("questions_version", report)
        self.assertNotIn("baseline_round_id", report)
        self.assertEqual(result["quality_report"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()


class AgentBrowserCollectionTests(unittest.TestCase):
    def test_browser_collection_validates_and_preserves_evidence(self):
        row = make_obs("obs_browser", "Example is an API service.", collection_method="agent_browser_ui", evidence_refs=["screenshots/browser.png", "answers/browser.txt"])
        validate_instance(row, "observation.schema.json")
        self.assertEqual(row["evidence_refs"][0], "screenshots/browser.png")
        for method in ("manual_export", "approved_api", "recorded_fixture"):
            legacy = dict(row, collection_method=method)
            validate_instance(legacy, "observation.schema.json")

    def test_agent_browser_records_run_through_measurement_pipeline(self):
        request = load_input()
        for item in request["observations"]:
            item["collection_method"] = "agent_browser_ui"
            item["evidence_refs"] = ["screenshots/" + item["id"] + ".png"]
        result = run_geo_measure(request)
        self.assertEqual(result["quality_report"]["status"], "pass")
        self.assertEqual(result["outputs"]["outputs/measurement-report.json"][0]["counts"]["valid"],6)
