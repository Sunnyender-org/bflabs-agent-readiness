from __future__ import annotations

import unittest

from bflabs_readiness.registry import CapabilityRegistry, RegistryError


class RegistryTests(unittest.TestCase):
    def test_registry_validates_and_lists_current_state(self) -> None:
        registry = CapabilityRegistry()
        registry.validate()
        active = {capability.id for capability in registry.list_capabilities("active")}
        planned = {capability.id for capability in registry.list_capabilities("planned")}
        self.assertEqual(
            active,
            {"bflabs-agent-readiness", "geo-content", "geo-discover", "geo-measure", "geo-optimize", "seo-plan", "webmcp-enable"},
        )
        self.assertEqual(planned, set())

    def test_unknown_capability_cannot_execute(self) -> None:
        with self.assertRaisesRegex(RegistryError, "unknown capability"):
            CapabilityRegistry().resolve("not-a-capability", executable=True)

    def test_only_skill_entrypoints_are_readable(self) -> None:
        text = CapabilityRegistry().read_entrypoint("geo-optimize")
        self.assertIn("name: geo-optimize", text)
        with self.assertRaisesRegex(RegistryError, "unknown capability"):
            CapabilityRegistry().read_entrypoint("not-a-capability")


if __name__ == "__main__":
    unittest.main()
