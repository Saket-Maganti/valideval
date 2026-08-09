from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import yaml

from valideval.validation.confirmatory_v7 import run_confirmatory_validation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen V7 confirmatory synthetic validation.")
    parser.add_argument(
        "--config", type=Path, default=Path("configs/synthetic/confirmatory_v7.yaml")
    )
    parser.add_argument("--output", type=Path, default=Path("results/v7/synthetic/confirmatory"))
    args = parser.parse_args()
    started = time.perf_counter()
    config_bytes = args.config.read_bytes()
    config = yaml.safe_load(config_bytes)
    freeze_ref = str(config.get("freeze_ref", ""))
    if not freeze_ref:
        raise ValueError("confirmatory config must record the pre-run freeze ref")
    freeze_commit = subprocess.check_output(
        ["git", "rev-parse", f"{freeze_ref}^{{commit}}"], text=True
    ).strip()
    current_blob = subprocess.check_output(["git", "show", f"{freeze_commit}:{args.config}"])
    if current_blob != config_bytes:
        raise ValueError("working confirmatory config differs from the frozen commit")
    results, summary = run_confirmatory_validation(config)
    criteria = config["success_criteria"]
    acceptance = {
        "median_AUPRC": summary["median_AUPRC"] >= float(criteria["median_AUPRC_minimum"]),
        "median_precision_at_k": summary["median_precision_at_k"]
        >= float(criteria["median_precision_at_k_minimum"]),
        "median_FDR": summary["median_FDR"] <= float(criteria["median_FDR_maximum"]),
    }
    summary["acceptance_criteria"] = acceptance
    summary["acceptance_status"] = (
        "FROZEN_ACCEPTANCE_GATES_PASSED"
        if all(acceptance.values())
        else "FROZEN_ACCEPTANCE_GATES_FAILED"
    )
    args.output.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output / "scenario_metrics.csv", index=False)
    summary.update(
        {
            "freeze_commit": freeze_commit,
            "freeze_ref": freeze_ref,
            "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
            "runtime_seconds": time.perf_counter() - started,
        }
    )
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
