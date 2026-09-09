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

`actions.json` is the only writable change list. Each action points at one page, question ids, fact ids, an issue type, a summary, optional deliverable, and release/recheck fields. `released` requires `released_at`, non-empty `release_evidence`, and a deliverable. `verified_public` requires all of that plus a public recheck that passed, has a non-empty note, and was checked after the release time. `reverted` may omit `released_at` when the change never went public; that case is never counted as public. Compared action ids on a round must exist.

`business-events.json` is owner-supplied imports. Money (`amount_minor`, `currency`) is allowed only on `purchase`. An `ai` source requires a non-null `source_evidence_url` and a known `attribution_method`. `unknown` is never promoted to `ai`. Test events never count toward real revenue. The same `(source, external_id)` twice in one import is invalid. The same pair in a later import is kept on the record but excluded as a duplicate.

## How the files move

1. Setup: copy templates, fill site/market/brand, write facts, freeze questions, leave actions planned.
2. Baseline: add a baseline round, capture observations with geo-measure, set `baseline` and `current_phase`.
3. Change: add or update actions; `changed_local` means the public page does not have it yet.
4. Release: set `released` plus `released_at`, evidence, and a deliverable. Do not treat `changed_local` as released.
5. Retest: add an after-release or follow-up round; do not invent AI metrics here.
6. Business review: import owner data; a stage report is complete even with no business file.
7. Report: generate `report.md`. Next round: new ids or a new project directory; never rewrite released history.

## Resume

1. Run `bflabs-readiness round status --project DIR` first.
2. Do not redo released actions.
3. `changed_local` is not released and is not a public recheck.
4. A declared baseline must be resolvable: the observation file exists inside the project, parses as JSONL or as JSON with `observations`, every row matches the baseline round, `phase=baseline`, the frozen question version, and the experiment id when present, and every question id has at least one observation. That check is a precondition for `change`, `release`, `retest`, `business_review`, `report`, and `next_round`. A later phase does not waive it.

## Business import rules

- No data: not measured. The stage report is still complete.
- Coverage `unknown`: `data_incomplete`. Never write zero.
- Coverage `complete` and no real events: `measured_zero`, counts are 0.
- Signup rate needs visits. Purchase rate needs signups. Otherwise rates stay null and only counts are shown.
- Separate currencies. Separate test events from real revenue.
- Overlapping import windows are flagged.
- Before/after comparison needs an imported baseline window whose start and end match the experiment baseline window to the day, with coverage `complete`. The after window must have the same length in whole days, must not overlap, and cannot have unknown coverage. Missing baseline import, partial or unknown baseline coverage, unknown after coverage, overlap, or unequal length are not comparable. The before side is the import or null; it is never a fabricated zero.
- Events outside the import window, or whose page host is not the experiment site or a subdomain of it, are excluded. A missing page URL is allowed. Only included events feed counts, rates, and revenue. Excluded counts are shown when they are not zero.
- No GEO causation claims. Chinese demo results and English market results are never merged.

## Measurement report association

`round report --measurement-report` accepts a measurement report only when it belongs to this experiment. The file must match `measurement-report.schema.json`, use the same `site_domain`, carry `experiment_id` and `questions_version` that match the experiment, bind every pair to this experiment's baseline round and to a recorded after round, and have a `stage_table` whose length and Chinese results match the pair verdicts (`improved` → 改善, `regressed` → 回退, `unchanged` → 持平, `insufficient` → 样本不足, `not_comparable` → 不可比). A report from another site or an old file that cannot be associated is rejected; no `report.md` is written. Display lines are generated only from the accepted pairs and table rows.

## CLI

```bash
bflabs-readiness round validate --project DIR
bflabs-readiness round status --project DIR --format json
bflabs-readiness round status --project DIR --format summary
bflabs-readiness round report --project DIR
bflabs-readiness round report --project DIR --measurement-report PATH --output DIR/report.md
```

`validate` and `report` exit 1 when schema or cross-file checks fail. `report` also exits 1 when a supplied measurement report cannot be associated; it then prints `{"status":"failed","errors":[...]}` and does not write the report file. A valid measurement report is embedded after those checks; this module does not compute AI-answer metrics.
