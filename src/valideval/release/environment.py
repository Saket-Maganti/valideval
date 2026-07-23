from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

from valideval import __version__
from valideval.forensics.provenance import stable_hash
from valideval.schemas import utc_now

CORE_PACKAGES = ["valideval", "numpy", "pandas", "pydantic", "pyyaml", "rich", "scipy"]


def capture_environment(
    *,
    command: str | None = None,
    config_paths: list[str | Path] | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    configs = _config_hashes(config_paths or [])
    return {
        "schema_version": "0.1",
        "captured_at": utc_now(),
        "valideval_version": __version__,
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
        },
        "os": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "packages": _package_versions(CORE_PACKAGES),
        "git": _git_state(),
        "command": command,
        "config_hashes": configs,
        "config_hash": stable_hash(configs),
        "random_seeds": {"default_seed": seed},
        "environment": {
            "cwd": str(Path.cwd()),
            "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
        },
        "limitations": [
            "Environment capture records local package versions and hashes; it does not recreate external services or missing data."
        ],
    }


def write_environment(
    path: str | Path,
    *,
    command: str | None = None,
    config_paths: list[str | Path] | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    payload = capture_environment(command=command, config_paths=config_paths, seed=seed)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {"environment_json": str(output), "environment": payload}


def _package_versions(names: list[str]) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = __version__ if name == "valideval" else None
    return versions


def _git_state() -> dict[str, Any]:
    commit = _git(["rev-parse", "HEAD"])
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    dirty = _git(["status", "--porcelain"])
    return {
        "commit": commit,
        "branch": branch,
        "is_git_repository": commit is not None,
        "dirty": bool(dirty) if dirty is not None else None,
        "status_unavailable_reason": None if commit is not None else "not a git repository",
    }


def _git(args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _config_hashes(paths: list[str | Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path_like in paths:
        path = Path(path_like)
        if path.exists():
            hashes[str(path)] = stable_hash(path.read_text(encoding="utf-8"))
        else:
            hashes[str(path)] = "missing"
    return hashes
