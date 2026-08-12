from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from valideval.human.planning_v7 import annotation_power_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7 human annotation precision planning.")
    parser.add_argument(
        "--output", type=Path, default=Path("results/v7_1/planning/human_annotation_power.csv")
    )
    args = parser.parse_args()
    started = time.perf_counter()
    result = annotation_power_plan()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    runtime = time.perf_counter() - started
    summary = {
        "status": "HUMAN_STUDY_RESOURCE_ACCOUNTING_READY",
        "runtime_seconds": runtime,
        "design_count": len(result),
        "planning_only": True,
    }
    args.output.with_name("human_annotation_power_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{summary['status']}: {runtime:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
