from __future__ import annotations

import json
import unittest

from bflabs_readiness.paths import repository_root
from bflabs_readiness.providers.geo_optimize import run_geo_optimize


class CompatibilityTests(unittest.TestCase):
    def test_existing_geo_optimize_receipt_shape_is_preserved(self) -> None:
        root = repository_root()
        legacy = json.loads((root / "skills/geo-optimize/examples/beefapi-repair-receipt.json").read_text("utf-8"))
        request = json.loads((root / "tests/fixtures/geo-optimize-audit-input.json").read_text("utf-8"))
        self.assertEqual(set(legacy), set(request["receipt"]))
        output = run_geo_optimize(request)
        report = output["outputs"]["outputs/readiness-report.json"][0]
        self.assertEqual(report["mode"], legacy["mode"])
        self.assertEqual(report["axes"]["actionable"]["webmcp_status"], "not_present")


if __name__ == "__main__":
    unittest.main()
