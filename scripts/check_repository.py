#!/usr/bin/env python3
"""Validate the BFLabs Agent Readiness public monorepo."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "AGENTS.md",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
    "SKILL.md",
    "skill.yml",
    "agents/openai.yaml",
    "registry/capabilities.json",
    "registry/workflows.json",
    "schemas/capabilities-registry.schema.json",
    "schemas/artifact-pack.schema.json",
    "schemas/evidence-ledger.schema.json",
    "schemas/quality-report.schema.json",
    "schemas/readiness-report.schema.json",
    "schemas/run-manifest.schema.json",
    "schemas/route-decision.schema.json",
    "schemas/discovery-brief.schema.json",
    "schemas/query-map.schema.json",
    "schemas/opportunity-map.schema.json",
    "schemas/workflow-receipt.schema.json",
    "schemas/content-brief.schema.json",
    "schemas/content-spec.schema.json",
    "schemas/content-evidence-units.schema.json",
    "schemas/discover-content-input.schema.json",
    "schemas/measurement-input.schema.json",
    "schemas/observation.schema.json",
    "schemas/measurement-report.schema.json",
    "schemas/round-experiment.schema.json",
    "schemas/round-facts.schema.json",
    "schemas/round-questions.schema.json",
    "schemas/round-actions.schema.json",
    "schemas/round-business-events.schema.json",
    "schemas/research-evidence-registry.schema.json",
    "schemas/research-context.schema.json",
    "schemas/seo-plan-brief.schema.json",
    "schemas/seo-plan.schema.json",
    "schemas/seo-official-sources.schema.json",
    "src/bflabs_readiness/cli.py",
    "src/bflabs_readiness/registry.py",
    "src/bflabs_readiness/router.py",
    "src/bflabs_readiness/orchestrator.py",
    "src/bflabs_readiness/artifacts.py",
    "src/bflabs_readiness/evals.py",
    "src/bflabs_readiness/packaging.py",
    "src/bflabs_readiness/providers/geo_discover.py",
    "src/bflabs_readiness/providers/geo_content.py",
    "src/bflabs_readiness/providers/geo_measure.py",
    "src/bflabs_readiness/providers/seo_plan.py",
    "scripts/run_evals.py",
    "scripts/package.py",
    "scripts/verify_packages.py",
    "references/root-agent-contract.md",
    "references/routing.md",
    "references/product-boundary.md",
    "references/licensing-and-attribution.md",
    "references/round-record.md",
    "src/bflabs_readiness/geo_round.py",
    "templates/readiness-report.json",
    "templates/round-experiment.json",
    "templates/round-facts.json",
    "templates/round-questions.json",
    "templates/round-actions.json",
    "templates/round-business-events.json",
    "templates/round-report.md",
    "examples/beefapi-deidentified-artifact-pack.json",
    "examples/beefapi-readiness-case.md",
    "docs/architecture.md",
    "docs/artifact-protocol.md",
    "docs/install-codex-claude.md",
    "docs/release-checklist.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "workflows/discover-diagnose.md",
    "workflows/discover-content.md",
    "evals/trigger_cases.json",
    "skills/geo-optimize/SKILL.md",
    "skills/geo-discover/SKILL.md",
    "skills/geo-content/SKILL.md",
    "skills/geo-measure/SKILL.md",
    "skills/seo-plan/SKILL.md",
    "skills/webmcp-enable/SKILL.md",
    "app/readiness-web/package.json",
    "app/readiness-web/public/index.html",
    "app/readiness-web/public/app.js",
    "app/readiness-web/README.md",
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        fail(f"missing {relative}")

agents = (ROOT / "AGENTS.md").read_text("utf-8")
user_copy_rule = "用户看见的字只对使用者负责。实现约束用来遵守，不要写进产品。没见过这次讨论的人读不懂的句子，就不该出现。"
if user_copy_rule not in agents:
    fail("project AGENTS.md must preserve the user-facing copy rule")

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

skill_body = skill[frontmatter.end():]
visible_skill_body = re.sub(r"<!--.*?-->", "", skill_body, flags=re.S)
visible_copy_text = re.sub(r"\]\([^)]+\)", "]", visible_skill_body)
if "![" in visible_skill_body or re.search(r"<img\b", visible_skill_body, re.I):
    fail("root Skill body must not embed a logo or other image")
if len(re.findall(r"[\u4e00-\u9fff]", visible_copy_text)) < 100:
    fail("root Skill body must remain Chinese-first for the public SkillHub page")
for implementation_term in [
    "not_measured",
    "ai_visibility",
    "business_outcome",
    "扫描指纹",
    "路由",
    "验证命令",
    "外部读回",
    "回滚",
    "报告合同",
    "Agent Skills 索引",
    "--publish-to-leaderboard",
    "readiness-report.json",
]:
    if implementation_term in visible_copy_text:
        fail(f"root Skill rendered copy exposes implementation language: {implementation_term}")
for user_outcome in ["免费检查网站", "把提示词和网站仓库交给你自己的 Agent", "部署后再次检查", "联系 BFLabs", "榜单默认不会公开"]:
    if user_outcome not in visible_copy_text:
        fail(f"root Skill rendered copy is missing the user outcome: {user_outcome}")
if re.search(r"\]\((?:references|skills|templates|app)/", visible_skill_body):
    fail("root Skill rendered copy must not expose repository-relative implementation links")
if "references/root-agent-contract.md" not in skill_body:
    fail("root Skill must point agents to the Agent-only root contract")

agent_contract = (ROOT / "references/root-agent-contract.md").read_text("utf-8")
for routed_path in [
    "skills/geo-discover/SKILL.md",
    "skills/geo-content/SKILL.md",
    "skills/geo-measure/SKILL.md",
    "skills/seo-plan/SKILL.md",
    "skills/geo-optimize/SKILL.md",
    "skills/webmcp-enable/SKILL.md",
    "app/readiness-web/README.md",
    "references/routing.md",
    "references/product-boundary.md",
]:
    if routed_path not in agent_contract:
        fail(f"Agent-only root contract does not route to {routed_path}")

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
for required_id in [
    'id="download-report"',
    'id="copy-agent-prompt"',
    'id="evidence-gaps"',
    'id="opportunities"',
    'id="skill-routes"',
]:
    if required_id not in app_html:
        fail(f"diagnostic app is missing protocol UI control {required_id}")
if "三项分别计分" not in app_html or "外部 AI 平台表现" not in app_html or "业务结果" not in app_html:
    fail("diagnostic app does not state the scoring and measurement boundary")

app_js = (ROOT / "app/readiness-web/public/app.js").read_text("utf-8")
if "artifact_pack" not in app_js or "agent_prompt" not in app_js:
    fail("diagnostic app does not consume Artifact Pack and Agent prompt data")

if "MIT License" not in (ROOT / "LICENSE").read_text("utf-8"):
    fail("root LICENSE is not MIT")
if 'license = { text = "MIT" }' not in (ROOT / "pyproject.toml").read_text("utf-8"):
    fail("pyproject license is not MIT")

registry = json.loads((ROOT / "registry/capabilities.json").read_text("utf-8"))
capability_ids = [capability["id"] for capability in registry["capabilities"]]
if len(capability_ids) != len(set(capability_ids)):
    fail("duplicate capability ids")
for capability in registry["capabilities"]:
    if capability["status"] == "active" and not capability["entrypoint"]:
        fail(f"active capability lacks entrypoint: {capability['id']}")
    if capability["status"] == "planned" and capability["entrypoint"] is not None:
        fail(f"planned capability exposes entrypoint: {capability['id']}")

workflows = json.loads((ROOT / "registry/workflows.json").read_text("utf-8"))["workflows"]
if {workflow["id"] for workflow in workflows} != {"discover-diagnose", "discover-content"}:
    fail("registry must contain exactly the two approved workflows")

router_cases = json.loads((ROOT / "evals/router_cases.json").read_text("utf-8"))["cases"]
if len(router_cases) < 40:
    fail("router eval needs at least 40 bilingual and boundary cases")

allowed_suffixes = {".md", ".json", ".yaml", ".yml", ".py", ".js", ".mjs", ".toml"}
ignored_parts = {".git", ".grok-companion", ".receipts", "node_modules", ".venv", "dist", "build", "runs"}
for path in ROOT.rglob("*"):
    if not path.is_file() or ignored_parts.intersection(path.parts) or path.suffix not in allowed_suffixes:
        continue
    content = path.read_text("utf-8")
    mac_user_prefix = "/" + "Users/"
    windows_user_prefix = "C:" + "\\Users\\"
    if mac_user_prefix in content or windows_user_prefix in content:
        fail(f"private absolute path leaked in {path.relative_to(ROOT)}")
    stale_repo = "Sunnyender-org/" + "geo-optimize"
    if stale_repo in content:
        fail(f"stale repository URL in {path.relative_to(ROOT)}")
    license_marker = "SPDX-License-Identifier:"
    agpl_token = "A" + "GPL"
    if license_marker in content and agpl_token in content:
        fail(f"{agpl_token}-licensed implementation marker in {path.relative_to(ROOT)}")

print(
    f"PASS: bflabs-agent-readiness repository "
    f"({positive} positive routes, {negative} negative routes, {len(capability_ids)} capabilities)"
)
