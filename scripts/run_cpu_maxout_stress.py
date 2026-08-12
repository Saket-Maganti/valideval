from __future__ import annotations

import argparse
import json

from valideval.statistics.cpu_maxout_stress import run_cpu_maxout_stress_suite


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the final CPU statistical stress suite.")
    parser.add_argument(
        "--confirmation-records",
        default="results/final_cpu_maxout/claim_policy/confirmation_records.csv",
    )
    parser.add_argument(
        "--power-grid", default="results/v7_1/planning/power/primary_estimand_power_grid.csv"
    )
    parser.add_argument("--output")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    args = parser.parse_args()
    output = args.output or (
        "results/final_cpu_maxout/stress_fixture"
        if args.quick
        else "results/final_cpu_maxout/stress"
    )
    payload = run_cpu_maxout_stress_suite(
        confirmation_records_path=args.confirmation_records,
        power_grid_path=args.power_grid,
        output_root=output,
        quick=args.quick,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
