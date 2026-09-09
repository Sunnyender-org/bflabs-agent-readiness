# Per-Page Fact Checklist

Use this checklist for one website and one frozen `questions_version`. The first-round default of three key pages is a starting sample, not full-site coverage. A single CLI receipt never marks a phase complete.

## Question → fact → page → action → evidence

| Step | Record | Required fields | Rule |
|---|---|---|---|
| Question | `questions.json` | `question_id`, `observation_line` (`A` \| `B` \| `C` \| `D`), `intent_tag` (`brand` \| `category` \| `compare` \| `evaluate` \| `act`), `text`, `provides_url`, `asks_for_browsing`, `required_fact_ids[]`, `critical_error_fact_ids[]`, `partial_credit_rule`, `frozen_at` | Lines are never merged. The set is frozen before any site change. |
| Fact | `facts.json` | `fact_id`, `statement`, `category` (`identity` \| `audience` \| `capability` \| `domain` \| `pricing` \| `integration` \| `limitation` \| `other`), `source_url`, `source_captured_at`, `source_hash`, `evidence_status` (`official` \| `third_party` \| `unverified` \| `conflict` \| `forbidden`), `conflict_note`, `last_reviewed_at` | `forbidden` and `conflict` never enter copy. `unverified` appears only as marked pending. A changed `source_hash` or source content makes prior verification stale. |
| Page | `experiment.json.representative_pages[]` | `url`, `purpose`, `selection_reason`, `fetch_status` (`ok` \| `failed` \| `unknown`) | Default three key pages, chosen from homepage navigation, sitemap, and internal links. Fewer or a different scope needs a stated reason. |
| Action | `actions.json` | `action_id`, `page_url`, `question_ids[]`, `fact_ids[]`, `issue_type` (`fact` \| `structure` \| `source` \| `execution`), `summary`, `deliverable`, `status` (`planned` \| `changed_local` \| `released` \| `verified_public` \| `reverted`), `released_at`, `release_evidence`, `public_recheck` | One finding → one action. Status follows evidence, not local tests. |
| Evidence | `release_evidence`, `public_recheck`, `observations.jsonl` | deploy log / live-branch commit / public fetch; `{checked_at, result pass\|fail\|unknown, note}`; observation rows tagged with line and intent | A CLI receipt or passing local test is not `released` or `verified_public`. Observation lines A–D stay separate. |

## Page checks

| Check | Pass | Fail or stop | `issue_type` |
|---|---|---|---|
| Page selected | `purpose` and `selection_reason` recorded | Missing reason for a non-default scope | do not score until recorded |
| Fetch | `fetch_status` is `ok` | `failed` or `unknown`: record "evidence missing" | do not score |
| Questions mapped | every frozen question this page must answer is listed | required question has no page mapping | `fact` if the answer is missing; `structure` if the answer exists but cannot be read |
| Facts carried | each required `fact_id` appears in the page body | missing, wrong, or conflicting statement | `fact` |
| User-visible | a person can read the required facts on the rendered page | facts only in comments, hidden nodes, or agent notes | `structure` |
| Crawler-readable | the same facts are in the initial HTML without JavaScript | facts appear only after client rendering | `structure` |
| AI-extractable | definition sentence, key-value facts, tables or FAQ where needed, dates, canonical URL, consistent entity names | prose-only blob with no extractable units | `structure` |
| Schema matches body | Schema.org / JSON-LD restates body facts only | schema invents a fact absent from the body | `fact` |
| Evidence status | copy uses `official` or `third_party`; `unverified` is marked pending; `forbidden` / `conflict` omitted | unevidenced or forbidden fact in copy | `source` if no usable source; `fact` if the published statement is wrong or conflicting |
| Source freshness | `source_hash` and content match the last review | source changed after last review | `source` |
| Release | `released` has `released_at` and `release_evidence` | local change only | `execution` |
| Public recheck | `verified_public` has a live-URL `public_recheck` | released but not rechecked | `execution` |

## Six scenarios

### 1. One page answers several questions

Keep one `representative_pages[]` row. List every served `question_id` on the actions and on the page checklist. Shared `fact_id`s may support several questions. Do not merge observation lines or intent tags because they share a URL.

### 2. A fact without evidence

Do not treat it as established copy. Leave it out, or show it only as clearly marked pending when `evidence_status` is `unverified`. Record `issue_type` `source`. If the page already states it as settled truth, record `issue_type` `fact`.

### 3. A page that cannot be fetched

Set `fetch_status` to `failed`. Record "evidence missing". Do not score the page. Do not invent body facts or structured data from memory.

### 4. Changed but not deployed

Keep `status` at `changed_local`. Classify the gap as `execution`, not `fact`. A CLI receipt, repair receipt, or passing local test is not `release_evidence`.

### 5. Deployed but not rechecked

`released` is allowed only with `released_at` and `release_evidence`. Do not set `verified_public` until a public fetch of the live URL is recorded in `public_recheck`. Until then the open gap is `execution`.

### 6. A fact changed after release

If `source_hash` or source content changed, prior verification is stale. Re-check the fact before reuse. Do not keep `verified_public` on dependent actions without a new public recheck. If the statement or the facts a frozen question depends on changed, create a new `questions_version` and a new baseline. Never ease the question. Never back-fill a baseline.

## Phase completion

`current_phase` on `experiment.json` moves only with the matching record evidence. A single CLI receipt never completes `baseline`, `change`, `release`, `retest`, or `verified_public`.
