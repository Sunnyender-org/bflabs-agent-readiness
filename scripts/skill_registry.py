#!/usr/bin/env python3
"""Bounded list/read/validate interface for public Agent Skill SOP."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bflabs_readiness.registry import CapabilityRegistry  # noqa: E402
from bflabs_readiness.schemas import validate_all_schemas  # noqa: E402

ALLOWED_NAMES = {"SKILL.md"}
ALLOWED_PARTS = {"references", "templates", "evals"}


def allowed(path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return False
    if not path.is_file() or ".receipts" in relative.parts or "scripts" in relative.parts:
        return False
    return path.name in ALLOWED_NAMES or bool(set(relative.parts) & ALLOWED_PARTS)


def list_sop(output_format: str) -> None:
    registry = CapabilityRegistry(ROOT)
    payload = {
        capability.id: {
            "path": str(Path(capability.entrypoint).parent) if capability.entrypoint and capability.entrypoint != "SKILL.md" else ".",
            "entrypoint": capability.entrypoint,
            "status": capability.status,
        }
        for capability in registry.list_capabilities("active")
        if capability.entrypoint
    }
    if output_format == "json":
        print(json.dumps(payload, indent=2))
        return
    for name, item in payload.items():
        print(f"- `{name}` ({item['status']}): `{item['entrypoint'] or 'unavailable'}`")


def read_sop(relative: str) -> None:
    path = ROOT / relative
    if not allowed(path):
        raise SystemExit("FAIL: path is outside the agent-readable SOP surface")
    print(path.read_text("utf-8"), end="")


def validate() -> None:
    CapabilityRegistry(ROOT).validate()
    validate_all_schemas()
    commands = [
        [sys.executable, str(ROOT / "scripts/check_repository.py")],
        [sys.executable, str(ROOT / "skills/geo-discover/scripts/check_package.py")],
        [sys.executable, str(ROOT / "skills/geo-content/scripts/check_package.py")],
        [sys.executable, str(ROOT / "skills/geo-measure/scripts/check_package.py")],
        [sys.executable, str(ROOT / "skills/seo-plan/scripts/check_package.py")],
        [sys.executable, str(ROOT / "skills/geo-optimize/scripts/check_package.py")],
        [sys.executable, str(ROOT / "skills/webmcp-enable/scripts/check_package.py")],
        [sys.executable, str(ROOT / "scripts/run_evals.py")],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
    ]
    child_env = os.environ.copy()
    existing_pythonpath = child_env.get("PYTHONPATH")
    child_env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    for command in commands:
        subprocess.run(command, check=True, cwd=ROOT, env=child_env)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("path")
    subparsers.add_parser("validate")
    args = parser.parse_args()
    if args.command == "list":
        list_sop(args.format)
    elif args.command == "read":
        read_sop(args.path)
    else:
        validate()


if __name__ == "__main__":
    main()
