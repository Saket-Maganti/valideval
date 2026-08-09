from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def benjamini_hochberg(p_values: Sequence[float]) -> np.ndarray:
    """Return monotone Benjamini-Hochberg adjusted p-values."""

    return _step_up_adjustment(p_values, dependency_factor=1.0)


def benjamini_yekutieli(p_values: Sequence[float]) -> np.ndarray:
    """Return Benjamini-Yekutieli adjusted p-values for arbitrary dependence."""

    count = len(p_values)
    harmonic = float(np.sum(1.0 / np.arange(1, count + 1))) if count else 1.0
    return _step_up_adjustment(p_values, dependency_factor=harmonic)


def _step_up_adjustment(
    p_values: Sequence[float],
    *,
    dependency_factor: float,
) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1:
        raise ValueError("p_values must be one-dimensional")
    if np.any(~np.isfinite(values)) or np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("p_values must be finite and in [0, 1]")
    if not len(values):
        return values.copy()
    order = np.argsort(values)
    ordered = values[order]
    ranks = np.arange(1, len(values) + 1, dtype=float)
    adjusted = ordered * len(values) * dependency_factor / ranks
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    restored = np.empty_like(adjusted)
    restored[order] = np.clip(adjusted, 0.0, 1.0)
    return restored
