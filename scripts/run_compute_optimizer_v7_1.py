from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from valideval.planning.compute_optimizer_v7_1 import optimize_study_c_compute


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the post-S2 Study-C compute optimizer.")
    parser.add_argument("--s2-measurements", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/v7_1/planning/study_c_compute_optimizer.json"),
    )
    args = parser.parse_args()
    started = time.perf_counter()
    throughput = None
    if args.s2_measurements is not None:
        payload = json.loads(args.s2_measurements.read_text(encoding="utf-8"))
        throughput = float(payload["accepted_examples_per_second"])
    candidates = [
        {
            "design_id": "s2_recalibrated_minimum",
            "model_count": models,
            "family_count": families,
            "item_count": items,
            "benchmark_count": 3,
            "power": power,
        }
        for models, families in ((8, 7), (11, 9), (13, 11))
        for items, power in ((200, 0.50), (1319, 0.80), (6507, 0.90))
    ]
    result = optimize_study_c_compute(
        candidates,
        measured_examples_per_second=throughput,
    )
    result["runtime_seconds"] = time.perf_counter() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
