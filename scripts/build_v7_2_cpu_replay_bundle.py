from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

FILES = (
    "configs/statistics/claim_policy_v7_2_candidates.yaml",
    "configs/statistics/claim_policy_v7_2_scenarios.yaml",
    "configs/diagnostics/v8_exploratory_development.yaml",
    "configs/statistics/study_c_power_v7_1.yaml",
    "configs/statistics/study_c_claim_hierarchy_v7_2.yaml",
    "results/v7_2/claim_policy/policy_development_manifest.json",
    "results/v7_2/claim_policy/policy_validation_manifest.json",
    "results/v7_2/claim_policy/policy_confirmation_manifest.json",
    "results/v7_2/claim_policy/claim_policy_v7_2_frozen.yaml",
)
DEPENDENCIES = (
    "numpy",
    "pandas",
    "scipy",
    "pydantic",
    "PyYAML",
    "rich",
    "valideval",
)
COMMANDS = (
    "python3 scripts/run_claim_policy_v7_2.py --phase select",
    "python3 scripts/run_claim_policy_v7_2.py --phase confirm",
    "python3 scripts/run_v7_2_stress_studies.py",
    "python3 scripts/run_v8_difficulty_development.py",
    "python3 scripts/run_s1_v7_2_mock_integration.py",
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "replay/v7_2"
    output.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for relative in FILES:
        source = root / relative
        if not source.is_file():
            raise FileNotFoundError(f"replay input missing: {source}")
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(destination)
    lock_lines = []
    for distribution in DEPENDENCIES:
        try:
            version = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            if distribution == "valideval":
                version = "local-editable"
            else:
                raise
        lock_lines.append(f"{distribution}=={version}")
    lock_path = output / "requirements-cpu-v7-2.lock"
    lock_path.write_text("\n".join(lock_lines) + "\n", encoding="utf-8")
    commands_path = output / "COMMANDS.txt"
    commands_path.write_text("\n".join(COMMANDS) + "\n", encoding="utf-8")
    copied.extend([lock_path, commands_path])

    checksums = {
        path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(copied)
    }
    checksums_path = output / "CHECKSUMS.json"
    checksums_path.write_text(
        json.dumps(
            {"schema_version": "valideval.cpu-replay-checksums.v7.2", "files": checksums},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    environment = {
        "schema_version": "valideval.environment-identity.v7.2",
        "source_commit": source_commit,
        "config_hash": hashlib.sha256(
            (output / "configs/statistics/claim_policy_v7_2_candidates.yaml").read_bytes()
        ).hexdigest(),
        "dependency_lock_hash": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "platform_metadata": {
            "python": sys.version,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "seed_manifest_hash": hashlib.sha256(
            (output / "results/v7_2/claim_policy/policy_confirmation_manifest.json").read_bytes()
        ).hexdigest(),
        "normalized_result_hash": json.loads(
            (root / "results/v7_2/v8/development_summary.json").read_text(encoding="utf-8")
        )["normalized_metrics_sha256"],
        "replay_boundary": (
            "Exact replay is required only within this frozen dependency/platform identity. "
            "No identical-hash promise is made across arbitrary NumPy/SciPy versions."
        ),
    }
    (output / "ENVIRONMENT_IDENTITY.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"V7_2_CPU_REPLAY_BUNDLE_READY: {len(checksums)} checked files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
