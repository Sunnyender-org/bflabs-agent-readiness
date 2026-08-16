from __future__ import annotations

import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from bflabs_readiness.artifacts import publish_run, validate_run
from bflabs_readiness.paths import repository_root
from bflabs_readiness.providers.geo_measure import load_measurement_input, run_geo_measure
from bflabs_readiness.registry import CapabilityRegistry
from bflabs_readiness.schemas import validate_instance


def load_input():
    return json.loads((repository_root() / "tests/fixtures/measurement-input.json").read_text("utf-8"))


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


if __name__ == "__main__":
    unittest.main()
