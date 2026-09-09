# Changelog

All notable changes to the public release candidate are documented here.

## 0.5.0 - 2026-09-09

- Described the free single-website GEO round in the root Skill (facts and goals, baseline before any change, issues and pages, change, public retest, answer comparison, business review, report, next round) and added a fixed start prompt that only points to the root Skill URL.
- Added the Agent-only round contract: request classification, per-phase precondition checks, a mandatory real-baseline gate before answer-affecting changes, resume-from-record rules, and the resource URL scheme. Full-round and continuation requests route to the root capability; the two CLI workflows remain the only automatic multi-capability executions.
- Served every Skill's companion files online at `/skills/<id>/<path>` with a versioned, SHA-256 manifest at `/skills/<id>/manifest.json`, ETag/304 support, traversal rejection, and honest 404s; a test proves the whole reference graph resolves from the root Skill and that served files are a subset of the Skill Hub package.
- Extended geo-measure with rounds, sample slots, technical-failure replacements, duplicate-import exclusion, four observation lines, collection method, answer verdicts, before/after pairing with comparability reasons, and a readable stage table. Legacy single-batch input produces the same six metrics.
- Added the portable single-site round record (experiment, facts, questions, actions, business events) with schemas, flat templates, cross-file validation, business-window analysis that never turns unknown coverage into zero, a Chinese stage report, and `bflabs-readiness round validate|status|report`.
- Added the per-page fact checklist, three content layers, schema-must-match-body rule, issue classification, action lifecycle, and the frozen question-set method to geo-optimize, geo-discover, and geo-content; corrected the stale `discover-content` availability note.
- Reframed the free/service boundary: the complete method is free; BFLabs' service is BFLabs performing implementation, repeated sampling, hosting, monitoring, and ongoing review.

## 0.4.6 - 2026-08-27

- Reworked Actionable scoring around two capabilities: a stable human fallback and at least one structured Agent task path.
- Made verified WebMCP and typed MCP alternative implementations of the same task-path capability so they cannot be double-counted.
- Kept static WebMCP signals as `present_unverified`; absence or non-applicability no longer imposes a universal 25-point penalty.
- Added `not_applicable` and `blocked` WebMCP evidence states while preserving `unknown` for missing evidence.

## 0.4.5 - 2026-08-23

- Rewrote the rendered SkillHub body around the user workflow: diagnose, copy to an Agent, authorize changes, deploy, and retest.
- Moved status enums, routing mechanics, validation receipts, interfaces, and rollback instructions into an Agent-only root contract.
- Added a repository gate that rejects implementation-language regressions in the rendered root Skill body.

## 0.4.4 - 2026-08-23

- Rewrote the public SkillHub body in user-facing Chinese while preserving the three-layer product boundary.
- Removed the body-level Markdown logo that broke on external hosts; the approved BFLabs card icon remains platform-managed.
- Added a repository check that prevents the root Skill body from regressing to an English-first or embedded-image presentation.
- Exposed the documented `skillhub` package target through the installed CLI and covered it with a regression test.
- Excluded local virtual environments from source-package discovery.

## 0.4.3 - 2026-08-23

- Bound the approved BFLabs SkillHub icon URL into the portable publication metadata.

## 0.4.2 - 2026-08-23

- Excluded local Wrangler state and generated Worker build output from source packages.
- Added a verified, platform-bounded SkillHub ZIP that stays under 200 files, uses supported file types, and includes the BFLabs logo.

## 0.4.1 - 2026-08-23

- Added the official SkillHub front-matter fields and a portable BFLabs logo asset so the public Skill can be uploaded without platform-specific repackaging.
- Aligned the packaged CLI user-agent with the installed package version.

## 0.4.0 - 2026-08-23

- Made the diagnostic result prompt-first: one click copies the current evidence, root Skill, and the single owning child Skill directly to an Agent.
- Added deterministic Agent Journey evidence for entering, understanding, and continuing through one bounded public path without changing readiness scores.
- Added versioned JSON and Markdown scan responses, a packaged remote CLI, a read-only MCP surface, OpenAPI, `llms.txt`, and a SHA-256-bound Agent Skills index.
- Added an explicit opt-in public leaderboard with server-rendered share pages, disclosed ranking, summary-only storage, and 30-day retention.
- Added stable site-hosted root and child Skill URLs for external SkillHub and agent-host discovery.

## 0.3.0 - 2026-08-11

- Added the bilingual root router, seven active capabilities, and exactly two stable workflows.
- Added Artifact Protocol 1.0.0, JSON Schemas, evidence ledger, quality report, manifest hashes, and atomic run publication.
- Added `geo-discover`, `geo-content`, `geo-measure`, and `seo-plan` beside the existing `geo-optimize` and `webmcp-enable` Skills.
- Added seven evidence-bounded content modes, offline visibility measurement, official-source SEO planning, and dynamic-fact freshness gates.
- Migrated the local diagnostic app to the shared readiness schema while preserving its legacy response compatibility surface and promoting the committed Grok BFLabs prototype as the canonical visual shell.
- Added downloadable Artifact Packs, Agent handoff prompts, 360px and accessibility regression checks.
- Added source, unified wheel, and six independent child Skill packages with allowlist and isolated-install verification.

GitHub release creation, package upload, and public deployment remain separate Owner gates.
