from __future__ import annotations

from typing import Any

from valideval.psychometrics.reliability_stats import kendall_tau, spearman_correlation
from valideval.schemas import ResponseMatrix


def naive_accuracy_ranking(matrix: ResponseMatrix) -> list[dict[str, float | int | str]]:
    scores = matrix.to_dataframe().astype(float).mean(axis=1).sort_values(ascending=False)
    return [
        {"rank": rank, "model_id": model_id, "score": float(score)}
        for rank, (model_id, score) in enumerate(scores.items(), start=1)
    ]


def compare_rankings(
    baseline: list[dict[str, Any]],
    alternative: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_map = {entry["model_id"]: int(entry["rank"]) for entry in baseline}
    alternative_map = {entry["model_id"]: int(entry["rank"]) for entry in alternative}
    shared = [model_id for model_id in baseline_map if model_id in alternative_map]
    baseline_ranks = [baseline_map[model_id] for model_id in shared]
    alternative_ranks = [alternative_map[model_id] for model_id in shared]
    flips = [
        {
            "model_id": model_id,
            "baseline_rank": baseline_map[model_id],
            "alternative_rank": alternative_map[model_id],
            "delta": baseline_map[model_id] - alternative_map[model_id],
        }
        for model_id in shared
        if baseline_map[model_id] != alternative_map[model_id]
    ]
    return {
        "spearman": spearman_correlation(baseline_ranks, alternative_ranks),
        "kendall": kendall_tau(baseline_ranks, alternative_ranks),
        "rank_flips": flips,
    }


def ability_ranking(per_model_metrics: dict[str, Any]) -> list[dict[str, float | int | str]]:
    scores = sorted(
        (
            (model_id, float(metrics["latent_ability_proxy"]))
            for model_id, metrics in per_model_metrics.items()
            if "latent_ability_proxy" in metrics
        ),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return [
        {"rank": rank, "model_id": model_id, "score": score}
        for rank, (model_id, score) in enumerate(scores, start=1)
    ]
