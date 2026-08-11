from __future__ import annotations

import json
import unittest

from bflabs_readiness.paths import repository_root
from bflabs_readiness.providers.geo_discover import DIMENSIONS, run_geo_discover
from bflabs_readiness.quality import evaluate_discovery
from bflabs_readiness.schemas import validate_instance


def load_brief():
    return json.loads((repository_root() / "skills/geo-discover/examples/beefapi-gpt-5-6-brief.json").read_text("utf-8"))


class DiscoverTests(unittest.TestCase):
    def test_discovery_outputs_all_dimensions_with_trace_and_no_volume_claim(self) -> None:
        result = run_geo_discover(load_brief())
        query_map = result["outputs"]["outputs/query-map.json"][0]
        opportunity_map = result["outputs"]["outputs/opportunity-map.json"][0]
        validate_instance(query_map, "query-map.schema.json")
        validate_instance(opportunity_map, "opportunity-map.schema.json")
        self.assertEqual({query["dimension"] for query in query_map["queries"]}, set(DIMENSIONS))
        self.assertTrue(all(query["trace"]["source_type"] in {"seed", "input", "assumption"} for query in query_map["queries"]))
        self.assertTrue(all(item["search_volume"] == {"status": "not_measured", "value": None} for item in opportunity_map["opportunities"]))
        self.assertEqual(result["quality_report"]["status"], "pass")

    def test_priority_scores_use_only_declared_formula(self) -> None:
        result = run_geo_discover(load_brief())
        opportunity_map = result["outputs"]["outputs/opportunity-map.json"][0]
        for item in opportunity_map["opportunities"]:
            self.assertEqual(item["priority_score"], item["coverage_gap"] + item["evidence_gap"] + item["business_relevance"])

    def test_search_volume_invention_blocks_quality(self) -> None:
        result = run_geo_discover(load_brief())
        query_map = result["outputs"]["outputs/query-map.json"][0]
        opportunity_map = result["outputs"]["outputs/opportunity-map.json"][0]
        opportunity_map["opportunities"][0]["search_volume"] = {"status": "measured", "value": 100}
        quality = evaluate_discovery(query_map, opportunity_map, result["evidence_ledger"])
        self.assertEqual(quality["status"], "blocked")
        self.assertIn("search volume was invented", quality["blockers"][0])

    def test_dangling_opportunity_trace_blocks_quality(self) -> None:
        result = run_geo_discover(load_brief())
        query_map = result["outputs"]["outputs/query-map.json"][0]
        opportunity_map = result["outputs"]["outputs/opportunity-map.json"][0]
        opportunity_map["opportunities"][0]["query_ids"] = ["qry_missing"]
        opportunity_map["opportunities"][0]["trace"]["source_query_ids"] = ["qry_missing"]
        quality = evaluate_discovery(query_map, opportunity_map, result["evidence_ledger"])
        self.assertEqual(quality["status"], "blocked")
        self.assertTrue(any("source-query trace" in blocker for blocker in quality["blockers"]))

    def test_duplicate_evidence_ids_block_quality(self) -> None:
        result = run_geo_discover(load_brief())
        query_map = result["outputs"]["outputs/query-map.json"][0]
        opportunity_map = result["outputs"]["outputs/opportunity-map.json"][0]
        result["evidence_ledger"]["items"].append(dict(result["evidence_ledger"]["items"][0]))
        quality = evaluate_discovery(query_map, opportunity_map, result["evidence_ledger"])
        self.assertEqual(quality["status"], "blocked")
        self.assertIn("duplicate evidence ids", quality["blockers"])


if __name__ == "__main__":
    unittest.main()
