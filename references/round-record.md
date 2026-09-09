# Round record

Agent-only. This is the portable local file set for one site, one market, and one GEO round. It is not an Artifact Protocol run, not a hosted account, and not a second writable ledger. Do not sync it with the diagnostic site.

Phase workflow lives in `references/round-contract.md`. Observation capture lives in `skills/geo-measure/references/sampling-guide.md`. This file owns the record shape, resume rules, business import honesty, and CLI.

## Project directory

The owner chooses the directory (convention: `geo-round/`). Required file: `experiment.json`. Optional until the stage needs them: `facts.json`, `questions.json`, `actions.json`, `business-events.json`. `observations.jsonl` is the geo-measure input, not this module. `report.md` is generated.

Start from the flat templates: `templates/round-experiment.json`, `templates/round-facts.json`, `templates/round-questions.json`, `templates/round-actions.json`, `templates/round-business-events.json`. Schemas are `schemas/round-*.schema.json`.

## Files and fields

`experiment.json` pins the site, market, brand, fact/question/rubric versions, representative pages, optional baseline (`round_id`, `observation_file`, `captured_window`), recorded `rounds`, `current_phase`, `next_step`, and `updated_at`. `baseline.round_id` must exist in `rounds`.

`facts.json` is the frozen public-fact list for this `facts_version`. Each fact has a statement, category, source URL, capture time, optional `sha256:` hash, evidence status, and optional conflict note.

`questions.json` is the frozen prompt list for this `questions_version`. Each question names an observation line, intent, text, URL/browsing flags, required and critical fact ids, a partial-credit rule, and `frozen_at`. Versions must match the experiment.

`actions.json` is the only writable change list. Each action points at one page, question ids, fact ids, an issue type, a summary, optional deliverable, and release/recheck fields. `released` requires `released_at`. `verified_public` requires `public_recheck.result` of `pass`. Compared action ids on a round must exist.

`business-events.json` is owner-supplied imports. Money (`amount_minor`, `currency`) is allowed only on `purchase`. An `ai` source requires a non-null `source_evidence_url` and a known `attribution_method`. `unknown` is never promoted to `ai`. Test events never count toward real revenue.

## How the files move

1. Setup: copy templates, fill site/market/brand, write facts, freeze questions, leave actions planned.
2. Baseline: add a baseline round, capture observations with geo-measure, set `baseline` and `current_phase`.
3. Change: add or update actions; `changed_local` means the public page does not have it yet.
4. Release: set `released` plus `released_at` and evidence. Do not treat `changed_local` as released.
5. Retest: add an after-release or follow-up round; do not invent AI metrics here.
6. Business review: import owner data; a stage report is complete even with no business file.
7. Report: generate `report.md`. Next round: new ids or a new project directory; never rewrite released history.

## Resume

1. Run `bflabs-readiness round status --project DIR` first.
2. Do not redo released actions.
3. `changed_local` is not released and is not a public recheck.
4. Missing baseline observations before the change phase is a precondition, not a score.

## Business import rules

- No data: not measured. The stage report is still complete.
- Coverage `unknown`: `data_incomplete`. Never write zero.
- Coverage `complete` and no real events: `measured_zero`, counts are 0.
- Signup rate needs visits. Purchase rate needs signups. Otherwise rates stay null and only counts are shown.
- Separate currencies. Separate test events from real revenue.
- Overlapping import windows are flagged.
- Before/after comparison needs the experiment baseline window and a later import window. Comparable only when lengths match within one day and the windows do not overlap. Different lengths: not comparable; still show both.
- No GEO causation claims. Chinese demo results and English market results are never merged.

## CLI

```bash
bflabs-readiness round validate --project DIR
bflabs-readiness round status --project DIR --format json
bflabs-readiness round status --project DIR --format summary
bflabs-readiness round report --project DIR
bflabs-readiness round report --project DIR --measurement-report PATH --output DIR/report.md
```

`validate` and `report` exit 1 when schema or cross-file checks fail. `report` embeds a supplied measurement `stage_table` and does not compute AI-answer metrics.
