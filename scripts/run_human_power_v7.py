from __future__ import annotations

import argparse
import time
from pathlib import Path

from valideval.human.planning_v7 import annotation_power_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7 human annotation precision planning.")
    parser.add_argument(
        "--output", type=Path, default=Path("results/planning/human_annotation_power_v7.csv")
    )
    args = parser.parse_args()
    started = time.perf_counter()
    result = annotation_power_plan()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"HUMAN_CONFIRMATORY_PROTOCOL_READY: {time.perf_counter() - started:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
