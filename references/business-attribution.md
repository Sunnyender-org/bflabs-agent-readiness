# Business attribution

Agent reference. Analyze only the supplied records. This is independent of AI answer sampling: a user can ask for business analysis alone, without starting a round.

Use `schemas/round-business-events.schema.json` and `templates/round-business-events.json`. Keep raw source signals, pseudonymous identity links, optional self-reports and transaction identifiers. Never insert synthetic transactions into a user's real project. An absent export is not a measured zero.

With the installed CLI:

```sh
bflabs-readiness business --input business-events.json --format markdown --output business-report.md
```

For an installed SkillHub package, use `scripts/analyze_business.py`; its companion modules are `scripts/business_attribution.py` and `scripts/business_report.py`. Online users download all three from this root Skill's resource directory into the same local directory. The generated companions come from the same source files as the CLI; there is no separate calculation implementation. Python 3.9+ is needed only for this deterministic analysis step. If this runtime is unavailable, explain the missing execution capability and continue the tasks the host can perform; do not invent a computed result.

```sh
python scripts/analyze_business.py --input business-events.json --format markdown --output business-report.md
```

If an experiment exists, add `--experiment experiment.json`. Its optional `business_window` describes independently selected before/after periods and `as_of`; `selected_import_ids`, `selected_metric` and `selected_filters` state the chosen evidence and view. The AI baseline's capture period does not supply business windows. Without an explicit comparison, report the supplied records only. Add `--as-of` to obtain a historical cutoff.

## Reading the result

- Event counts are occurrences; user rates need linked identities. Amounts keep their currency. Top-ups are not confirmed revenue.
- Cash flow follows payment/refund occurrence. Order net collections follow the selected order cohort through the cutoff, including its later linked refunds.
- First recorded source, this visit, self-report and page contact can describe the same payment. Never add these views together or infer a shared person from a page visit.
- Preserve raw source labels alongside derived channels. Tests and self-distributed links are separate from natural referrals; Google Search alone does not identify an AI click.
- A before/after difference is descriptive unless a separate experiment supports an incremental claim. Missing or unmatched evidence restricts that conclusion, not unrelated work.

Use `--format json` for an evidence export; present the concise Markdown result to the user. Keep technical field names and implementation instructions out of the final report. In a full round, `round report` uses the same analyzer.

`selected_metric=first_success_call` selects explicitly recorded first-success events (event type or existing boolean flag), not all activation events. Reports show record counts and separately identified users when available; neither proves lifetime-first use unless the export establishes that scope. Never infer first success from payment, a missing earlier log, or an incomplete history. Tests and self-promotion follow the selected filters, and absent coverage stays unknown.

For this metric, an import declares `covered_event_types: ["first_success_call"]` only when the export really covers that event. A payments-only export cannot establish zero first calls. Existing imports without this field remain compatible for other metrics. Complete time windows and the normal comparison rules still apply.
