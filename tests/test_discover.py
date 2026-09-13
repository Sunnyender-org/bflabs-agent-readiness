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
        handoff = result["coverage_handoff"]
        self.assertTrue(handoff)
        self.assertTrue(any(row["status"] == "unmapped" and row["url"] is None for row in handoff))
        validate_instance(
            {
                "schema_version": "1.0.0",
                "questions_version": "1",
                "rows": handoff,
            },
            "round-coverage.schema.json",
        )

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

    def test_query_map_keeps_brief_provenance_and_marks_hypotheses(self) -> None:
        brief = load_brief()
        brief["schema_version"] = "1.1.0"
        brief["market"] = "zh-CN"
        brief["redacted"] = False
        brief["provenance"] = {
            "source_kind": "user_reported",
            "captured_at": "2026-08-11T05:00:00Z",
            "market": "zh-CN",
            "redacted": False,
        }
        brief["seed_query_provenance"] = [
            {
                "query": brief["seed_queries"][0],
                "source_kind": "user_reported",
                "captured_at": "2026-08-11T05:00:00Z",
                "market": "zh-CN",
                "redacted": False,
            }
        ]
        validate_instance(brief, "discovery-brief.schema.json")
        result = run_geo_discover(brief)
        query_map = result["outputs"]["outputs/query-map.json"][0]
        opportunity_map = result["outputs"]["outputs/opportunity-map.json"][0]
        validate_instance(query_map, "query-map.schema.json")
        self.assertEqual(query_map["schema_version"], "1.1.0")
        seed_queries = [query for query in query_map["queries"] if query["trace"]["source_type"] == "seed"]
        self.assertTrue(seed_queries)
        for query in seed_queries:
            self.assertEqual(query["provenance"]["source_kind"], "user_reported")
            self.assertEqual(query["provenance"]["captured_at"], "2026-08-11T05:00:00Z")
            self.assertEqual(query["provenance"]["market"], "zh-CN")
        hypotheses = [query for query in query_map["queries"] if query["trace"]["source_type"] == "assumption"]
        self.assertTrue(hypotheses)
        for query in hypotheses:
            self.assertEqual(query["provenance"]["source_kind"], "agent_hypothesis")
        self.assertTrue(
            all(item["search_volume"] == {"status": "not_measured", "value": None} for item in opportunity_map["opportunities"])
        )

    def test_duplicate_evidence_ids_block_quality(self) -> None:
        result = run_geo_discover(load_brief())
        query_map = result["outputs"]["outputs/query-map.json"][0]
        opportunity_map = result["outputs"]["outputs/opportunity-map.json"][0]
        result["evidence_ledger"]["items"].append(dict(result["evidence_ledger"]["items"][0]))
        quality = evaluate_discovery(query_map, opportunity_map, result["evidence_ledger"])
        self.assertEqual(quality["status"], "blocked")
        self.assertIn("duplicate evidence ids", quality["blockers"])

    def test_core_candidates_are_separate_from_named_brand_extensions(self):
        brief = load_brief()
        brief.update(brand="Northstar", brand_aliases=["北辰"], category="AI gateways",
                     site_url="https://northstar.example", language="en",
                     audiences=["developers"], scenarios=["building text and image features"])
        validate_instance(brief, "discovery-brief.schema.json")
        query_map = run_geo_discover(brief)["outputs"]["outputs/query-map.json"][0]
        validate_instance(query_map, "query-map.schema.json")
        core = [q for q in query_map["queries"] if q.get("question_group") == "core"]
        self.assertEqual(len(core), 6)
        unprompted = [q for q in core if q["observation_line"] == "D"]
        self.assertEqual(len(unprompted), 2)
        for q in unprompted:
            self.assertNotIn("northstar", q["text"].lower())
            self.assertNotIn("北辰", q["text"])
            self.assertEqual(q["provenance"]["source_kind"], "agent_hypothesis")
            self.assertTrue(q["purpose"] and q["judgement"])
        self.assertFalse(query_map["core_question_gaps"])

    def test_nonbrand_leakage_and_missing_category_remain_gaps(self):
        brief = load_brief()
        brief.update(brand="Northstar", brand_aliases=["北辰"], category="AI gateways",
                     site_url="https://northstar.example", scenarios=["迁移到北辰"])
        result = run_geo_discover(brief)["outputs"]["outputs/query-map.json"][0]
        self.assertFalse(any(q.get("observation_line") == "D" for q in result["queries"]))
        self.assertEqual(len([g for g in result["core_question_gaps"] if "leaked" in g["reason"]]), 2)
        del brief["category"]
        result = run_geo_discover(brief)["outputs"]["outputs/query-map.json"][0]
        self.assertTrue(any("category" in g["reason"] for g in result["core_question_gaps"]))

    def test_real_seed_matching_core_keeps_original_provenance(self):
        brief = load_brief()
        seed = "What is Northstar and what does it do?"
        brief.update(brand="Northstar", language="en", seed_queries=[seed],
                     seed_query_provenance=[dict(query=seed, source_kind="support",
                         captured_at=brief["captured_at"], market="en", redacted=True)])
        result = run_geo_discover(brief)["outputs"]["outputs/query-map.json"][0]
        matches = [q for q in result["queries"] if q["text"] == seed]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["provenance"]["source_kind"], "support")
        self.assertEqual(matches[0]["assumptions"], [])
        self.assertEqual(matches[0]["trace"]["source_type"], "seed")

    def test_nonbrand_www_and_compact_aliases(self):
        for brand, url, category in [
            ("Acme Cloud", "https://www.acme.io", "acme.io API gateways"),
            ("North Star", "https://northstar.example", "northstar gateways"),
            ("North-Star", "https://northstar.example", "North Star gateways"),
        ]:
            brief = load_brief()
            brief.update(brand=brand, site_url=url, category=category,
                         audiences=["developers"], scenarios=["building agents"], language="en")
            result = run_geo_discover(brief)["outputs"]["outputs/query-map.json"][0]
            self.assertFalse(any(q.get("observation_line") == "D" for q in result["queries"]))
            self.assertEqual(len([g for g in result["core_question_gaps"] if "leaked" in g["reason"]]), 2)

    def test_actual_upstream_requirement_is_not_target_brand_priming(self):
        brief = load_brief()  # Preserves the original audience needing GPT-5.6.
        brief.update(brand="BeefAPI", category="模型 API 平台", site_url="https://www.beefapi.com")
        result = run_geo_discover(brief)["outputs"]["outputs/query-map.json"][0]
        unprompted = [q for q in result["queries"] if q.get("observation_line") == "D"]
        self.assertEqual(len(unprompted), 2)
        self.assertTrue(all("BeefAPI" not in q["text"] for q in unprompted))
        self.assertTrue(all("GPT-5.6" in q["text"] for q in unprompted))

    def test_short_brand_does_not_match_inside_unrelated_words(self):
        from bflabs_readiness.question_library import mentions
        self.assertFalse(mentions("trail planning", "AI"))
        self.assertTrue(mentions("AI gateways", "AI"))


if __name__ == "__main__":
    unittest.main()
