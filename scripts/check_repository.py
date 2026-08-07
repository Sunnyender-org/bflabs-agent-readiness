#!/usr/bin/env python3
"""Validate the BFLabs Agent Readiness public monorepo."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "README.md",
    "LICENSE",
    "SKILL.md",
    "agents/openai.yaml",
    "references/routing.md",
    "references/product-boundary.md",
    "templates/readiness-report.json",
    "evals/trigger_cases.json",
    "skills/geo-optimize/SKILL.md",
    "skills/webmcp-enable/SKILL.md",
    "app/readiness-web/package.json",
    "app/readiness-web/public/index.html",
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        fail(f"missing {relative}")

skill = (ROOT / "SKILL.md").read_text("utf-8")
frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
if not frontmatter:
    fail("root SKILL.md frontmatter is missing")
if "name: bflabs-agent-readiness" not in frontmatter.group(1):
    fail("unexpected root skill name")
if "Not for" not in frontmatter.group(1):
    fail("root description must include exclusions")
if "sunny_skill_type: library" not in frontmatter.group(1):
    fail("root skill must be classified as library")

for routed_path in [
    "skills/geo-optimize/SKILL.md",
    "skills/webmcp-enable/SKILL.md",
    "app/readiness-web/README.md",
    "references/routing.md",
    "references/product-boundary.md",
]:
    if routed_path not in skill:
        fail(f"root SKILL.md does not route to {routed_path}")

cases = json.loads((ROOT / "evals/trigger_cases.json").read_text("utf-8"))["cases"]
ids = [case["id"] for case in cases]
if len(ids) != len(set(ids)):
    fail("duplicate root trigger case ids")
positive = sum(case["should_trigger"] is True for case in cases)
negative = sum(case["should_trigger"] is False for case in cases)
if positive < 4 or negative < 4:
    fail("root trigger evals need at least four positive and four negative cases")

app_html = (ROOT / "app/readiness-web/public/index.html").read_text("utf-8")
expected_repo = "Sunnyender-org/bflabs-agent-readiness"
if expected_repo not in app_html:
    fail("diagnostic app does not link to the consolidated repository")

allowed_suffixes = {".md", ".json", ".yaml", ".yml", ".py", ".js", ".mjs"}
for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or ".receipts" in path.parts or path.suffix not in allowed_suffixes:
        continue
    content = path.read_text("utf-8")
    mac_user_prefix = "/" + "Users/"
    windows_user_prefix = "C:" + "\\Users\\"
    if mac_user_prefix in content or windows_user_prefix in content:
        fail(f"private absolute path leaked in {path.relative_to(ROOT)}")
    stale_repo = "Sunnyender-org/" + "geo-optimize"
    if stale_repo in content:
        fail(f"stale repository URL in {path.relative_to(ROOT)}")

print(f"PASS: bflabs-agent-readiness repository ({positive} positive routes, {negative} negative routes)")
