from __future__ import annotations

import hashlib
import json
import subprocess
import unittest

from bflabs_readiness.paths import repository_root
from bflabs_readiness.schemas import validate_instance


NODE_SCRIPT = r"""
import { buildArtifactPack, buildReadinessReport } from './app/readiness-web/src/scanner.mjs';
const axes = [
  { id: 'discoverable', status: 'partial', limitations: [], checks: [{ id: 'D-HTML', state: 'pass', evidence_ids: ['ev_home'] }] },
  { id: 'understandable', status: 'unknown', limitations: ['fixture'], checks: [{ id: 'U-DEFINITION', state: 'unknown', evidence_ids: [] }] },
  { id: 'actionable', status: 'unverified', limitations: ['browser task not run'], checks: [{ id: 'A-WEBMCP', state: 'pass', evidence_ids: ['ev_home'] }] },
];
const report = buildReadinessReport('https://example.com', axes, [], { advertised: true });
const ledger = {
  schema_version: '1.0.0',
  items: [{ id: 'ev_home', summary: 'home fixture', source_type: 'fixture', locator: 'fixture:web/home', captured_at: '2026-08-11T07:10:00Z', content_hash: 'sha256:' + 'a'.repeat(64), support_scope: 'web protocol test', limitations: [], dynamic_fact: false, fact_version: null, license: 'MIT' }],
  claims: [],
};
const quality = { schema_version: '1.0.0', status: 'pass_with_warnings', checks: [{ id: 'unknown-preservation', status: 'warning', message: 'one predicate remains unknown' }], warnings: ['one predicate remains unknown'], blockers: [] };
const input = { schema_version: '1.0.0', capability: 'bflabs-agent-readiness', captured_at: '2026-08-11T07:10:00Z', url: 'https://example.com' };
const pack = buildArtifactPack({ input, completedAt: '2026-08-11T07:10:00.000Z', readinessReport: report, ledger, qualityReport: quality, externalGates: report.external_gates });
console.log(JSON.stringify(pack));
"""


class WebProtocolTests(unittest.TestCase):
    def test_web_artifact_pack_is_schema_equivalent_to_cli_protocol(self) -> None:
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", NODE_SCRIPT],
            cwd=repository_root(),
            check=True,
            capture_output=True,
            text=True,
        )
        pack = json.loads(completed.stdout)
        validate_instance(pack, "artifact-pack.schema.json")
        validate_instance(pack["manifest"], "run-manifest.schema.json")
        validate_instance(pack["files"]["outputs/readiness-report.json"], "readiness-report.schema.json")
        validate_instance(pack["files"]["evidence-ledger.json"], "evidence-ledger.schema.json")
        validate_instance(pack["files"]["quality-report.json"], "quality-report.schema.json")
        for artifact in pack["manifest"]["artifacts"]:
            body = (json.dumps(pack["files"][artifact["path"]], ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            self.assertEqual(hashlib.sha256(body).hexdigest(), artifact["sha256"])
        input_artifact = next(item for item in pack["manifest"]["artifacts"] if item["path"] == "input/request.json")
        self.assertEqual(pack["manifest"]["input_hash"], "sha256:" + input_artifact["sha256"])


if __name__ == "__main__":
    unittest.main()
