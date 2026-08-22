# Architecture

BFLabs Agent Readiness is one MIT repository with three delivery surfaces:

```text
Natural-language request
  -> bilingual router
    -> one smallest child Skill
    -> or one of exactly two explicit workflows
      -> Artifact Protocol run
        -> evidence ledger + quality report + typed outputs + manifest hashes
```

The diagnostic app is another consumer of the same readiness report schema. It is not a separate product and does not own a second score model. Its web UI, versioned API, Markdown response, packaged CLI, and MCP scan tool return the same scan object.

## Capability registry

The root capability and six child Skills are declared in `registry/capabilities.json`. The registry records status, entrypoint, input schema, output types, permissions, external gates, and degradation behavior. A planned capability cannot expose an entrypoint; an active capability must have one.

One intent enters one smallest capability. Multi-stage execution occurs only for:

- `discover-diagnose`: question discovery, then brand/site diagnosis;
- `discover-content`: question discovery, then evidence-bounded content production.

## Modules and seams

- `registry.py`: capability and workflow contracts.
- `router.py`: deterministic Chinese/English intent selection and forbidden boundaries.
- `orchestrator.py`: the two explicit workflow DAGs.
- `artifacts.py`: atomic publication, file hashing, replay validation, and path safety.
- `evidence.py`: evidence normalization and claim linkage.
- `quality.py`: schema, freshness, unsupported-claim, and measurement-boundary gates.
- `providers/`: deterministic adapters for offline and local runs.
- `packaging.py`: release allowlists and archive safety checks.
- `app/readiness-web/src/product-contract.mjs`: Markdown projection, structured problems, methodology, and public interface constants.
- `app/readiness-web/src/leaderboard.mjs`: explicit opt-in summary publication and disclosed three-axis ordering.
- `app/readiness-web/src/mcp-server.mjs`: read-only Agent host tools over the same public report contract.

## Public Agent seam

The public site hosts the root and child Skills and publishes a SHA-256-bound Agent Skills index. A generated repair prompt selects one child Skill and includes enough current evidence to remain useful if the Agent cannot fetch the Skill.

Agent Journey is a deterministic enter-understand-continue trace derived from already fetched public responses. It is stored in the scan report but has `affects_readiness_score: false`, `ai_visibility: not_measured`, and `business_outcome: not_measured`.

The public leaderboard is opt-in. Its runtime truth owner is `leaderboard.mjs`; it stores only canonical origin, three readiness axes, scan fingerprint, and capture time. Ranking is lexicographic by passed-axis count, weakest-axis score, then average axis score, and is disclosed in the UI. No combined score enters the report contract. Each opted-in entry has a server-rendered `/leaderboard/{host}` share page so search visibility does not depend on client-side leaderboard rendering.

## Measurement model

Readiness has three independent axes: Discoverable, Understandable, and Actionable. AI visibility and business outcome are separate evidence domains. A site can be technically ready without being cited, recommended, or converting; a single model response cannot establish stable platform behavior.

## External action seam

Open-source providers stop at public evidence, local code changes, offline aggregation, and owner-gated plans. Real platform sampling, private consoles, CMS or infrastructure mutation, production deployment, monitoring, and attribution belong to separately authorized adapters and receipts.
