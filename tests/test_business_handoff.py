"""Real service-export fixture: preserve evidence semantics across a one-time handoff."""
import json
import unittest
import copy
import io
import shutil
import tempfile
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

from bflabs_readiness.business_attribution import analyze
from bflabs_readiness.business_transfer import from_service, to_service
from bflabs_readiness.paths import repository_root
from bflabs_readiness.schemas import validate_instance
from bflabs_readiness.cli import main
from bflabs_readiness.geo_round import analyze_business, load_project


def normalized(value):
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalized(item) for item in value]
    if isinstance(value, str) and "T" in value and value.endswith("Z"):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            pass
    return value


class BusinessHandoffTests(unittest.TestCase):
    def test_actual_sqlite_export_retains_business_meaning(self):
        folder = repository_root() / "tests/fixtures/business-handoff"
        original = json.loads((folder / "portable.json").read_text())
        returned = from_service(json.loads((folder / "service.json").read_text()))
        validate_instance(returned["business_events"], "round-business-events.schema.json")
        self.assertEqual(original["experiment_business_fields"], returned["experiment_business_fields"])
        before = analyze(original["business_events"], experiment_doc=original["experiment_business_fields"])
        after = analyze(returned["business_events"], experiment_doc=returned["experiment_business_fields"])
        for key in ("event_counts", "views", "cashflow", "cohort_net", "comparison"):
            self.assertEqual(normalized(before[key]), normalized(after[key]), key)
        self.assertEqual(after["cashflow"]["totals_by_currency"]["USD"]["amount_minor"], 500)
        imports = to_service(original["business_events"], original["experiment_business_fields"])
        self.assertEqual(imports[0]["surveys"][0]["respondent_ref"], "user:usr_example")
        self.assertEqual(imports[0]["events"][-1]["original_order_id"], "order1")

    def test_native_unmapped_records_are_not_silently_reconstructed(self):
        with self.assertRaises(ValueError):
            from_service({"project": {}, "business_batches": [{"source": "native"}]})

    def test_standalone_and_round_use_the_same_evidence_scope(self):
        original = json.loads((repository_root() / "tests/fixtures/business-handoff/portable.json").read_text())
        document = original["business_events"]
        payment = next(row for row in document["imports"][0]["events"] if row["type"] == "purchase")
        outside = {**copy.deepcopy(payment), "external_id": "old-payment", "order_id": "old-order", "occurred_at": "2025-01-01T00:00:00Z", "amount_minor": 4000}
        foreign = {**copy.deepcopy(payment), "external_id": "foreign-payment", "order_id": "foreign-order", "page_url": "https://example.net/", "amount_minor": 2000}
        document["imports"][0]["events"].extend([outside, foreign])
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / "project"
            shutil.copytree(repository_root() / "tests/fixtures/round/valid", project)
            experiment = json.loads((project / "experiment.json").read_text())
            experiment.update(schema_version="1.1.0", **original["experiment_business_fields"])
            (project / "experiment.json").write_text(json.dumps(experiment))
            path = project / "business-events.json"
            path.write_text(json.dumps(document))
            raw = path.read_bytes()
            output = io.StringIO()
            with redirect_stdout(output):
                result = main(["business", "--input", str(path), "--experiment", str(project / "experiment.json"), "--format", "json"])
            self.assertEqual(result, 0)
            standalone = json.loads(output.getvalue())
            round_result = analyze_business(load_project(project))["attribution"]
            self.assertEqual(standalone["cashflow"], round_result["cashflow"])
            self.assertEqual(standalone["cashflow"]["totals_by_currency"]["USD"]["amount_minor"], 500)
            self.assertEqual(path.read_bytes(), raw)
