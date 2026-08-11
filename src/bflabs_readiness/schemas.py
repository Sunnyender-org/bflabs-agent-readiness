"""JSON Schema loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .paths import repository_root


class SchemaValidationError(ValueError):
    """Raised when an instance violates a public contract."""


def _jsonschema():
    try:
        import jsonschema
    except ModuleNotFoundError as exc:
        raise RuntimeError("jsonschema is required; install the package with `python3 -m pip install -e .`") from exc
    return jsonschema


def schema_path(name: str) -> Path:
    path = (repository_root() / "schemas" / name).resolve()
    if path.parent != (repository_root() / "schemas").resolve() or not path.is_file():
        raise FileNotFoundError("unknown schema: {}".format(name))
    return path


def load_schema(name: str) -> Dict[str, Any]:
    return json.loads(schema_path(name).read_text("utf-8"))


def _schema_registry():
    from referencing import Registry, Resource

    resources = []
    for path in sorted((repository_root() / "schemas").glob("*.schema.json")):
        schema = json.loads(path.read_text("utf-8"))
        if schema.get("$id"):
            resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def validate_instance(instance: Any, schema_name: str) -> None:
    jsonschema = _jsonschema()
    schema = load_schema(schema_name)
    validator = jsonschema.Draft202012Validator(
        schema,
        registry=_schema_registry(),
        format_checker=jsonschema.FormatChecker(),
    )
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    if errors:
        details: List[str] = []
        for error in errors[:10]:
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            details.append("{}: {}".format(location, error.message))
        raise SchemaValidationError("{} failed schema validation: {}".format(schema_name, "; ".join(details)))


def validate_all_schemas() -> None:
    jsonschema = _jsonschema()
    for path in sorted((repository_root() / "schemas").glob("*.schema.json")):
        schema = json.loads(path.read_text("utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
