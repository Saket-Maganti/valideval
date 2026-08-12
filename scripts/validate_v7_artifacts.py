from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from valideval.execution.config import load_run_config

FORBIDDEN_LICENSE_STATES = {"LICENSED", "SUPPORTED", "TRANSFER_SUPPORTED", "REPAIR_SUPPORTED"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail closed on stale or contradictory V7 artifacts."
    )
    parser.add_argument("--write-checksums", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run_configs = sorted((root / "configs/runs_v7").glob("*.yaml"))
    if not run_configs:
        raise SystemExit("no V7 run configs")
    for path in run_configs:
        load_run_config(path, repository_root=root)

    ledger_path = root / "results/v7/evidence/claim_evidence_ledger_v7.csv"
    ledger = pd.read_csv(ledger_path)
    required = {"claim_id", "claim", "status", "evidence", "scope", "blocked_by"}
    if not required.issubset(ledger.columns) or ledger["claim_id"].duplicated().any():
        raise SystemExit("V7 evidence ledger is malformed")
    synthetic = json.loads(
        (root / "results/v7/synthetic/confirmatory/summary.json").read_text(encoding="utf-8")
    )
    if synthetic["acceptance_status"] != "FROZEN_ACCEPTANCE_GATES_FAILED":
        raise SystemExit("unexpected synthetic acceptance state; update policy explicitly")
    blocked_claims = ledger[ledger["claim_id"].isin(["V7-C04", "V7-C06", "V7-C07", "V7-C08"])]
    if any(status in FORBIDDEN_LICENSE_STATES for status in blocked_claims["status"]):
        raise SystemExit("unsupported claim is represented as licensed")

    result_targets = [
        path
        for pattern in ("*.json", "*.csv")
        for path in (root / "results/v7").rglob(pattern)
        if path.name != "artifact_checksums.json"
    ]
    checksum_targets = {
        *run_configs,
        root / "configs/preregistration/icml2027_primary_v7.yaml",
        root / "configs/synthetic/confirmatory_v7.yaml",
        *sorted((root / "configs/panels").glob("*_v7.yaml")),
        *sorted((root / "configs/benchmarks").glob("*_v7.yaml")),
        *sorted((root / "results/freeze/study_c_v7").glob("*.json")),
        *sorted((root / "kaggle_v7").glob("*.ipynb")),
        *result_targets,
        *sorted((root / "reports/v7").glob("*.md")),
        root / "VALID_EVAL_ICML2027_EXECUTION_PLAN.md",
        root / "VALID_EVAL_V7_FINAL_MAXIMUM_PRE_EXECUTION_HANDOFF.md",
        root / "VALID_EVAL_V7_MACHINE_STATE.json",
        root / "requirements-cpu-v7.txt",
        root / "requirements-kaggle-t4x2-v7.txt",
    }
    checksums = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(checksum_targets)
        if path.is_file()
    }
    manifest_path = root / "results/v7/evidence/artifact_checksums.json"
    payload = {"schema_version": "7.0", "files": checksums}
    if args.write_checksums:
        manifest_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    else:
        observed = json.loads(manifest_path.read_text(encoding="utf-8"))
        if observed != payload:
            raise SystemExit("V7 artifact checksum manifest is stale")
    print(f"V7_ARTIFACTS_VALID: {len(run_configs)} run configs, {len(checksums)} checksums")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
