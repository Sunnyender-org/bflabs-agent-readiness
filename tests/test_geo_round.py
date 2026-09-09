from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from bflabs_readiness.cli import main
from bflabs_readiness.geo_round import (
    ERR_AI_EVENT_EVIDENCE,
    ERR_BASELINE_ROUND_ID,
    ERR_FACTS_VERSION,
    ERR_MONEY_ONLY_ON_PURCHASE,
    ERR_QUESTIONS_VERSION,
    ERR_RELEASED_REQUIRES_RELEASED_AT,
    ERR_UNKNOWN_ACTION_ID,
    ERR_UNKNOWN_FACT_ID,
    ERR_UNKNOWN_QUESTION_ID,
    ERR_VERIFIED_PUBLIC_REQUIRES_PASS,
    MISSING_BASELINE_BEFORE_CHANGE,
    analyze_business,
    load_project,
    project_status,
    render_report,
    validate_project,
    write_report,
)
from bflabs_readiness.paths import repository_root
from bflabs_readiness.schemas import validate_all_schemas, validate_instance


FIXTURES = repository_root() / "tests/fixtures/round"
TEMPLATE_SCHEMAS = (
    ("templates/round-experiment.json", "round-experiment.schema.json"),
    ("templates/round-facts.json", "round-facts.schema.json"),
    ("templates/round-questions.json", "round-questions.schema.json"),
    ("templates/round-actions.json", "round-actions.schema.json"),
    ("templates/round-business-events.json", "round-business-events.schema.json"),
)


def _copy_fixture(name: str, dest: Path) -> Path:
    source = FIXTURES / name
    shutil.copytree(source, dest)
    return dest


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", "utf-8")


def _empty_import(**overrides: object) -> dict:
    batch = {
        "import_id": "imp_case",
        "source": "manual",
        "source_label": "test import",
        "window": {
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-01-08T00:00:00Z",
            "timezone": "UTC",
        },
        "coverage": "complete",
        "export_filter": None,
        "events": [],
    }
    batch.update(overrides)
    return batch


def _event(**overrides: object) -> dict:
    event = {
        "external_id": "e1",
        "type": "visit",
        "occurred_at": "2026-01-02T00:00:00Z",
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


def _records_with_business(*imports: dict, experiment: dict | None = None) -> dict:
    return {
        "experiment": experiment,
        "facts": None,
        "questions": None,
        "actions": None,
        "business_events": {"schema_version": "1.0.0", "imports": list(imports)},
    }


class GeoRoundTests(unittest.TestCase):
    def run_cli(self, arguments: list[str]) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(arguments)
        return status, output.getvalue()

    def test_schemas_and_templates_are_valid(self) -> None:
        validate_all_schemas()
        for relative, schema_name in TEMPLATE_SCHEMAS:
            with self.subTest(relative=relative):
                payload = json.loads((repository_root() / relative).read_text("utf-8"))
                validate_instance(payload, schema_name)

    def test_valid_project_passes(self) -> None:
        project = FIXTURES / "valid"
        self.assertEqual(validate_project(project), [])
        records = load_project(project)
        self.assertIsNotNone(records["experiment"])
        self.assertEqual(records["experiment"]["experiment_id"], "exp_valid")

    def test_cross_file_baseline_round_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            experiment = json.loads((project / "experiment.json").read_text("utf-8"))
            experiment["baseline"]["round_id"] = "rnd_missing"
            _write_json(project / "experiment.json", experiment)
            errors = validate_project(project)
            self.assertTrue(any(ERR_BASELINE_ROUND_ID in item for item in errors))

    def test_cross_file_facts_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            facts = json.loads((project / "facts.json").read_text("utf-8"))
            facts["facts_version"] = "other"
            _write_json(project / "facts.json", facts)
            errors = validate_project(project)
            self.assertTrue(any(ERR_FACTS_VERSION in item for item in errors))

    def test_cross_file_questions_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            questions = json.loads((project / "questions.json").read_text("utf-8"))
            questions["questions_version"] = "other"
            _write_json(project / "questions.json", questions)
            errors = validate_project(project)
            self.assertTrue(any(ERR_QUESTIONS_VERSION in item for item in errors))

    def test_cross_file_unknown_fact_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            actions = json.loads((project / "actions.json").read_text("utf-8"))
            actions["actions"][0]["fact_ids"] = ["fact_missing"]
            _write_json(project / "actions.json", actions)
            errors = validate_project(project)
            self.assertTrue(any(ERR_UNKNOWN_FACT_ID in item for item in errors))

    def test_cross_file_unknown_question_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            actions = json.loads((project / "actions.json").read_text("utf-8"))
            actions["actions"][0]["question_ids"] = ["q_missing"]
            _write_json(project / "actions.json", actions)
            errors = validate_project(project)
            self.assertTrue(any(ERR_UNKNOWN_QUESTION_ID in item for item in errors))

    def test_cross_file_unknown_compared_action_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            experiment = json.loads((project / "experiment.json").read_text("utf-8"))
            experiment["rounds"][1]["compared_action_ids"] = ["act_missing"]
            _write_json(project / "experiment.json", experiment)
            errors = validate_project(project)
            self.assertTrue(any(ERR_UNKNOWN_ACTION_ID in item for item in errors))

    def test_cross_file_released_requires_released_at(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            actions = json.loads((project / "actions.json").read_text("utf-8"))
            actions["actions"][1]["released_at"] = None
            _write_json(project / "actions.json", actions)
            errors = validate_project(project)
            self.assertTrue(any(ERR_RELEASED_REQUIRES_RELEASED_AT in item for item in errors))

    def test_cross_file_verified_public_requires_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            actions = json.loads((project / "actions.json").read_text("utf-8"))
            actions["actions"][0]["public_recheck"]["result"] = "fail"
            _write_json(project / "actions.json", actions)
            errors = validate_project(project)
            self.assertTrue(any(ERR_VERIFIED_PUBLIC_REQUIRES_PASS in item for item in errors))

    def test_cross_file_ai_event_needs_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            business = json.loads((project / "business-events.json").read_text("utf-8"))
            business["imports"][0]["events"].append(
                _event(external_id="ai-bad", type="visit", source_type="ai", source_evidence_url=None, attribution_method="unknown")
            )
            _write_json(project / "business-events.json", business)
            errors = validate_project(project)
            self.assertTrue(any(ERR_AI_EVENT_EVIDENCE in item for item in errors))

    def test_cross_file_money_only_on_purchase(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            business = json.loads((project / "business-events.json").read_text("utf-8"))
            business["imports"][0]["events"][0]["amount_minor"] = 100
            business["imports"][0]["events"][0]["currency"] = "USD"
            _write_json(project / "business-events.json", business)
            errors = validate_project(project)
            self.assertTrue(any(ERR_MONEY_ONLY_ON_PURCHASE in item for item in errors))

    def test_status_reports_missing_baseline_in_change_phase(self) -> None:
        status = project_status(FIXTURES / "change-missing-baseline")
        self.assertEqual(status["current_phase"], "change")
        self.assertFalse(status["baseline_present"])
        self.assertIn(MISSING_BASELINE_BEFORE_CHANGE, status["missing_preconditions"])
        self.assertEqual(status["actions_by_status"]["planned"], 1)

    def test_business_no_data_is_not_measured(self) -> None:
        analysis = analyze_business(
            {
                "experiment": None,
                "facts": None,
                "questions": None,
                "actions": None,
                "business_events": None,
            }
        )
        self.assertEqual(analysis["status"], "not_measured")
        self.assertEqual(analysis["imports"], [])

    def test_business_complete_zero_is_measured_zero(self) -> None:
        analysis = analyze_business(_records_with_business(_empty_import(coverage="complete", events=[])))
        item = analysis["imports"][0]
        self.assertEqual(item["status"], "measured_zero")
        self.assertEqual(item["counts"]["visit"], 0)
        self.assertEqual(item["counts"]["purchase"], 0)
        self.assertEqual(item["test_event_count"], 0)

    def test_business_unknown_coverage_is_data_incomplete(self) -> None:
        analysis = analyze_business(_records_with_business(_empty_import(coverage="unknown", events=[])))
        self.assertEqual(analysis["imports"][0]["status"], "data_incomplete")
        self.assertEqual(analysis["imports"][0]["counts"]["visit"], 0)

    def test_business_missing_visits_nulls_signup_rate(self) -> None:
        analysis = analyze_business(
            _records_with_business(
                _empty_import(events=[_event(external_id="s1", type="signup", source_type="direct")])
            )
        )
        item = analysis["imports"][0]
        self.assertIsNone(item["signup_rate"])
        self.assertEqual(item["signup_rate_reason"], "missing visits")
        self.assertEqual(item["counts"]["signup"], 1)

    def test_business_only_test_events(self) -> None:
        analysis = analyze_business(
            _records_with_business(
                _empty_import(
                    events=[
                        _event(
                            external_id="t1",
                            type="purchase",
                            source_type="direct",
                            amount_minor=999,
                            currency="USD",
                            is_test=True,
                        )
                    ]
                )
            )
        )
        item = analysis["imports"][0]
        self.assertEqual(item["status"], "measured_zero")
        self.assertEqual(item["counts"]["purchase"], 0)
        self.assertEqual(item["test_counts"]["purchase"], 1)
        self.assertEqual(item["revenue_by_currency"], {})

    def test_business_social_purchase_stays_social(self) -> None:
        analysis = analyze_business(load_project(FIXTURES / "valid"))
        sources = analysis["imports"][0]["source_type_counts"]
        self.assertEqual(sources["social"], 1)
        self.assertEqual(sources["ai"], 0)

    def test_business_unknown_source_never_ai(self) -> None:
        analysis = analyze_business(
            _records_with_business(_empty_import(events=[_event(source_type="unknown")]))
        )
        sources = analysis["imports"][0]["source_type_counts"]
        self.assertEqual(sources["unknown"], 1)
        self.assertEqual(sources["ai"], 0)

    def test_business_two_currencies_are_separate(self) -> None:
        analysis = analyze_business(
            _records_with_business(
                _empty_import(
                    events=[
                        _event(
                            external_id="p-usd",
                            type="purchase",
                            source_type="direct",
                            amount_minor=1000,
                            currency="USD",
                        ),
                        _event(
                            external_id="p-eur",
                            type="purchase",
                            source_type="direct",
                            amount_minor=400,
                            currency="EUR",
                        ),
                    ]
                )
            )
        )
        self.assertEqual(analysis["imports"][0]["revenue_by_currency"], {"USD": 1000, "EUR": 400})

    def test_business_overlapping_windows_are_flagged(self) -> None:
        analysis = analyze_business(
            _records_with_business(
                _empty_import(import_id="imp_a"),
                _empty_import(
                    import_id="imp_b",
                    window={
                        "start": "2026-01-07T00:00:00Z",
                        "end": "2026-01-14T00:00:00Z",
                        "timezone": "UTC",
                    },
                ),
            )
        )
        self.assertEqual(
            analysis["flags"]["overlapping_windows"],
            [{"left": "imp_a", "right": "imp_b"}],
        )

    def test_business_unequal_windows_are_not_comparable(self) -> None:
        experiment = json.loads((FIXTURES / "valid" / "experiment.json").read_text("utf-8"))
        analysis = analyze_business(
            _records_with_business(
                _empty_import(import_id="imp_before"),
                _empty_import(
                    import_id="imp_after",
                    window={
                        "start": "2026-01-09T00:00:00Z",
                        "end": "2026-01-23T00:00:00Z",
                        "timezone": "UTC",
                    },
                ),
                experiment=experiment,
            )
        )
        comparison = analysis["comparison"]
        self.assertIsNotNone(comparison)
        self.assertFalse(comparison["comparable"])
        self.assertEqual(comparison["reason"], "unequal window length")
        self.assertEqual(comparison["before"]["import_id"], "imp_before")
        self.assertEqual(comparison["after"]["import_id"], "imp_after")

    def test_report_renders_without_measurement(self) -> None:
        markdown = render_report(FIXTURES / "valid", None)
        self.assertIn("改了哪几页、哪些事实？", markdown)
        self.assertIn("未测", markdown)
        self.assertIn("记录来源", markdown)
        self.assertIn("experiment.json", markdown)
        body, footer = markdown.split("## 记录来源", 1)
        self.assertNotIn("changed_local", body)
        self.assertNotIn("measured_zero", body)
        self.assertIn("facts.json", footer)

    def test_report_embeds_measurement_stage_table(self) -> None:
        measurement = json.loads((FIXTURES / "measurement-report.json").read_text("utf-8"))
        markdown = render_report(FIXTURES / "valid", measurement)
        self.assertIn("品牌被提到", markdown)
        self.assertIn("1/10", markdown)
        self.assertIn("3/10", markdown)
        self.assertNotIn("\n未测\n", "\n" + markdown.split("## 前后对比", 1)[1].split("## 转化率", 1)[0])

    def test_write_report_creates_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            path = write_report(project, FIXTURES / "measurement-report.json")
            self.assertEqual(path, (project / "report.md").resolve())
            text = path.read_text("utf-8")
            self.assertIn("品牌被提到", text)

    def test_cli_round_validate_status_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            status, output = self.run_cli(["round", "validate", "--project", str(project)])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(output)["status"], "pass")

            status, output = self.run_cli(["round", "status", "--project", str(project), "--format", "json"])
            payload = json.loads(output)
            self.assertEqual(status, 0)
            self.assertEqual(payload["current_phase"], "business_review")
            self.assertTrue(payload["baseline_present"])

            status, output = self.run_cli(
                [
                    "round",
                    "report",
                    "--project",
                    str(project),
                    "--measurement-report",
                    str(FIXTURES / "measurement-report.json"),
                ]
            )
            result = json.loads(output)
            self.assertEqual(status, 0)
            self.assertTrue(Path(result["report"]).is_file())
            self.assertIn("品牌被提到", Path(result["report"]).read_text("utf-8"))

    def test_cli_round_validate_fails_on_named_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = _copy_fixture("valid", Path(temp) / "project")
            experiment = json.loads((project / "experiment.json").read_text("utf-8"))
            experiment["facts_version"] = "mismatch"
            _write_json(project / "experiment.json", experiment)
            status, output = self.run_cli(["round", "validate", "--project", str(project)])
            self.assertEqual(status, 1)
            self.assertIn(ERR_FACTS_VERSION, output)

    def test_cli_status_summary_for_change_without_baseline(self) -> None:
        status, output = self.run_cli(
            ["round", "status", "--project", str(FIXTURES / "change-missing-baseline"), "--format", "summary"]
        )
        self.assertEqual(status, 0)
        self.assertIn("current_phase: change", output)
        self.assertIn(MISSING_BASELINE_BEFORE_CHANGE, output)


if __name__ == "__main__":
    unittest.main()
