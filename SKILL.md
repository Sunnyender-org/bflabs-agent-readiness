---
name: bflabs-agent-readiness
description: Diagnose and improve whether a product website is discoverable, understandable, and actionable by AI agents. Use when auditing a public website or repository, routing evidence-backed GEO repairs, exposing approved WebMCP tools, or verifying a readiness report. Not for ranking guarantees, bulk SEO content, hidden admin exposure, autonomous payments, production traffic changes, or business-outcome attribution without independent evidence.
metadata:
  short-description: Diagnose, improve, and verify AI-agent website readiness
  sunny_skill_type: library
---

# BFLabs Agent Readiness

Treat website readiness as three independent questions:

1. **Discoverable**: can public pages and machine entry points be found?
2. **Understandable**: are product facts explicit, current, and internally consistent?
3. **Actionable**: can an Agent complete approved tasks through stable links, typed tools, MCP, or WebMCP?

Never fold Actionable into a GEO indexing score. Never present readiness as proof of ranking, recommendation, conversion, or revenue.

## Workflow

1. Identify whether the input is a public URL, an existing repository, or a prior report.
2. Record evidence for all three axes before recommending changes.
3. Route only the smallest necessary repair:
   - For evidence-backed question and opportunity discovery, read and follow [skills/geo-discover/SKILL.md](skills/geo-discover/SKILL.md).
   - For evidence-linked titles, explainers, comparisons, rankings, page blueprints, refinements, or article restructuring, read and follow [skills/geo-content/SKILL.md](skills/geo-content/SKILL.md).
   - For offline aggregation of supplied AI answer observations, read and follow [skills/geo-measure/SKILL.md](skills/geo-measure/SKILL.md).
   - For evidence-bounded technical SEO planning, read and follow [skills/seo-plan/SKILL.md](skills/seo-plan/SKILL.md).
   - For repository-local GEO and public-fact work, read and follow [skills/geo-optimize/SKILL.md](skills/geo-optimize/SKILL.md).
   - For WebMCP implementation, external enablement, or compatible-browser task verification, read and follow [skills/webmcp-enable/SKILL.md](skills/webmcp-enable/SKILL.md).
   - For a local read-only domain scan, use [app/readiness-web/README.md](app/readiness-web/README.md).
4. Keep AI visibility and business outcome explicitly `not_measured` unless separate evidence exists.
5. Return changed paths, deterministic checks, external readback, unresolved gates, and a rollback route when applicable.

## Routing Boundary

Read [references/routing.md](references/routing.md) before choosing a sub-Skill. Read [references/product-boundary.md](references/product-boundary.md) before making product claims or proposing paid delivery.

`geo-optimize` may repair an approved local repository but does not enable external services. `webmcp-enable` is explicit-only for real Cloudflare, BrowserRun, browser-session, permission, or production-facing actions.

## Output Contract

A valid readiness result includes:

- independent Discoverable, Understandable, and Actionable states;
- evidence URLs or repository paths;
- failed or blocked predicates;
- the owning sub-Skill for each repair;
- verification commands and receipts;
- `ai_visibility` and `business_outcome` states;
- any external or production gate still requiring the owner.

Use [templates/readiness-report.json](templates/readiness-report.json) when a portable machine-readable report is required.

## Agent-readable Package Interface

```bash
bflabs-readiness list --format markdown
bflabs-readiness read geo-optimize
bflabs-readiness route --text "Audit this website for GEO readiness"
bflabs-readiness run --text "先挖掘用户问题，然后诊断网站" --input workflow-request.json --output runs
bflabs-readiness run --capability geo-discover --input discovery-brief.json --output runs
bflabs-readiness run --workflow discover-diagnose --input workflow-request.json --output runs
bflabs-readiness run --capability geo-content --input content-brief.json --output runs
bflabs-readiness run --workflow discover-content --input workflow-request.json --output runs
bflabs-readiness run --capability geo-measure --input observations.json --output runs
bflabs-readiness run --capability seo-plan --input seo-plan-brief.json --output runs
bflabs-readiness run --capability geo-optimize --input request.json --output runs
bflabs-readiness validate --run runs/run-id
bflabs-readiness eval
bflabs-readiness package --target source
bflabs-readiness package --target unified
bflabs-readiness package --target geo-optimize
```

The legacy interface remains available during the v1 compatibility window:

```bash
python3 scripts/skill_registry.py list --format markdown
python3 scripts/skill_registry.py read skills/geo-optimize/SKILL.md
python3 scripts/skill_registry.py validate
```

The legacy registry read wrapper exposes only Skill SOP files. It refuses scripts, private receipts, arbitrary paths, and generated artifacts. Release packages use a separate explicit allowlist and include only declared portable assets. Successful runtime executions publish an atomic Artifact Protocol run with a manifest, evidence ledger, quality report, and schema-validated capability outputs.

The deterministic router returns one minimum capability for a single intent. It returns a workflow DAG only for an explicit discovery-then-diagnosis or discovery-then-content request. Both approved workflows are executable and publish one atomic run; other planned routes remain non-executable and expose an active fallback without silently running hidden stages.
