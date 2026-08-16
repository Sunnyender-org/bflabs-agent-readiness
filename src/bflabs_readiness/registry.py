"""Capability registry: one interface for status, contracts, and public entrypoints."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .paths import repository_root
from .schemas import validate_instance


class RegistryError(ValueError):
    """Raised when registry state is invalid or not executable."""


@dataclass(frozen=True)
class Capability:
    id: str
    version: str
    status: str
    intents: List[str]
    languages: List[str]
    entrypoint: Optional[str]
    execution: str
    input_schema: Optional[str]
    outputs: List[str]
    permissions: List[str]
    external_gates: List[str]
    degrades_to: str

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "Capability":
        return cls(**value)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "status": self.status,
            "intents": self.intents,
            "languages": self.languages,
            "entrypoint": self.entrypoint,
            "execution": self.execution,
            "input_schema": self.input_schema,
            "outputs": self.outputs,
            "permissions": self.permissions,
            "external_gates": self.external_gates,
            "degrades_to": self.degrades_to,
        }


@dataclass(frozen=True)
class Workflow:
    id: str
    version: str
    status: str
    steps: List[str]

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "Workflow":
        return cls(**value)


class CapabilityRegistry:
    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = (root or repository_root()).resolve()
        payload = json.loads((self.root / "registry/capabilities.json").read_text("utf-8"))
        self.schema_version = payload.get("schema_version")
        self._payload = payload
        self._capabilities = [Capability.from_dict(item) for item in payload.get("capabilities", [])]
        workflow_payload = json.loads((self.root / "registry/workflows.json").read_text("utf-8"))
        self._workflow_payload = workflow_payload
        self._workflows = [Workflow.from_dict(item) for item in workflow_payload.get("workflows", [])]

    def list_capabilities(self, status: Optional[str] = None) -> List[Capability]:
        capabilities: Iterable[Capability] = self._capabilities
        if status is not None:
            capabilities = (capability for capability in capabilities if capability.status == status)
        return sorted(capabilities, key=lambda capability: capability.id)

    def resolve(self, capability_id: str, executable: bool = False) -> Capability:
        match = next((capability for capability in self._capabilities if capability.id == capability_id), None)
        if match is None:
            raise RegistryError("unknown capability: {}".format(capability_id))
        if executable and match.status != "active":
            raise RegistryError(
                "capability {} is {}; nearest fallback is {}".format(match.id, match.status, match.degrades_to)
            )
        return match

    def read_entrypoint(self, capability_id: str) -> str:
        capability = self.resolve(capability_id)
        if not capability.entrypoint:
            raise RegistryError("capability {} has no runnable entrypoint".format(capability_id))
        path = (self.root / capability.entrypoint).resolve()
        if self.root not in path.parents and path != self.root:
            raise RegistryError("entrypoint escapes repository root")
        if path.name != "SKILL.md" or not path.is_file():
            raise RegistryError("entrypoint is not a public SKILL.md")
        return path.read_text("utf-8")

    def list_workflows(self, status: Optional[str] = None) -> List[Workflow]:
        workflows: Iterable[Workflow] = self._workflows
        if status is not None:
            workflows = (workflow for workflow in workflows if workflow.status == status)
        return sorted(workflows, key=lambda workflow: workflow.id)

    def resolve_workflow(self, workflow_id: str, executable: bool = False) -> Workflow:
        match = next((workflow for workflow in self._workflows if workflow.id == workflow_id), None)
        if match is None:
            raise RegistryError("unknown workflow: {}".format(workflow_id))
        if executable and match.status != "active":
            raise RegistryError("workflow {} is {}".format(match.id, match.status))
        return match

    def validate(self) -> None:
        validate_instance(self._payload, "capabilities-registry.schema.json")
        ids = [capability.id for capability in self._capabilities]
        if len(ids) != len(set(ids)):
            raise RegistryError("duplicate capability ids")

        for capability in self._capabilities:
            if capability.status == "active" and not capability.entrypoint:
                raise RegistryError("active capability {} needs an entrypoint".format(capability.id))
            if capability.status == "planned" and capability.entrypoint is not None:
                raise RegistryError("planned capability {} cannot expose an entrypoint".format(capability.id))
            if capability.entrypoint and not (self.root / capability.entrypoint).is_file():
                raise RegistryError("missing entrypoint for {}".format(capability.id))
            if capability.input_schema and not (self.root / capability.input_schema).is_file():
                raise RegistryError("missing input schema for {}".format(capability.id))

        workflows = self._workflow_payload
        validate_instance(workflows, "workflows-registry.schema.json")
        known = set(ids)
        for workflow in workflows["workflows"]:
            missing = [step for step in workflow["steps"] if step not in known]
            if missing:
                raise RegistryError("workflow {} references unknown capabilities {}".format(workflow["id"], missing))
            if workflow["status"] == "active":
                inactive = [step for step in workflow["steps"] if self.resolve(step).status != "active"]
                if inactive:
                    raise RegistryError("active workflow {} contains inactive steps {}".format(workflow["id"], inactive))
