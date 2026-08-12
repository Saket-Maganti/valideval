from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from valideval.execution.provenance_v7_2_1 import audit_source_coherence
from valideval.release.machine_state_v7_2_1 import validate_machine_state

REQUIRED_REPORTS = (
    "CPU_MAXOUT_EXECUTIVE_VERDICT.md",
    "CPU_MAXOUT_REPAIR_LEDGER.md",
    "CPU_MAXOUT_CLAIM_POLICY.md",
    "CPU_MAXOUT_FINITE_SAMPLE_CALIBRATION.md",
    "CPU_MAXOUT_RARE_EVENT_SAFETY.md",
    "CPU_MAXOUT_DEPENDENCE.md",
    "CPU_MAXOUT_RANK_INFERENCE.md",
    "CPU_MAXOUT_SELECTIVE_DECISIONS.md",
    "CPU_MAXOUT_NULL_SENSITIVITY.md",
    "CPU_MAXOUT_HISTORICAL_MMLU.md",
    "CPU_MAXOUT_V8_EXPLORATORY.md",
    "CPU_MAXOUT_HUMAN_PLANNING.md",
    "CPU_MAXOUT_POWER_AND_COMPUTE.md",
    "CPU_MAXOUT_ARCHITECTURE_HARDENING.md",
    "CPU_MAXOUT_TESTING_AND_SECURITY.md",
    "CPU_MAXOUT_REPRODUCIBILITY.md",
    "CPU_MAXOUT_KAGGLE_PREP.md",
    "CPU_MAXOUT_ICML_RED_TEAM.md",
    "CPU_MAXOUT_REMAINING_BLOCKERS.md",
)


def validate_cpu_maxout_release(repository_root: str | Path) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    problems: list[str] = []
    coherence = audit_source_coherence(root)
    if coherence["status"] != "RUNBOOK_PROVENANCE_COHERENT":
        problems.extend(coherence["problems"])
    report_root = root / "reports/final_cpu_maxout"
    missing_reports = [name for name in REQUIRED_REPORTS if not (report_root / name).is_file()]
    if missing_reports:
        problems.append(f"missing required reports: {missing_reports}")
    machine_path = root / "VALID_EVAL_FINAL_CPU_MAXOUT_MACHINE_STATE.json"
    if machine_path.exists():
        machine = json.loads(machine_path.read_text(encoding="utf-8"))
        required_machine = {
            "baseline_commit",
            "final_source_commit",
            "final_source_tag",
            "canonical_s1_source_ref",
            "claim_policy_status",
            "s1_status",
            "s2_status",
            "s3_status",
            "s4_status",
            "exact_next_action",
        }
        missing = sorted(required_machine.difference(machine))
        if missing:
            problems.append(f"machine state missing fields: {missing}")
        try:
            validate_machine_state(machine)
        except ValueError as exc:
            problems.append(f"machine state schema validation failed: {exc}")
    else:
        problems.append("final CPU maxout machine state is missing")
    manifest_path = root / "results/final_cpu_maxout/release/report_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for relative, expected in manifest.get("reports", {}).items():
            path = root / relative
            if not path.is_file():
                problems.append(f"manifested report is missing: {relative}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                problems.append(f"manifested report hash mismatch: {relative}")
        source_path = root / str(manifest.get("structured_input", ""))
        if not source_path.is_file():
            problems.append("structured report input is missing")
        elif hashlib.sha256(source_path.read_bytes()).hexdigest() != manifest.get(
            "structured_input_sha256"
        ):
            problems.append("structured report input hash mismatch")
    else:
        problems.append("report manifest is missing")
    replay_path = root / "results/final_cpu_maxout/replay/cpu_replay.json"
    if (
        not replay_path.is_file()
        or json.loads(replay_path.read_text()).get("status") != "CPU_REPLAY_PASS"
    ):
        problems.append("CPU replay is missing or failed")
    for lock in ("requirements-cpu-v7-2-1.lock", "requirements-kaggle-t4x2-v7-2-1.lock"):
        if not (root / lock).is_file():
            problems.append(f"dependency lock is missing: {lock}")
    bundle_manifest_path = root / "results/final_cpu_maxout/release/bundle_manifest.json"
    if bundle_manifest_path.exists():
        bundle_manifest = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
        for relative, contract in bundle_manifest.get("members", {}).items():
            path = root / relative
            if not path.is_file():
                problems.append(f"pre-GPU bundle member is missing: {relative}")
            elif path.stat().st_size != contract.get("size"):
                problems.append(f"pre-GPU bundle member size mismatch: {relative}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != contract.get("sha256"):
                problems.append(f"pre-GPU bundle member hash mismatch: {relative}")
    else:
        problems.append("pre-GPU bundle manifest is missing")
    return {
        "schema_version": "valideval.release-validation.v7.2.1",
        "status": "RELEASE_VALIDATION_PASS" if not problems else "RELEASE_VALIDATION_BLOCKED",
        "source_coherence": coherence,
        "required_reports": len(REQUIRED_REPORTS),
        "missing_reports": missing_reports,
        "problems": problems,
    }
