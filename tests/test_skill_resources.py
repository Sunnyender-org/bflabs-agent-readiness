from __future__ import annotations

import json
import shutil
import subprocess
import unittest

from bflabs_readiness.packaging import skillhub_files
from bflabs_readiness.paths import repository_root


class SkillResourcePublicationTests(unittest.TestCase):
    def test_served_web_resources_are_a_subset_of_the_skillhub_zip(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not on PATH")
        completed = subprocess.run(
            ["node", "app/readiness-web/scripts/print-skill-resources.mjs"],
            cwd=repository_root(),
            check=True,
            capture_output=True,
            text=True,
        )
        served = json.loads(completed.stdout)
        hub_paths = {path.as_posix() for path, _data, _mode in skillhub_files()}
        missing = [item["path"] for item in served if item["path"] not in hub_paths]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
