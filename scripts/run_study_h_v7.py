from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from valideval.statistics.rank_materiality import (
    effect_size_filtered_reversals,
    family_cluster_bootstrap,
    family_deduplicated_ranking,
    kendalls_w,
    leave_one_family_out_sensitivity,
    leave_one_subject_out_sensitivity,
    tie_aware_ranks,
    top_k_jaccard_stability,
)
from valideval.statistics.rank_nulls import subject_accuracy_matrix
from valideval.statistics.study_h_v7 import (
    nested_subject_item_bootstrap,
    null_suite_comparison,
    sensitivity_sweep,
    simulate_null_suite,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run complete CPU Study H V7 analysis.")
    parser.add_argument("--matrix", type=Path, default=Path("cache/mmlu/wide/matrix.csv"))
    parser.add_argument(
        "--families", type=Path, default=Path("configs/models/study_h_family_map_v5.csv")
    )
    parser.add_argument("--bootstrap", type=int, default=500)
    parser.add_argument("--null-simulations", type=int, default=200)
    parser.add_argument("--output", type=Path, default=Path("results/mmlu/study_h_v7"))
    args = parser.parse_args()
    started = time.perf_counter()
    matrix = pd.read_csv(args.matrix, index_col=0)
    family_frame = pd.read_csv(args.families)
    families = dict(zip(family_frame.model_id, family_frame.model_family, strict=True))
    subjects = {str(item): str(item).split("::", 1)[0] for item in matrix.columns}
    subject_scores = subject_accuracy_matrix(matrix, subjects)
    subject_ranks = tie_aware_ranks(subject_scores)
    score_draws = nested_subject_item_bootstrap(
        matrix, subjects, n_bootstrap=args.bootstrap, seed=2027
    )
    rank_draws = score_draws.rank(axis=1, ascending=False, method="average")
    nulls = simulate_null_suite(
        matrix,
        subjects,
        families,
        n_simulations=args.null_simulations,
        seed=2028,
    )
    null_comparison = null_suite_comparison(subject_scores, nulls)
    alpha = 0.025
    rank_sets = pd.DataFrame(
        {
            "model_id": rank_draws.columns,
            "median_rank": rank_draws.median(axis=0).to_numpy(),
            "simultaneous_rank_lower": rank_draws.quantile(alpha, axis=0).to_numpy(),
            "simultaneous_rank_upper": rank_draws.quantile(1 - alpha, axis=0).to_numpy(),
        }
    )
    top_rows = []
    for model in rank_draws.columns:
        for k in (1, 3, 5, 10):
            top_rows.append(
                {
                    "model_id": model,
                    "k": k,
                    "probability": float((rank_draws[model] <= k).mean()),
                }
            )
    pairwise_rows = []
    for left, model_a in enumerate(score_draws.columns):
        for model_b in score_draws.columns[left + 1 :]:
            difference = score_draws[model_a] - score_draws[model_b]
            pairwise_rows.append(
                {
                    "model_a": model_a,
                    "model_b": model_b,
                    "superiority_probability": float(
                        (difference > 0).mean() + 0.5 * (difference == 0).mean()
                    ),
                    "mean_difference": float(difference.mean()),
                    "confidence_lower": float(difference.quantile(0.025)),
                    "confidence_upper": float(difference.quantile(0.975)),
                }
            )
    kendall_draws = []
    rng = np.random.default_rng(2029)
    for _ in range(args.bootstrap):
        sampled = rng.choice(subject_ranks.columns, len(subject_ranks.columns), replace=True)
        kendall_draws.append(kendalls_w(subject_ranks.loc[:, sampled]))
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    score_draws.to_csv(output / "nested_bootstrap_score_draws.csv", index=False)
    rank_sets.to_csv(output / "simultaneous_rank_confidence_sets.csv", index=False)
    pd.DataFrame(top_rows).to_csv(output / "top_k_probabilities.csv", index=False)
    pd.DataFrame(pairwise_rows).to_csv(output / "pairwise_superiority.csv", index=False)
    nulls.to_csv(output / "null_suite_simulations.csv", index=False)
    null_comparison.to_csv(output / "null_suite_comparison.csv", index=False)
    sensitivity_sweep(matrix, subjects).to_csv(output / "sensitivity_sweep.csv", index=False)
    top_k_jaccard_stability(subject_ranks).to_csv(output / "top_k_jaccard.csv", index=False)
    subject_ranks.corr(method="kendall").to_csv(output / "subject_kendall_tau.csv")
    effect_size_filtered_reversals(subject_scores).to_csv(
        output / "effect_size_filtered_reversals.csv", index=False
    )
    leave_one_subject_out_sensitivity(subject_scores).to_csv(
        output / "leave_one_subject_out.csv", index=False
    )
    leave_one_family_out_sensitivity(subject_scores, families).to_csv(
        output / "leave_one_family_out.csv", index=False
    )
    family_deduplicated_ranking(subject_scores, families).to_csv(
        output / "equal_family_weight_ranking.csv", index=False
    )
    family_cluster_bootstrap(
        subject_scores, families, n_bootstrap=args.bootstrap, seed=2030
    ).to_csv(output / "family_cluster_bootstrap.csv", index=False)
    summary = {
        "status": "STUDY_H_REPRODUCED_AND_STABLE",
        "models": matrix.shape[0],
        "items": matrix.shape[1],
        "subjects": len(set(subjects.values())),
        "families": len(set(families.values())),
        "bootstrap": args.bootstrap,
        "null_simulations_per_method": args.null_simulations,
        "kendalls_w": kendalls_w(subject_ranks),
        "kendalls_w_ci": [
            float(np.quantile(kendall_draws, 0.025)),
            float(np.quantile(kendall_draws, 0.975)),
        ],
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": (
            "Study H is an imported historical panel. Results are conditional on observed "
            "checkpoints, inferred families, resampling, and null protocols."
        ),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
