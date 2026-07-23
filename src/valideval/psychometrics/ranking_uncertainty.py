from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np

from valideval.schemas import ResponseMatrix


def bootstrap_rank_uncertainty(
    matrix: ResponseMatrix,
    *,
    n_boot: int = 500,
    seed: int = 0,
    top_k: int = 3,
) -> dict[str, Any]:
    frame = matrix.to_dataframe().astype(float)
    rng = np.random.default_rng(seed)
    item_ids = list(frame.columns)
    models = list(frame.index)
    rank_samples: dict[str, list[int]] = {model_id: [] for model_id in models}
    beat_counts = {f"{left}__beats__{right}": 0 for left, right in combinations(models, 2)}
    top_k_sets = []

    for _ in range(n_boot):
        sampled_items = rng.choice(item_ids, size=len(item_ids), replace=True).tolist()
        scores = frame[sampled_items].mean(axis=1).to_dict()
        ranked = _rank(scores)
        top_k_sets.append(set(ranked[:top_k]))
        for rank, model_id in enumerate(ranked, start=1):
            rank_samples[model_id].append(rank)
        for left, right in combinations(models, 2):
            if scores[left] >= scores[right]:
                beat_counts[f"{left}__beats__{right}"] += 1

    full_ranked = _rank(frame.mean(axis=1).to_dict())
    full_top = set(full_ranked[:top_k])
    return {
        "rank_distributions": {
            model_id: {
                "mean_rank": float(np.mean(samples)) if samples else float("nan"),
                "rank_ci": _rank_ci(samples),
                "rank_counts": {str(rank): samples.count(rank) for rank in sorted(set(samples))},
            }
            for model_id, samples in rank_samples.items()
        },
        "probability_model_a_beats_model_b": {
            key: count / n_boot if n_boot else float("nan") for key, count in beat_counts.items()
        },
        "top_k_stability": (
            float(np.mean([len(full_top & top_set) / top_k for top_set in top_k_sets]))
            if top_k_sets and top_k
            else float("nan")
        ),
        "ranking_flip_detector": [
            {
                "model_id": model_id,
                "full_rank": full_ranked.index(model_id) + 1,
                "mean_bootstrap_rank": float(np.mean(rank_samples[model_id])),
            }
            for model_id in models
            if rank_samples[model_id]
            and abs((full_ranked.index(model_id) + 1) - float(np.mean(rank_samples[model_id])))
            >= 1.0
        ],
        "n_boot": n_boot,
    }


def _rank(scores: dict[str, float]) -> list[str]:
    return sorted(scores, key=lambda model_id: (scores[model_id], model_id), reverse=True)


def _rank_ci(samples: list[int]) -> dict[str, float | int]:
    if not samples:
        return {"lower": float("nan"), "upper": float("nan"), "n": 0}
    lower, upper = np.quantile(samples, [0.025, 0.975])
    return {"lower": float(lower), "upper": float(upper), "n": len(samples)}
