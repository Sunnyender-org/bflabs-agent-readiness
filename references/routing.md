# Routing

## Unified Router Contract

Use `bflabs-readiness route --text` when a portable machine-readable decision is needed. The router applies this order:

1. reject forbidden guarantees, bulk publishing, hidden admin exposure, auth bypass, and autonomous payments;
2. recognize only the two explicit multi-stage requests below;
3. honor one explicitly named capability;
4. select the smallest matching capability for a single intent;
5. return `needs_clarification` when the request is ambiguous or outside this product.

The only workflow definitions are:

- `discover-diagnose`: `geo-discover -> geo-optimize`;
- `discover-content`: `geo-discover -> geo-content`.

Both approved workflows are active and must run as one atomic workflow. Any planned capability is returned as non-executable with its nearest active fallback. Routing recognition is not permission to run an incomplete provider or cross an external gate.

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

Use `skills/seo-plan/SKILL.md` for migration, indexing, international, or technical SEO planning. It produces evidence gaps, prioritized read-only checks, captured official-source context, and owner-gated rollback-ready implementation actions. It does not access Search Console, mutate a CMS/server, or run live ranking queries.

## Route to `webmcp-enable`

Use `skills/webmcp-enable/SKILL.md` when the requested outcome includes:

- native WebMCP registration;
- connecting a same-origin MCP server to WebMCP;
- enabling Cloudflare WebMCP or a tool pack;
- compatible-browser or BrowserRun tool discovery and task calls;
- security review of browser Agent tools.

External enablement and production mutations are explicit-only. A local audit does not authorize them.

## Route to the diagnostic app

Use `app/readiness-web` only for bounded, read-only inspection of public fixed paths. Treat its score as an evidence index, not a ranking or business score.

## Do not route here

- generic SEO, backlink purchasing, or bulk content;
- real-platform ranking guarantees;
- hidden admin or permission mutation exposure;
- autonomous payment or credential handling;
- conversion or revenue attribution without customer-authorized data.
