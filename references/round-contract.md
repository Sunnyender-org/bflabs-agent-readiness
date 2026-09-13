# Full Round Contract

This file is Agent-only. It defines the free, single-website GEO round. Do not project file names, phase enums, or comparison labels into rendered product copy.

Read `references/root-agent-contract.md` first. Record files and field names are in `references/round-record.md`. Sampling and pairing rules are in `skills/geo-measure/references/sampling-guide.md`. Page binding is in `skills/geo-optimize/references/page-fact-checklist.md`. Question freezing is in `skills/geo-discover/references/round-questions-method.md`.

The two registered CLI workflows do not execute this round and must not be advertised as a full round. A single-item request — including attribution on one supplied business export — must not be expanded into this round.

Do not enter this round for:

- **no-site / build-only** — produce a site-foundation plan via `seo-plan`. Do not invent a public URL. Do not start unrelated sampling. Do not create `experiment.json`.
- **explain-only** — answer the method question and stop. Do not start execution.
- **single-item attribution** — analyze the supplied export only. Do not open a full round.

**resume** continues an existing record. It does not redo already-released actions and does not restart setup or recapture a baseline that already exists for the same frozen questions.

Older records remain readable. Do not fabricate identity, survey, refund, or business-window fields that the record does not contain.

## Scope

One website. One frozen fact set. One frozen question set. One project directory chosen by the user.

The user brings the Agent, site access, platform accounts or answer records, and any business data. BFLabs paid work is BFLabs performing implementation, repeated sampling, hosted storage, monitoring, and ongoing review. A convenience host is never a prerequisite.

## Observation lines

Keep these four lines separate. Never merge them into one score.

- **A** — brand recognition without a URL and without browsing.
- **B** — explain a given URL.
- **C** — find the brand or official docs autonomously with browsing.
- **D** — non-brand category or selection questions.

## Comparison labels

For each question, platform, and line, report exactly one of: `improved`, `unchanged`, `regressed`, `not comparable`, `not measured`.

`not comparable` is required when the question text, fact set, platform, or collection method changed. `not measured` is required when that cell was never captured. Do not upgrade either label to `unchanged`.

A stage report without business data is complete for that stage. A valid zero-event window is reported as zero. No sales does not block method acceptance and must never be called a closed acquisition loop.

## Local record check

When the sibling CLI is present, use it as a read-only check. It does not execute the round.

```bash
bflabs-readiness round validate --project DIR
bflabs-readiness round status --project DIR
bflabs-readiness round report --project DIR
```

## Phase: setup

**Entry.** The user asked for a full round on one existing site that already has a real public URL, or a resume has no `experiment.json` yet. A no-site or build-only request does not enter this phase.

**Need.** A real site URL. Facts source. Target market if known. If there is no URL, stop: plan site foundation instead. Do not invent a public URL. Do not start unrelated sampling.

**Record.** Create or update `experiment.json` with `site_domain`, `site_url`, `target_market`, `brand`, version stamps, `current_phase=setup`, and `baseline=null`. Write `facts.json`. Freeze `questions.json`. Start optional `coverage.json` rows for important clusters. Leave `actions.json` empty or unchanged. Do not write observations yet.

**Exit evidence.** One site identity. Each fact has a source and `evidence_status`. Each question has `question_id`, `observation_line`, `intent_tag`, `text`, `frozen_at`, and its fact links. `questions_version` is set. Whole-site construction is not complete until P0 coverage rows have pages; a later verified homepage action is only that batch.

**Report.** Facts and questions are ready. AI answers are `not measured`. Business is `not measured`.

**Immediate verify.** The question set is frozen before any baseline capture. Dynamic facts have a source and capture time.

**May show no change.** AI answers. Business events.

## Phase: baseline

**Entry.** `questions.json` is frozen. `experiment.json.baseline` is null or does not point at a real observation set for this `questions_version`.

**Need.** Platform access or user-supplied answer records. Not repository access. Not a business export.

**Record.** Append baseline rows to `observations.jsonl` (`phase=baseline`, `round_id`, `question_version`, collection method, `answer_verdict`). Point `experiment.json.baseline` at that set (`round_id`, `observation_file`, `captured_window`). Push a `rounds[]` row with `phase=baseline`. Set `current_phase=baseline`, then `next_step` toward issue finding.

**Exit evidence.** Every frozen question that was in scope has an observation or an explicit exclusion. `experiment.json.baseline` is non-null and resolvable. No Optimize-mode edit for AI-answer effect has been made.

**Report.** Baseline only. No improvement claim.

**Immediate verify.** The baseline references the current frozen `questions.json`. Observations are real. None were invented or copied from a later window.

**May show no change.** Site copy. Business events.

**Gate.** If this baseline is missing, do not enter `change` for AI-answer effect. Never fabricate or back-fill.

## Phase: change

**Entry.** The baseline gate passed, or the user records an emergency site fix.

**Need.** Repository or CMS access.

**Record.** Write `actions.json` rows (`action_id`, `page_url`, `question_ids`, `fact_ids`, `issue_type`, `summary`, `deliverable`, `status=planned` then `changed_local`). Set `current_phase=change`. An emergency fix must include the reason and must never be used as AI-answer improvement evidence.

**Exit evidence.** Each intended edit is a `changed_local` action bound to pages, questions, and facts. No action is treated as live.

**Report.** Local work only. Public AI answers remain `not measured` for effect.

**Immediate verify.** `changed_local` is not `released`. Unrelated dirty files are left alone.

**May show no change.** Public AI answers. Business events.

## Phase: release

**Entry.** One or more `changed_local` actions are ready, and the owner authorizes going public.

**Need.** Owner confirmation. Release evidence (public URL, deploy receipt, or equivalent).

**Record.** Set those actions to `released` with `released_at` and `release_evidence`. Set `current_phase=release`.

**Exit evidence.** The public URL shows the intended change. `changed_local` remaining actions are listed as not released.

**Report.** Released. Retest not yet done, so AI-answer effect is `not measured`.

**Immediate verify.** A released action is not `verified_public`.

**May show no change.** AI answers (cache or index delay). Business events.

## Phase: retest

**Entry.** At least one action is `released`. `questions.json` is unchanged from the baseline it will be compared with.

**Need.** Platform access or user-supplied answer records.

**Record.** Append `observations.jsonl` rows with `phase=after_release` (or `follow_up` when that is the recorded window). Fill `public_recheck` on the compared actions. Promote an action to `verified_public` only after that public recheck. Push a `rounds[]` row with `phase=after_release` or `follow_up` and `compared_action_ids`. Set `current_phase=retest`.

**Exit evidence.** Same questions. Pairing follows `skills/geo-measure/references/sampling-guide.md`. Each compared cell has one comparison label. Lines A/B/C/D remain separate.

**Report.** Improved / unchanged / regressed / not comparable / not measured. No single blended score.

**Immediate verify.** A `released` action without public recheck is not verified. Replacements and failed collection attempts are explicit.

**May show no change.** Some questions. Some platforms. That is a valid `unchanged` or `not measured`, not a failed round.

## Phase: business_review

**Entry.** The owner wants business readback, or the round has reached this step. Absence of data is allowed.

**Need.** A business export only when the owner has one.

**Record.** Write `business-events.json` `imports[]` with `source`, `window`, `coverage` (`complete` / `partial` / `unknown`), and `events[]`. Set `current_phase=business_review`.

**Exit evidence.** Coverage is stated. A valid empty window is zero events, not missing evidence. Test rows stay marked `is_test`.

**Report.** Business cells use the same comparison labels. Missing import ⇒ `not measured`, and the stage report remains complete.

**Immediate verify.** Do not infer visits, leads, or revenue from AI answers or readiness scores.

**May show no change.** Conversion. Revenue. AI answers.

## Phase: report

**Entry.** The work that was actually done has recorded exit evidence. Business data is optional.

**Record.** Generate `report.md`. Set `current_phase=report` and a concrete `next_step`.

**Exit evidence.** The report states what changed, what was retested, each line's comparison, what was not measured, and the next step. It does not call a no-sale window a closed acquisition loop.

**Immediate verify.** Readiness, AI answers, and business stay independent. Emergency fixes are not scored as AI-answer gains.

**May show no change.** Any cell that was never in scope.

## Phase: next_round

**Entry.** The stage report exists.

**Record.** Set `current_phase=next_round`. Keep `next_step` specific. If `questions.json` or `facts.json` will change, bump the matching version and require a new baseline. If they do not change, the last public retest may become the next baseline.

**Exit evidence.** Released or `verified_public` actions are not redone. A `changed_local` leftover is either released, reverted, or explicitly deferred.

**Immediate verify.** Continuation will read this record instead of restarting.

**May show no change.** Previous scores.

## Stop conditions

Stop the blocked external step when:

- required external authorization is missing;
- platform quota or access is blocked;
- sampling conditions cannot be fixed;
- site ownership or target-market conflict is unresolved.

Do not invent access, samples, or ownership. Continue every independent local step that does not need the blocked resource: record what is known, write the stage report for completed phases, and leave `next_step` on the blocked gate.
