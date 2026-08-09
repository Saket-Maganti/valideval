from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from valideval.diagnostics.multiplicity import benjamini_hochberg, benjamini_yekutieli
from valideval.diagnostics.stability import (
    cluster_bootstrap_scores,
    percentile_intervals,
    selection_frequency,
)
from valideval.statistics.rank_nulls import validate_binary_response_matrix

REQUIRED_INFERENTIAL_FIELDS = (
    "diagnostic_score",
    "standard_error",
    "confidence_lower",
    "confidence_upper",
    "null_p_value",
    "FDR_q_value",
    "BY_q_value",
    "bootstrap_stability",
    "effect_size",
    "subject",
    "difficulty",
    "claim_status",
)


def item_discrimination_scores(matrix: pd.DataFrame) -> np.ndarray:
    """Leave-one-item corrected response/ability correlation for each item."""

    frame = validate_binary_response_matrix(matrix)
    values = frame.to_numpy(dtype=float)
    observed = np.isfinite(values)
    filled = np.nan_to_num(values, nan=0.0)
    row_sum = filled.sum(axis=1)
    row_count = observed.sum(axis=1)
    if observed.all():
        ability = (row_sum[:, None] - values) / (frame.shape[1] - 1)
        response_centered = values - values.mean(axis=0, keepdims=True)
        ability_centered = ability - ability.mean(axis=0, keepdims=True)
        numerator = np.sum(response_centered * ability_centered, axis=0)
        denominator = np.sqrt(
            np.sum(response_centered**2, axis=0) * np.sum(ability_centered**2, axis=0)
        )
        return np.divide(
            numerator,
            denominator,
            out=np.zeros(frame.shape[1], dtype=float),
            where=denominator > 0.0,
        )
    scores = np.empty(frame.shape[1], dtype=float)
    for item in range(frame.shape[1]):
        mask = observed[:, item] & (row_count > 1)
        if mask.sum() < 3:
            scores[item] = np.nan
            continue
        ability = (row_sum[mask] - filled[mask, item]) / (row_count[mask] - 1)
        responses = values[mask, item]
        if np.std(ability) == 0.0 or np.std(responses) == 0.0:
            scores[item] = 0.0
        else:
            scores[item] = float(np.corrcoef(ability, responses)[0, 1])
    return scores


def infer_item_diagnostics(
    matrix: pd.DataFrame,
    subjects: Sequence[str] | Mapping[str, str],
    *,
    model_families: Sequence[str] | Mapping[str, str] | None = None,
    n_bootstrap: int = 500,
    n_permutations: int = 500,
    confidence_level: float = 0.95,
    fdr_level: float = 0.05,
    stability_threshold: float = 0.80,
    risk_threshold: float = 0.0,
    seed: int = 2027,
) -> pd.DataFrame:
    """Infer negative-discrimination risk with family-aware stability and null control.

    The diagnostic is deliberately narrow: it detects evidence consistent with an item being
    anti-correlated with leave-one-item aggregate ability. It does not label the cause.
    """

    frame = validate_binary_response_matrix(matrix)
    subject_values = _subjects(frame.columns.astype(str), subjects)
    observed_discrimination = item_discrimination_scores(frame)
    observed_risk = -np.nan_to_num(observed_discrimination, nan=0.0)
    bootstrap_discrimination = cluster_bootstrap_scores(
        frame,
        item_discrimination_scores,
        clusters=model_families,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )
    bootstrap_risk = -np.nan_to_num(bootstrap_discrimination, nan=0.0)
    lower, upper = percentile_intervals(bootstrap_risk, confidence_level=confidence_level)
    standard_error = np.nanstd(bootstrap_risk, axis=0, ddof=1)
    stability = selection_frequency(bootstrap_risk, threshold=risk_threshold)
    null_scores = _permutation_null(
        frame,
        n_permutations=n_permutations,
        seed=seed + 1,
    )
    p_values = (1.0 + np.sum(null_scores >= observed_risk[None, :], axis=0)) / (
        n_permutations + 1.0
    )
    bh = benjamini_hochberg(p_values)
    by = benjamini_yekutieli(p_values)
    difficulty = frame.mean(axis=0, skipna=True).to_numpy(dtype=float)
    claim_status = np.where(
        (bh <= fdr_level) & (stability >= stability_threshold) & (lower > risk_threshold),
        "STABLE_FDR_CONTROLLED_FLAG",
        "EXPLORATORY_ONLY",
    )
    return pd.DataFrame(
        {
            "item_id": frame.columns.astype(str),
            "diagnostic": "negative_discrimination",
            "diagnostic_score": observed_risk,
            "standard_error": standard_error,
            "confidence_lower": lower,
            "confidence_upper": upper,
            "null_p_value": p_values,
            "FDR_q_value": bh,
            "BY_q_value": by,
            "bootstrap_stability": stability,
            "effect_size": observed_risk,
            "subject": subject_values,
            "difficulty": difficulty,
            "claim_status": claim_status,
        }
    )


def empirical_bayes_shrinkage(
    estimates: Sequence[float],
    standard_errors: Sequence[float],
) -> np.ndarray:
    """Normal-normal empirical-Bayes shrinkage toward the grand mean."""

    theta = np.asarray(estimates, dtype=float)
    se = np.asarray(standard_errors, dtype=float)
    if theta.shape != se.shape or theta.ndim != 1:
        raise ValueError("estimates and standard_errors must be aligned vectors")
    if np.any(se < 0.0) or np.any(~np.isfinite(theta)) or np.any(~np.isfinite(se)):
        raise ValueError(
            "estimates and standard errors must be finite; standard errors non-negative"
        )
    mean = float(np.mean(theta))
    between = max(float(np.var(theta, ddof=1) - np.mean(se**2)), 0.0) if len(theta) > 1 else 0.0
    if between == 0.0:
        return np.full_like(theta, mean)
    weight = between / (between + se**2)
    return mean + weight * (theta - mean)


def diagnostic_agreement_taxonomy(frame: pd.DataFrame) -> pd.DataFrame:
    """Assign an explicit agreement/disagreement class to wide boolean risk indicators."""

    required = {"item_id", "difficulty", "discrimination", "rank_material", "forensic"}
    if not required.issubset(frame.columns):
        raise ValueError(f"diagnostic frame is missing {sorted(required - set(frame.columns))}")
    output = frame.copy()

    def classify(row: pd.Series) -> str:
        active = [
            name
            for name in ("difficulty", "discrimination", "rank_material", "forensic")
            if bool(row[name])
        ]
        if len(active) >= 3:
            return "CONSISTENT_HIGH_RISK"
        singleton = {
            "difficulty": "DIFFICULTY_ONLY",
            "discrimination": "DISCRIMINATION_ONLY",
            "rank_material": "RANK_MATERIAL_ONLY",
            "forensic": "FORENSIC_ONLY",
        }
        if len(active) == 1:
            return singleton[active[0]]
        if len(active) == 2:
            return "DIAGNOSTIC_CONFLICT"
        return "LOW_SIGNAL"

    output["agreement_class"] = output.apply(classify, axis=1)
    return output


def _permutation_null(
    matrix: pd.DataFrame,
    *,
    n_permutations: int,
    seed: int,
) -> np.ndarray:
    if n_permutations <= 0:
        raise ValueError("n_permutations must be positive")
    rng = np.random.default_rng(seed)
    values = matrix.to_numpy(dtype=float)
    draws = np.empty((n_permutations, matrix.shape[1]), dtype=float)
    ability = np.nanmean(values, axis=1)
    for replicate in range(n_permutations):
        draws[replicate] = -np.nan_to_num(
            _column_correlations(values, rng.permutation(ability)), nan=0.0
        )
    return draws


def _column_correlations(values: np.ndarray, row_score: np.ndarray) -> np.ndarray:
    output = np.empty(values.shape[1], dtype=float)
    if np.isfinite(values).all() and np.isfinite(row_score).all():
        centered_values = values - values.mean(axis=0, keepdims=True)
        centered_score = row_score - row_score.mean()
        numerator = centered_score @ centered_values
        denominator = np.sqrt(np.sum(centered_score**2) * np.sum(centered_values**2, axis=0))
        return np.divide(
            numerator,
            denominator,
            out=np.zeros(values.shape[1], dtype=float),
            where=denominator > 0.0,
        )
    for item in range(values.shape[1]):
        mask = np.isfinite(values[:, item]) & np.isfinite(row_score)
        if mask.sum() < 3 or np.std(values[mask, item]) == 0.0 or np.std(row_score[mask]) == 0.0:
            output[item] = 0.0
        else:
            output[item] = float(np.corrcoef(values[mask, item], row_score[mask])[0, 1])
    return output


def _subjects(
    item_ids: pd.Index,
    subjects: Sequence[str] | Mapping[str, str],
) -> list[str]:
    if isinstance(subjects, Mapping):
        missing = [item for item in item_ids if item not in subjects]
        if missing:
            raise ValueError(f"subject mapping is missing {len(missing)} item(s)")
        return [str(subjects[item]) for item in item_ids]
    values = [str(value) for value in subjects]
    if len(values) != len(item_ids):
        raise ValueError("subjects must have one entry per item")
    return values
