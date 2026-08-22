from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from bflabs_readiness.cli import main
from bflabs_readiness.paths import repository_root


class CliTests(unittest.TestCase):
    def run_cli(self, arguments: list[str]) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(arguments)
        return status, output.getvalue()

    def test_eval_command_uses_packaged_router_cases(self) -> None:
        status, output = self.run_cli(["eval"])
        report = json.loads(output)
        self.assertEqual(status, 0)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["passed"], 62)

    def test_run_text_can_select_an_explicit_stable_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            status, output = self.run_cli([
                "run",
                "--text",
                "先挖掘用户问题和意图，然后诊断网站。",
                "--input",
                str(repository_root() / "tests/fixtures/discover-diagnose-input.json"),
                "--output",
                temp,
            ])
            result = json.loads(output)
            self.assertEqual(status, 0)
            self.assertEqual(result["status"], "pass")
            self.assertTrue(Path(result["run_dir"]).is_dir())

    def test_package_command_builds_one_child_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            status, output = self.run_cli(["package", "--target", "geo-optimize", "--output", temp])
            report = json.loads(output)
            self.assertEqual(status, 0)
            self.assertEqual(report["target"], "geo-optimize")
            self.assertEqual(report["status"], "pass")

    def test_package_command_builds_skillhub_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            status, output = self.run_cli(["package", "--target", "skillhub", "--output", temp])
            report = json.loads(output)
            self.assertEqual(status, 0)
            self.assertEqual(report["target"], "skillhub")
            self.assertEqual(report["status"], "pass")

    @mock.patch("bflabs_readiness.cli.scan_public_site")
    def test_scan_command_uses_versioned_public_api_without_leaderboard_by_default(self, scan) -> None:
        scan.return_value = ("application/json", '{"scan_fingerprint":"sha256:test"}')
        status, output = self.run_cli(["scan", "https://example.com", "--endpoint", "https://readiness.example", "--format", "json"])
        self.assertEqual(status, 0)
        self.assertIn("scan_fingerprint", output)
        scan.assert_called_once_with(
            "https://example.com",
            "https://readiness.example",
            output_format="json",
            publish_to_leaderboard=False,
            timeout=90.0,
        )


if __name__ == "__main__":
    unittest.main()
