# Sampling Guide

This guide is for agents collecting or importing observations. It is not a live sampling tool.

For question design, use the [core question method](https://readiness.bflabs.cn/skills/geo-discover/references/core-question-method.md). It prepares candidates, not observations; keep generated ideas distinct from recorded user questions.

## Freeze the question set first

Write the question texts, facts, and rubric, then leave them unchanged while the site or content changes. Changing question text creates a new `question_version` and needs a new baseline. Never ease a question to produce a hit.

The original frozen questions stay the denominator for this batch. New questions freeze as their own set and must be measured before their content changes. They cannot claim improvement from an older six-question baseline. Multi-batch releases record each action's actual `released_at`. If changes landed on different days, do not call them a single-window effect.

## What each line can prove this time

Keep the four observation lines separate. Never merge them into one score.

- A: brand recognition without a URL and without browsing.
- B: explain a given URL.
- C: find the brand or official docs autonomously with browsing.
- D: a non-brand category or selection question.

"Given a URL it can answer" only proves page reading this time. "Found without a URL" proves retrieval this time. Neither proves model retraining.

## Platforms and sessions

First-round surfaces are ChatGPT, Perplexity, and Google Search. Use the surfaces the target users actually use and that the operator can legally access. Gemini chat, if collected, is an optional independent surface and does not replace Google Search. Collect 3 independent sessions per question per platform per terminal per round. Sampling sessions stay separate from implementation sessions. Do not inject project context, prior answers, or internal notes into the sampling account.

API, App, and web are different terminals. Do not pair an API answer with a web measurement. Google Search observations are either an authorized Search export or a recorded AI Overview / AI Mode answer. An ordinary web search result is never a model answer. Google AI impressions are not clicks, queries, or order sources, and they must not be added to ordinary Search impression totals.

Record platform, terminal, visible model, account alias (never credentials), language, region, network evidence, and personalization evidence. A "new chat" label alone does not prove a clean state. Record the actual personalization setting (`off`, `on`, or `unknown`).

## Slots, attempts, and replacements

Each `(round_id, prompt_id, platform, terminal)` has a frozen sample-slot set. Default is `slot_1` … `slot_N` where `N` is `planned_slots_per_question` (default 3). Set `sample_slot_ids` to name the set explicitly. Each planned slot contributes at most one valid answer. A second valid observation in the same slot is excluded as `duplicate_slot_answer` and retained in counts.

An observation whose `sample_slot_id` is outside the frozen set is excluded as `unplanned_slot`. It stays in the file and in `attempts`, and is counted as `exploratory_answers`. It never enters a valid denominator. `valid_slots` cannot exceed `planned_slots`. A valid observation that has `round_id` but no `sample_slot_id` is excluded as `missing_slot`. Replacement still only fills the original planned slot.

A valid observation that reuses a `session_id` already used on the same `(platform, terminal)` is excluded as `shared_session`, even across questions or rounds. Keep only the first answer from that session in valid counts; retain later attempts as evidence. A pair containing a reused session is `session_reused` and cannot be compared. In particular, do not ask a non-brand question in a chat that already contains a brand question. The same session label on a different platform or terminal does not indicate the same conversation.

Technical failures stay in the file. Count them in `attempts` and `technical_failures`, not in valid denominators. At most one replacement per slot per round, and only for a technical failure in that same slot. `replacement_of` must point at that failed observation. Failed attempts are never deleted.

Judged answers have `answer_verdict` of `correct`, `partially_correct`, `wrong`, or `no_answer`. `unknown` or a missing verdict is unjudged, not wrong. Pair rates use `correct/judged`. If either side has unjudged answers or zero judged answers, the pair verdict is `insufficient` with reason `unjudged_answers`.

Report these together: `correct/judged`, `judged/valid`, `valid slots/planned slots`, and `attempts` with `technical failures`. Unmeasured is not zero. A valid answer with no recommendation may be a legitimate zero.

## What to retain

For authorized browser collection, capture each completed answer before navigating away, closing the tab, or asking another question. Save the screenshot together with the full answer, citations, capture time, and its round/question/sample-slot identifier; verify the saved image is readable and matches that answer. Capture additional overlapping views when the answer or citations extend beyond one screen. A screenshot does not replace full text or citations. This guide does not grant platform access or turn the offline aggregation Skill into a live collector.

Keep the same viewport and comparable answer region for before/after presentation. Put matched images side by side and identify the exact changed sentence, citation, or recommendation; report no change when none is visible. Preserve originals when adding highlights. Do not select only improved samples or change scale/cropping to exaggerate an effect.

If an original image was missed, mark it missing. A later capture of the still-open original answer must carry its actual later capture time. Never re-ask to manufacture an original screenshot. API/export-only records may retain the original response or export instead; disclose that no browser screenshot exists and keep this separate from answer validity.

Keep raw answers, cited URLs, capture time, and screenshots or exports. Label user-provided imports as such. Brand mention is judged with the brand's canonical name, aliases, and official domains from the project record (`facts.json` / `experiment.json.brand`). Unknown spellings go to pending, not to hit or miss. Report the full set. Never select only favorable screenshots.

## Collection methods

Use one of:

- `manual_export`: a person exported the answer or official report through the product UI.
- `agent_browser_ui`: an already-authorized host Agent operating the real platform browser UI. Retain the screenshot, full answer, citations, actual browser/model conditions and capture time through existing `evidence_refs`. This value grants no platform access and does not turn this offline Skill into a browser automation service.
- `approved_api`: an official, permitted API the operator is allowed to use.
- `recorded_fixture`: a stored synthetic or replay fixture, not a live sample.

Official Search or webmaster numbers start as an authorized export. Do not build a generic scraper. If every valid observation is `recorded_fixture`, the report adds the limitation that it does not demonstrate live platform visibility.

Reject any material obtained by bypassing login, CAPTCHA, anti-automation, or regional controls.

## Input formats and pairing

JSON is the pairing format. Put `actions`, `baseline_round_id`, `sample_slot_ids`, `planned_slots_per_question`, `experiment_id`, `questions_version`, and `notes` on the JSON object. Bind the frozen baseline with `baseline_round_id`. If that field is omitted and the file has exactly one baseline round, that round is used. If more than one baseline round is present and none is bound, every pair is `baseline_ambiguous`. JSONL and CSV load observations; JSONL does not carry `actions` or `planned_slots_per_question`. Use JSON when you need before/after pairing or release evidence.

CSV may include the optional columns. An absent column means the field is absent, not `null`.

## Comparability and after-release evidence

A later round is comparable to baseline only when required conditions are present, unique within each round group, and then equal between rounds. If any valid member is missing `question_version`, `facts_version`, `rubric_version`, `language`, or `region`, the pair records `<field>_missing`. Multiple values inside either group are `<field>_mixed`, even when both groups contain the same list of values. After each side has one known value, unequal values are `<field>_mismatch`. `personalization_status` must be `off` or `on` on every valid member of both sides; `unknown` or missing is `personalization_unknown`, and mixed settings are `personalization_status_mixed`. `visible_model` must have one known value per group and match between groups; unknown model is `visible_model_unknown`, and multiple models are `visible_model_mixed`. Collect different models or conditions as separate comparisons rather than pooling their results.

Normalize `prompt_text` (NFKC, collapse whitespace, strip, casefold) and fingerprint it. Every valid member of a round group must share one fingerprint; a difference inside the group is a quality blocker. Baseline and after fingerprints must match, or the pair is `prompt_text_mismatch`.

Lines B, C, and D need `network_status=verified` on both sides. Line A needs `network_status=not-used` on both sides. `network_status=unknown` on any valid member is `network_mode_unverified`. The after window's earliest `captured_at` must be strictly later than the baseline window's latest `captured_at`.

For `after_release`, an action counts only when it exists in input `actions`, `released_at` is earlier than that observation's `captured_at`, and `release_evidence` is non-empty. A known action with empty `release_evidence` is `release_evidence_missing` even if the timestamp is earlier. Otherwise the pair is `release_evidence_missing` or `sampled_before_release`.

Verdicts are `improved`, `regressed`, `unchanged`, `insufficient`, or `not_comparable`. They compare `correct/judged` only. They are not significance tests. Three repetitions support process trial and direction, not statistics.
