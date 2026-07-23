from __future__ import annotations

from typing import Any

import numpy as np


def resampled_null_distribution(
    clean_scores: list[float],
    *,
    n_samples: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    values = [float(score) for score in clean_scores]
    if not values:
        return {"status": "unavailable", "samples": []}
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=n_samples, replace=True).astype(float).tolist()
    return {
        "status": "measured",
        "n_samples": n_samples,
        "mean": float(np.mean(samples)),
        "p95": float(np.quantile(samples, 0.95)),
        "p99": float(np.quantile(samples, 0.99)),
        "samples": samples,
    }


def score_to_null_percentile(score: float, null_scores: list[float]) -> float | None:
    if not null_scores:
        return None
    return sum(1 for null_score in null_scores if null_score <= score) / len(null_scores)
