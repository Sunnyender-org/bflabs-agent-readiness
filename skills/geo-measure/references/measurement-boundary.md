# Measurement Boundary

## Valid sample

A valid observation is a complete `model-answer` with no exclusion reason and `execution_status` valid or absent. `network_status=verified` additionally requires explicit network evidence. An ordinary web search result is never a model answer, even if it links to the target site. Technical failures (`execution_status` of `technical_failure`, `quota`, `login_failed`, or `mode_mismatch`) stay in the record and are never deleted.

## Denominators

- Network rate: valid model answers with known network status.
- Site citation rate: valid model answers with verified network use.
- Content absorption, brand mention, recommendation, and dynamic fact accuracy: valid model answers where that field is known.
- Planned slots: the frozen sample-slot set for the question, platform, terminal, and round (`sample_slot_ids`, or `slot_1` … `slot_N` from `planned_slots_per_question`, default 3).
- Valid slots: distinct planned `sample_slot_id` values that contributed a valid answer. This count never exceeds planned slots.
- Attempts: observations in the group except duplicate imports.
- Technical failures: attempts whose `execution_status` is not valid.
- Valid answers: valid model answers in the group after exclusions.
- Judged answers: valid answers whose `answer_verdict` is `correct`, `partially_correct`, `wrong`, or `no_answer`.
- Unjudged answers: valid answers with `unknown` or missing verdict. Unjudged is not wrong.
- Exploratory answers: observations excluded as `unplanned_slot`. They stay in `attempts` and never enter valid denominators.
- Pairs: an after-release or follow-up group compared to the bound baseline group with the same question, observation line, platform, and terminal. Bind the baseline with `baseline_round_id`, or with the only baseline round in the file. Multiple unbound baseline rounds are `baseline_ambiguous`.

Every metric reports numerator, denominator, exclusions, missing values, rate, denominator rule, and a 95% Wilson interval. If the denominator is zero, rate and interval are `null`. Pair verdicts use `correct/judged`, not `correct/valid`. Report `correct/judged`, `judged/valid`, `valid slots/planned slots`, and `attempts` with `technical failures` together. A missing slot is not a zero score.

## Exclusion reasons

- Ordinary web search result, incomplete evidence, or an existing caller-supplied `exclusion_reason`.
- `duplicate_import`: a later row with the same `answer_hash`, `prompt_id`, platform, terminal, and `captured_at`. Evidence is retained; the sample count does not increase.
- `duplicate_slot_answer`: a second valid answer in the same `(round_id, prompt_id, platform, terminal, sample_slot_id)`. The first valid answer is kept.
- `unplanned_slot`: `sample_slot_id` is outside the frozen planned set. Retained as an exploratory sample.
- `missing_slot`: a valid observation has `round_id` but no `sample_slot_id`.
- `shared_session`: a later valid observation reuses a `session_id` already used on the same `(platform, terminal)`, including another question or round. It remains an attempt but cannot count as an independent answer; pairs containing the reused observation are `session_reused`.

Replacement rules are quality blockers, not silent exclusions: at most one replacement per slot per round; `replacement_of` must name a technical failure in that same slot; a replacement of a valid observation, a second replacement, or a slot change blocks the run. Prompt text that differs among valid members of one round group is also a blocker.

## Interpretation

Aggregates remain descriptive and are stratified by platform and terminal. Observation lines A, B, C, and D are never merged. Small, user-supplied, or convenience samples do not support causal conclusions. Three repetitions support process trial and direction only. Readiness and answer observations do not establish traffic, conversion, or revenue.

Comparability requires known conditions that are unique inside each round group and equal between rounds. Missing or mixed versions, language, region, model, or personalization; unverified network; mismatched prompt fingerprints; reused sessions; or empty release evidence prevent comparison. Matching lists of mixed models or conditions do not qualify as equal conditions. `not_comparable` and `insufficient` pairs still pass quality. A `not_comparable` pair lists every failed condition; it is not a regression. Unjudged answers cannot turn a regression into an improvement.
