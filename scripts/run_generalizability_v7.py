from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from valideval.reliability import (
    benchmark_design_curve,
    estimate_variance_components,
    minimum_design,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7 Study-H generalizability analysis.")
    parser.add_argument("--matrix", type=Path, default=Path("cache/mmlu/wide/matrix.csv"))
    parser.add_argument(
        "--families", type=Path, default=Path("configs/models/study_h_family_map_v5.csv")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/v7/reliability/generalizability")
    )
    args = parser.parse_args()
    started = time.perf_counter()
    matrix = pd.read_csv(args.matrix, index_col=0)
    family_frame = pd.read_csv(args.families)
    families = dict(zip(family_frame.model_id, family_frame.model_family, strict=True))
    subjects = {str(item): str(item).split("::", 1)[0] for item in matrix.columns}
    components = estimate_variance_components(matrix, subjects, families)
    curve = benchmark_design_curve(components)
    designs = []
    for outcome in (
        "aggregate_benchmark_score",
        "pairwise_model_comparison",
        "top_k_selection",
        "subject_conditioned_score",
    ):
        for target in (0.80, 0.90, 0.95):
            designs.append(
                minimum_design(curve, outcome=outcome, target=target)
                or {"outcome": outcome, "target": target, "status": "NOT_REACHED_ON_GRID"}
            )
    args.output.mkdir(parents=True, exist_ok=True)
    curve.to_csv(args.output / "benchmark_design_reliability_curves.csv", index=False)
    summary = {
        "status": "GENERALIZABILITY_ANALYSIS_READY",
        "variance_components": components,
        "minimum_designs": designs,
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": (
            "Components are descriptive method-of-moments quantities for an unbalanced, fixed "
            "historical panel and support design sensitivity, not population variance claims."
        ),
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
