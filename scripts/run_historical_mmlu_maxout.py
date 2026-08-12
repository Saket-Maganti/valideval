from __future__ import annotations

import argparse
import json

from valideval.statistics.historical_mmlu_maxout import run_historical_mmlu_maxout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run historical MMLU CPU max-out sensitivity.")
    parser.add_argument("--matrix", default="data/replay/v7_2_1/historical_mmlu_matrix.csv")
    parser.add_argument("--families", default="configs/models/study_h_family_map_v5.csv")
    parser.add_argument("--bootstrap", type=int)
    parser.add_argument("--output")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    args = parser.parse_args()
    bootstrap = args.bootstrap or (100 if args.quick else 500)
    output = args.output or (
        "results/final_cpu_maxout/historical_mmlu_fixture"
        if args.quick
        else "results/final_cpu_maxout/historical_mmlu"
    )
    payload = run_historical_mmlu_maxout(
        matrix_path=args.matrix,
        family_path=args.families,
        output_root=output,
        bootstrap_draws=bootstrap,
        quick=args.quick,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
