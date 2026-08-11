from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bflabs_readiness.artifacts import publish_run, validate_run
from bflabs_readiness.paths import repository_root
from bflabs_readiness.providers.geo_content import MODES, run_geo_content
from bflabs_readiness.registry import CapabilityRegistry
from bflabs_readiness.schemas import validate_instance


def load_brief():
    return json.loads(
        (repository_root() / "skills/geo-content/examples/beefapi-gpt-5-6-content-brief.json").read_text("utf-8")
    )


def brief_for_mode(mode: str):
    brief = load_brief()
    brief["mode"] = mode
    if mode == "comparison":
        brief["comparison_targets"] = ["gpt-5.6-luna", "gpt-5.6-terra"]
        brief["comparison_dimensions"] = ["input price", "output price", "billing unit"]
    if mode == "ranking":
        brief["ranking_method"] = {
            "title": "Captured public input-price ordering",
            "criteria": ["lower gpt-plus input CNY per 1M tokens ranks first"],
            "dataset_scope": "three GPT-5.6 models in the captured BeefAPI fixture",
        }
    if mode in {"refine", "article-friendly"}:
        brief["source_markdown"] = "# Existing source\n\nOnly confirmed facts may be retained.\n"
    return brief


class ContentTests(unittest.TestCase):
    def test_all_seven_modes_emit_schema_valid_evidence_linked_markdown(self) -> None:
        self.assertEqual(set(MODES), {"title", "explainer", "comparison", "ranking", "page-blueprint", "refine", "article-friendly"})
        for mode in MODES:
            with self.subTest(mode=mode):
                result = run_geo_content(brief_for_mode(mode))
                spec = result["outputs"]["outputs/content-spec.json"][0]
                units = result["outputs"]["outputs/content-evidence-units.json"][0]
                markdown = result["outputs"]["outputs/content.md"][0]
                validate_instance(spec, "content-spec.schema.json")
                validate_instance(units, "content-evidence-units.schema.json")
                self.assertEqual(result["quality_report"]["status"], "pass")
                self.assertTrue(all(unit["claim_id"] in markdown for unit in units["units"]))
                self.assertEqual(spec["publication_gate"], "owner-approval-required")

    def test_changed_canonical_snapshot_marks_old_fact_bindings_stale(self) -> None:
        brief = load_brief()
        brief["evidence_sources"][0]["content_hash"] = "sha256:" + "f" * 64
        result = run_geo_content(brief)
        self.assertEqual(result["quality_report"]["status"], "blocked")
        self.assertTrue(any("stale against canonical evidence" in item for item in result["quality_report"]["blockers"]))

    def test_ranking_without_method_is_blocked(self) -> None:
        brief = load_brief()
        brief["mode"] = "ranking"
        result = run_geo_content(brief)
        self.assertEqual(result["quality_report"]["status"], "blocked")
        self.assertIn("ranking requires a disclosed method and dataset scope", result["quality_report"]["blockers"])

    def test_asymmetric_comparison_is_blocked(self) -> None:
        brief = load_brief()
        brief["mode"] = "comparison"
        brief["comparison_targets"] = ["gpt-5.6-luna"]
        result = run_geo_content(brief)
        self.assertEqual(result["quality_report"]["status"], "blocked")
        self.assertTrue(any("symmetric dimensions" in item for item in result["quality_report"]["blockers"]))

    def test_markdown_artifact_is_hashed_and_revalidated(self) -> None:
        brief = load_brief()
        result = run_geo_content(brief)
        capability = CapabilityRegistry().resolve("geo-content", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = publish_run(capability, brief, result, Path(directory))
            self.assertEqual(validate_run(run_dir), [])
            manifest = json.loads((run_dir / "run-manifest.json").read_text("utf-8"))
            markdown_artifact = next(item for item in manifest["artifacts"] if item["path"] == "outputs/content.md")
            self.assertEqual(markdown_artifact["media_type"], "text/markdown; charset=utf-8")
            self.assertIsNone(markdown_artifact["schema"])


if __name__ == "__main__":
    unittest.main()
