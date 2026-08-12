from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

from valideval.statistics.study_c_power_v7_1 import study_c_power_redesign


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7.1 primary-estimand Study-C power design.")
    parser.add_argument(
        "--config", type=Path, default=Path("configs/statistics/study_c_power_v7_1.yaml")
    )
    parser.add_argument("--output", type=Path, default=Path("results/v7_1/planning/power"))
    args = parser.parse_args()
    started = time.perf_counter()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    grid, summary = study_c_power_redesign(config)
    summary["runtime_seconds"] = time.perf_counter() - started
    args.output.mkdir(parents=True, exist_ok=True)
    grid.to_csv(args.output / "primary_estimand_power_grid.csv", index=False)
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
