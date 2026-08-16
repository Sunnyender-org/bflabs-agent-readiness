"""Atomic Artifact Protocol 1.0 publication and verification."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .registry import Capability
from .schemas import validate_instance


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_json(root: Path, relative: str, value: Any) -> str:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    body = _json_bytes(value)
    path.write_bytes(body)
    return _sha256_bytes(body)


def _write_text(root: Path, relative: str, value: str) -> str:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    body = value.encode("utf-8")
    path.write_bytes(body)
    return _sha256_bytes(body)


def publish_run(
    capability: Capability,
    request: Dict[str, Any],
    provider_result: Dict[str, Any],
    output_root: Path,
    workflow_id: Optional[str] = None,
    input_schema_name: Optional[str] = None,
) -> Path:
    quality = provider_result["quality_report"]
    if quality["status"] not in {"pass", "pass_with_warnings"}:
        raise ValueError("quality gate blocked publication: {}".format(quality["blockers"]))

    now = datetime.now(timezone.utc)
    run_id = "run-{}-{}".format(now.strftime("%Y%m%dT%H%M%SZ"), uuid.uuid4().hex[:8])
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    temporary = output_root / (".tmp-" + run_id)
    final = output_root / run_id
    if temporary.exists() or final.exists():
        raise FileExistsError("run path already exists")
    temporary.mkdir()

    schemas: Dict[str, Optional[str]] = {
        "input/request.json": input_schema_name or (capability.input_schema.split("/")[-1] if capability.input_schema else None),
        "evidence-ledger.json": "evidence-ledger.schema.json",
        "quality-report.json": "quality-report.schema.json",
    }
    values: Dict[str, Any] = {
        "input/request.json": request,
        "evidence-ledger.json": provider_result["evidence_ledger"],
        "quality-report.json": quality,
    }
    media_types: Dict[str, str] = {relative: "application/json" for relative in values}
    for relative, pair in provider_result["outputs"].items():
        if len(pair) == 2:
            value, schema_name = pair
            media_type = "application/json"
        else:
            value, schema_name, media_type = pair
        values[relative] = value
        schemas[relative] = schema_name
        media_types[relative] = media_type

    try:
        artifacts: List[Dict[str, Any]] = []
        for relative in sorted(values):
            schema_name = schemas[relative]
            media_type = media_types[relative]
            if schema_name:
                validate_instance(values[relative], schema_name)
            if media_type == "application/json":
                digest = _write_json(temporary, relative, values[relative])
            elif media_type.startswith("text/") and isinstance(values[relative], str):
                digest = _write_text(temporary, relative, values[relative])
            else:
                raise ValueError("unsupported artifact media type: {}".format(media_type))
            artifacts.append(
                {
                    "path": relative,
                    "sha256": digest,
                    "media_type": media_type,
                    "schema": schema_name,
                }
            )

        input_hash = "sha256:" + _sha256_bytes(_json_bytes(request))
        manifest = {
            "protocol_version": "1.0.0",
            "run_id": run_id,
            "capability": capability.id,
            "capability_version": capability.version,
            "workflow_id": workflow_id,
            "created_at": now.isoformat().replace("+00:00", "Z"),
            "input_hash": input_hash,
            "status": quality["status"],
            "degradation": None,
            "external_gates": capability.external_gates,
            "artifacts": artifacts,
            "replay_command": (
                "bflabs-readiness run --workflow {} --input input/request.json --output runs".format(workflow_id)
                if workflow_id
                else "bflabs-readiness run --capability {} --input input/request.json --output runs".format(capability.id)
            ),
        }
        validate_instance(manifest, "run-manifest.schema.json")
        _write_json(temporary, "run-manifest.json", manifest)
        os.replace(str(temporary), str(final))
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return final


def validate_run(run_dir: Path) -> List[str]:
    run_dir = run_dir.resolve()
    errors: List[str] = []
    manifest_path = run_dir / "run-manifest.json"
    if not manifest_path.is_file():
        return ["missing run-manifest.json"]
    try:
        manifest = json.loads(manifest_path.read_text("utf-8"))
        validate_instance(manifest, "run-manifest.schema.json")
    except Exception as exc:
        return ["invalid manifest: {}".format(exc)]

    for artifact in manifest["artifacts"]:
        path = (run_dir / artifact["path"]).resolve()
        if run_dir not in path.parents:
            errors.append("artifact escapes run directory: {}".format(artifact["path"]))
            continue
        if not path.is_file():
            errors.append("missing artifact: {}".format(artifact["path"]))
            continue
        body = path.read_bytes()
        if _sha256_bytes(body) != artifact["sha256"]:
            errors.append("hash mismatch: {}".format(artifact["path"]))
            continue
        if artifact["schema"]:
            try:
                if artifact["media_type"] != "application/json":
                    raise ValueError("schema-bound artifact must be application/json")
                validate_instance(json.loads(body), artifact["schema"])
            except Exception as exc:
                errors.append("schema failure {}: {}".format(artifact["path"], exc))
    input_artifact = next((artifact for artifact in manifest["artifacts"] if artifact["path"] == "input/request.json"), None)
    if input_artifact is None:
        errors.append("manifest does not include input/request.json")
    elif manifest["input_hash"] != "sha256:" + input_artifact["sha256"]:
        errors.append("input_hash does not match input/request.json")
    return errors
