from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
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
        self.assertEqual(report["stage_table"][0]["result"], "regressed")
        self.assertIn("正确 2/3", report["stage_table"][0]["baseline"])
        self.assertIn("fixture-only: does not demonstrate live platform visibility", report["limitations"])
        self.assertEqual(result["quality_report"]["status"], "pass")

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
        baseline = next(item for item in report["rounds"] if item["round_id"] == "r_base_chatgpt")
        self.assertEqual(baseline["counts"]["valid_answers"], 3)
        self.assertEqual(baseline["counts"]["attempts"], 4)
        self.assertEqual(baseline["counts"]["technical_failures"], 1)


if __name__ == "__main__":
    unittest.main()

