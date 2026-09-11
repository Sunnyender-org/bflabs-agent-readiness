---
name: seo-plan
description: Produce an evidence-bounded technical SEO plan for migrations, indexing issues, international sites, technical SEO scope, or a missing-site foundation plan. Use for read-only checks covering robots, page-level directives, canonical, redirects, sitemap, IndexNow, structured data, Core Web Vitals lab/field evidence, AI crawlers, and hreflang. Not for live Search Console access, CMS or server mutation, ranking queries, backlink campaigns, site rebuilds, or indexing and traffic guarantees.
metadata:
  short-description: Plan technical SEO checks and gated implementation
  sunny_skill_type: library
---

# SEO Plan

Build a plan from supplied site evidence and a captured registry of current official guidance. Do not perform live Search Console, Bing Webmaster Tools, CMS, server, DNS, or ranking actions.

Read [references/technical-scope.md](references/technical-scope.md) before planning. Use [templates/seo-plan-brief.json](templates/seo-plan-brief.json) for input. A migration example is provided at [examples/migration-brief.json](examples/migration-brief.json). When the owner has no site, or asks only for a site foundation, also follow https://readiness.bflabs.cn/skills/bflabs-agent-readiness/references/site-foundation.md.

## Workflow

1. Record target, change type, symptoms, constraints, supplied observations, and evidence. If there is no public site, record that fact and plan the smallest publishable foundation. Do not invent a public URL.
2. Keep missing categories as evidence gaps. Never turn a missing scan or unavailable console into a failed finding.
3. Create prioritized read-only checks linked to captured Google, Microsoft Bing, IndexNow, and OpenAI official sources.
4. Create implementation actions only for confirmed failed observations. For a no-site plan, list the smallest pages, ordinary internal links, HTTPS, and the deploy handoff. Prefer fixing existing pages. Several questions may share one page. Six questions do not require six new pages. Do not rebuild an existing site.
5. Require owner approval, preconditions, and rollback for every implementation action. Actual scaffolding and deploy belong to the host Agent.
6. Emit `seo-plan.json`, `official-sources.json`, an evidence ledger, and quality report through Artifact Protocol 1.0. A site-foundation plan is still a plan, not a built site.

## Boundaries

- `robots.txt`, meta robots, and `X-Robots-Tag` are distinct controls.
- Search crawlers, AI search crawlers, and training/user agents are not interchangeable.
- Lab Core Web Vitals are not field data.
- Sitemap or IndexNow submission is not an indexing guarantee.
- Valid structured data does not guarantee a rich result.
- A technically correct plan does not prove ranking, traffic, conversion, or revenue.
- A no-site or foundation plan does not create a round experiment and does not start AI sampling unless the owner asked for a full round.

## Command

```bash
bflabs-readiness run --capability seo-plan --input seo-plan-brief.json --output runs
```
