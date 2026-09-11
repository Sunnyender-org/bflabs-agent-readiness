#!/usr/bin/env python3
"""Portable offline entry; release packages include the two sibling modules."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

source = Path(__file__).resolve().parents[1] / "src"
if (Path(__file__).resolve().parent / "business_attribution.py").is_file():
    from business_attribution import analyze
    from business_report import render_business_report
else:
    if source.is_dir():
        sys.path.insert(0, str(source))
    from bflabs_readiness.business_attribution import analyze
    from bflabs_readiness.business_report import render_business_report

parser = argparse.ArgumentParser(description="Analyze supplied records locally; no network or account changes.")
parser.add_argument("--input", required=True, type=Path)
parser.add_argument("--experiment", type=Path)
parser.add_argument("--as-of")
parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
parser.add_argument("--output", type=Path)
args = parser.parse_args()
document = json.loads(args.input.read_text("utf-8"))
experiment = json.loads(args.experiment.read_text("utf-8")) if args.experiment else None
report = analyze(document, experiment_doc=experiment, as_of=args.as_of)
output = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_business_report(report)
if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output + "\n", "utf-8")
else:
    print(output)
