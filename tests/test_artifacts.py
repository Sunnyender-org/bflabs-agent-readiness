from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bflabs_readiness.artifacts import publish_run, validate_run
from bflabs_readiness.paths import repository_root
from bflabs_readiness.providers.geo_optimize import run_geo_optimize
from bflabs_readiness.registry import CapabilityRegistry


def load_fixture():
    return json.loads((repository_root() / "tests/fixtures/geo-optimize-audit-input.json").read_text("utf-8"))


class ArtifactTests(unittest.TestCase):
    def test_geo_optimize_fixture_publishes_complete_run(self) -> None:
        request = load_fixture()
        capability = CapabilityRegistry().resolve("geo-optimize", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = publish_run(capability, request, run_geo_optimize(request), Path(directory))
            self.assertEqual(validate_run(run_dir), [])
            self.assertTrue((run_dir / "input/request.json").is_file())
            self.assertTrue((run_dir / "evidence-ledger.json").is_file())
            self.assertTrue((run_dir / "quality-report.json").is_file())
            self.assertTrue((run_dir / "outputs/readiness-report.json").is_file())
            report = json.loads((run_dir / "outputs/readiness-report.json").read_text("utf-8"))
            self.assertEqual(report["ai_visibility"], "not_measured")
            self.assertEqual(report["business_outcome"], "not_measured")
            self.assertEqual(set(report["axes"]), {"discoverable", "understandable", "actionable"})

    def test_manifest_detects_tampering(self) -> None:
        request = load_fixture()
        capability = CapabilityRegistry().resolve("geo-optimize", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = publish_run(capability, request, run_geo_optimize(request), Path(directory))
            (run_dir / "outputs/readiness-report.json").write_text("{}\n", "utf-8")
            self.assertIn("hash mismatch: outputs/readiness-report.json", validate_run(run_dir))

    def test_manifest_detects_input_hash_rewrite(self) -> None:
        request = load_fixture()
        capability = CapabilityRegistry().resolve("geo-optimize", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = publish_run(capability, request, run_geo_optimize(request), Path(directory))
            manifest_path = run_dir / "run-manifest.json"
            manifest = json.loads(manifest_path.read_text("utf-8"))
            manifest["input_hash"] = "sha256:" + "0" * 64
            manifest_path.write_text(json.dumps(manifest), "utf-8")
            self.assertIn("input_hash does not match input/request.json", validate_run(run_dir))

    def test_unsupported_claim_blocks_atomic_publication(self) -> None:
        request = load_fixture()
        request["evidence_sources"] = request["evidence_sources"][1:]
        capability = CapabilityRegistry().resolve("geo-optimize", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "quality gate blocked"):
                publish_run(capability, request, run_geo_optimize(request), Path(directory))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_unversioned_dynamic_fact_blocks_atomic_publication(self) -> None:
        request = load_fixture()
        request["evidence_sources"][0]["fact_version"] = None
        capability = CapabilityRegistry().resolve("geo-optimize", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "quality gate blocked"):
                publish_run(capability, request, run_geo_optimize(request), Path(directory))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_duplicate_evidence_id_blocks_atomic_publication(self) -> None:
        request = load_fixture()
        request["evidence_sources"][1]["id"] = request["evidence_sources"][0]["id"]
        capability = CapabilityRegistry().resolve("geo-optimize", executable=True)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "quality gate blocked"):
                publish_run(capability, request, run_geo_optimize(request), Path(directory))
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
