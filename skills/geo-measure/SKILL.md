---
name: geo-measure
description: Aggregate user-supplied AI answer observations into denominator-explicit GEO visibility metrics, including optional before/after rounds of a frozen question set under identical conditions. Use for ChatGPT, Perplexity, Google Search, Gemini, Tencent Yuanbao, Doubao, DeepSeek, Claude, Grok, Kimi, or Qwen observation batches in JSON, JSONL, or CSV. Not for platform scraping, login or CAPTCHA bypass, ordinary web search results disguised as model answers, treating API answers as web measurements, treating Google AI impressions as order sources, causal claims, ranking guarantees, or traffic, conversion, and revenue attribution.
metadata:
  short-description: Aggregate supplied AI answer observations
  sunny_skill_type: library
---

# GEO Measure

Measure only supplied observations. This Skill does not log in to platforms, sample them, browse on the user's behalf, scrape consoles, or infer business outcomes.

First-round observation surfaces are ChatGPT, Perplexity, and Google Search. Keep API, App, and web as separate terminals. Official platform numbers start as an authorized export from the product UI or a permitted API. There is no generic scraper. Google AI impressions are not order sources. An API answer is not a web measurement. Ordinary web search links are not model answers.

Read [references/measurement-boundary.md](references/measurement-boundary.md) before importing data. Follow [references/sampling-guide.md](references/sampling-guide.md) when collecting before/after rounds. Use [templates/measurement-input.json](templates/measurement-input.json) for JSON and [templates/observations.csv](templates/observations.csv) for CSV. A zero-valid-sample example is provided at [examples/measurement-input.json](examples/measurement-input.json). A labelled synthetic pairing example is at [examples/round-pairing-input.json](examples/round-pairing-input.json).

## Workflow

1. Preserve platform, terminal, prompt, session, captured time, raw answer text/hash, network evidence, citations, and exclusion reason. Keep optional round fields when present: sample slot, observation line, versions, verdict, collection method, and replacement links.
2. Exclude ordinary web search results, incomplete evidence, technical failures, duplicate imports, unplanned slots, missing slots, shared sessions, and a second valid answer in the same sample slot from valid model-answer denominators.
3. Report input, valid, excluded, and missing counts. A zero denominator produces `null`, never a fake `0%`. Unmeasured is not zero. Unjudged answers are not wrong.
4. Compute six separate metrics: network, site citation, content absorption, brand mention, recommendation, and dynamic fact accuracy. Never merge observation lines A, B, C, and D into one score.
5. Add 95% Wilson intervals and platform/terminal strata.
6. When `round_id` is present, bind the baseline with `baseline_round_id` (or the only baseline round in the file). Group by round, phase, observation line, question, platform, and terminal. Report planned slots, valid slots, judged answers, attempts, technical failures, and answer verdicts together. Pair each after-release or follow-up group to that bound baseline only when conditions are known and comparable.
7. Emit a measurement report, research context, evidence ledger, and quality report through Artifact Protocol 1.0. A readable `stage_table` is for rendering; it is not a ranking.

Observation lines stay separate:

- A: brand recognition without a URL and without browsing
- B: explain a given URL
- C: find the brand or official docs autonomously with browsing
- D: a non-brand category or selection question

Collection methods are `manual_export`, `approved_api`, `recorded_fixture`, or `agent_browser_ui`. Pairing and release evidence require JSON input; JSONL carries observations only.

## Commands

```bash
bflabs-readiness run --capability geo-measure --input observations.json --output runs
bflabs-readiness run --capability geo-measure --input observations.jsonl --output runs
bflabs-readiness run --capability geo-measure --input observations.csv --output runs
```

The output is descriptive for the supplied batch only. It is not proof of ranking, causality, traffic, conversion, or revenue. Three repetitions support process trial and direction only. Source-association, on-site content-funnel tests, and GEO increment experiments stay separate. A small site may stop at a descriptive case. Do not emit a causal score without suitable comparison data.
