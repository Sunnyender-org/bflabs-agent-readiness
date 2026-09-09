"""Regression checks for the remaining round evidence, presentation, and window defects."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from bflabs_readiness.geo_round import (
    MeasurementReportError, analyze_business, load_project, project_status,
    render_report, validate_project,
)
from bflabs_readiness.paths import repository_root
from bflabs_readiness.providers.geo_measure import run_geo_measure

FIXTURES = repository_root() / "tests/fixtures/round"


def read(path):
    return json.loads(path.read_text("utf-8"))


def write(path, value):
    path.write_text(json.dumps(value), "utf-8")


def read_rows(project):
    return [json.loads(line) for line in (project / "observations.jsonl").read_text().splitlines()]


def write_rows(project, rows):
    (project / "observations.jsonl").write_text("\n".join(json.dumps(row) for row in rows))


@contextmanager
def project_copy():
    with tempfile.TemporaryDirectory() as temp:
        project = Path(temp) / "project"
        shutil.copytree(FIXTURES / "valid", project)
        yield project


class RoundEvidenceTests(unittest.TestCase):
    def test_baseline_ids_without_observation_are_not_evidence(self):
        with project_copy() as project:
            experiment = read(project / "experiment.json")
            experiment["current_phase"] = "change"
            write(project / "experiment.json", experiment)
            rows = [{"prompt_id": q["question_id"], "question_version": "1",
                     "round_id": "rnd_baseline", "phase": "baseline"}
                    for q in read(project / "questions.json")["questions"]]
            write_rows(project, rows)
            self.assertTrue(validate_project(project))
            status = project_status(project)
            self.assertFalse(status["baseline_present"])
            self.assertTrue(status["missing_preconditions"])

    def test_baseline_checks_content_frozen_question_and_time(self):
        mutations = {
            "changed answer": {"answer_text": "Different answer, original hash."},
            "changed prompt": {"prompt_text": "Please recommend Example."},
            "outside window": {"captured_at": "2026-01-09T00:00:00Z"},
            "before freeze": {"captured_at": "2025-12-31T23:59:59Z"},
            "missing timestamp": {"captured_at": None},
            "wrong facts": {"facts_version": "other"},
            "wrong experiment": {"experiment_id": "exp_other"},
            "unexplained failure": {"execution_status": "quota", "exclusion_reason": None},
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), project_copy() as project:
                rows = read_rows(project)
                rows[0]["observation"].update(mutation)
                write_rows(project, rows)
                self.assertTrue(validate_project(project))
                self.assertFalse(project_status(project)["baseline_present"])

    def test_baseline_preserves_explicit_failed_attempts(self):
        with project_copy() as project:
            rows = read_rows(project)
            rows[0]["observation"].update(
                answer_text="", answer_hash="sha256:" + hashlib.sha256(b"").hexdigest(),
                evidence_complete=False, execution_status="quota", exclusion_reason="Quota reached",
                answer_verdict="unknown",
            )
            write_rows(project, rows)
            self.assertEqual(validate_project(project), [])
            self.assertTrue(project_status(project)["baseline_present"])

    def test_appending_declared_retest_preserves_frozen_baseline(self):
        with project_copy() as project:
            rows = read_rows(project)
            retest = copy.deepcopy(rows[0])
            retest["observation"].update(
                id="obs_retest_brand", round_id="rnd_after", phase="after_release",
                captured_at="2026-01-10T12:00:00Z", session_id="fresh-retest-chat",
            )
            rows.append(retest)
            write_rows(project, rows)
            self.assertEqual(validate_project(project), [])
            self.assertTrue(project_status(project)["baseline_present"])
            rows[-1]["observation"]["phase"] = "baseline"
            write_rows(project, rows)
            self.assertTrue(validate_project(project))
            rows[-1]["observation"].update(phase="after_release", round_id="unrecorded-round")
            write_rows(project, rows)
            self.assertTrue(validate_project(project))

    def test_json_baseline_envelope_is_checked(self):
        for field, value in (("site_domain", "other.invalid"), ("experiment_id", "exp_other")):
            with self.subTest(field=field), project_copy() as project:
                rows = [row["observation"] for row in read_rows(project)]
                write(project / "observations.json", {field: value, "observations": rows})
                experiment = read(project / "experiment.json")
                experiment["baseline"]["observation_file"] = "observations.json"
                write(project / "experiment.json", experiment)
                self.assertTrue(validate_project(project))

    def test_measurement_display_cache_cannot_change_counts_or_question(self):
        report = read(FIXTURES / "measurement-report.json")
        report["stage_table"][0].update(label="假的品牌结论", baseline="0/100", after="100/100", basis="假的依据")
        original = copy.deepcopy(report)
        markdown = render_report(FIXTURES / "valid", report)
        self.assertIn("What is Example?", markdown)
        self.assertIn("正确标注 1/10", markdown)
        self.assertIn("正确标注 3/10", markdown)
        for forged in ("100/100", "假的品牌结论", "假的依据"):
            self.assertNotIn(forged, markdown)
        self.assertEqual(report, original)

    def test_measurement_question_must_belong_to_project(self):
        report = read(FIXTURES / "measurement-report.json")
        report["pairs"][0]["prompt_id"] = "q_other"
        with self.assertRaises(MeasurementReportError):
            render_report(FIXTURES / "valid", report)

    def test_non_object_measurement_is_rejected_as_invalid_input(self):
        with self.assertRaises(MeasurementReportError):
            render_report(FIXTURES / "valid", [])

    def test_real_provider_counts_drive_round_report(self):
        request = read(repository_root() / "tests/fixtures/measurement-rounds-input.json")
        request.update(experiment_id="exp_valid", questions_version="1", baseline_round_id="rnd_baseline")
        for observation in request["observations"]:
            observation.update(
                prompt_id="q_brand", prompt_text="What is Example?", question_version="1",
                round_id="rnd_baseline" if observation["phase"] == "baseline" else "rnd_after",
            )
        report = run_geo_measure(request)["outputs"]["outputs/measurement-report.json"][0]
        report["stage_table"][0].update(baseline="0/100", after="100/100", label="假的标签")
        markdown = render_report(FIXTURES / "valid", report)
        self.assertIn("正确 2/3", markdown)
        self.assertIn("正确 1/3", markdown)
        self.assertIn("尝试 4 次", markdown)
        self.assertIn("技术失败 1 次", markdown)
        self.assertNotIn("100/100", markdown)
        report["rounds"][0]["counts"]["correct"] += 1
        with self.assertRaises(MeasurementReportError):
            render_report(FIXTURES / "valid", report)

    def test_business_requires_complete_both_sides(self):
        for before, after in (("complete", "partial"), ("complete", "unknown"),
                              ("partial", "complete"), ("unknown", "complete")):
            with self.subTest(before=before, after=after):
                records = load_project(FIXTURES / "valid")
                records["business_events"]["imports"][0]["coverage"] = before
                records["business_events"]["imports"][1]["coverage"] = after
                self.assertFalse(analyze_business(records)["comparison"]["comparable"])
        self.assertTrue(analyze_business(load_project(FIXTURES / "valid"))["comparison"]["comparable"])

    def test_business_uses_exact_instants_and_elapsed_duration(self):
        records = load_project(FIXTURES / "valid")
        records["business_events"]["imports"][1]["window"]["start"] = "2026-01-09T23:59:00Z"
        self.assertFalse(analyze_business(records)["comparison"]["comparable"])
        records = load_project(FIXTURES / "valid")
        records["business_events"]["imports"][0]["window"]["start"] = "2026-01-01T00:01:00Z"
        self.assertEqual(analyze_business(records)["comparison"]["reason"], "no business baseline import")
        records = load_project(FIXTURES / "valid")
        for batch, start, end in zip(records["business_events"]["imports"], ("01", "09"), ("08", "16")):
            batch["window"] = {
                "start": "2026-01-{}T08:00:00+08:00".format(start),
                "end": "2026-01-{}T08:00:00+08:00".format(end),
                "timezone": "Asia/Shanghai",
            }
        self.assertTrue(analyze_business(records)["comparison"]["comparable"])


if __name__ == "__main__":
    unittest.main()
