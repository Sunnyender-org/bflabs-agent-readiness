# Frozen Question Set For A Round

Build `questions.json` for one website, one language, and one `questions_version`. Freeze the set before any site change. Field names match the root Skill's round-record reference (served at `https://readiness.bflabs.cn/skills/bflabs-agent-readiness/references/round-record.md`).

Observation lines are never merged:

- `A`: brand recognition without a URL and without browsing
- `B`: explain a given URL
- `C`: find the brand or its official docs autonomously, with browsing
- `D`: non-brand category or selection questions

Intent tags: `brand`, `category`, `compare`, `evaluate`, `act`.

## Dimension → line / intent

Place each of the seven discovery dimensions on the line that matches how the question will be asked. One dimension may produce more than one question; one question still has exactly one `observation_line` and one `intent_tag`.

| Dimension | Primary line | Typical `intent_tag` | Placement rule |
|---|---|---|---|
| audience | `A` or `B` | `brand` | `A` when no URL is given; `B` when the question names a URL |
| scenario | `B` or `D` | `evaluate` or `act` | `D` when the prompt is a job-to-be-done with no brand |
| comparison | `D` | `compare` | Keep the brand out of the prompt; judge mention separately |
| decision | `D` or `C` | `evaluate` | `C` only when the asker must find official docs first |
| price and cost | `B` or `C` | `evaluate` or `act` | `B` with a given pricing URL; `C` to find the official source |
| integration | `B` or `C` | `act` | `C` when the question is to find official getting-started docs |
| limitation | `B` or `D` | `evaluate` | `D` for class-level "when not to use this kind of service" |

Chinese demo questions and English market questions are separate sets. Never merge languages into one `questions_version`.

## Freeze and version

- Freeze before any site change. Record `questions_version`, `language`, and `frozen_at` on every question.
- Changing a question's `text`, its `required_fact_ids` / `critical_error_fact_ids`, or the facts or rubric it depends on creates a new `questions_version` and needs a new baseline. Never back-fill a baseline.
- Never ease a question after seeing results.
- Every question lists required facts, critical-error facts, allowed omissions, and a `partial_credit_rule`. Put allowed omissions in `partial_credit_rule`; do not invent extra fields.
- For line `D`, score brand mention, official-site citation, recommendation, and fact correctness separately.
- `not mentioned`, `wrong`, `don't know`, and `no recommendation` are valid observation results. They are not failures of this method.

A later Optimize pass that aims to change AI answers requires `experiment.json.baseline` for this frozen `questions_version`. Building the question set does not create that baseline.

## Example set (first case site)

Placeholder `fact_id`s only. This block is a method example, not scored answers and not a claim about current AI output.

```json
{
  "questions_version": "v1",
  "language": "en",
  "questions": [
    {
      "question_id": "q_a_what_is_beefapi",
      "observation_line": "A",
      "intent_tag": "brand",
      "text": "What is BeefAPI?",
      "provides_url": false,
      "asks_for_browsing": false,
      "required_fact_ids": ["fact_identity", "fact_audience"],
      "critical_error_fact_ids": ["fact_identity"],
      "partial_credit_rule": "Credit a correct identity sentence if audience is omitted. Fail if identity is wrong. Do not require a URL.",
      "frozen_at": "2026-09-09T00:00:00Z"
    },
    {
      "question_id": "q_b_explain_site",
      "observation_line": "B",
      "intent_tag": "brand",
      "text": "What does https://global.beefapi.com/ do, and who is it for?",
      "provides_url": true,
      "asks_for_browsing": false,
      "required_fact_ids": ["fact_identity", "fact_audience", "fact_official_domain"],
      "critical_error_fact_ids": ["fact_identity", "fact_official_domain"],
      "partial_credit_rule": "Credit a correct service sentence for the given URL if audience is omitted. Fail if the URL is described as a different product.",
      "frozen_at": "2026-09-09T00:00:00Z"
    },
    {
      "question_id": "q_c_find_official_site",
      "observation_line": "C",
      "intent_tag": "brand",
      "text": "Find BeefAPI's official website and explain its service.",
      "provides_url": false,
      "asks_for_browsing": true,
      "required_fact_ids": ["fact_official_domain", "fact_identity"],
      "critical_error_fact_ids": ["fact_official_domain"],
      "partial_credit_rule": "Credit finding the official domain plus a correct service sentence. Fail if a non-official domain is treated as official. Pricing may be omitted.",
      "frozen_at": "2026-09-09T00:00:00Z"
    },
    {
      "question_id": "q_c_find_api_docs",
      "observation_line": "C",
      "intent_tag": "act",
      "text": "Find BeefAPI's official API documentation and explain how to get started.",
      "provides_url": false,
      "asks_for_browsing": true,
      "required_fact_ids": ["fact_docs_url", "fact_official_domain"],
      "critical_error_fact_ids": ["fact_docs_url"],
      "partial_credit_rule": "Credit finding official docs and a correct start path. Billing details may be omitted. Fail if unofficial docs are treated as official.",
      "frozen_at": "2026-09-09T00:00:00Z"
    },
    {
      "question_id": "q_d_unified_api_category",
      "observation_line": "D",
      "intent_tag": "category",
      "text": "Which services provide a unified API for multiple AI models?",
      "provides_url": false,
      "asks_for_browsing": false,
      "required_fact_ids": [],
      "critical_error_fact_ids": [],
      "partial_credit_rule": "Score category membership, brand mention, official-site citation, recommendation, and fact correctness separately. not mentioned, wrong, don't know, and no recommendation are valid results. Do not require a BeefAPI mention.",
      "frozen_at": "2026-09-09T00:00:00Z"
    },
    {
      "question_id": "q_d_unified_api_compare",
      "observation_line": "D",
      "intent_tag": "compare",
      "text": "What should a developer compare when choosing a unified API for multiple AI models, and which providers are worth evaluating?",
      "provides_url": false,
      "asks_for_browsing": false,
      "required_fact_ids": [],
      "critical_error_fact_ids": [],
      "partial_credit_rule": "Score comparison dimensions separately from naming or recommending any provider. Official-site citation and fact correctness are separate. no recommendation and not mentioned are valid results.",
      "frozen_at": "2026-09-09T00:00:00Z"
    }
  ]
}
```
