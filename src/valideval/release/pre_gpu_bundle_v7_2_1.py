from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Any

from valideval.execution.manifest import atomic_write_json, sha256_file


def build_pre_gpu_bundle(
    repository_root: str | Path,
    *,
    output: str | Path = "dist/valideval-v7.2.1-pre-gpu-cpu-maxout.zip",
) -> dict[str, Any]:
    """Build a deterministic handoff bundle with the registered replay fixture."""

    root = Path(repository_root).resolve()
    fixed = [
        "VALID_EVAL_FINAL_CPU_MAXOUT_MACHINE_STATE.json",
        "VALID_EVAL_FINAL_CPU_MAXOUT_HANDOFF.md",
        "VALID_EVAL_ICML2027_CANONICAL_EXECUTION_HANDBOOK.md",
        "VALID_EVAL_V7_2_KAGGLE_S1_RUNBOOK.md",
        "VALID_EVAL_V7_2_1_FAILURE_RECOVERY_RUNBOOK.md",
        "VALID_EVAL_V7_2_1_S2_DRAFT_RUNBOOK.md",
        "VALID_EVAL_V7_2_1_S3_PROPOSAL_CONTRACT.md",
        "VALID_EVAL_V7_2_1_S4_OPTIONAL_TEMPLATE.md",
        "requirements-cpu-v7-2-1.lock",
        "requirements-kaggle-t4x2-v7-2-1.lock",
        "data/replay/v7_2_1/historical_mmlu_matrix.csv",
        "configs/statistics/claim_policy_v7_2_1.yaml",
        "results/final_cpu_maxout/replay/cpu_replay.json",
        "results/final_cpu_maxout/release/report_inputs.json",
        "results/final_cpu_maxout/release/report_manifest.json",
        "results/v7_1/study_h/summary.json",
        "results/v7_1/planning/power/summary.json",
        "results/v7_1/planning/power/primary_estimand_power_grid.csv",
        "results/claims/claim_registry.json",
        "results/methods/method_contracts.json",
        "results/experiments/experiment_registry.json",
    ]
    patterns = (
        "configs/release/*v7_2_1*",
        "configs/runs_v7_2/*.yaml",
        "kaggle_icml2027/*.ipynb",
        "reports/final_cpu_maxout/*.md",
    )
    members = {relative for relative in fixed if (root / relative).is_file()}
    for pattern in patterns:
        members.update(
            path.relative_to(root).as_posix() for path in root.glob(pattern) if path.is_file()
        )
    missing = sorted(set(fixed).difference(members))
    if missing:
        raise ValueError(f"pre-GPU bundle inputs are missing: {missing}")
    manifest = {
        "schema_version": "valideval.pre-gpu-bundle.v7.2.1",
        "members": {
            relative: {
                "size": (root / relative).stat().st_size,
                "sha256": sha256_file(root / relative),
            }
            for relative in sorted(members)
        },
        "exclusions": ["mutable caches", "virtual environments", "model weights", "secrets"],
    }
    manifest_path = root / "results/final_cpu_maxout/release/bundle_manifest.json"
    atomic_write_json(manifest_path, manifest)
    members.add(manifest_path.relative_to(root).as_posix())
    destination = Path(output)
    if not destination.is_absolute():
        destination = root / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            for relative in sorted(members):
                info = zipfile.ZipInfo(relative, date_time=(2000, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, (root / relative).read_bytes())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "status": "PRE_GPU_BUNDLE_BUILT",
        "path": str(destination),
        "sha256": sha256_file(destination),
        "member_count": len(members),
        "manifest": str(manifest_path),
    }
