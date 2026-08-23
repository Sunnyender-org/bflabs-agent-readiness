# Root Agent Contract

This file is Agent-only. Do not project its status names, routing mechanics, file paths, validation receipts, or rollback language into rendered product copy.

## Required reading

Read `references/routing.md` before selecting a child Skill. Read `references/product-boundary.md` before making product claims or proposing paid delivery. For a local read-only domain scan, follow `app/readiness-web/README.md`.

## Workflow

1. Classify the input as a public URL, repository, or prior report.
2. Record evidence for Discoverable, Understandable, and Actionable before recommending changes.
3. Select only the smallest active capability unless the request explicitly matches one of the two registered workflows.
4. Keep `ai_visibility` and `business_outcome` as `not_measured` unless separate evidence satisfies their contracts.
5. Treat `agent_journey` as supporting public-page evidence only. It never changes readiness scores and never establishes AI visibility or business outcome.
6. For approved repository changes, return changed paths, deterministic checks, external readback, unresolved gates, and a rollback route when applicable.

## Capability routing

- Question and opportunity discovery: `skills/geo-discover/SKILL.md`
- Evidence-linked content work: `skills/geo-content/SKILL.md`
- Offline aggregation of supplied AI observations: `skills/geo-measure/SKILL.md`
- Evidence-bounded technical SEO planning: `skills/seo-plan/SKILL.md`
- Repository-local public-fact and readiness work: `skills/geo-optimize/SKILL.md`
- MCP or WebMCP implementation and verification: `skills/webmcp-enable/SKILL.md`

`geo-optimize` may change an approved local repository but does not enable external services. `webmcp-enable` requires explicit authorization for real browser sessions, permissions, third-party services, or production-facing actions.

## Output contract

A valid result contains:

- independent Discoverable, Understandable, and Actionable states;
- evidence URLs or repository paths;
- failed, blocked, and unknown predicates;
- exactly one owning child Skill for a single repair intent;
- verification commands and receipts;
- `ai_visibility` and `business_outcome` states;
- external or production gates that remain unresolved.

Use `templates/readiness-report.json` for a portable machine-readable report.

## Package and public interfaces

```bash
bflabs-readiness scan https://example.com --format json
bflabs-readiness scan https://example.com --format markdown
bflabs-readiness list --format markdown
bflabs-readiness read geo-optimize
bflabs-readiness route --text "Audit this website for GEO readiness"
bflabs-readiness run --workflow discover-diagnose --input workflow-request.json --output runs
bflabs-readiness run --workflow discover-content --input workflow-request.json --output runs
bflabs-readiness validate --run runs/run-id
bflabs-readiness eval
bflabs-readiness package --target source
bflabs-readiness package --target unified
bflabs-readiness package --target skillhub
```

- Agent Skills index: `https://readiness.bflabs.cn/.well-known/agent-skills/index.json`
- Root Skill: `https://readiness.bflabs.cn/skills/bflabs-agent-readiness`
- OpenAPI: `https://readiness.bflabs.cn/openapi.json`
- MCP: `https://readiness.bflabs.cn/mcp`
- SkillHub: `https://skillhub.cn/skills/user_49f8ec71/bflabs-agent-readiness`

The website, CLI, Markdown response, and MCP scan tool use the same report contract. `scan` does not publish to the leaderboard unless the caller explicitly requests it. The leaderboard may store only the opted-in domain summary, three readiness axes, scan time, and fingerprint under the disclosed retention policy.

## Compatibility boundary

The deterministic router returns one capability for a single intent. It returns a workflow DAG only for explicit `discover-diagnose` or `discover-content` requests. Both workflows publish one atomic run. Planned or forbidden routes must never execute silently.
