---
name: geo-measure
description: Aggregate user-supplied AI answer observations into denominator-explicit GEO visibility metrics with platform and terminal strata. Use for ChatGPT, Gemini, Tencent Yuanbao, Doubao, or DeepSeek observation batches in JSON, JSONL, or CSV. Not for platform scraping, ordinary web search results disguised as model answers, causal claims, ranking guarantees, or traffic, conversion, and revenue attribution.
metadata:
  short-description: Aggregate supplied AI answer observations
  sunny_skill_type: library
---

# GEO Measure

Measure only supplied observations. This Skill does not log in to platforms, sample them, browse on the user's behalf, or infer business outcomes.

Read [references/measurement-boundary.md](references/measurement-boundary.md) before importing data. Use [templates/measurement-input.json](templates/measurement-input.json) for JSON and [templates/observations.csv](templates/observations.csv) for CSV. A zero-valid-sample example is provided at [examples/measurement-input.json](examples/measurement-input.json).

## Workflow

1. Preserve platform, terminal, prompt, session, captured time, raw answer text/hash, network evidence, citations, and exclusion reason.
2. Exclude ordinary web search results and incomplete evidence from valid model-answer denominators.
3. Report input, valid, excluded, and missing counts. A zero denominator produces `null`, never a fake `0%`.
4. Compute six separate metrics: network, site citation, content absorption, brand mention, recommendation, and dynamic fact accuracy.
5. Add 95% Wilson intervals and platform/terminal strata.
6. Emit a measurement report, research context, evidence ledger, and quality report through Artifact Protocol 1.0.

## Commands

```bash
bflabs-readiness run --capability geo-measure --input observations.json --output runs
bflabs-readiness run --capability geo-measure --input observations.jsonl --output runs
bflabs-readiness run --capability geo-measure --input observations.csv --output runs
```

The output is descriptive for the supplied batch only. It is not proof of ranking, causality, traffic, conversion, or revenue.
