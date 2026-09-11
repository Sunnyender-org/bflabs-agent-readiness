"""Command-line interface for the public readiness registry and Artifact Protocol."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from . import __version__
from .artifacts import publish_run, validate_run
from .evals import run_router_evals
from .geo_round import MeasurementReportError, project_status, render_report, validate_project, write_report
from .orchestrator import run_discover_content, run_discover_diagnose
from .packaging import CAPABILITY_IDS, PackageError, package_target, validate_archive
from .paths import repository_root
from .providers.geo_content import run_geo_content
from .providers.geo_discover import run_geo_discover
from .providers.geo_measure import load_measurement_input, run_geo_measure
from .providers.geo_optimize import run_geo_optimize
from .providers.seo_plan import run_seo_plan
from .registry import CapabilityRegistry, RegistryError
from .remote import scan_public_site
from .router import route
from .schemas import validate_all_schemas, validate_instance
from .business_attribution import analyze as analyze_business_export
from .business_report import render_business_report
from .business_transfer import to_service, from_service


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

    business = commands.add_parser("business", help="Analyze a supplied business export offline")
    business.add_argument("--input", required=True, type=Path)
    business.add_argument("--experiment", type=Path)
    business.add_argument("--as-of")
    business.add_argument("--format", choices=["json", "markdown"], default="markdown")
    business.add_argument("--output", type=Path)

    scan_parser = commands.add_parser("scan")
    scan_parser.add_argument("url")
    scan_parser.add_argument("--endpoint", default=os.environ.get("BFLABS_READINESS_ENDPOINT", "https://readiness.bflabs.cn"))
    scan_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    scan_parser.add_argument("--publish-to-leaderboard", action="store_true")
    scan_parser.add_argument("--timeout", type=float, default=90.0)

    transfer = commands.add_parser("business-transfer", help="Convert a portable export to/from the existing GEO service")
    transfer.add_argument("--direction", choices=["to-service", "from-service"], required=True)
    transfer.add_argument("--input", type=Path, required=True)
    transfer.add_argument("--experiment", type=Path)
    transfer.add_argument("--output", type=Path, required=True)

    package_parser = commands.add_parser("package")
    package_parser.add_argument("--target", required=True, choices=["source", "unified", "skillhub", *CAPABILITY_IDS])
    package_parser.add_argument("--output", type=Path, default=Path("dist"))

    round_parser = commands.add_parser("round")
    round_commands = round_parser.add_subparsers(dest="round_command", required=True)
    round_validate = round_commands.add_parser("validate")
    round_validate.add_argument("--project", required=True, type=Path)
    round_status = round_commands.add_parser("status")
    round_status.add_argument("--project", required=True, type=Path)
    round_status.add_argument("--format", choices=["json", "summary"], default="json")
    round_report = round_commands.add_parser("report")
    round_report.add_argument("--project", required=True, type=Path)
    round_report.add_argument("--measurement-report", type=Path)
    round_report.add_argument("--output", type=Path)
    return parser


def _print_round_status(status: Dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return
    print("current_phase: {}".format(status["current_phase"]))
    print("next_step: {}".format(status["next_step"]))
    print("baseline_present: {}".format(str(status["baseline_present"]).lower()))
    print("last_updated: {}".format(status["last_updated"]))
    counts = status["actions_by_status"]
    print("actions_by_status: {}".format(", ".join("{}={}".format(name, counts[name]) for name in counts)))
    if status["missing_preconditions"]:
        print("missing_preconditions: {}".format("; ".join(status["missing_preconditions"])))
    else:
        print("missing_preconditions: none")


def _run_round_command(args: argparse.Namespace) -> int:
    if args.round_command == "validate":
        errors = validate_project(args.project)
        if errors:
            print(json.dumps({"status": "failed", "errors": errors}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps({"status": "pass"}, ensure_ascii=False, indent=2))
        return 0
    if args.round_command == "status":
        _print_round_status(project_status(args.project), args.format)
        return 0
    if args.round_command == "report":
        errors = validate_project(args.project)
        if errors:
            print(json.dumps({"status": "failed", "errors": errors}, ensure_ascii=False, indent=2))
            return 1
        try:
            if args.output is None:
                path = write_report(args.project, args.measurement_report)
            else:
                measurement = None
                if args.measurement_report is not None:
                    measurement = _load_json(args.measurement_report)
                text = render_report(args.project, measurement)
                if not text.endswith("\n"):
                    text += "\n"
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text, "utf-8")
                path = args.output
        except MeasurementReportError as exc:
            print(json.dumps({"status": "failed", "errors": exc.errors}, ensure_ascii=False, indent=2))
            return 1
        except (OSError, ValueError) as exc:
            print(json.dumps({"status": "failed", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps({"status": "pass", "report": str(path)}, ensure_ascii=False, indent=2))
        return 0
    return 2


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
        if args.command == "scan":
            _content_type, output = scan_public_site(
                args.url,
                args.endpoint,
                output_format=args.format,
                publish_to_leaderboard=args.publish_to_leaderboard,
                timeout=args.timeout,
            )
            print(output.rstrip())
            return 0
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
        if args.command == "round":
            return _run_round_command(args)
        if args.command == "business-transfer":
            value = _load_json(args.input)
            if args.direction == "to-service":
                validate_instance(value, "round-business-events.schema.json")
                experiment = _load_json(args.experiment) if args.experiment else None
                if experiment is not None:
                    validate_instance(experiment, "round-experiment.schema.json")
                output = {"imports": to_service(value, experiment)}
            else:
                output = from_service(value)
                validate_instance(output["business_events"], "round-business-events.schema.json")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", "utf-8")
            return 0
        if args.command == "business":
            document = _load_json(args.input)
            validate_instance(document, "round-business-events.schema.json")
            experiment = _load_json(args.experiment) if args.experiment else None
            if experiment is not None:
                validate_instance(experiment, "round-experiment.schema.json")
            report = analyze_business_export(document, experiment_doc=experiment, as_of=args.as_of)
            output = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_business_report(report)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(output + "\n", "utf-8")
            else:
                print(output)
            return 0
    except (OSError, ValueError, RegistryError, PackageError, RuntimeError) as exc:
        print("FAIL: {}".format(exc), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
