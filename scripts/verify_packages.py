#!/usr/bin/env python3
"""Build and verify all release-candidate packages in isolated temporary paths."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bflabs_readiness.packaging import CAPABILITY_IDS, package_target, validate_archive  # noqa: E402


def run(command: List[str], *, cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError("command failed: {}\n{}".format(" ".join(command), completed.stderr or completed.stdout))
    return completed


def verify(output: Path) -> dict[str, object]:
    output = output.resolve()
    artifacts = []
    source = package_target("source", output, ROOT)
    artifacts.append(validate_archive(source, "source"))
    unified = package_target("unified", output, ROOT)
    artifacts.append(validate_archive(unified, "unified"))
    for capability_id in CAPABILITY_IDS:
        archive = package_target(capability_id, output, ROOT)
        artifacts.append(validate_archive(archive, capability_id))
        with tempfile.TemporaryDirectory(prefix="bflabs-skill-install-") as skill_temp:
            install_root = Path(skill_temp)
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(install_root)
            skill = (install_root / capability_id / "SKILL.md").read_text("utf-8")
            if not skill.startswith("---\n") or "description:" not in skill:
                raise RuntimeError("{} package entrypoint is unreadable".format(capability_id))

    with tempfile.TemporaryDirectory(prefix="bflabs-install-") as temp:
        environment = Path(temp) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        environment = environment.resolve()
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        cli = environment / ("Scripts/bflabs-readiness.exe" if os.name == "nt" else "bin/bflabs-readiness")
        clean_env = os.environ.copy()
        clean_env.pop("PYTHONPATH", None)
        clean_env.pop("BFLABS_READINESS_ROOT", None)
        run([str(python), "-m", "pip", "install", "--disable-pip-version-check", str(unified)], cwd=Path(temp), env=clean_env)
        list_result = json.loads(run([str(cli), "list", "--status", "active", "--format", "json"], cwd=Path(temp), env=clean_env).stdout)
        if len(list_result["capabilities"]) != 7:
            raise RuntimeError("installed unified package does not expose seven active capabilities")
        run([str(cli), "read", "geo-optimize"], cwd=Path(temp), env=clean_env)
        run([str(cli), "validate"], cwd=Path(temp), env=clean_env)
        eval_report = json.loads(run([str(cli), "eval"], cwd=Path(temp), env=clean_env).stdout)
        if eval_report["status"] != "pass":
            raise RuntimeError("installed router eval failed")

        runs = Path(temp) / "runs"
        run([
            str(cli), "run", "--workflow", "discover-diagnose", "--input",
            str(ROOT / "tests/fixtures/discover-diagnose-input.json"), "--output", str(runs),
        ], cwd=Path(temp), env=clean_env)
        run([
            str(cli), "run", "--workflow", "discover-content", "--input",
            str(ROOT / "tests/fixtures/discover-content-input.json"), "--output", str(runs),
        ], cwd=Path(temp), env=clean_env)
        run_count = len(list(runs.glob("run-*")))
        if run_count != 2:
            raise RuntimeError("installed unified package did not publish both workflow runs")

        source_environment = Path(temp) / "source-venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(source_environment)
        source_environment = source_environment.resolve()
        source_python = source_environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        source_cli = source_environment / ("Scripts/bflabs-readiness.exe" if os.name == "nt" else "bin/bflabs-readiness")
        run([str(source_python), "-m", "pip", "install", "--disable-pip-version-check", str(source)], cwd=Path(temp), env=clean_env)
        run([str(source_cli), "list", "--status", "active", "--format", "json"], cwd=Path(temp), env=clean_env)
        run([str(source_cli), "validate"], cwd=Path(temp), env=clean_env)

    return {
        "schema_version": "1.0.0",
        "status": "pass",
        "artifacts": artifacts,
        "isolated_python_installs": 2,
        "installed_child_skills": len(CAPABILITY_IDS),
        "isolated_workflow_runs": 2,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        print(json.dumps(verify(args.output), indent=2))
        return 0
    with tempfile.TemporaryDirectory(prefix="bflabs-packages-") as temp:
        print(json.dumps(verify(Path(temp)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
