from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bflabs_readiness.artifacts import publish_run, validate_run
from bflabs_readiness.paths import repository_root
from bflabs_readiness.providers.seo_plan import CATEGORIES, run_seo_plan
from bflabs_readiness.registry import CapabilityRegistry
from bflabs_readiness.schemas import validate_instance


def load_brief():
    return json.loads((repository_root() / "tests/fixtures/seo-plan-input.json").read_text("utf-8"))


class SEOPlanTests(unittest.TestCase):
    def test_migration_fixture_produces_evidence_findings_checks_and_gated_actions(self) -> None:
        brief = load_brief()
        validate_instance(brief, "seo-plan-brief.schema.json")
        result = run_seo_plan(brief)
        plan = result["outputs"]["outputs/seo-plan.json"][0]
        sources = result["outputs"]["outputs/official-sources.json"][0]
        validate_instance(plan, "seo-plan.schema.json")
        validate_instance(sources, "seo-official-sources.schema.json")
        self.assertEqual({item["category"] for item in plan["findings"]}, {"canonical", "redirects", "sitemap", "ai-crawlers"})
        self.assertEqual(len(plan["checks"]), len(CATEGORIES))
        self.assertEqual(len(plan["implementation_actions"]), 4)
        self.assertTrue(all(item["authorization"] == "owner-approval-required" and item["rollback"] for item in plan["implementation_actions"]))
        self.assertIn("No Search Console", plan["live_actions_not_performed"][0])
        self.assertEqual(result["quality_report"]["status"], "pass")

    def test_no_site_evidence_produces_gaps_without_findings(self) -> None:
        brief = load_brief()
        brief["observations"] = []
        brief["evidence_sources"] = []
        result = run_seo_plan(brief)
        plan = result["outputs"]["outputs/seo-plan.json"][0]
        self.assertEqual(plan["findings"], [])
        self.assertEqual(plan["implementation_actions"], [])
        self.assertEqual({item["category"] for item in plan["evidence_gaps"]}, set(CATEGORIES))
        self.assertEqual(result["quality_report"]["status"], "pass_with_warnings")
        capability = CapabilityRegistry().resolve("seo-plan", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = publish_run(capability, brief, result, Path(directory))
            self.assertEqual(validate_run(run_dir), [])

    def test_failed_observation_without_evidence_is_blocked(self) -> None:
        brief = load_brief()
        brief["observations"][0]["evidence_ids"] = []
        result = run_seo_plan(brief)
        self.assertEqual(result["quality_report"]["status"], "blocked")
        self.assertTrue(any("lack supplied site evidence" in item for item in result["quality_report"]["blockers"]))

    def test_stale_official_source_registry_blocks_plan(self) -> None:
        brief = load_brief()
        brief["captured_at"] = "2027-08-11T07:00:00Z"
        result = run_seo_plan(brief)
        self.assertEqual(result["quality_report"]["status"], "blocked")
        self.assertTrue(any("official guidance sources" in item for item in result["quality_report"]["blockers"]))

    def test_plan_publishes_and_revalidates_as_atomic_run(self) -> None:
        brief = load_brief()
        result = run_seo_plan(brief)
        capability = CapabilityRegistry().resolve("seo-plan", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = publish_run(capability, brief, result, Path(directory))
            self.assertEqual(validate_run(run_dir), [])


if __name__ == "__main__":
    unittest.main()
