from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from valideval.statistics.claim_calibration_v7_1 import run_claim_policy_calibration


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V7.1 claim-policy calibration study.")
    parser.add_argument("--simulations", type=int, default=200)
    parser.add_argument("--output", type=Path, default=Path("results/v7_1/claim_calibration"))
    args = parser.parse_args()
    started = time.perf_counter()
    calibration, decisions, summary = run_claim_policy_calibration(simulations=args.simulations)
    summary["runtime_seconds"] = time.perf_counter() - started
    args.output.mkdir(parents=True, exist_ok=True)
    calibration.to_csv(args.output / "claim_policy_operating_characteristics.csv", index=False)
    decisions.to_csv(args.output / "selective_decision_guarantee_study.csv", index=False)
    family_stress = (
        calibration.groupby(["method", "family_dependence", "effective_n"], as_index=False)
        .agg(
            false_license_rate=("false_license_rate", "mean"),
            power=("power", "mean"),
            coverage=("coverage", "mean"),
        )
        .sort_values(["method", "family_dependence", "effective_n"])
    )
    family_stress.to_csv(args.output / "family_dependence_stress.csv", index=False)
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
