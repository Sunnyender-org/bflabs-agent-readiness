#!/usr/bin/env python3
"""Validate the public geo-optimize Skill package without third-party dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/readiness-rules.md",
    "references/dynamic-facts.md",
    "references/framework-mapping.md",
    "references/service-boundary.md",
    "templates/public-facts.yaml",
    "templates/repair-receipt.json",
    "evals/trigger_cases.json",
    "examples/beefapi.md",
    "examples/beefapi-repair-receipt.json",
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        fail(f"missing {rel}")

skill = (ROOT / "SKILL.md").read_text("utf-8")
front = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
if not front:
    fail("SKILL.md frontmatter is missing")
keys = re.findall(r"^([a-z_]+):", front.group(1), re.M)
if keys != ["name", "description"]:
    fail(f"SKILL.md frontmatter must contain only name and description, got {keys}")
if "name: geo-optimize" not in front.group(1):
    fail("unexpected skill name")
if "Not for" not in front.group(1):
    fail("description must include exclusions")
if "TODO" in skill or "[TODO" in skill:
    fail("SKILL.md contains TODO text")

for ref in [
    "readiness-rules.md",
    "dynamic-facts.md",
    "framework-mapping.md",
    "service-boundary.md",
]:
    if f"references/{ref}" not in skill:
        fail(f"SKILL.md does not route to {ref}")

for rel in [
    "templates/repair-receipt.json",
    "evals/trigger_cases.json",
    "examples/beefapi-repair-receipt.json",
]:
    try:
        json.loads((ROOT / rel).read_text("utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {rel}: {exc}")

receipt = json.loads((ROOT / "templates/repair-receipt.json").read_text("utf-8"))
for field in [
    "schema_version",
    "mode",
    "scope",
    "findings",
    "verification",
    "ai_visibility",
    "business_outcome",
    "service_escalations",
]:
    if field not in receipt:
        fail(f"repair receipt missing {field}")
if receipt["ai_visibility"].get("status") != "not_measured":
    fail("template must default AI visibility to not_measured")
if receipt["business_outcome"].get("status") != "not_measured":
    fail("template must default business outcome to not_measured")

evals = json.loads((ROOT / "evals/trigger_cases.json").read_text("utf-8"))["cases"]
ids = [case["id"] for case in evals]
if len(ids) != len(set(ids)):
    fail("duplicate trigger case ids")
positive = sum(case["should_trigger"] is True for case in evals)
negative = sum(case["should_trigger"] is False for case in evals)
if positive < 3 or negative < 3:
    fail("trigger evals need at least three positive and three negative cases")

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.suffix not in {".md", ".json", ".yaml", ".yml", ".py"}:
        continue
    text = path.read_text("utf-8")
    mac_user_prefix = "/" + "Users/"
    windows_user_prefix = "C:" + "\\Users\\"
    if mac_user_prefix in text or windows_user_prefix in text:
        fail(f"private absolute path leaked in {path.relative_to(ROOT)}")

print(f"PASS: geo-optimize package ({positive} positive routes, {negative} negative routes)")
