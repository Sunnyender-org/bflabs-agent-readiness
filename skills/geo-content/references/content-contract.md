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

## Output boundary

Markdown uses internal claim markers that map to the evidence ledger. They prove local traceability only. They do not imply that an external model, search engine, or publisher cited the content.

Publishing, deployment, CMS writes, and bulk generation require separate approval and are not performed by this Skill.
