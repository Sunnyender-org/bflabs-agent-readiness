# Opportunity Method

## Coverage

- `covered`: the supplied brief declares that a public page already addresses the dimension;
- `missing`: the supplied brief does not declare coverage;
- `partial` and `unknown` are reserved for future evidence adapters and must not be guessed by the deterministic provider.

Coverage gap is `0` for covered and `2` for missing.

## Evidence

Evidence gap is `0` when the query traces to a supplied source item and `1` when it depends on an explicit assumption. Evidence gap does not measure truth quality, citation probability, or authority.

## Business Relevance

Business relevance is `3` only for dimensions explicitly listed by the user as priorities. Other dimensions receive `1`. The provider does not infer commercial value, conversion rate, or revenue.

## Priority

```text
priority_score = coverage_gap + evidence_gap + business_relevance
```

The score ranges from 1 to 6 and is only an explainable work-order heuristic. It is not search demand, ranking difficulty, AI visibility, or expected business impact.
