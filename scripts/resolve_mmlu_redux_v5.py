from __future__ import annotations

import argparse
import json
from pathlib import Path

from valideval.external_labels.mmlu_redux_linkage_v5 import resolve_mmlu_redux_linkage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve MMLU-Redux identity using the fail-closed V5 linkage order."
    )
    parser.add_argument(
        "--redux",
        type=Path,
        default=Path("data/ground_truth/mmlu_redux_issues.normalized.jsonl"),
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=Path("data/external/mmlu/prediction_details_wide.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/mmlu_redux/linkage_v5.csv"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("results/mmlu_redux/linkage_summary_v5.json"),
    )
    parser.add_argument("--fuzzy-threshold", type=float, default=0.9)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = resolve_mmlu_redux_linkage(
        redux_path=args.redux,
        benchmark_path=args.benchmark,
        output_csv=args.output,
        summary_json=args.summary,
        fuzzy_threshold=args.fuzzy_threshold,
    )
    print(json.dumps(summary.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
