# Sampling Guide

This guide is for agents collecting or importing observations. It is not a live sampling tool.

## Freeze the question set first

Write the question texts, facts, and rubric, then leave them unchanged while the site or content changes. Changing question text creates a new `question_version` and needs a new baseline. Never ease a question to produce a hit.

## What each line can prove this time

Keep the four observation lines separate. Never merge them into one score.

- A: brand recognition without a URL and without browsing.
- B: explain a given URL.
- C: find the brand or official docs autonomously with browsing.
- D: a non-brand category or selection question.

"Given a URL it can answer" only proves page reading this time. "Found without a URL" proves retrieval this time. Neither proves model retraining.

## Platforms and sessions

Use two platforms the target users actually use and that the operator can legally access. Collect 3 independent sessions per question per platform per round. Sampling sessions stay separate from implementation sessions. Do not inject project context, prior answers, or internal notes into the sampling account.

Record platform, terminal, visible model, account alias (never credentials), language, region, network evidence, and personalization evidence. A "new chat" label alone does not prove a clean state. Record the actual personalization setting (`off`, `on`, or `unknown`).

## Slots, attempts, and replacements

Each `(round_id, prompt_id, platform, terminal)` has planned sample slots (default 3). Each slot contributes at most one valid answer. A second valid observation in the same slot is excluded as `duplicate_slot_answer` and retained in counts.

Technical failures stay in the file. Count them in `attempts` and `technical_failures`, not in valid denominators. At most one replacement per slot per round, and only for a technical failure in that same slot. `replacement_of` must point at that failed observation. Failed attempts are never deleted.

Report these together: `correct/valid`, `valid slots/planned slots`, and `attempts` with `technical failures`. Unmeasured is not zero. A valid answer with no recommendation may be a legitimate zero.

## What to retain

Keep raw answers, cited URLs, capture time, and screenshots or exports. Label user-provided imports as such. Brand mention is judged with the brand's canonical name, aliases, and official domains from the project record (`facts.json` / `experiment.json.brand`). Unknown spellings go to pending, not to hit or miss. Report the full set. Never select only favorable screenshots.

## Collection methods

Use one of:

- `manual_export`: a person exported the answer through the product UI.
- `approved_api`: an official, permitted API the operator is allowed to use.
- `recorded_fixture`: a stored synthetic or replay fixture, not a live sample.

If every valid observation is `recorded_fixture`, the report adds the limitation that it does not demonstrate live platform visibility.

Reject any material obtained by bypassing login, CAPTCHA, anti-automation, or regional controls.

## Input formats and pairing

JSON is the pairing format. Put `actions`, `planned_slots_per_question`, `experiment_id`, `questions_version`, and `notes` on the JSON object. JSONL and CSV load observations; JSONL does not carry `actions` or `planned_slots_per_question`. Use JSON when you need before/after pairing or release evidence.

CSV may include the optional columns. An absent column means the field is absent, not `null`.

## Comparability and after-release evidence

A later round is comparable to baseline only when `question_version`, `facts_version`, `rubric_version`, `language`, `region`, and `personalization_status` match, and `visible_model` matches when both sides are known. Unknown model on either side is `visible_model_unknown`.

Lines B, C, and D need `network_status=verified` on both sides. Line A needs `network_status=not-used` on both sides. The after window's earliest `captured_at` must be strictly later than the baseline window's latest `captured_at`.

For `after_release`, every after observation must list at least one `compared_action_ids` entry whose action exists in input `actions` with `released_at` earlier than that observation's `captured_at`. Otherwise the pair is `release_evidence_missing` or `sampled_before_release`.

Verdicts are `improved`, `regressed`, `unchanged`, `insufficient`, or `not_comparable`. They compare `correct/valid` only. They are not significance tests. Three repetitions support process trial and direction, not statistics.
