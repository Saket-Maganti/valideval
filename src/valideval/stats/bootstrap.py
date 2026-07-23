from __future__ import annotations

from typing import Any

import numpy as np


def bootstrap_mean_ci(values: list[float], *, n_boot: int = 1000, seed: int = 0) -> dict[str, Any]:
    clean = np.array([float(value) for value in values], dtype=float)
    if clean.size == 0:
        return {"estimate": None, "lower": None, "upper": None, "n_boot": 0}
    rng = np.random.default_rng(seed)
    samples = [
        float(np.mean(rng.choice(clean, size=clean.size, replace=True))) for _ in range(n_boot)
    ]
    lower, upper = np.quantile(samples, [0.025, 0.975])
    return {
        "estimate": float(np.mean(clean)),
        "lower": float(lower),
        "upper": float(upper),
        "n_boot": n_boot,
    }
