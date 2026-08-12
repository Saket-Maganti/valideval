from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np

from valideval.schemas import ResponseMatrix


def ranking_significance(
    matrix: ResponseMatrix,
    *,
    n_boot: int = 500,
    seed: int = 0,
    top_k: int = 3,
) -> dict[str, Any]:
    frame = matrix.to_dataframe().astype(float)
    rng = np.random.default_rng(seed)
    item_ids = list(frame.columns)
    if not item_ids:
        return {
            "paired_bootstrap_differences": [],
            "rank_distributions": {},
            "top_k_stability": None,
            "do_not_overinterpret_within_points": None,
            "warnings": ["No items were available for ranking significance."],
        }

    pairwise = []
    rank_counts: dict[str, dict[int, int]] = {
        model_id: {rank: 0 for rank in range(1, len(frame.index) + 1)} for model_id in frame.index
    }
    top_k_matches = []
    full_ranking = _rank_scores(frame.mean(axis=1).to_dict())
    full_top_k = set(full_ranking[: min(top_k, len(full_ranking))])
    pair_samples: dict[tuple[str, str], list[float]] = {
        (left, right): [] for left, right in combinations(frame.index, 2)
    }

    for _ in range(n_boot):
        sampled = rng.choice(item_ids, size=len(item_ids), replace=True).tolist()
        scores = frame[sampled].mean(axis=1).to_dict()
        ranked = _rank_scores(scores)
        for rank, model_id in enumerate(ranked, start=1):
            rank_counts[model_id][rank] += 1
        top_k_matches.append(
            len(set(ranked[: len(full_top_k)]) & full_top_k) / max(len(full_top_k), 1)
        )
        for left, right in pair_samples:
            pair_samples[(left, right)].append(float(scores[left] - scores[right]))

    for (left, right), values in pair_samples.items():
        array = np.asarray(values, dtype=float)
        pairwise.append(
            {
                "model_a": left,
                "model_b": right,
                "mean_difference": float(np.mean(array)),
                "ci_lower": float(np.quantile(array, 0.025)),
                "ci_upper": float(np.quantile(array, 0.975)),
                "probability_a_beats_b": float(np.mean(array > 0)),
            }
        )

    standard_errors = []
    for model_id in frame.index:
        score = float(frame.loc[model_id].mean())
        standard_errors.append(np.sqrt(max(score * (1.0 - score), 0.0) / max(len(item_ids), 1)))
    do_not_overinterpret = (
        float(1.96 * np.mean(standard_errors) * 100.0) if standard_errors else None
    )

    return {
        "paired_bootstrap_differences": sorted(
            pairwise,
            key=lambda row: (row["model_a"], row["model_b"]),
        ),
        "rank_distributions": {
            model_id: {str(rank): count / n_boot for rank, count in ranks.items()}
            for model_id, ranks in rank_counts.items()
        },
        "top_k_stability": float(np.mean(top_k_matches)) if top_k_matches else None,
        "do_not_overinterpret_within_points": do_not_overinterpret,
        "assumptions": [
            "Bootstrap resamples benchmark items with replacement.",
            "Intervals are conditional on the cached response matrix and audited model panel.",
            "This does not produce a true or corrected ranking.",
        ],
    }


def _rank_scores(scores: dict[str, float]) -> list[str]:
    return sorted(scores, key=lambda model_id: (scores[model_id], model_id), reverse=True)
