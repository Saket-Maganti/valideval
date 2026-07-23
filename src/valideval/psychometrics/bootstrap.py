from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np


def bootstrap_ci(
    values: Sequence[float],
    statistic_fn: Callable[[np.ndarray], float] = np.mean,
    n_boot: int = 1000,
    seed: int = 0,
    alpha: float = 0.05,
) -> dict[str, float | int]:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return {"estimate": float("nan"), "lower": float("nan"), "upper": float("nan"), "n": 0}
    estimate = float(statistic_fn(array))
    if array.size == 1 or n_boot <= 0:
        return {"estimate": estimate, "lower": estimate, "upper": estimate, "n": int(array.size)}

    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(n_boot):
        sample = rng.choice(array, size=array.size, replace=True)
        boot.append(float(statistic_fn(sample)))
    lower, upper = np.quantile(boot, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {
        "estimate": estimate,
        "lower": float(lower),
        "upper": float(upper),
        "n": int(array.size),
    }
