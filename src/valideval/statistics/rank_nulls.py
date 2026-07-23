from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit, logit


def validate_binary_response_matrix(matrix: pd.DataFrame) -> pd.DataFrame:
    """Validate a model-by-item response matrix without silently coercing bad values."""

    if not isinstance(matrix, pd.DataFrame):
        raise TypeError("matrix must be a pandas DataFrame")
    if matrix.shape[0] < 2 or matrix.shape[1] < 2:
        raise ValueError("matrix must contain at least two models and two items")
    if matrix.index.has_duplicates or matrix.columns.has_duplicates:
        raise ValueError("model and item identifiers must be unique")
    try:
        frame = matrix.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("matrix values must be numeric binary responses or missing") from exc
    finite_values = frame.to_numpy()[~np.isnan(frame.to_numpy())]
    if finite_values.size == 0 or not np.isin(finite_values, [0.0, 1.0]).all():
        raise ValueError("matrix values must be 0, 1, or missing")
    if frame.notna().sum(axis=1).eq(0).any() or frame.notna().sum(axis=0).eq(0).any():
        raise ValueError("models and items with no observed responses are not permitted")
    return frame


def normalize_subject_ids(
    columns: Sequence[Any],
    subject_ids: Sequence[str] | Mapping[Any, str],
) -> pd.Series:
    """Return a complete item-to-subject mapping and fail on omissions."""

    item_ids = list(columns)
    if isinstance(subject_ids, Mapping):
        missing = [item_id for item_id in item_ids if item_id not in subject_ids]
        if missing:
            raise ValueError(f"subject mapping is missing {len(missing)} item(s)")
        values = [subject_ids[item_id] for item_id in item_ids]
    else:
        values = list(subject_ids)
        if len(values) != len(item_ids):
            raise ValueError("subject_ids must have one entry per matrix column")
    if any(value is None or not str(value).strip() for value in values):
        raise ValueError("subject identifiers must be non-empty")
    return pd.Series([str(value) for value in values], index=item_ids, name="subject_id")


def subject_accuracy_matrix(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
) -> pd.DataFrame:
    frame = validate_binary_response_matrix(matrix)
    subjects = normalize_subject_ids(frame.columns, subject_ids)
    scores = {
        subject: frame.loc[:, subjects.index[subjects.eq(subject)]].mean(axis=1, skipna=True)
        for subject in sorted(subjects.unique())
    }
    return pd.DataFrame(scores, index=frame.index)


def subject_rank_ranges(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
) -> pd.Series:
    scores = subject_accuracy_matrix(matrix, subject_ids)
    ranks = scores.rank(axis=0, method="average", ascending=False, na_option="bottom")
    return ranks.max(axis=1) - ranks.min(axis=1)


def additive_probability_matrix(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
    *,
    smoothing: float = 0.5,
) -> pd.DataFrame:
    """Fit the transparent ability-plus-subject-difficulty null in closed form."""

    frame = validate_binary_response_matrix(matrix)
    if smoothing <= 0:
        raise ValueError("smoothing must be positive")
    subjects = normalize_subject_ids(frame.columns, subject_ids)
    observed = frame.notna().astype(float)
    successes = frame.fillna(0.0)
    global_probability = (successes.to_numpy().sum() + smoothing) / (
        observed.to_numpy().sum() + 2.0 * smoothing
    )
    model_probability = (successes.sum(axis=1) + smoothing) / (
        observed.sum(axis=1) + 2.0 * smoothing
    )
    subject_success = pd.Series(
        {
            subject: successes.loc[:, subjects.eq(subject).to_numpy()].to_numpy().sum()
            for subject in subjects.unique()
        }
    )
    subject_observed = pd.Series(
        {
            subject: observed.loc[:, subjects.eq(subject).to_numpy()].to_numpy().sum()
            for subject in subjects.unique()
        }
    )
    subject_probability = (subject_success + smoothing) / (subject_observed + 2.0 * smoothing)
    global_eta = float(logit(np.clip(global_probability, 1e-8, 1.0 - 1e-8)))
    model_eta = logit(model_probability.clip(1e-8, 1.0 - 1e-8))
    subject_eta = logit(subject_probability.clip(1e-8, 1.0 - 1e-8))
    probabilities = pd.DataFrame(index=frame.index, columns=frame.columns, dtype=float)
    for item_id in frame.columns:
        subject = subjects.loc[item_id]
        probabilities[item_id] = expit(model_eta + float(subject_eta.loc[subject]) - global_eta)
    return probabilities.clip(1e-8, 1.0 - 1e-8)


def sample_additive_null(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
    *,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Sample the additive null while preserving the original missingness pattern."""

    frame = validate_binary_response_matrix(matrix)
    probabilities = additive_probability_matrix(frame, subject_ids)
    sampled = rng.binomial(1, probabilities.to_numpy()).astype(float)
    sampled[np.isnan(frame.to_numpy())] = np.nan
    return pd.DataFrame(sampled, index=frame.index, columns=frame.columns)


def model_only_probability_matrix(
    matrix: pd.DataFrame,
    *,
    smoothing: float = 0.5,
) -> pd.DataFrame:
    """Model-ability binomial null that preserves subject/item sample sizes, not effects."""

    frame = validate_binary_response_matrix(matrix)
    if smoothing <= 0:
        raise ValueError("smoothing must be positive")
    observations = frame.notna().sum(axis=1)
    probabilities = (frame.fillna(0.0).sum(axis=1) + smoothing) / (observations + 2.0 * smoothing)
    return pd.DataFrame(
        np.repeat(probabilities.to_numpy()[:, None], frame.shape[1], axis=1),
        index=frame.index,
        columns=frame.columns,
    )


def empirical_bayes_probability_matrix(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
    *,
    prior_strength: float = 20.0,
    smoothing: float = 0.5,
) -> pd.DataFrame:
    """Shrink subject effects toward the global rate before combining with ability."""

    frame = validate_binary_response_matrix(matrix)
    subjects = normalize_subject_ids(frame.columns, subject_ids)
    if prior_strength <= 0 or smoothing <= 0:
        raise ValueError("prior_strength and smoothing must be positive")
    global_probability = float(
        (frame.fillna(0.0).to_numpy().sum() + smoothing)
        / (frame.notna().to_numpy().sum() + 2.0 * smoothing)
    )
    model_probabilities = (frame.fillna(0.0).sum(axis=1) + smoothing) / (
        frame.notna().sum(axis=1) + 2.0 * smoothing
    )
    global_eta = float(logit(np.clip(global_probability, 1e-8, 1.0 - 1e-8)))
    model_eta = logit(model_probabilities.clip(1e-8, 1.0 - 1e-8))
    probabilities = pd.DataFrame(index=frame.index, columns=frame.columns, dtype=float)
    for subject in sorted(subjects.unique()):
        item_ids = subjects.index[subjects.eq(subject)]
        values = frame.loc[:, item_ids]
        observations = int(values.notna().to_numpy().sum())
        successes = float(values.fillna(0.0).to_numpy().sum())
        raw_subject_probability = (successes + smoothing) / (observations + 2.0 * smoothing)
        shrinkage = observations / (observations + prior_strength)
        shrunk_probability = (
            shrinkage * raw_subject_probability + (1.0 - shrinkage) * global_probability
        )
        subject_eta = float(logit(np.clip(shrunk_probability, 1e-8, 1.0 - 1e-8)))
        subject_model_probability = expit(model_eta + subject_eta - global_eta)
        probabilities.loc[:, item_ids] = np.repeat(
            subject_model_probability.to_numpy()[:, None], len(item_ids), axis=1
        )
    return probabilities.clip(1e-8, 1.0 - 1e-8)


def sample_probability_null(
    matrix: pd.DataFrame,
    probabilities: pd.DataFrame,
    *,
    rng: np.random.Generator,
) -> pd.DataFrame:
    frame = validate_binary_response_matrix(matrix)
    if not probabilities.index.equals(frame.index) or not probabilities.columns.equals(
        frame.columns
    ):
        raise ValueError("probability matrix identifiers must exactly match the response matrix")
    values = probabilities.to_numpy(dtype=float)
    if not np.isfinite(values).all() or ((values <= 0.0) | (values >= 1.0)).any():
        raise ValueError("null probabilities must be finite and lie strictly between 0 and 1")
    sampled = rng.binomial(1, values).astype(float)
    sampled[np.isnan(frame.to_numpy())] = np.nan
    return pd.DataFrame(sampled, index=frame.index, columns=frame.columns)


def sample_model_margin_permutation_null(
    matrix: pd.DataFrame,
    *,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Permute each model's observed responses, preserving exact model totals."""

    frame = validate_binary_response_matrix(matrix)
    values = frame.to_numpy(copy=True)
    for row_index in range(values.shape[0]):
        observed_indices = np.flatnonzero(~np.isnan(values[row_index]))
        values[row_index, observed_indices] = rng.permutation(values[row_index, observed_indices])
    return pd.DataFrame(values, index=frame.index, columns=frame.columns)


def simulate_rank_range_null(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
    *,
    method: str = "additive",
    n_simulations: int = 500,
    seed: int = 2027,
    empirical_bayes_prior_strength: float = 20.0,
) -> pd.DataFrame:
    """Simulate null rank dispersion with deterministic seeds and add-one-ready output."""

    frame = validate_binary_response_matrix(matrix)
    subjects = normalize_subject_ids(frame.columns, subject_ids)
    if n_simulations <= 0:
        raise ValueError("n_simulations must be positive")
    allowed_methods = {
        "additive",
        "binomial_subject_size",
        "empirical_bayes_additive",
        "model_margin_permutation",
    }
    if method not in allowed_methods:
        raise ValueError(f"method must be one of {sorted(allowed_methods)}")
    rng = np.random.default_rng(seed)
    additive_probabilities = (
        additive_probability_matrix(frame, subjects.to_dict()) if method == "additive" else None
    )
    model_only_probabilities = (
        model_only_probability_matrix(frame) if method == "binomial_subject_size" else None
    )
    empirical_bayes_probabilities = (
        empirical_bayes_probability_matrix(
            frame,
            subjects.to_dict(),
            prior_strength=empirical_bayes_prior_strength,
        )
        if method == "empirical_bayes_additive"
        else None
    )
    rows: list[dict[str, Any]] = []
    denominator = max(frame.shape[0] - 1, 1)
    subject_indices = [
        np.flatnonzero(subjects.to_numpy() == subject) for subject in sorted(subjects.unique())
    ]
    for simulation in range(n_simulations):
        if method == "additive":
            assert additive_probabilities is not None
            sampled = sample_probability_null(frame, additive_probabilities, rng=rng)
        elif method == "binomial_subject_size":
            assert model_only_probabilities is not None
            sampled = sample_probability_null(frame, model_only_probabilities, rng=rng)
        elif method == "empirical_bayes_additive":
            assert empirical_bayes_probabilities is not None
            sampled = sample_probability_null(frame, empirical_bayes_probabilities, rng=rng)
        else:
            sampled = sample_model_margin_permutation_null(frame, rng=rng)
        sampled_values = sampled.to_numpy(dtype=float)
        with np.errstate(invalid="ignore"):
            scores = np.column_stack(
                [np.nanmean(sampled_values[:, indices], axis=1) for indices in subject_indices]
            )
        ranks = pd.DataFrame(scores, index=frame.index).rank(
            axis=0, method="average", ascending=False, na_option="bottom"
        )
        ranges = ranks.max(axis=1) - ranks.min(axis=1)
        rows.append(
            {
                "simulation": simulation,
                "method": method,
                "median_rank_range": float(ranges.median()),
                "mean_rank_range": float(ranges.mean()),
                "maximum_rank_range": float(ranges.max()),
                "mean_normalized_rank_range": float((ranges / denominator).mean()),
                "evidence_status": "REPRODUCED",
                "simulation_role": "calibration_null_not_observed_benchmark_output",
            }
        )
    return pd.DataFrame(rows)


def compare_observed_rank_ranges_to_null(
    observed_ranges: pd.Series,
    null_simulations: pd.DataFrame,
) -> dict[str, float | int | str]:
    """Compare observed dispersion to a simulated null using add-one p-values."""

    required = {"median_rank_range", "maximum_rank_range"}
    if observed_ranges.empty or not required.issubset(null_simulations.columns):
        raise ValueError("observed ranges and required null columns must be present")
    n = len(null_simulations)
    if n == 0:
        raise ValueError("at least one null simulation is required")
    observed_median = float(observed_ranges.median())
    observed_maximum = float(observed_ranges.max())
    median_exceedances = int((null_simulations["median_rank_range"] >= observed_median).sum())
    maximum_exceedances = int((null_simulations["maximum_rank_range"] >= observed_maximum).sum())
    return {
        "observed_median_rank_range": observed_median,
        "observed_maximum_rank_range": observed_maximum,
        "median_null_exceedance_probability": (median_exceedances + 1) / (n + 1),
        "maximum_null_exceedance_probability": (maximum_exceedances + 1) / (n + 1),
        "n_null_simulations": n,
        "interpretation": "Under this diagnostic and null protocol only.",
    }
