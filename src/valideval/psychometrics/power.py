from __future__ import annotations

import math
from itertools import combinations
from typing import Any

import numpy as np

from valideval.schemas import ResponseMatrix


def paired_score_difference_ci(
    model_a: np.ndarray,
    model_b: np.ndarray,
    *,
    n_boot: int = 1000,
    seed: int = 0,
    alpha: float = 0.05,
) -> dict[str, float | int]:
    delta = np.asarray(model_a, dtype=float) - np.asarray(model_b, dtype=float)
    if delta.size == 0:
        return {"estimate": float("nan"), "lower": float("nan"), "upper": float("nan"), "n": 0}
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(max(0, n_boot)):
        sample = rng.choice(delta, size=delta.size, replace=True)
        samples.append(float(np.mean(sample)))
    estimate = float(np.mean(delta))
    if not samples:
        return {"estimate": estimate, "lower": estimate, "upper": estimate, "n": int(delta.size)}
    lower, upper = np.quantile(samples, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {
        "estimate": estimate,
        "lower": float(lower),
        "upper": float(upper),
        "n": int(delta.size),
    }


def standard_error_for_accuracy(score: float, n_items: int) -> float:
    if n_items <= 0:
        return float("nan")
    return math.sqrt(max(score * (1.0 - score), 0.0) / n_items)


def required_item_count(
    *,
    score: float,
    difference_points: float,
    z_alpha: float = 1.96,
    power_z: float = 0.84,
) -> int:
    difference = difference_points / 100.0
    if difference <= 0:
        return 0
    variance = max(score * (1.0 - score), 1e-6)
    return int(math.ceil(((z_alpha + power_z) ** 2) * variance / (difference**2)))


def redundancy_adjusted_effective_n(n_items: int, redundancy_fraction: float) -> float:
    return max(1.0, n_items * (1.0 - min(max(redundancy_fraction, 0.0), 0.95)))


def power_summary(
    matrix: ResponseMatrix,
    *,
    redundancy_fraction: float = 0.0,
    n_boot: int = 500,
    seed: int = 0,
) -> dict[str, Any]:
    frame = matrix.to_dataframe().astype(float)
    n_items = frame.shape[1]
    effective_n = redundancy_adjusted_effective_n(n_items, redundancy_fraction)
    model_scores = frame.mean(axis=1).to_dict()
    average_score = float(np.mean(list(model_scores.values()))) if model_scores else 0.5
    standard_errors = {
        model_id: standard_error_for_accuracy(score, int(effective_n))
        for model_id, score in model_scores.items()
    }
    pairwise = {}
    for index, (left, right) in enumerate(combinations(frame.index, 2)):
        ci = paired_score_difference_ci(
            frame.loc[left].to_numpy(),
            frame.loc[right].to_numpy(),
            n_boot=n_boot,
            seed=seed + index,
        )
        pairwise[f"{left}__vs__{right}"] = ci
    mdd = 1.96 * math.sqrt(2.0 * average_score * (1.0 - average_score) / effective_n)
    return {
        "n_items": n_items,
        "effective_item_count": effective_n,
        "redundancy_fraction": redundancy_fraction,
        "model_standard_errors": standard_errors,
        "paired_score_difference_intervals": pairwise,
        "minimum_detectable_difference": mdd,
        "required_item_count": {
            "1_point": required_item_count(score=average_score, difference_points=1),
            "2_point": required_item_count(score=average_score, difference_points=2),
            "5_point": required_item_count(score=average_score, difference_points=5),
        },
        "do_not_overinterpret_within_points": 100.0 * mdd,
    }
