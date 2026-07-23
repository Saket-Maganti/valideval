from __future__ import annotations

from typing import Any

from valideval.validation.null_models import resampled_null_distribution


def empirical_null(values: list[float], *, n_samples: int = 1000, seed: int = 0) -> dict[str, Any]:
    return resampled_null_distribution(values, n_samples=n_samples, seed=seed)
