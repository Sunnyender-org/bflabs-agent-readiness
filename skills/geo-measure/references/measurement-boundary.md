# Measurement Boundary

## Valid sample

A valid observation is a complete `model-answer` with no exclusion reason and `execution_status` valid or absent. `network_status=verified` additionally requires explicit network evidence. An ordinary web search result is never a model answer, even if it links to the target site. Technical failures (`execution_status` of `technical_failure`, `quota`, `login_failed`, or `mode_mismatch`) stay in the record and are never deleted.

## Denominators

- Network rate: valid model answers with known network status.
- Site citation rate: valid model answers with verified network use.
- Content absorption, brand mention, recommendation, and dynamic fact accuracy: valid model answers where that field is known.
- Planned slots: intended independent sessions per question, platform, terminal, and round (default 3).
- Valid slots: distinct `sample_slot_id` values that contributed a valid answer.
- Attempts: observations in the group except duplicate imports.
- Technical failures: attempts whose `execution_status` is not valid.
- Valid answers: valid model answers in the group after exclusions.
- Pairs: an after-release or follow-up group compared to the baseline group with the same question, observation line, platform, and terminal.

Every metric reports numerator, denominator, exclusions, missing values, rate, denominator rule, and a 95% Wilson interval. If the denominator is zero, rate and interval are `null`. Report `correct/valid`, `valid slots/planned slots`, and `attempts` with `technical failures` together. A missing slot is not a zero score.

## Exclusion reasons

- Ordinary web search result, incomplete evidence, or an existing caller-supplied `exclusion_reason`.
- `duplicate_import`: a later row with the same `answer_hash`, `prompt_id`, platform, terminal, and `captured_at`. Evidence is retained; the sample count does not increase.
- `duplicate_slot_answer`: a second valid answer in the same `(round_id, prompt_id, platform, terminal, sample_slot_id)`. The first valid answer is kept.

Replacement rules are quality blockers, not silent exclusions: at most one replacement per slot per round; `replacement_of` must name a technical failure in that same slot; a replacement of a valid observation, a second replacement, or a slot change blocks the run.

## Interpretation

Aggregates remain descriptive and are stratified by platform and terminal. Observation lines A, B, C, and D are never merged. Small, user-supplied, or convenience samples do not support causal conclusions. Three repetitions support process trial and direction only. Readiness and answer observations do not establish traffic, conversion, or revenue. A `not_comparable` pair lists every failed condition; it is not a regression.
