from __future__ import annotations

import hashlib
import json
import unittest

from bflabs_readiness.paths import repository_root
from bflabs_readiness.schemas import validate_instance


class PublicExampleTests(unittest.TestCase):
    def test_deidentified_artifact_pack_is_complete_and_replayable(self) -> None:
        pack = json.loads((repository_root() / "examples/beefapi-deidentified-artifact-pack.json").read_text("utf-8"))
        validate_instance(pack, "artifact-pack.schema.json")
        validate_instance(pack["manifest"], "run-manifest.schema.json")
        validate_instance(pack["files"]["evidence-ledger.json"], "evidence-ledger.schema.json")
        validate_instance(pack["files"]["quality-report.json"], "quality-report.schema.json")
        validate_instance(pack["files"]["outputs/readiness-report.json"], "readiness-report.schema.json")
        for artifact in pack["manifest"]["artifacts"]:
            body = (json.dumps(pack["files"][artifact["path"]], ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            self.assertEqual(hashlib.sha256(body).hexdigest(), artifact["sha256"])
        report = pack["files"]["outputs/readiness-report.json"]
        self.assertEqual(report["ai_visibility"], "not_measured")
        self.assertEqual(report["business_outcome"], "not_measured")


if __name__ == "__main__":
    unittest.main()
