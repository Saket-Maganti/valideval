from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

from valideval.validation.synthetic_controls_v7_1 import run_synthetic_control_completion


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the separate V7.1 synthetic control suite.")
    parser.add_argument(
        "--config", type=Path, default=Path("configs/synthetic/control_completion_v7_1.yaml")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/v7_1/synthetic/control_completion")
    )
    args = parser.parse_args()
    started = time.perf_counter()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    results, summary = run_synthetic_control_completion(config)
    summary["runtime_seconds"] = time.perf_counter() - started
    args.output.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output / "control_metrics.csv", index=False)
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0 if summary["status"].endswith("COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
