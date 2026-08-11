from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bflabs_readiness.artifacts import validate_run
from bflabs_readiness.orchestrator import run_discover_content, run_discover_diagnose
from bflabs_readiness.paths import repository_root


class OrchestratorTests(unittest.TestCase):
    def test_discover_diagnose_publishes_one_atomic_workflow_run(self) -> None:
        request = json.loads((repository_root() / "tests/fixtures/discover-diagnose-input.json").read_text("utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            run_dir = run_discover_diagnose(request, Path(directory))
            self.assertEqual(validate_run(run_dir), [])
            manifest = json.loads((run_dir / "run-manifest.json").read_text("utf-8"))
            receipt = json.loads((run_dir / "outputs/workflow-receipt.json").read_text("utf-8"))
            report = json.loads((run_dir / "outputs/geo-optimize/readiness-report.json").read_text("utf-8"))
            ledger = json.loads((run_dir / "evidence-ledger.json").read_text("utf-8"))
            self.assertEqual(manifest["workflow_id"], "discover-diagnose")
            self.assertEqual(receipt["steps"], ["geo-discover", "geo-optimize"])
            self.assertEqual(receipt["data_flow"]["producer_artifact"], "outputs/geo-discover/opportunity-map.json")
            self.assertIn("discovery-opportunity-coverage", {finding["id"] for finding in report["findings"]})
            self.assertIn("ev_discovery_opportunity_map", {item["id"] for item in ledger["items"]})
            self.assertTrue((run_dir / "outputs/geo-discover/query-map.json").is_file())
            self.assertTrue((run_dir / "outputs/geo-discover/opportunity-map.json").is_file())

    def test_discover_content_consumes_opportunity_map_in_one_atomic_run(self) -> None:
        request = json.loads((repository_root() / "tests/fixtures/discover-content-input.json").read_text("utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            run_dir = run_discover_content(request, Path(directory))
            self.assertEqual(validate_run(run_dir), [])
            receipt = json.loads((run_dir / "outputs/workflow-receipt.json").read_text("utf-8"))
            spec = json.loads((run_dir / "outputs/geo-content/content-spec.json").read_text("utf-8"))
            ledger = json.loads((run_dir / "evidence-ledger.json").read_text("utf-8"))
            self.assertEqual(receipt["steps"], ["geo-discover", "geo-content"])
            self.assertEqual(receipt["data_flow"]["consumer_field"], "discovery_context")
            self.assertEqual(spec["discovery_context"]["evidence_id"], "ev_discovery_opportunity_map")
            self.assertIn("ev_discovery_opportunity_map", {item["id"] for item in ledger["items"]})
            self.assertTrue((run_dir / "outputs/geo-content/content.md").is_file())


if __name__ == "__main__":
    unittest.main()
