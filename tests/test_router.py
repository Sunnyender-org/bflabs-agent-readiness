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

    def test_full_round_routes_to_root_capability(self) -> None:
        decision = route("帮我完整做一轮 GEO 优化，从改前基线到复测")
        self.assertEqual(decision["kind"], "capability")
        self.assertEqual(decision["selected"]["id"], "bflabs-agent-readiness")
        self.assertTrue(decision["executable"])
        self.assertNotEqual(decision["kind"], "workflow")

    def test_resume_stays_full_round_root_capability(self) -> None:
        decision = route("继续上次的 GEO 轮次")
        self.assertEqual(decision["kind"], "capability")
        self.assertEqual(decision["selected"]["id"], "bflabs-agent-readiness")
        self.assertTrue(decision["executable"])

    def test_no_site_and_build_only_select_seo_plan(self) -> None:
        for prompt in (
            "我还没有网站，先帮我做网站基础",
            "I don't have a website yet, plan the site foundation",
            "只帮我建网站，先不要做 AI 采样",
        ):
            decision = route(prompt)
            self.assertEqual(decision["kind"], "capability")
            self.assertEqual(decision["selected"]["id"], "seo-plan")
            self.assertTrue(decision["executable"])

    def test_explain_and_attribution_do_not_start_execution(self) -> None:
        for prompt in (
            "解释一下来源归因怎么做，先不要执行",
            "Explain GEO attribution but do not start a workflow",
            "只分析我这份业务导出，不要开整轮",
        ):
            decision = route(prompt)
            self.assertEqual(decision["kind"], "needs_clarification")
            self.assertIsNone(decision["selected"])
            self.assertFalse(decision["executable"])


if __name__ == "__main__":
    unittest.main()
