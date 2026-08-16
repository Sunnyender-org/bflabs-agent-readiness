from __future__ import annotations

import json
import unittest

from bflabs_readiness.paths import repository_root
from bflabs_readiness.router import route
from bflabs_readiness.schemas import validate_instance


class RouterTests(unittest.TestCase):
    def test_fixed_bilingual_router_cases(self) -> None:
        cases = json.loads((repository_root() / "evals/router_cases.json").read_text("utf-8"))["cases"]
        for case in cases:
            with self.subTest(case=case["id"]):
                decision = route(case["prompt"])
                validate_instance(decision, "route-decision.schema.json")
                selected = decision["selected"]
                self.assertEqual(decision["kind"], case["kind"])
                self.assertEqual(selected["id"] if selected else None, case["selected_id"])
                self.assertEqual(selected["status"] if selected else None, case["status"])
                self.assertEqual(decision["executable"], case["executable"])

    def test_last_v1_capability_is_active_without_external_gate(self) -> None:
        decision = route("规划网站迁移 SEO")
        self.assertEqual(decision["selected"]["id"], "seo-plan")
        self.assertTrue(decision["executable"])
        self.assertIsNone(decision["fallback"])
        self.assertEqual(decision["required_gates"], [])

    def test_single_intent_never_expands_to_workflow(self) -> None:
        for prompt in ["诊断网站", "发现问题机会", "生成价格页面蓝图"]:
            self.assertNotEqual(route(prompt)["kind"], "workflow")


if __name__ == "__main__":
    unittest.main()
