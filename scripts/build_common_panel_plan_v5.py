from __future__ import annotations

import argparse
from pathlib import Path

from valideval.planning.panel_power import (
    PanelPowerConfig,
    parse_numeric_sequence,
    write_common_panel_plan,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a deterministic, non-evidence common-panel power planning table."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/planning/common_panel_power_v5.csv"),
    )
    parser.add_argument("--panel-sizes", default="4,8,12,16,24,28,30,32,36,40")
    parser.add_argument("--target-rank-correlations", default="0.3,0.5,0.7")
    parser.add_argument("--simulations", type=int, default=2_000)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=2027)
    parser.add_argument("--minimum-independent-families", type=int, default=4)
    parser.add_argument("--external-label-positive-count", type=int, default=50)
    parser.add_argument("--external-label-negative-count", type=int, default=150)
    parser.add_argument("--anticipated-external-auc", type=float, default=0.70)
    parser.add_argument("--human-review-sample-size", type=int, default=200)
    parser.add_argument("--anticipated-human-precision", type=float, default=0.50)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = PanelPowerConfig(
        panel_sizes=parse_numeric_sequence(args.panel_sizes, cast=int),
        target_rank_correlations=parse_numeric_sequence(args.target_rank_correlations, cast=float),
        n_simulations=args.simulations,
        alpha=args.alpha,
        seed=args.seed,
        minimum_independent_families=args.minimum_independent_families,
        external_label_positive_count=args.external_label_positive_count,
        external_label_negative_count=args.external_label_negative_count,
        anticipated_external_auc=args.anticipated_external_auc,
        human_review_sample_size=args.human_review_sample_size,
        anticipated_human_precision=args.anticipated_human_precision,
    )
    frame = write_common_panel_plan(args.output, config)
    print(f"Wrote {len(frame)} PLANNED non-evidence scenarios to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
