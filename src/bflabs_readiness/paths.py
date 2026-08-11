"""Repository path discovery for source and editable installs."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def repository_root() -> Path:
    override = os.environ.get("BFLABS_READINESS_ROOT")
    if override:
        candidate = Path(override).expanduser().resolve()
        if (candidate / "registry/capabilities.json").is_file():
            return candidate
        raise RuntimeError("BFLABS_READINESS_ROOT does not contain registry/capabilities.json")

    source_root = Path(__file__).resolve().parents[2]
    if (source_root / "registry/capabilities.json").is_file():
        return source_root

    for candidate in [Path.cwd().resolve(), *Path.cwd().resolve().parents]:
        if (candidate / "registry/capabilities.json").is_file():
            return candidate

    installed_root = Path(sys.prefix).resolve() / "share" / "bflabs-agent-readiness"
    if (installed_root / "registry/capabilities.json").is_file():
        return installed_root
    raise RuntimeError("cannot locate the bflabs-agent-readiness repository root")
