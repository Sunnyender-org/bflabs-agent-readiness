# Routing

## Request classes

Classify every request as exactly one of:

1. **no-site** — there is no public URL yet, or the user only wants site-foundation / build-only work. Select `seo-plan`. Do not invent a public URL. Do not start unrelated sampling. Do not open a round experiment.
2. **existing-site** — a real site or public URL is in scope. Pick the smallest matching capability, or an explicit full round if that is what was asked.
3. **explain-only** — a definition or method explanation, including “how attribution works” with do-not-execute. Answer and stop. The router returns `needs_clarification`. Do not start a capability, workflow, or round.
4. **single-item** — one child Skill, one registered CLI workflow, or one offline analysis of a supplied export. Never escalate into a full round. Attribution-only analysis does not select `bflabs-agent-readiness`.
5. **full-round** — an explicit request to run the free method end to end for one existing site. Select `bflabs-agent-readiness`. The two CLI workflows are not a full round.
6. **resume** — an explicit request to continue an existing project record. Select `bflabs-agent-readiness`. Start at `next_step`. Do not redo already-released actions.

Older records remain readable. Do not fabricate identity, survey, refund, or business-window fields that the record does not contain.

## Unified Router Contract

Use `bflabs-readiness route --text` when a portable machine-readable decision is needed. The router applies this order:

1. reject forbidden guarantees, bulk publishing, hidden admin exposure, auth bypass, and autonomous payments;
2. return `needs_clarification` for a bare ambiguous GEO/SEO/website ask;
3. return `needs_clarification` for explain-only, attribution-only, and do-not-execute requests so they cannot match a workflow or a full round;
4. select `seo-plan` for no-site / build-only / site-foundation requests;
5. recognize only the two explicit multi-stage requests below;
6. honor one explicitly named capability;
7. recognize an explicit full-round or resume request as root Skill guidance;
8. select the smallest matching capability for a single intent;
9. return `needs_clarification` when the request is ambiguous or outside this product.

The only workflow definitions are:

- `discover-diagnose`: `geo-discover -> geo-optimize`;
- `discover-content`: `geo-discover -> geo-content`.

Both approved workflows are active and must run as one atomic workflow. They are not a full round and must not be advertised as one. Any planned capability is returned as non-executable with its nearest active fallback. Routing recognition is not permission to run an incomplete provider or cross an external gate.

## Route to `geo-discover`

Use `skills/geo-discover/SKILL.md` when the requested outcome is a traceable question or opportunity map across audience, scenario, comparison, decision, price/cost, integration, and limitation. Opportunity scoring may use only coverage gap, evidence gap, and declared business relevance; it must not invent search volume.

## Route to `geo-optimize`

Use `skills/geo-optimize/SKILL.md` when the requested outcome is repository-local:

- audit public facts, answer pages, schema, sitemap, robots, or `llms.txt`;
- repair volatile pricing or other machine-readable facts;
- check Agent Actionability without implementing WebMCP;
- verify approved GEO changes.

## Route to `geo-content`

Use `skills/geo-content/SKILL.md` for one bounded evidence-linked content mode: title, explainer, comparison, ranking with disclosed method, page blueprint, refine, or article-friendly restructuring. Stale dynamic facts, unsupported claims, asymmetric comparisons, and rankings without method are blocked. Publication always remains owner-gated.

## Route to `geo-measure`

Use `skills/geo-measure/SKILL.md` only to aggregate user-supplied model-answer observations. It accepts JSON, JSONL, or CSV, preserves platform/terminal strata, reports numerator/denominator/excluded/missing counts and Wilson intervals, and excludes ordinary web search results. It does not perform platform sampling or infer causality and business outcomes.

## Route to `seo-plan`

Use `skills/seo-plan/SKILL.md` for migration, indexing, international, or technical SEO planning, and for site-foundation planning when there is no public URL yet. A no-site or build-only request selects this capability. It produces evidence gaps, prioritized read-only checks, captured official-source context, and owner-gated rollback-ready implementation actions. It does not invent a public URL, start unrelated AI sampling, access Search Console, mutate a CMS/server, or run live ranking queries.

## Route to `webmcp-enable`

Use `skills/webmcp-enable/SKILL.md` when the requested outcome includes:

- native WebMCP registration;
- connecting a same-origin MCP server to WebMCP;
- enabling Cloudflare WebMCP or a tool pack;
- compatible-browser or BrowserRun tool discovery and task calls;
- security review of browser Agent tools.

External enablement and production mutations are explicit-only. A local audit does not authorize them.

## Full round and resume

Route an explicit full-round request, or an explicit resume of an existing round, to the root Skill's guidance. The selected capability is `bflabs-agent-readiness`. Follow `references/root-agent-contract.md` and `references/round-contract.md`.

Resume starts at the recorded `next_step`. It does not redo an action whose status is already `released` or `verified_public`, and it does not recapture a baseline that already exists for the same frozen questions.

The two CLI workflows remain the only automatic multi-capability executions. A full round is not `discover-diagnose` and is not `discover-content`. Do not claim those workflows captured a baseline, released a change, retested public answers, compared AI answers, or reviewed business data.

Explain-only requests are answered without executing a capability or a workflow. A definitional prompt such as what GEO is, how attribution works, or a do-not-execute instruction must not start a round or a workflow.

A single-item request — including attribution on one supplied business export — is never escalated into a full round.

## Route to the diagnostic app

For a URL-only readiness check, first read `skills/geo-optimize/references/readiness-rules.md` (online: https://readiness.bflabs.cn/skills/geo-optimize/references/readiness-rules.md). These same judgment rules apply even without a repository or a repair request.

Use `app/readiness-web` only for bounded, read-only inspection of public fixed paths. Treat its score as an evidence index, not a ranking or business score.

## Do not route here

- generic SEO, backlink purchasing, or bulk content;
- real-platform ranking guarantees;
- hidden admin or permission mutation exposure;
- autonomous payment or credential handling;
- conversion or revenue attribution without customer-authorized data.
