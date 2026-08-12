from __future__ import annotations

import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from valideval import __version__
from valideval.execution.config import load_run_config
from valideval.execution.config_v7_2 import V7_2_CANONICAL_SOURCE_REF
from valideval.execution.models import load_panel_config
from valideval.execution.provenance_v7_2_1 import audit_source_coherence


def run_cpu_maxout_doctor(
    repository_root: str | Path,
    *,
    output_root: str | Path = "kaggle_icml2027_outputs",
    require_gpu: bool = False,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    checks: list[dict[str, Any]] = []

    def add(name: str, status: str, details: Any) -> None:
        checks.append({"name": name, "status": status, "details": details})

    add(
        "python",
        "PASS" if sys.version_info >= (3, 10) else "BLOCK",
        {"version": sys.version.split()[0], "minimum": "3.10"},
    )
    dependency_versions: dict[str, str] = {}
    missing: list[str] = []
    for package in ("numpy", "pandas", "pydantic", "PyYAML", "scipy"):
        try:
            dependency_versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            missing.append(package)
    add(
        "dependencies",
        "PASS" if not missing else "BLOCK",
        {"versions": dependency_versions, "missing": missing},
    )
    coherence = audit_source_coherence(root)
    add(
        "source_coherence",
        "PASS" if coherence["status"] == "RUNBOOK_PROVENANCE_COHERENT" else "BLOCK",
        coherence,
    )
    config_problems: list[str] = []
    for path in sorted((root / "configs/runs_v7_2").glob("*.yaml")):
        try:
            load_run_config(path, repository_root=root)
        except Exception as exc:  # pragma: no cover - details are returned to CLI.
            config_problems.append(f"{path.name}: {exc}")
    add("s1_configs", "PASS" if not config_problems else "BLOCK", config_problems)
    panel = load_panel_config(root / "configs/panels/s1_smoke_exact_v6.yaml")
    model_bytes = sum(int(model["expected_download_size"]) for model in panel["models"])
    minimum_disk_bytes = model_bytes + 7 * 1024**3
    disk = shutil.disk_usage(root)
    add(
        "disk",
        "PASS" if disk.free >= minimum_disk_bytes else "BLOCK",
        {
            "free_bytes": disk.free,
            "minimum_bytes": minimum_disk_bytes,
            "expected_model_cache_bytes": model_bytes,
        },
    )
    output = Path(output_root)
    parent = (root / output).parent if not output.is_absolute() else output.parent
    add(
        "writable_output",
        "PASS" if parent.exists() and parent.is_dir() and os.access(parent, os.W_OK) else "WARN",
        {"path": str(parent), "exists": parent.exists(), "writable": os.access(parent, os.W_OK)},
    )
    add("package_version", "PASS", {"valideval": __version__})
    try:
        tag_commit = subprocess.run(
            ["git", "rev-parse", f"{V7_2_CANONICAL_SOURCE_REF}^{{commit}}"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
        add(
            "git_tag",
            "PASS" if head == tag_commit else "WARN",
            {"source_ref": V7_2_CANONICAL_SOURCE_REF, "tag_commit": tag_commit, "head": head},
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        add(
            "git_tag",
            "WARN",
            {"source_ref": V7_2_CANONICAL_SOURCE_REF, "reason": "tag not created yet"},
        )
    if require_gpu:
        try:
            import torch

            names = [
                torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())
            ]
            gpu_status = (
                "PASS" if len(names) == 2 and all("T4" in name for name in names) else "BLOCK"
            )
            add("gpu", gpu_status, {"count": len(names), "names": names})
        except ImportError:
            add("gpu", "BLOCK", {"reason": "torch is unavailable"})
    blocking = [check for check in checks if check["status"] == "BLOCK"]
    warnings = [check for check in checks if check["status"] == "WARN"]
    status = "BLOCK" if blocking else ("WARN" if warnings else "PASS")
    return {
        "schema_version": "valideval.doctor.v7.2.1",
        "status": status,
        "checks": checks,
        "gpu_requested": require_gpu,
        "claim_boundary": "Doctor validates execution prerequisites, not scientific evidence.",
    }


def doctor_json(repository_root: str | Path, *, require_gpu: bool = False) -> str:
    return json.dumps(
        run_cpu_maxout_doctor(repository_root, require_gpu=require_gpu),
        indent=2,
        sort_keys=True,
    )
