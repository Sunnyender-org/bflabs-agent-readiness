from __future__ import annotations

import unittest

from bflabs_readiness.registry import CapabilityRegistry
from bflabs_readiness.router import route


class WorkflowTests(unittest.TestCase):
    def test_registry_contains_only_two_stable_workflow_definitions(self) -> None:
        workflows = CapabilityRegistry().list_workflows()
        self.assertEqual([workflow.id for workflow in workflows], ["discover-content", "discover-diagnose"])
        self.assertEqual(
            {workflow.id: workflow.status for workflow in workflows},
            {"discover-content": "active", "discover-diagnose": "active"},
        )

    def test_explicit_discover_diagnose_returns_exact_dag(self) -> None:
        decision = route("先挖掘用户问题和意图，然后诊断网站")
        self.assertEqual(decision["kind"], "workflow")
        self.assertEqual(decision["selected"]["id"], "discover-diagnose")
        self.assertEqual(decision["selected"]["steps"], ["geo-discover", "geo-optimize"])
        self.assertTrue(decision["executable"])

    def test_explicit_discover_content_returns_exact_dag(self) -> None:
        decision = route("Discover buyer questions, then create a comparison page")
        self.assertEqual(decision["kind"], "workflow")
        self.assertEqual(decision["selected"]["id"], "discover-content")
        self.assertEqual(decision["selected"]["steps"], ["geo-discover", "geo-content"])
        self.assertTrue(decision["executable"])


if __name__ == "__main__":
    unittest.main()
