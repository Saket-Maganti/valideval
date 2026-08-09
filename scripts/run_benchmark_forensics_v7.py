from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from valideval.forensics.benchmark_v7 import analyze_mcq_answer_positions


def main() -> int:
    parser = argparse.ArgumentParser(description="Run cached MMLU position forensics.")
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path("data/external/mmlu/prediction_details_wide.jsonl"),
    )
    parser.add_argument("--output", type=Path, default=Path("results/v7/forensics/mmlu_v7.json"))
    args = parser.parse_args()
    started = time.perf_counter()
    result = analyze_mcq_answer_positions(args.predictions)
    result["runtime_seconds"] = time.perf_counter() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"BENCHMARK_FORENSICS_READY: {result['runtime_seconds']:.2f}s")
    return 0 if result["status"] == "REPRODUCED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
