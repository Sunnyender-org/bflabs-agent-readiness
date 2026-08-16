"""Allowlisted release-candidate package builders and archive checks."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from . import __version__
from .paths import repository_root


CAPABILITY_IDS: Tuple[str, ...] = (
    "geo-discover",
    "geo-optimize",
    "geo-content",
    "geo-measure",
    "seo-plan",
    "webmcp-enable",
)

SOURCE_ROOT_FILES = {
    ".gitignore",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "SKILL.md",
    "THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
}
SOURCE_DIRS = {
    ".github",
    "agents",
    "app",
    "evals",
    "examples",
    "references",
    "registry",
    "schemas",
    "scripts",
    "skills",
    "src",
    "templates",
    "tests",
    "workflows",
}
PUBLIC_DOCS = {
    "docs/architecture.md",
    "docs/artifact-protocol.md",
    "docs/install-codex-claude.md",
    "docs/release-checklist.md",
}
IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".receipts",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "runs",
}
TEXT_SUFFIXES = {"", ".css", ".csv", ".html", ".js", ".json", ".md", ".mjs", ".py", ".toml", ".txt", ".yaml", ".yml"}
PRIVATE_PATTERNS = (
    (re.compile(rb"/(?:Users|home)/[^/\s]+/"), "private home path"),
    (re.compile(rb"[A-Za-z]:\\Users\\[^\\\s]+\\"), "private Windows home path"),
    (re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private key"),
    (re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"), "API key shaped token"),
    (re.compile(rb"\bBearer\s+[A-Za-z0-9._~-]{20,}"), "bearer token"),
)


class PackageError(ValueError):
    """Raised when a requested package would violate its public contract."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative(path: Path, root: Path) -> PurePosixPath:
    if path.is_symlink():
        raise PackageError("symlinks are not allowed in release packages: {}".format(path))
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise PackageError("path escapes repository root: {}".format(path)) from exc
    return PurePosixPath(relative.as_posix())


def _is_source_allowed(relative: PurePosixPath) -> bool:
    value = relative.as_posix()
    if value in SOURCE_ROOT_FILES or value in PUBLIC_DOCS:
        return True
    return len(relative.parts) > 1 and relative.parts[0] in SOURCE_DIRS


def source_files(root: Optional[Path] = None) -> List[Tuple[PurePosixPath, Path]]:
    base = (root or repository_root()).resolve()
    files: List[Tuple[PurePosixPath, Path]] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or IGNORED_PARTS.intersection(path.parts):
            continue
        relative = _safe_relative(path, base)
        if _is_source_allowed(relative):
            files.append((relative, path))
    missing = sorted(item for item in SOURCE_ROOT_FILES | PUBLIC_DOCS if not (base / item).is_file())
    if missing:
        raise PackageError("source package allowlist is missing required files: {}".format(", ".join(missing)))
    return files


def skill_files(capability_id: str, root: Optional[Path] = None) -> List[Tuple[PurePosixPath, bytes, int]]:
    if capability_id not in CAPABILITY_IDS:
        raise PackageError("unknown package target: {}".format(capability_id))
    base = (root or repository_root()).resolve()
    skill_root = base / "skills" / capability_id
    files: List[Tuple[PurePosixPath, bytes, int]] = []
    for path in sorted(skill_root.rglob("*")):
        if not path.is_file() or IGNORED_PARTS.intersection(path.parts) or path.name == "check_package.py":
            continue
        relative = _safe_relative(path, skill_root)
        mode = 0o755 if relative.parts[0] == "scripts" and path.suffix == ".py" else 0o644
        files.append((PurePosixPath(capability_id) / relative, path.read_bytes(), mode))
    for name in ["LICENSE", "THIRD_PARTY_NOTICES.md"]:
        files.append((PurePosixPath(capability_id) / name, (base / name).read_bytes(), 0o644))
    if not any(path.as_posix() == "{}/SKILL.md".format(capability_id) for path, _, _ in files):
        raise PackageError("{} package has no SKILL.md".format(capability_id))
    return sorted(files, key=lambda item: item[0].as_posix())


def _package_manifest(target: str, entries: Sequence[Tuple[PurePosixPath, bytes, int]]) -> Dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "target": target,
        "version": __version__,
        "license": "MIT",
        "files": [
            {"path": path.as_posix(), "sha256": sha256_bytes(data), "mode": oct(mode)}
            for path, data, mode in entries
        ],
    }


def build_skill_package(capability_id: str, output_dir: Path, root: Optional[Path] = None) -> Path:
    entries = skill_files(capability_id, root)
    manifest = _package_manifest(capability_id, entries)
    manifest_path = PurePosixPath(capability_id) / "PACKAGE_MANIFEST.json"
    manifest_data = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    entries = [*entries, (manifest_path, manifest_data, 0o644)]
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / "{}-{}.zip".format(capability_id, __version__)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for relative, data, mode in entries:
            info = zipfile.ZipInfo(relative.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (mode & 0xFFFF) << 16
            bundle.writestr(info, data)
    validate_archive(archive, target=capability_id)
    return archive


def build_source_package(output_dir: Path, root: Optional[Path] = None) -> Path:
    base = (root or repository_root()).resolve()
    source = source_files(base)
    prefix = "bflabs-agent-readiness-{}".format(__version__)
    entries: List[Tuple[PurePosixPath, bytes, int]] = []
    for relative, path in source:
        mode = 0o755 if relative.parts[0] == "scripts" and path.suffix == ".py" else 0o644
        entries.append((PurePosixPath(prefix) / relative, path.read_bytes(), mode))
    manifest = _package_manifest("source", entries)
    entries.append((PurePosixPath(prefix) / "PACKAGE_MANIFEST.json", (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"), 0o644))
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / "bflabs-agent-readiness-{}.tar.gz".format(__version__)
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as bundle:
                for relative, data, mode in entries:
                    info = tarfile.TarInfo(relative.as_posix())
                    info.size = len(data)
                    info.mode = mode
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    bundle.addfile(info, fileobj=io.BytesIO(data))
    validate_archive(archive, target="source")
    return archive


def build_unified_package(output_dir: Path, root: Optional[Path] = None) -> Path:
    base = (root or repository_root()).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bflabs-source-") as temp:
        source_archive = build_source_package(Path(temp), base)
        command = [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--disable-pip-version-check",
            "--no-deps",
            "--wheel-dir",
            str(output_dir),
            str(source_archive),
        ]
        completed = subprocess.run(command, cwd=base, text=True, capture_output=True)
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip().splitlines()
            raise PackageError("unified wheel build failed: {}".format(detail[-1] if detail else "unknown pip error"))
    wheels = sorted(output_dir.glob("bflabs_agent_readiness-{}-*.whl".format(__version__)))
    if len(wheels) != 1:
        raise PackageError("unified wheel build did not produce exactly one wheel")
    validate_archive(wheels[0], target="unified")
    return wheels[0]


def package_target(target: str, output_dir: Path, root: Optional[Path] = None) -> Path:
    if target == "source":
        return build_source_package(output_dir, root)
    if target == "unified":
        return build_unified_package(output_dir, root)
    return build_skill_package(target, output_dir, root)


def _archive_entries(path: Path) -> Iterable[Tuple[str, bytes, int]]:
    if path.suffix == ".whl" or path.suffix == ".zip":
        with zipfile.ZipFile(path) as bundle:
            for info in bundle.infolist():
                if info.is_dir():
                    continue
                yield info.filename, bundle.read(info), (info.external_attr >> 16) & 0xFFFF
        return
    with tarfile.open(path, "r:gz") as bundle:
        for info in bundle.getmembers():
            if info.issym() or info.islnk():
                raise PackageError("archive contains a link: {}".format(info.name))
            if not info.isfile():
                continue
            handle = bundle.extractfile(info)
            if handle is None:
                raise PackageError("cannot read archive member: {}".format(info.name))
            yield info.name, handle.read(), info.mode


def validate_archive(path: Path, target: str) -> Dict[str, Any]:
    entries = list(_archive_entries(path))
    entry_data = {name: data for name, data, _mode in entries}
    names: List[str] = []
    has_license = False
    has_notices = False
    for name, data, _mode in entries:
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "" in relative.parts:
            raise PackageError("unsafe archive member: {}".format(name))
        names.append(name)
        has_license = has_license or relative.name == "LICENSE"
        has_notices = has_notices or relative.name == "THIRD_PARTY_NOTICES.md"
        if relative.suffix.lower() in TEXT_SUFFIXES:
            for pattern, label in PRIVATE_PATTERNS:
                if pattern.search(data):
                    raise PackageError("{} leaked in {}".format(label, name))
    if len(names) != len(set(names)):
        raise PackageError("archive contains duplicate members")
    if not has_license or not has_notices:
        raise PackageError("archive must contain LICENSE and THIRD_PARTY_NOTICES.md")
    if target in CAPABILITY_IDS:
        prefix = target + "/"
        if not names or any(not name.startswith(prefix) for name in names):
            raise PackageError("child Skill archive escapes its target directory")
        if prefix + "SKILL.md" not in names or prefix + "PACKAGE_MANIFEST.json" not in names:
            raise PackageError("child Skill archive lacks its entrypoint or manifest")
    elif target == "source":
        prefix = "bflabs-agent-readiness-{}/".format(__version__)
        for name in names:
            if not name.startswith(prefix):
                raise PackageError("source archive member escapes version root: {}".format(name))
            relative = PurePosixPath(name[len(prefix):])
            if relative.as_posix() != "PACKAGE_MANIFEST.json" and not _is_source_allowed(relative):
                raise PackageError("source archive member is outside the allowlist: {}".format(name))
    elif target == "unified":
        code_prefix = "bflabs_readiness/"
        metadata_prefix = "bflabs_agent_readiness-{}.dist-info/".format(__version__)
        data_prefix = "bflabs_agent_readiness-{}.data/data/share/bflabs-agent-readiness/".format(__version__)
        for name in names:
            if not name.startswith((code_prefix, metadata_prefix, data_prefix)):
                raise PackageError("unified wheel member is outside the allowlist: {}".format(name))
            if name.startswith(code_prefix) and not (name.endswith(".py") or name.endswith("/py.typed")):
                raise PackageError("unified wheel code member is not Python or py.typed: {}".format(name))
    for skill_name in [name for name in names if name.endswith("/SKILL.md") or name == "SKILL.md"]:
        body = entry_data[skill_name].decode("utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", body):
            if link.startswith(("http://", "https://", "#")):
                continue
            clean_link = link.split("#", 1)[0]
            target_path = (PurePosixPath(skill_name).parent / clean_link)
            normalized_parts: List[str] = []
            for part in target_path.parts:
                if part == "..":
                    if not normalized_parts:
                        raise PackageError("Skill link escapes package: {} -> {}".format(skill_name, link))
                    normalized_parts.pop()
                elif part not in ("", "."):
                    normalized_parts.append(part)
            normalized = PurePosixPath(*normalized_parts).as_posix()
            if normalized not in entry_data:
                raise PackageError("Skill link is missing from package: {} -> {}".format(skill_name, link))
    return {
        "target": target,
        "path": str(path),
        "files": len(names),
        "sha256": sha256_bytes(path.read_bytes()),
        "status": "pass",
    }
