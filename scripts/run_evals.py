#!/usr/bin/env python3
"""Run deterministic router and workflow routing evals."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bflabs_readiness.evals import run_router_evals  # noqa: E402


def main() -> int:
    report = run_router_evals()
    import json
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
