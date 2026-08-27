from __future__ import annotations

import json
import unittest
from pathlib import Path

from bflabs_readiness.paths import repository_root
from bflabs_readiness.schemas import SchemaValidationError, validate_all_schemas, validate_instance


class SchemaTests(unittest.TestCase):
    def test_all_public_schemas_are_valid(self) -> None:
        validate_all_schemas()

    def test_geo_optimize_fixture_is_valid(self) -> None:
        fixture = json.loads((repository_root() / "tests/fixtures/geo-optimize-audit-input.json").read_text("utf-8"))
        validate_instance(fixture, "geo-optimize-run-input.schema.json")

    def test_dynamic_evidence_requires_boolean_marker(self) -> None:
        fixture = json.loads((repository_root() / "tests/fixtures/geo-optimize-audit-input.json").read_text("utf-8"))
        del fixture["evidence_sources"][0]["dynamic_fact"]
        with self.assertRaises(SchemaValidationError):
            validate_instance(fixture, "geo-optimize-run-input.schema.json")

    def test_readiness_report_accepts_every_evidence_bounded_webmcp_state(self) -> None:
        pack = json.loads((repository_root() / "examples/beefapi-deidentified-artifact-pack.json").read_text("utf-8"))
        report = pack["files"]["outputs/readiness-report.json"]
        for state in ("unknown", "not_applicable", "not_present", "present_unverified", "verified", "blocked"):
            report["axes"]["actionable"]["webmcp_status"] = state
            validate_instance(report, "readiness-report.schema.json")


if __name__ == "__main__":
    unittest.main()
