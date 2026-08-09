from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

import numpy as np
import pandas as pd

ScoreFunction = Callable[[pd.DataFrame], np.ndarray]


def cluster_bootstrap_scores(
    matrix: pd.DataFrame,
    score_function: ScoreFunction,
    *,
    clusters: Sequence[str] | Mapping[str, str] | None = None,
    n_bootstrap: int = 500,
    seed: int = 2027,
) -> np.ndarray:
    """Bootstrap model rows, optionally sampling dependence clusters first."""

    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be positive")
    if matrix.empty:
        raise ValueError("matrix must not be empty")
    labels = _cluster_labels(matrix.index.astype(str), clusters)
    groups = {label: np.flatnonzero(labels == label) for label in sorted(set(labels.tolist()))}
    rng = np.random.default_rng(seed)
    draws = np.empty((n_bootstrap, matrix.shape[1]), dtype=float)
    group_names = np.asarray(list(groups))
    for replicate in range(n_bootstrap):
        if clusters is None:
            indices = rng.choice(matrix.shape[0], size=matrix.shape[0], replace=True)
        else:
            sampled_groups = rng.choice(group_names, size=len(group_names), replace=True)
            sampled: list[int] = []
            for group in sampled_groups:
                members = groups[str(group)]
                sampled.extend(rng.choice(members, size=len(members), replace=True).tolist())
            indices = np.asarray(sampled, dtype=int)
        sampled_frame = matrix.iloc[indices].copy()
        sampled_frame.index = [f"bootstrap_{replicate}_{index}" for index in range(len(indices))]
        draws[replicate] = score_function(sampled_frame)
    return draws


def selection_frequency(
    bootstrap_scores: np.ndarray,
    *,
    threshold: float,
    absolute: bool = False,
) -> np.ndarray:
    values = np.asarray(bootstrap_scores, dtype=float)
    if values.ndim != 2:
        raise ValueError("bootstrap_scores must be bootstrap-by-item")
    selected = np.abs(values) >= threshold if absolute else values >= threshold
    return np.nanmean(selected, axis=0)


def percentile_intervals(
    bootstrap_scores: np.ndarray,
    *,
    confidence_level: float = 0.95,
) -> tuple[np.ndarray, np.ndarray]:
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in (0, 1)")
    values = np.asarray(bootstrap_scores, dtype=float)
    if values.ndim != 2:
        raise ValueError("bootstrap_scores must be bootstrap-by-item")
    alpha = 1.0 - confidence_level
    return (
        np.nanquantile(values, alpha / 2.0, axis=0),
        np.nanquantile(values, 1.0 - alpha / 2.0, axis=0),
    )


def _cluster_labels(
    model_ids: pd.Index,
    clusters: Sequence[str] | Mapping[str, str] | None,
) -> np.ndarray:
    if clusters is None:
        return model_ids.to_numpy(dtype=str)
    if isinstance(clusters, Mapping):
        missing = [model for model in model_ids if model not in clusters]
        if missing:
            raise ValueError(f"cluster mapping is missing {len(missing)} model(s)")
        return np.asarray([str(clusters[model]) for model in model_ids])
    values = np.asarray([str(value) for value in clusters])
    if len(values) != len(model_ids):
        raise ValueError("clusters must have one value per model")
    return values
