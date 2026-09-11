# Content Contract

## Required evidence rules

- Every rendered factual sentence is a `direct` or `derived` fact unit.
- Every fact unit links to existing evidence ids.
- `evidence_hash` binds the fact to the primary canonical evidence snapshot.
- Dynamic facts additionally bind to a non-empty `fact_version` that matches that snapshot.
- A mismatch is `stale` and blocks artifact publication.

## Mode-specific gates

- Comparison: at least two targets and one shared comparison dimension.
- Ranking: method title, criteria, and dataset scope are mandatory. No data or no method means blocked.
- Refine and article-friendly: source Markdown is mandatory.
- Page blueprint: direct answer, pricing/facts, integration/action, and source/freshness sections remain distinct.

## Whitehat page rules

Write real product value for a person who will read the page and take the next step. Use ordinary internal links between related pages. Cite real sources and the dates when the body actually changed.

Do not require a page to leave human navigation. Do not invent reviews, testimonials, or authority. Do not change a date to make an unchanged page look new. A legal or policy page that is reachable from the footer or a related page, but not from the top menu, is not a defect.

Prefer an existing page. Several questions may share one page when they use the same facts and the same task. Do not create a new page for every wording variant.

人和 AI 看到同一批事实。格式可以不同，不能给机器单独加一套正文没有的断言。

## Output boundary

Markdown uses internal claim markers that map to the evidence ledger. They prove local traceability only. They do not imply that an external model, search engine, or publisher cited the content.

Publishing, deployment, CMS writes, and bulk generation require separate approval and are not performed by this Skill.

## Facts From A Round Record

When a content brief draws facts from a project-record `facts.json`:

- Carry each fact's `evidence_status`.
- `forbidden` and `conflict` never enter drafts.
- `unverified` may appear only as clearly marked pending.
- If `source_hash` or the source content changed, prior verification is stale; re-check before reuse.

