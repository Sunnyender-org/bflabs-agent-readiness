#!/usr/bin/env python3
"""Validate the public geo-content Skill package."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/content-contract.md",
    "templates/content-brief.json",
    "examples/beefapi-gpt-5-6-content-brief.json",
    "evals/trigger_cases.json",
]


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        fail("missing " + relative)

skill = (ROOT / "SKILL.md").read_text("utf-8")
front = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
if not front or "name: geo-content" not in front.group(1) or "Not for" not in front.group(1):
    fail("invalid SKILL.md frontmatter")
for relative in ["references/content-contract.md", "templates/content-brief.json"]:
    if relative not in skill:
        fail("SKILL.md does not route to " + relative)

for relative in ["templates/content-brief.json", "examples/beefapi-gpt-5-6-content-brief.json", "evals/trigger_cases.json"]:
    json.loads((ROOT / relative).read_text("utf-8"))

cases = json.loads((ROOT / "evals/trigger_cases.json").read_text("utf-8"))["cases"]
positive = sum(case["should_trigger"] is True for case in cases)
negative = sum(case["should_trigger"] is False for case in cases)
if positive < 8 or negative < 8:
    fail("trigger evals need eight positive and eight negative cases")

for path in ROOT.rglob("*"):
    if not path.is_file() or path.suffix not in {".md", ".json", ".yaml", ".yml", ".py"}:
        continue
    content = path.read_text("utf-8")
    mac_user_prefix = "/" + "Users/"
    windows_user_prefix = "C:" + "\\Users\\"
    if mac_user_prefix in content or windows_user_prefix in content:
        fail("private absolute path leaked in " + str(path.relative_to(ROOT)))

print("PASS: geo-content package ({} positive routes, {} negative routes)".format(positive, negative))
