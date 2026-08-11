---
name: geo-content
description: Produce evidence-linked GEO content specifications and Markdown in one of seven bounded modes. Use for titles, explainers, comparisons, disclosed-method rankings, page blueprints, evidence-preserving refinements, or AI-friendly article restructuring. Not for unsupported facts, stale dynamic prices, fake citations, undisclosed rankings, bulk publishing, or publication without owner approval.
metadata:
  short-description: Produce bounded evidence-linked GEO content
  sunny_skill_type: library
---

# GEO Content

Generate content only from the fact units and evidence sources in a schema-valid content brief.

## Modes

- `title`: evidence-safe title direction;
- `explainer`: definition, operation, limits, and evidence;
- `comparison`: symmetric targets and dimensions;
- `ranking`: only with a disclosed method and dataset scope;
- `page-blueprint`: answer-page structure, canonical facts, freshness, and next action;
- `refine`: local improvement that requires source Markdown;
- `article-friendly`: evidence-preserving restructuring that requires source Markdown.

Read [references/content-contract.md](references/content-contract.md) before producing output. Use [templates/content-brief.json](templates/content-brief.json) as the portable input shape. The GPT-5.6 price blueprint example is [examples/beefapi-gpt-5-6-content-brief.json](examples/beefapi-gpt-5-6-content-brief.json).

## Workflow

1. Validate every fact against an evidence id, content hash, and dynamic fact version when applicable.
2. Stop publication when a fact is unsupported or stale. Return the blocker; do not silently omit or refresh it from an unapproved source.
3. Apply the selected mode contract. Comparison requires symmetric dimensions; ranking requires a disclosed method and dataset scope.
4. Emit `content-spec.json`, `content-evidence-units.json`, and `content.md` through Artifact Protocol 1.0.
5. Keep publication behind `owner-approval-required`. A passing artifact pack is not permission to edit a site, deploy, or bulk publish.

## Boundaries

- Internal evidence markers are provenance links, not claims of external citations.
- Do not claim ranking, recommendation, conversion, or revenue effects.
- Do not treat discovery opportunity scores as search volume.
- Dynamic price claims must match the canonical evidence hash and `fact_version` captured in the brief.
- HTML is not a v1 output format. If HTML is added later, user-controlled strings must be escaped and independently tested.

## Verification

```bash
bflabs-readiness run --capability geo-content --input content-brief.json --output runs
bflabs-readiness validate --run runs/run-id
```
