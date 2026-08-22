from __future__ import annotations

import io
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from bflabs_readiness.packaging import CAPABILITY_IDS, PackageError, build_skill_package, build_skillhub_package, build_source_package, validate_archive


class PackagingTests(unittest.TestCase):
    def test_every_child_skill_builds_from_an_explicit_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            for capability_id in CAPABILITY_IDS:
                archive = build_skill_package(capability_id, Path(temp))
                report = validate_archive(archive, capability_id)
                self.assertEqual(report["status"], "pass")

    def test_archive_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "geo-optimize-unsafe.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("../SKILL.md", "---\nname: bad\n---\n")
                bundle.writestr("LICENSE", "MIT License")
                bundle.writestr("THIRD_PARTY_NOTICES.md", "notices")
            with self.assertRaises(PackageError):
                validate_archive(archive, "geo-optimize")

    def test_archive_rejects_private_paths_and_tokens(self) -> None:
        private_path = b"/" + b"Users/" + b"example/private/report.json"
        token_shape = b"sk" + b"-" + b"123456789012345678901234"
        for value in [private_path, token_shape]:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temp:
                archive = Path(temp) / "geo-optimize-unsafe.zip"
                with zipfile.ZipFile(archive, "w") as bundle:
                    bundle.writestr("geo-optimize/SKILL.md", value)
                    bundle.writestr("geo-optimize/LICENSE", "MIT License")
                    bundle.writestr("geo-optimize/THIRD_PARTY_NOTICES.md", "notices")
                    bundle.writestr("geo-optimize/PACKAGE_MANIFEST.json", "{}")
                with self.assertRaises(PackageError):
                    validate_archive(archive, "geo-optimize")

    def test_archive_requires_license_and_notices(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "geo-optimize-unsafe.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("geo-optimize/SKILL.md", "---\nname: geo-optimize\n---\n")
                bundle.writestr("geo-optimize/PACKAGE_MANIFEST.json", "{}")
            with self.assertRaises(PackageError):
                validate_archive(archive, "geo-optimize")

    def test_source_package_excludes_local_and_generated_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = build_source_package(Path(temp))
            with tarfile.open(archive, "r:gz") as bundle:
                names = bundle.getnames()
            self.assertFalse(any("/.wrangler/" in name for name in names))
            self.assertFalse(any("/.worker-build/" in name for name in names))
            self.assertFalse(any("/.venv/" in name for name in names))

    def test_skillhub_package_is_bounded_and_contains_the_brand_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = build_skillhub_package(Path(temp))
            report = validate_archive(archive, "skillhub")
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
            self.assertEqual(report["status"], "pass")
            self.assertLessEqual(len(names), 200)
            self.assertIn("SKILL.md", names)
            self.assertIn("assets/bflabs-logo.svg", names)
            self.assertNotIn("LICENSE", names)
            self.assertFalse(any(".wrangler" in name or ".worker-build" in name for name in names))


if __name__ == "__main__":
    unittest.main()
