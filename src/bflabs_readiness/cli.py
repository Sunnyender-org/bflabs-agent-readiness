"""Command-line interface for the public readiness registry and Artifact Protocol."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from . import __version__
from .artifacts import publish_run, validate_run
from .evals import run_router_evals
from .orchestrator import run_discover_content, run_discover_diagnose
from .paths import repository_root
from .packaging import CAPABILITY_IDS, PackageError, package_target, validate_archive
from .providers.geo_optimize import run_geo_optimize
from .providers.geo_discover import run_geo_discover
from .providers.geo_content import run_geo_content
from .providers.geo_measure import load_measurement_input, run_geo_measure
from .providers.seo_plan import run_seo_plan
from .registry import CapabilityRegistry, RegistryError
from .router import route
from .schemas import validate_all_schemas, validate_instance


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def _print_capabilities(registry: CapabilityRegistry, status: Optional[str], output_format: str) -> None:
    capabilities = [capability.as_dict() for capability in registry.list_capabilities(status)]
    if output_format == "json":
        print(json.dumps({"schema_version": registry.schema_version, "capabilities": capabilities}, ensure_ascii=False, indent=2))
        return
    for capability in capabilities:
        entrypoint = capability["entrypoint"] or "unavailable"
        print("- `{}` ({}, {}): `{}`".format(capability["id"], capability["status"], capability["version"], entrypoint))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bflabs-readiness")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    list_parser = commands.add_parser("list")
    list_parser.add_argument("--status", choices=["active", "planned", "disabled", "deprecated"])
    list_parser.add_argument("--format", choices=["json", "markdown"], default="json")

    read_parser = commands.add_parser("read")
    read_parser.add_argument("capability_id")

    route_parser = commands.add_parser("route")
    route_parser.add_argument("--text", required=True)
    route_parser.add_argument("--format", choices=["json", "summary"], default="json")

    run_parser = commands.add_parser("run")
    run_target = run_parser.add_mutually_exclusive_group(required=True)
    run_target.add_argument("--capability")
    run_target.add_argument("--workflow")
    run_target.add_argument("--text")
    run_parser.add_argument("--input", required=True, type=Path)
    run_parser.add_argument("--output", type=Path, default=Path("runs"))

    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--run", type=Path)

    commands.add_parser("eval")

    package_parser = commands.add_parser("package")
    package_parser.add_argument("--target", required=True, choices=["source", "unified", *CAPABILITY_IDS])
    package_parser.add_argument("--output", type=Path, default=Path("dist"))
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    registry = CapabilityRegistry()
    try:
        if args.command == "list":
            _print_capabilities(registry, args.status, args.format)
            return 0
        if args.command == "read":
            print(registry.read_entrypoint(args.capability_id), end="")
            return 0
        if args.command == "route":
            decision = route(args.text, registry)
            if args.format == "json":
                print(json.dumps(decision, ensure_ascii=False, indent=2))
            else:
                selected = decision["selected"]["id"] if decision["selected"] else "none"
                print("{}: {} (executable={})".format(decision["kind"], selected, str(decision["executable"]).lower()))
            return 0
        if args.command == "run":
            capability_id = args.capability
            workflow_id = args.workflow
            if args.text:
                decision = route(args.text, registry)
                if not decision["executable"] or not decision["selected"]:
                    raise RegistryError("request is not directly executable: {}".format(decision["kind"]))
                if decision["kind"] == "workflow":
                    workflow_id = decision["selected"]["id"]
                else:
                    capability_id = decision["selected"]["id"]
            request = (
                load_measurement_input(args.input)
                if capability_id == "geo-measure"
                else _load_json(args.input)
            )
            if workflow_id:
                if workflow_id == "discover-diagnose":
                    run_dir = run_discover_diagnose(request, args.output)
                elif workflow_id == "discover-content":
                    run_dir = run_discover_content(request, args.output)
                else:
                    raise RegistryError("workflow {} is not executable".format(workflow_id))
                manifest = json.loads((run_dir / "run-manifest.json").read_text("utf-8"))
                print(json.dumps({"status": manifest["status"], "run_dir": str(run_dir)}, indent=2))
                return 0
            capability = registry.resolve(capability_id, executable=True)
            if capability.input_schema:
                validate_instance(request, capability.input_schema.split("/")[-1])
            if capability.id == "geo-optimize":
                result = run_geo_optimize(request)
            elif capability.id == "geo-discover":
                result = run_geo_discover(request)
            elif capability.id == "geo-content":
                result = run_geo_content(request)
            elif capability.id == "geo-measure":
                result = run_geo_measure(request)
            elif capability.id == "seo-plan":
                result = run_seo_plan(request)
            else:
                raise RegistryError("capability {} has no CLI provider".format(capability.id))
            run_dir = publish_run(capability, request, result, args.output)
            print(json.dumps({"status": result["quality_report"]["status"], "run_dir": str(run_dir)}, indent=2))
            return 0
        if args.command == "eval":
            report = run_router_evals()
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["status"] == "pass" else 1
        if args.command == "package":
            archive = package_target(args.target, args.output)
            print(json.dumps(validate_archive(archive, args.target), indent=2))
            return 0
        if args.command == "validate":
            registry.validate()
            validate_all_schemas()
            errors = validate_run(args.run) if args.run else []
            if errors:
                print(json.dumps({"status": "failed", "errors": errors}, indent=2))
                return 1
            print(json.dumps({"status": "pass", "root": str(repository_root()), "run": str(args.run) if args.run else None}, indent=2))
            return 0
    except (OSError, ValueError, RegistryError, PackageError, RuntimeError) as exc:
        print("FAIL: {}".format(exc), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
