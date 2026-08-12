from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

from valideval.statistics.panel_power_v7 import panel_power_grid


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen V7 Study C panel power planning.")
    parser.add_argument(
        "--config", type=Path, default=Path("configs/statistics/panel_power_v7.yaml")
    )
    parser.add_argument("--output", type=Path, default=Path("results/v7/planning/panel_power"))
    args = parser.parse_args()
    started = time.perf_counter()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    grid = panel_power_grid(config)
    args.output.mkdir(parents=True, exist_ok=True)
    grid.to_csv(args.output / "power_grid.csv", index=False)
    material = grid[grid["pairwise_difference"] == float(config["materiality_threshold"])]
    summary = {
        "status": "PANEL_POWER_PLANNING_COMPLETE",
        "primary_estimand": config["primary_estimand"],
        "materiality_threshold": config["materiality_threshold"],
        "s2_materiality_power_range": [
            float(material[material["stage"] == "S2"]["power"].min()),
            float(material[material["stage"] == "S2"]["power"].max()),
        ],
        "s3_materiality_power_range": [
            float(material[material["stage"] == "S3"]["power"].min()),
            float(material[material["stage"] == "S3"]["power"].max()),
        ],
        "s4_materiality_power_range": [
            float(material[material["stage"] == "S4"]["power"].min()),
            float(material[material["stage"] == "S4"]["power"].max()),
        ],
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": config["claim_boundary"],
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
