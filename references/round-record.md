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

`business-events.json` is owner-supplied imports. Money (`amount_minor`, `currency`) is allowed on `purchase` and `refund`. Refunds retain their transaction ID and original order association. An `ai` source requires a non-null `source_evidence_url` and a known `attribution_method`. `unknown` is never promoted to `ai`. Test events never count toward real revenue. The same `(source, external_id)` twice in one import is invalid. The same pair in a later import is kept on the record but excluded as a duplicate.

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
4. A declared baseline must be resolvable: the observation file stays inside the project and parses as JSONL or JSON with observations. Each row must satisfy the observation schema and answer hash, match a frozen question text and observation line, and have a capture time inside the baseline window and no earlier than question freezing. Round, phase, question/fact/rubric versions and any supplied site/experiment identity must match. Missing answers or incomplete/failed captures require explicit exclusion reasons; those attempts remain evidence of a gap, not successful answers. The file may also contain observations appended for other declared rounds: their round/phase must agree with the experiment, and they never replace the frozen baseline set. Every frozen question must be represented in that baseline set. This is a precondition for change and all later phases; a later phase does not waive it.

## Business import rules

- No data: not measured. The stage report is still complete.
- Coverage `unknown`: `data_incomplete`. Never write zero.
- Coverage `complete` and no real events: `measured_zero`, counts are 0.
- Signup rate needs visits. Purchase rate needs signups. Otherwise rates stay null and only counts are shown.
- Separate currencies. Separate test events from real revenue.
- Overlapping import windows are flagged.
- Before/after business comparison uses only explicit `business_window`, `selected_import_ids` and `selected_metric` from the experiment. It never infers those windows from AI baseline sampling. Missing coverage prevents a comparison but does not prevent a stage report. The same analyzer is available through the standalone `business` CLI; see `references/business-attribution.md`.
- Events outside the import window, or whose page host is not the experiment site or a subdomain of it, are excluded. A missing page URL is allowed. Only included events feed counts, rates, and revenue. Excluded counts are shown when they are not zero.
- No GEO causation claims. Chinese demo results and English market results are never merged.

## Measurement report association

`round report --measurement-report` accepts a report only when it belongs to this experiment. The file must match measurement-report.schema.json, use the same site, experiment and question version, and bind each pair to the frozen baseline, a recorded after round and a known project question. Any supplied full round counts must match the pair counts. Display numbers come from structured counts and labels from frozen project questions; imported stage_table prose is not copied. Older associated reports with only pair counts show those counts without inventing judgement or attempt details. Contradictory counts, unknown questions, other sites and unassociated reports are rejected without writing a report. The reporter does not resample platforms or recalculate AI judgements.

## CLI

```bash
bflabs-readiness round validate --project DIR
bflabs-readiness round status --project DIR --format json
bflabs-readiness round status --project DIR --format summary
bflabs-readiness round report --project DIR
bflabs-readiness round report --project DIR --measurement-report PATH --output DIR/report.md
```

`validate` and `report` exit 1 when schema or cross-file checks fail. `report` also exits 1 when a supplied measurement report cannot be associated; it then prints `{"status":"failed","errors":[...]}` and does not write the report file. A valid measurement report is embedded after those checks; this module does not compute AI-answer metrics.

## Hosted handoff

For a one-time move to the existing GEO service, use `bflabs-readiness business-transfer --direction to-service --input business-events.json --experiment experiment.json --output transfer.json`. Import each emitted batch through `geo_business_import` into the same site project. Keep the source files until every batch is acknowledged; replay uses stable identifiers. Stop writing the local copy when the hosted project becomes authoritative. To exit, use `geo_project_export`, then `business-transfer --direction from-service --input export.json --output returned.json`. The result contains `business_events` and `experiment_business_fields` to apply to the portable project. This conversion preserves portable business evidence; native-only historical service records remain in their service snapshot instead of inventing missing fields.

Optional `question-backlog.json` uses `schemas/question-backlog.schema.json`. Its version and frozen question IDs must match this round. Candidate questions never enter the current measurement denominator.
