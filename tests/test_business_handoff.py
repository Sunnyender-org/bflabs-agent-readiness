"""Real service-export fixture: preserve evidence semantics across a one-time handoff."""
import json
import unittest
from datetime import datetime

from bflabs_readiness.business_attribution import analyze
from bflabs_readiness.business_transfer import from_service, to_service
from bflabs_readiness.paths import repository_root
from bflabs_readiness.schemas import validate_instance


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
