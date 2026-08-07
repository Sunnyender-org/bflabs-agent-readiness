#!/usr/bin/env python3
"""Validate the public webmcp-enable Skill package."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/implementation-patterns.md",
    "references/security-boundary.md",
    "references/cloudflare-webmcp.md",
    "templates/task-plan.json",
    "templates/verification-receipt.json",
    "evals/trigger_cases.json",
    "examples/beefapi-task-plan.json",
    "examples/beefapi-verification-receipt.json",
    "scripts/verify_site_mcp.py",
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
    fail(f"unexpected frontmatter keys: {keys}")
if "name: webmcp-enable" not in front.group(1):
    fail("unexpected skill name")
if "Not for" not in front.group(1):
    fail("description must include exclusions")
if "allow_implicit_invocation: false" not in (ROOT / "agents/openai.yaml").read_text("utf-8"):
    fail("external enablement skill must be explicit-only")

for rel in [
    "references/implementation-patterns.md",
    "references/security-boundary.md",
    "references/cloudflare-webmcp.md",
    "templates/task-plan.json",
    "templates/verification-receipt.json",
]:
    if rel not in skill:
        fail(f"SKILL.md does not route to {rel}")

for rel in [
    "templates/task-plan.json",
    "templates/verification-receipt.json",
    "evals/trigger_cases.json",
    "examples/beefapi-task-plan.json",
    "examples/beefapi-verification-receipt.json",
]:
    try:
        json.loads((ROOT / rel).read_text("utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {rel}: {exc}")

receipt = json.loads((ROOT / "templates/verification-receipt.json").read_text("utf-8"))
for field in [
    "target",
    "canonical_mcp",
    "external_setting",
    "tool_inventory",
    "contract_checks",
    "browser_run",
    "rollback",
    "ai_visibility",
    "business_outcome",
]:
    if field not in receipt:
        fail(f"verification receipt missing {field}")
if receipt["ai_visibility"] != "not_measured" or receipt["business_outcome"] != "not_measured":
    fail("visibility and business outcome must default to not_measured")

cases = json.loads((ROOT / "evals/trigger_cases.json").read_text("utf-8"))["cases"]
ids = [case["id"] for case in cases]
if len(ids) != len(set(ids)):
    fail("duplicate trigger case ids")
positive = sum(case["should_trigger"] is True for case in cases)
negative = sum(case["should_trigger"] is False for case in cases)
if positive < 4 or negative < 4:
    fail("trigger evals need at least four positive and four negative cases")

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.suffix not in {".md", ".json", ".yaml", ".yml", ".py"}:
        continue
    content = path.read_text("utf-8")
    mac_user_prefix = "/" + "Users/"
    windows_user_prefix = "C:" + "\\Users\\"
    if mac_user_prefix in content or windows_user_prefix in content:
        fail(f"private absolute path leaked in {path.relative_to(ROOT)}")

print(f"PASS: webmcp-enable package ({positive} positive routes, {negative} negative routes)")
