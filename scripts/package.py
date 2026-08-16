#!/usr/bin/env python3
"""Build one allowlisted release-candidate package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bflabs_readiness.packaging import CAPABILITY_IDS, package_target, validate_archive  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=["source", "unified", *CAPABILITY_IDS])
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    archive = package_target(args.target, args.output, ROOT)
    print(json.dumps(validate_archive(archive, args.target), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
