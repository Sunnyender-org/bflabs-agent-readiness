"""Synthetic E03-E11 proofs for offline business attribution. Not live traffic."""

from __future__ import annotations

import copy
import json
import unittest

from bflabs_readiness.business_attribution import RETURN_KEYS, RULE_VERSION, VIEW_WARNING, analyze, derive_channel
from bflabs_readiness.paths import repository_root
from bflabs_readiness.schemas import validate_instance


# Synthetic fixture — not live traffic.
VALID = repository_root() / "tests/fixtures/round/valid"


def _event(**overrides: object) -> dict:
    event = {
        "external_id": "e1",
        "type": "visit",
        "occurred_at": "2026-01-02T10:00:00Z",
        "page_url": "https://example.com/",
        "source_type": "unknown",
        "source_evidence_url": None,
        "attribution_method": "unknown",
        "amount_minor": None,
        "currency": None,
        "is_test": False,
    }
    event.update(overrides)
    return event


def _batch(import_id: str, events: list, **overrides: object) -> dict:
    batch = {
        "import_id": import_id,
        "source": "analytics",
        "source_label": "synthetic export",
        "window": {
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-03-01T00:00:00Z",
            "timezone": "UTC",
        },
        "coverage": "complete",
        "export_filter": None,
        "events": events,
    }
    batch.update(overrides)
    return batch


def _doc(*batches: dict, surveys: list | None = None, identity_links: list | None = None) -> dict:
    payload = {"schema_version": "1.1.0", "imports": list(batches)}
    if identity_links is not None:
        payload["identity_links"] = identity_links
    if surveys is not None:
        payload["surveys"] = surveys
    return payload


def _experiment(**overrides: object) -> dict:
    experiment = {
        "schema_version": "1.1.0",
        "experiment_id": "exp_synthetic",
        "site_domain": "example.com",
        "site_url": "https://example.com",
        "target_market": {"language": "en", "region": "US"},
        "brand": {
            "canonical_name": "Example",
            "aliases": ["Example Co"],
            "official_domains": ["example.com"],
        },
        "facts_version": "1",
        "questions_version": "1",
        "rubric_version": "1",
        "representative_pages": [
            {
                "url": "https://example.com/",
                "purpose": "homepage",
                "selection_reason": "Public entry page.",
                "fetch_status": "ok",
            }
        ],
        "baseline": None,
        "rounds": [],
        "current_phase": "business_review",
        "next_step": "先核对本轮已记下的来源和收款。",
        "updated_at": "2026-01-16T12:00:00Z",
    }
    experiment.update(overrides)
    return experiment


class SchemaCompatTests(unittest.TestCase):
    def test_v100_round_fixtures_stay_valid(self) -> None:
        for name, schema_name in (
            ("experiment.json", "round-experiment.schema.json"),
            ("facts.json", "round-facts.schema.json"),
            ("questions.json", "round-questions.schema.json"),
            ("actions.json", "round-actions.schema.json"),
            ("business-events.json", "round-business-events.schema.json"),
        ):
            payload = json.loads((VALID / name).read_text("utf-8"))
            self.assertEqual(payload["schema_version"], "1.0.0")
            validate_instance(payload, schema_name)

    def test_v110_templates_are_valid(self) -> None:
        for relative, schema_name in (
            ("templates/round-experiment.json", "round-experiment.schema.json"),
            ("templates/round-facts.json", "round-facts.schema.json"),
            ("templates/round-questions.json", "round-questions.schema.json"),
            ("templates/round-actions.json", "round-actions.schema.json"),
            ("templates/round-business-events.json", "round-business-events.schema.json"),
            ("templates/question-backlog.json", "question-backlog.schema.json"),
        ):
            payload = json.loads((repository_root() / relative).read_text("utf-8"))
            validate_instance(payload, schema_name)


class AnalyzeContractTests(unittest.TestCase):
    def test_return_keys_and_no_raw_overwrite(self) -> None:
        raw = {
            "referrer_url": "https://chat.openai.com/",
            "referrer_host": "chat.openai.com",
            "utm_source": None,
            "utm_medium": None,
            "utm_campaign": None,
            "landing_url": "https://example.com/",
            "distribution_source": None,
        }
        stored = {
            "source_type": "search",
            "rule_version": "old-rule",
            "reason": "stale label",
        }
        visit = _event(
            external_id="v-raw",
            raw_touch=copy.deepcopy(raw),
            derived_channel=copy.deepcopy(stored),
            source_type="search",
            attribution_method="referrer",
        )
        events = _doc(_batch("imp_one", [visit]))
        snapshot = copy.deepcopy(events)
        result = analyze(events)
        self.assertEqual(events, snapshot)
        self.assertEqual(events["imports"][0]["events"][0]["raw_touch"], raw)
        self.assertEqual(events["imports"][0]["events"][0]["derived_channel"], stored)
        self.assertEqual(set(RETURN_KEYS), set(result))
        self.assertEqual(result["schema_version"], "1.1.0")
        self.assertEqual(result["rule_version"], RULE_VERSION)
        self.assertEqual(result["view_warning"], VIEW_WARNING)

    def test_google_referrer_is_never_ai(self) -> None:
        event = _event(
            source_type="ai",
            attribution_method="referrer",
            source_evidence_url="https://example.com/ref",
            raw_touch={"referrer_host": "www.google.com", "referrer_url": "https://www.google.com/"},
        )
        channel, reason = derive_channel(event)
        self.assertEqual(channel, "search")
        self.assertIn("Google", reason)

    def test_ip_link_is_rejected_and_conflict_is_kept(self) -> None:
        visit = _event(external_id="v1", visitor_id="vis_1", user_id=None)
        events = _doc(_batch("imp_one", [visit]))
        result = analyze(
            events,
            identity_links=[
                {
                    "link_id": "lnk_keep",
                    "visitor_id": "vis_1",
                    "user_id": "usr_a",
                    "evidence": "explicit_login",
                    "linked_at": "2026-01-02T11:00:00Z",
                },
                {
                    "link_id": "lnk_conflict",
                    "visitor_id": "vis_1",
                    "user_id": "usr_b",
                    "evidence": "explicit_login",
                    "linked_at": "2026-01-02T12:00:00Z",
                },
                {
                    "link_id": "lnk_ip",
                    "visitor_id": "vis_1",
                    "user_id": "usr_c",
                    "evidence": "ip_match",
                    "linked_at": "2026-01-02T12:30:00Z",
                },
            ],
        )
        actions = {item["link_id"]: item["action"] for item in result["identity_conflicts"]}
        self.assertEqual(actions["lnk_conflict"], "kept_existing")
        self.assertEqual(actions["lnk_ip"], "ignored")

    def test_pending_failed_test_and_topup_are_not_paid(self) -> None:
        events = _doc(
            _batch(
                "imp_money",
                [
                    _event(
                        external_id="p-pending",
                        type="purchase",
                        order_id="ord_pending",
                        payment_status="pending",
                        amount_minor=9000,
                        currency="USD",
                    ),
                    _event(
                        external_id="p-failed",
                        type="purchase",
                        order_id="ord_failed",
                        payment_status="failed",
                        amount_minor=8000,
                        currency="USD",
                    ),
                    _event(
                        external_id="p-test",
                        type="purchase",
                        order_id="ord_test",
                        payment_status="paid",
                        is_test=True,
                        amount_minor=7000,
                        currency="USD",
                    ),
                    _event(
                        external_id="p-topup",
                        type="purchase",
                        order_id="ord_topup",
                        payment_status="paid",
                        is_topup=True,
                        amount_minor=6000,
                        currency="USD",
                    ),
                ],
            )
        )
        result = analyze(events)
        self.assertEqual(result["views"]["order_total"], {})
        self.assertTrue(any("充值没有当成确认收入" in line for line in result["limitations"]))


class E03Tests(unittest.TestCase):
    # Synthetic fixture — ChatGPT referrer to homepage + identity + paid. No AI sample.
    def test_chatgpt_homepage_paid_without_ai_observation(self) -> None:
        visit = _event(
            external_id="v-chatgpt",
            page_url="https://example.com/",
            visitor_id="vis_1",
            session_id="ses_1",
            source_type="unknown",
            attribution_method="referrer",
            source_evidence_url="https://chat.openai.com/",
            raw_touch={
                "referrer_url": "https://chat.openai.com/",
                "referrer_host": "chat.openai.com",
                "landing_url": "https://example.com/",
            },
        )
        purchase = _event(
            external_id="p-chatgpt",
            type="purchase",
            occurred_at="2026-01-03T10:00:00Z",
            page_url="https://example.com/",
            visitor_id="vis_1",
            session_id="ses_1",
            user_id="usr_1",
            order_id="ord_e03",
            payment_status="paid",
            purchase_kind="first",
            source_type="unknown",
            attribution_method="referrer",
            source_evidence_url="https://chat.openai.com/",
            amount_minor=3000,
            currency="USD",
        )
        events = _doc(
            _batch("imp_e03", [visit, purchase]),
            identity_links=[
                {
                    "link_id": "lnk_e03",
                    "visitor_id": "vis_1",
                    "session_id": "ses_1",
                    "user_id": "usr_1",
                    "evidence": "explicit_signup",
                    "linked_at": "2026-01-02T11:00:00Z",
                }
            ],
        )
        validate_instance(events, "round-business-events.schema.json")
        result = analyze(events, experiment_doc=_experiment(baseline=None))
        ai_money = result["views"]["first_observable_source"]["by_channel"]["ai"]["USD"]
        self.assertEqual(ai_money["amount_major"], "30.00")
        self.assertEqual(ai_money["currency_label"], "美元")
        self.assertEqual(result["views"]["order_total"]["USD"]["amount_major"], "30.00")
        self.assertTrue(any("AI 表现仍未测" in line for line in result["limitations"]))
        self.assertEqual(result["measurement_status"], "measured")


class E04Tests(unittest.TestCase):
    # Synthetic fixture — self-report AI + this-visit Google + docs touch + one $20 order.
    def test_three_views_keep_twenty_and_do_not_sum_to_sixty(self) -> None:
        visit = _event(
            external_id="v-google",
            occurred_at="2026-01-04T09:00:00Z",
            page_url="https://example.com/docs",
            user_id="usr_4",
            session_id="ses_4",
            source_type="search",
            attribution_method="referrer",
            raw_touch={"referrer_host": "www.google.com", "referrer_url": "https://www.google.com/"},
        )
        purchase = _event(
            external_id="p-20",
            type="purchase",
            occurred_at="2026-01-04T09:20:00Z",
            page_url="https://example.com/docs",
            user_id="usr_4",
            session_id="ses_4",
            order_id="ord_e04",
            payment_status="paid",
            source_type="search",
            attribution_method="referrer",
            amount_minor=2000,
            currency="USD",
        )
        surveys = [
            {
                "survey_id": "srv_e04",
                "respondent_ref": "user:usr_4",
                "asked_at": "2026-01-04T09:25:00Z",
                "first_awareness": {"answer_kind": "ai", "verbatim": "先在 ChatGPT 里看到的"},
                "this_visit": {"answer_kind": "search", "verbatim": "这次是 Google"},
                "ai_question": {"asked": True, "verbatim": "Example 现在多少钱？"},
                "selection_bias_note": "自愿填写，不能代表全部来访者。",
            }
        ]
        events = _doc(_batch("imp_e04", [visit, purchase]), surveys=surveys)
        validate_instance(events, "round-business-events.schema.json")
        result = analyze(events, surveys=surveys)
        self.assertEqual(result["views"]["self_report"]["by_channel"]["ai"]["USD"]["amount_major"], "20.00")
        self.assertEqual(result["views"]["this_visit_source"]["by_channel"]["search"]["USD"]["amount_major"], "20.00")
        self.assertEqual(
            result["views"]["page_touch"]["by_page"]["https://example.com/docs"]["USD"]["amount_major"],
            "20.00",
        )
        self.assertEqual(result["views"]["order_total"]["USD"]["amount_major"], "20.00")
        viewed = (
            int(result["views"]["self_report"]["totals_by_currency"]["USD"]["amount_minor"])
            + int(result["views"]["this_visit_source"]["totals_by_currency"]["USD"]["amount_minor"])
            + int(result["views"]["page_touch"]["totals_by_currency"]["USD"]["amount_minor"])
        )
        self.assertEqual(viewed, 6000)
        self.assertNotEqual(viewed, int(result["views"]["order_total"]["USD"]["amount_minor"]))
        self.assertEqual(result["view_warning"], VIEW_WARNING)


class E05Tests(unittest.TestCase):
    # Synthetic fixture — no-source answer page, self-promo AI tag, team test.
    def test_unknown_self_promo_and_test_are_not_natural_ai(self) -> None:
        unknown = _event(
            external_id="v-answer",
            page_url="https://example.com/answers/why",
            source_type="unknown",
        )
        self_promo = _event(
            external_id="v-promo",
            occurred_at="2026-01-02T11:00:00Z",
            source_type="ai",
            attribution_method="tracked_link",
            source_evidence_url="https://example.com/campaign/ai",
            is_self_promo=True,
            raw_touch={"referrer_host": "chat.openai.com"},
        )
        team_test = _event(
            external_id="v-test",
            occurred_at="2026-01-02T12:00:00Z",
            source_type="ai",
            attribution_method="referrer",
            source_evidence_url="https://chat.openai.com/",
            is_test=True,
            raw_touch={"referrer_host": "chat.openai.com"},
        )
        events = _doc(_batch("imp_e05", [unknown, self_promo, team_test]))
        validate_instance(events, "round-business-events.schema.json")
        result = analyze(events)
        self.assertEqual(len(result["unknown_source_visits"]), 1)
        self.assertEqual(result["unknown_source_visits"][0]["page_url"], "https://example.com/answers/why")
        kinds = {(item["external_id"], item["is_self_promo"], item["is_test"]) for item in result["test_or_self_promo"]}
        self.assertIn(("v-promo", True, False), kinds)
        self.assertIn(("v-test", False, True), kinds)
        self.assertNotIn("ai", result["views"]["first_observable_source"]["by_channel"])
        self.assertTrue(all(item["natural_ai"] is False for item in result["test_or_self_promo"]))
        self.assertTrue(all(item["natural_ai"] is False for item in result["unknown_source_visits"]))


class E06Tests(unittest.TestCase):
    # Synthetic fixture — same user 5 visits / 1 signup / 3 payments.
    def test_event_counts_and_user_rate(self) -> None:
        events = []
        for index in range(5):
            events.append(
                _event(
                    external_id="v{}".format(index),
                    occurred_at="2026-01-0{}T10:00:00Z".format(index + 1),
                    user_id="usr_6",
                    session_id="ses_{}".format(index),
                )
            )
        events.append(
            _event(
                external_id="s1",
                type="signup",
                occurred_at="2026-01-02T11:00:00Z",
                user_id="usr_6",
                session_id="ses_1",
                source_type="direct",
            )
        )
        for index, day in enumerate(("03", "04", "05")):
            events.append(
                _event(
                    external_id="p{}".format(index),
                    type="purchase",
                    occurred_at="2026-01-{}T12:00:00Z".format(day),
                    user_id="usr_6",
                    order_id="ord_e06_{}".format(index),
                    payment_status="paid",
                    source_type="direct",
                    amount_minor=1000,
                    currency="USD",
                    purchase_kind="first" if index == 0 else "repeat",
                )
            )
        doc = _doc(_batch("imp_e06", events))
        validate_instance(doc, "round-business-events.schema.json")
        result = analyze(doc)
        self.assertEqual(result["event_counts"]["visit"], 5)
        self.assertEqual(result["event_counts"]["signup"], 1)
        self.assertEqual(result["event_counts"]["purchase"], 3)
        self.assertEqual(result["user_funnel"]["pay_rate"]["text"], "1/1")
        self.assertEqual(result["user_funnel"]["paid"], 1)
        self.assertLessEqual(result["user_funnel"]["paid"], result["user_funnel"]["users"])

        stripped = copy.deepcopy(doc)
        for event in stripped["imports"][0]["events"]:
            event.pop("user_id", None)
            event.pop("session_id", None)
            event.pop("visitor_id", None)
        anonymous = analyze(stripped)
        self.assertIsNone(anonymous["user_funnel"])
        self.assertEqual(anonymous["event_counts"]["visit"], 5)
        self.assertEqual(anonymous["event_counts"]["signup"], 1)
        self.assertEqual(anonymous["event_counts"]["purchase"], 3)
        self.assertTrue(any("不计算用户比率" in line for line in anonymous["limitations"]))


class E07Tests(unittest.TestCase):
    # Synthetic fixture — duplicate order, partial refund, mixed currency, window vs cohort.
    def test_dedup_refund_and_mixed_currency(self) -> None:
        analytics_ten = _event(
            external_id="pay-10-analytics",
            type="purchase",
            occurred_at="2026-01-05T10:00:00Z",
            order_id="ord_shared",
            payment_status="paid",
            source_type="search",
            amount_minor=1000,
            currency="USD",
        )
        payments_ten = _event(
            external_id="pay-10-payments",
            type="purchase",
            occurred_at="2026-01-05T10:00:01Z",
            order_id="ord_shared",
            payment_status="paid",
            source_type="search",
            amount_minor=1000,
            currency="USD",
        )
        twenty = _event(
            external_id="pay-20",
            type="purchase",
            occurred_at="2026-01-06T10:00:00Z",
            order_id="ord_20",
            payment_status="paid",
            source_type="direct",
            amount_minor=2000,
            currency="USD",
        )
        euro = _event(
            external_id="pay-eur",
            type="purchase",
            occurred_at="2026-01-06T11:00:00Z",
            order_id="ord_eur",
            payment_status="paid",
            source_type="direct",
            amount_minor=1500,
            currency="EUR",
        )
        refund = _event(
            external_id="ref-5",
            type="refund",
            occurred_at="2026-01-08T10:00:00Z",
            order_id="ord_shared",
            payment_status="partial_refund",
            source_type="search",
            amount_minor=500,
            currency="USD",
        )
        unlinked = _event(
            external_id="ref-loose",
            type="refund",
            occurred_at="2026-01-08T12:00:00Z",
            source_type="unknown",
            amount_minor=200,
            currency="USD",
        )
        events = _doc(
            _batch("imp_analytics", [analytics_ten, twenty, euro, refund, unlinked], source="analytics"),
            _batch("imp_payments", [payments_ten], source="payments"),
        )
        validate_instance(events, "round-business-events.schema.json")
        result = analyze(events, as_of="2026-01-09T00:00:00Z")
        self.assertEqual(result["event_counts"]["purchase"], 4)
        self.assertEqual(result["views"]["order_total"]["USD"]["amount_major"], "30.00")
        self.assertEqual(result["cohort_net"]["by_currency"]["USD"]["amount_major"], "25.00")
        self.assertEqual(result["cohort_net"]["by_currency"]["EUR"]["amount_major"], "15.00")
        self.assertEqual(len(result["unlinked_refunds"]), 1)
        self.assertEqual(result["unlinked_refunds"][0]["external_id"], "ref-loose")

    def test_window_cashflow_versus_cohort_net(self) -> None:
        purchase = _event(
            external_id="pay-window",
            type="purchase",
            occurred_at="2026-01-05T10:00:00Z",
            order_id="ord_window",
            payment_status="paid",
            source_type="ai",
            attribution_method="referrer",
            source_evidence_url="https://chat.openai.com/",
            raw_touch={"referrer_host": "chat.openai.com"},
            amount_minor=1000,
            currency="USD",
        )
        refund = _event(
            external_id="ref-outside",
            type="refund",
            occurred_at="2026-02-01T10:00:00Z",
            order_id="ord_window",
            payment_status="partial_refund",
            source_type="ai",
            attribution_method="referrer",
            source_evidence_url="https://chat.openai.com/",
            amount_minor=500,
            currency="USD",
        )
        experiment = _experiment(
            business_window={
                "before": {"start": "2026-01-01T00:00:00Z", "end": "2026-01-15T00:00:00Z"},
                "after": {"start": "2026-01-15T00:00:00Z", "end": "2026-01-29T00:00:00Z"},
                "timezone": "UTC",
                "as_of": "2026-02-02T00:00:00Z",
            }
        )
        result = analyze(
            _doc(_batch("imp_e07b", [purchase, refund])),
            experiment_doc=experiment,
            as_of="2026-02-02T00:00:00Z",
            selected_import_ids=["imp_e07b"],
        )
        by_label = {item["label"]: item for item in result["cashflow"]["by_period"]}
        self.assertEqual(by_label["before"]["by_currency"]["USD"]["amount_major"], "10.00")
        self.assertNotIn("USD", by_label["after"]["by_currency"])
        self.assertEqual(by_label["outside"]["by_currency"]["USD"]["amount_major"], "-5.00")
        self.assertEqual(result["cohort_net"]["by_currency"]["USD"]["amount_major"], "5.00")
        self.assertTrue(result["cohort_net"]["orders"][0]["source_unchanged"])
        self.assertEqual(result["cohort_net"]["orders"][0]["original_channel"], "ai")


class E08Tests(unittest.TestCase):
    # Synthetic fixture — AI baseline 1 hour vs business before/after 14 days.
    def test_explicit_imports_no_auto_earliest_no_double_count_immature(self) -> None:
        early = _event(external_id="v-early", occurred_at="2025-12-01T00:00:00Z")
        before_visit = _event(external_id="v-before", occurred_at="2026-01-10T00:00:00Z")
        boundary = _event(external_id="v-boundary", occurred_at="2026-01-15T00:00:00Z")
        after_visit = _event(external_id="v-after", occurred_at="2026-01-16T00:00:00Z")
        events = _doc(
            _batch("imp_earliest", [early], coverage="complete"),
            _batch("imp_before", [before_visit], coverage="complete"),
            _batch("imp_after", [boundary, after_visit], coverage="complete"),
        )
        without_selection = analyze(events, experiment_doc=_experiment())
        self.assertIsNone(without_selection["comparison"])
        self.assertTrue(any("不自动取最早" in line for line in without_selection["limitations"]))

        experiment = _experiment(
            baseline={
                "round_id": "rnd_ai",
                "observation_file": "observations.jsonl",
                "captured_window": {
                    "start": "2026-01-14T12:00:00Z",
                    "end": "2026-01-14T13:00:00Z",
                },
            },
            rounds=[
                {
                    "round_id": "rnd_ai",
                    "phase": "baseline",
                    "window": {"start": "2026-01-14T12:00:00Z", "end": "2026-01-14T13:00:00Z"},
                    "compared_action_ids": [],
                }
            ],
            business_window={
                "before": {"start": "2026-01-01T00:00:00Z", "end": "2026-01-15T00:00:00Z"},
                "after": {"start": "2026-01-15T00:00:00Z", "end": "2026-01-29T00:00:00Z"},
                "timezone": "UTC",
                "as_of": "2026-01-29T00:00:00Z",
            },
            first_paid_lookback={"days": 14},
            cohort_maturity={"required_days": 14, "observed_days": 3},
            selected_import_ids=["imp_before", "imp_after"],
            selected_metric="visits",
        )
        validate_instance(experiment, "round-experiment.schema.json")
        result = analyze(
            events,
            experiment_doc=experiment,
            selected_import_ids=["imp_before", "imp_after"],
            metric="visits",
        )
        comparison = result["comparison"]
        self.assertIsNotNone(comparison)
        self.assertEqual(comparison["selected_import_ids"], ["imp_before", "imp_after"])
        self.assertNotEqual(comparison["ai_window"], comparison["business_window"]["before"])
        self.assertEqual(comparison["before"]["event_counts"]["visit"], 1)
        self.assertEqual(comparison["after"]["event_counts"]["visit"], 2)
        self.assertFalse(comparison["boundary_double_count"])
        self.assertFalse(comparison["cohort_maturity"]["mature"])
        self.assertIn("3 天", comparison["cohort_maturity"]["explanation"])
        self.assertTrue(any("不能和已观察满期的用户按同一标准比较" in line for line in result["limitations"]))

        partial = copy.deepcopy(events)
        partial["imports"][1]["coverage"] = "partial"
        blocked = analyze(
            partial,
            experiment_doc=experiment,
            selected_import_ids=["imp_before", "imp_after"],
        )
        self.assertFalse(blocked["comparison"]["comparable"])


class E09Tests(unittest.TestCase):
    # Synthetic fixture — new user question goes to backlog; current price + old answer is inaccurate.
    def test_backlog_does_not_replace_frozen_set(self) -> None:
        questions = {
            "schema_version": "1.1.0",
            "questions_version": "1",
            "language": "en",
            "questions": [
                {
                    "question_id": "q_price",
                    "observation_line": "C",
                    "intent_tag": "evaluate",
                    "text": "How much does Example cost?",
                    "provides_url": True,
                    "asks_for_browsing": False,
                    "required_fact_ids": ["fact_price"],
                    "critical_error_fact_ids": ["fact_price"],
                    "partial_credit_rule": "答对当前起步价即可。",
                    "frozen_at": "2026-01-01T00:00:00Z",
                    "provenance": {
                        "source_kind": "user_reported",
                        "captured_at": "2026-01-01T00:00:00Z",
                        "market": "en-US",
                        "redacted": False,
                    },
                }
            ],
        }
        facts = {
            "schema_version": "1.1.0",
            "facts_version": "1",
            "facts": [
                {
                    "fact_id": "fact_price",
                    "statement": "公开起步价是每月 20 美元。",
                    "category": "pricing",
                    "source_url": "https://example.com/pricing",
                    "source_captured_at": "2026-02-01T00:00:00Z",
                    "source_hash": None,
                    "evidence_status": "official",
                    "conflict_note": None,
                    "last_reviewed_at": "2026-03-01T00:00:00Z",
                    "effective_at": "2026-02-01T00:00:00Z",
                    "verified_at": "2026-03-01T00:00:00Z",
                    "content_updated_at": "2026-01-01T00:00:00Z",
                }
            ],
        }
        backlog = {
            "schema_version": "1.1.0",
            "questions_version": "1",
            "language": "en",
            "frozen_question_ids": ["q_price"],
            "next_round_pool": [
                {
                    "candidate_id": "cand_year_price",
                    "text": "现在月费是多少，有没有年付？",
                    "source_kind": "user_reported",
                    "captured_at": "2026-03-02T00:00:00Z",
                    "market": "en-US",
                    "redacted": False,
                    "selection_reason": "新用户问了现价和年付，本轮分母不变。",
                    "related_question_ids": ["q_price"],
                    "related_fact_ids": ["fact_price"],
                    "replaces_frozen_set": False,
                }
            ],
        }
        validate_instance(questions, "round-questions.schema.json")
        validate_instance(facts, "round-facts.schema.json")
        validate_instance(backlog, "question-backlog.schema.json")
        frozen_ids = {item["question_id"] for item in questions["questions"]}
        self.assertEqual(frozen_ids, set(backlog["frozen_question_ids"]))
        self.assertNotIn(backlog["next_round_pool"][0]["candidate_id"], frozen_ids)
        self.assertFalse(backlog["next_round_pool"][0]["replaces_frozen_set"])
        self.assertEqual(len(questions["questions"]), 1)
        fact = facts["facts"][0]
        self.assertLess(fact["content_updated_at"], fact["verified_at"])
        old_answer = "公开起步价是每月 10 美元。"
        self.assertNotIn("10 美元", fact["statement"])
        self.assertIn("20 美元", fact["statement"])
        self.assertNotEqual(old_answer, fact["statement"])
        self.assertNotEqual(facts["facts_version"], "2")


class E11Tests(unittest.TestCase):
    # Synthetic fixture — no export vs complete window with zero transactions.
    def test_missing_export_is_not_measured(self) -> None:
        result = analyze({"schema_version": "1.1.0", "imports": []}, experiment_doc=_experiment())
        self.assertEqual(result["measurement_status"], "not_measured")
        self.assertIsNone(result["comparison"])
        self.assertTrue(any("没有业务导出" in line for line in result["limitations"]))
        self.assertTrue(any("下一步" in line for line in result["limitations"]))

    def test_complete_window_zero_is_measured_zero(self) -> None:
        events = _doc(_batch("imp_empty", [], coverage="complete"))
        validate_instance(events, "round-business-events.schema.json")
        result = analyze(events)
        self.assertEqual(result["measurement_status"], "measured_zero")
        self.assertEqual(result["event_counts"]["purchase"], 0)
        self.assertTrue(any("实测零" in line for line in result["limitations"]))
        self.assertTrue(any("下一步" in line for line in result["limitations"]))


if __name__ == "__main__":
    unittest.main()
