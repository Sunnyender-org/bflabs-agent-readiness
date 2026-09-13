# Core questions, business extensions and real user questions

Use this before freezing a round. The six core patterns live in `../templates/core-question-library.json`; the question generator reads that same file. Do not create another copy of its templates.

## Start from the website, not a technical form

The host Agent identifies the brand, official domain, product category, audience and user scenario from public facts or supplied evidence. Add `brand`, `brand_aliases`, `site_url` and `category` to the existing discovery brief. Do not infer these from a namesake or treat an AI answer as product truth. Existing briefs still generate their seven business dimensions; missing core inputs are reported as gaps, not invented values. Ask the owner only about unresolved material facts. The host fills the brief; do not ask users to choose a Skill or fill JSON.

## The three groups

- **Core questions:** brand identity (A), official-site discovery (C), supplied-URL explanation (B), unprompted candidates (D), scenario selection (D), official getting-started path (C). The library owns the exact bilingual phrasing, purpose and judgement guidance. A requires confirmed no browsing; do not relabel a browsing answer as memory recognition.
- **Business extensions:** use the seven existing dimensions for price, risk, named comparisons, alternatives, integration and constraints. A named-brand comparison is useful but is not unprompted discovery. The existing subject-based extension templates are not automatically D-line questions. Include only applicable dimensions in the selected round.
- **Supplied questions:** preserve user/support/search/export wording and provenance. A supplied seed without verified demand data is not search volume. Generated candidates always remain `agent_hypothesis`; if a real recorded seed exactly matches a template, retain the original provenance instead of discarding it.

For D questions the target brand, its aliases and official domain must not appear in the question or its prior conversation. Check the entire generated prompt, including audience/scenario strings. The automatic check handles supplied names/aliases, space or hyphen variants and the supplied official host with or without www. The host must still check undisclosed aliases and context; this is not a semantic guarantee. A required upstream model or other genuine product constraint is allowed when it does not disclose the target brand; do not erase actual user needs merely to make a prompt generic. A target brand identical to a generic category term is ambiguous and needs a different question or judgement, not a silent exemption. If the generator detects leakage it omits that core candidate and reports a gap; rewrite the inputs before sampling. Do not simply delete an awkward brand word or silently replace it with a competitor.

## From candidates to a frozen round

The generator's query map is a question pool, not a sampled or frozen experiment. Select core and relevant business/user questions based on the actual goal. Keep one primary purpose per question. Bind required facts, critical errors and allowed omissions to the real fact sheet; the library's judgement text is a guide, not a complete answer key. Brand mention, official citation, recommendation and factual accuracy are separate observations.

A question may optionally carry `purpose` and `question_group` in `questions.json`. Keep `partial_credit_rule` as its actual judgement rule. Freeze the text, facts, rubric, language and conditions before the first observation. Test wording with fixtures before freezing, never optimize it against already observed hits.

If a round is already sampled, leave `questions.json` and its raw evidence unchanged. Put new candidates in existing `question-backlog.json.next_round_pool`, with source, market, capture time, selection reason and related question IDs. Generated questions do not become real user questions merely because they sound natural. The next round selects candidates, creates its own version and takes a new baseline.

## Present the comparison

Run the existing [comparison renderer](https://readiness.bflabs.cn/skills/bflabs-agent-readiness/scripts/render_comparison.py) from the root Skill package with the project directory. Its “本轮问什么” section shows fixed questions, what they measure and the recorded judgement rule; next-round candidates are separate. Site changes, actual AI answers and business results remain separate sections. Show all sampled slots, unchanged and worse results, failed attempts and missing after data. Never use brand-primed questions as proof of natural recommendation, a supplied URL as proof of discovery, or a few hits as evidence of total market performance.

## Research basis

Question grouping and contextual intent design draw on the public methods of Yao Jingang: https://github.com/yaojingang/yao-geo-skills/tree/201c0c45dcf09bb37bc46a467b4baf4d721db205/skills/yao-geo-effect-monitor and https://github.com/yaojingang/yao-geo-skills/tree/201c0c45dcf09bb37bc46a467b4baf4d721db205/skills/yao-geo-intent-miner . These are conceptual references; the templates and implementation here are original and do not import their code or report system.
