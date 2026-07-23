from __future__ import annotations

import math

import numpy as np


def cohens_d(left: list[float], right: list[float]) -> float | None:
    x = np.array([float(value) for value in left], dtype=float)
    y = np.array([float(value) for value in right], dtype=float)
    if x.size < 2 or y.size < 2:
        return None
    pooled = math.sqrt(
        ((x.size - 1) * float(np.var(x, ddof=1)) + (y.size - 1) * float(np.var(y, ddof=1)))
        / (x.size + y.size - 2)
    )
    if pooled == 0:
        return 0.0
    return float((np.mean(x) - np.mean(y)) / pooled)


def risk_ratio(event_rate: float, baseline_rate: float) -> float | None:
    if baseline_rate <= 0:
        return None
    return float(event_rate) / float(baseline_rate)
