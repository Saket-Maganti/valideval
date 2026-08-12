from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from valideval.validation.confirmatory_v7 import confirmatory_readout_components

V8_METHODS = (
    "DIFFICULTY_MATCHING",
    "CONDITIONAL_RESIDUALIZATION",
    "DIFFICULTY_STRATIFIED_NULL",
    "CROSS_FITTED_DIFFICULTY",
    "SUBJECT_CONDITIONED_DIFFICULTY",
    "FAMILY_BALANCED_DIFFICULTY",
    "V8_FULL",
)


class DifficultyAdjustedDetectorV8:
    """Label-isolated exploratory detector for response-matrix anomalies.

    Deliberately, neither construction nor scoring accepts a flaw-label argument.
    Sealed labels belong only in the caller's post-scoring evaluation step.
    """

    def score_methods(
        self,
        matrix: pd.DataFrame,
        *,
        model_families: Sequence[str] | Mapping[str, str],
    ) -> dict[str, np.ndarray]:
        values = matrix.to_numpy(dtype=float)
        if values.ndim != 2 or values.shape[0] < 4 or values.shape[1] < 4:
            raise ValueError("V8 requires at least four models and four items")
        families = _families(matrix.index.astype(str), model_families)
        unique_families = sorted(set(families.tolist()))
        if len(unique_families) < 3:
            raise ValueError("V8 family-balanced correction requires at least three families")
        subjects = np.asarray([str(item).split("::", 1)[0] for item in matrix.columns])
        components = confirmatory_readout_components(matrix)
        structural = np.maximum.reduce(
            [
                components["missingness"],
                components["duplicate"],
                components["negative_discrimination"],
                components["subject_residual"],
            ]
        )
        raw_difficulty = 1.0 - _safe_column_mean(values)
        family_difficulty = family_balanced_difficulty(values, families)
        crossfit_difficulty = cross_fitted_family_difficulty(values, families)
        subject_difficulty = subject_conditioned_difficulty(family_difficulty, subjects)

        matched = difficulty_matching(structural, family_difficulty)
        residualized = conditional_residualization(
            structural, family_difficulty, subjects
        )
        stratified = difficulty_stratified_null(structural, family_difficulty)
        crossfit = conditional_residualization(structural, crossfit_difficulty, subjects)
        subject_adjusted = conditional_residualization(
            structural, subject_difficulty, subjects
        )
        family_adjusted = conditional_residualization(
            structural, family_difficulty, subjects
        )
        full = residualized.copy()
        return {
            "DIFFICULTY_MATCHING": matched,
            "CONDITIONAL_RESIDUALIZATION": residualized,
            "DIFFICULTY_STRATIFIED_NULL": stratified,
            "CROSS_FITTED_DIFFICULTY": crossfit,
            "SUBJECT_CONDITIONED_DIFFICULTY": subject_adjusted,
            "FAMILY_BALANCED_DIFFICULTY": family_adjusted,
            "V8_FULL": full,
            "RAW_DIFFICULTY": raw_difficulty,
            "FAMILY_BALANCED_DIFFICULTY_ESTIMATE": family_difficulty,
            "FAMILY_DISAGREEMENT": family_disagreement(values, families),
        }

    def ablation_scores(
        self,
        matrix: pd.DataFrame,
        *,
        model_families: Sequence[str] | Mapping[str, str],
    ) -> dict[str, np.ndarray]:
        values = matrix.to_numpy(dtype=float)
        families = _families(matrix.index.astype(str), model_families)
        subjects = np.asarray([str(item).split("::", 1)[0] for item in matrix.columns])
        difficulty = family_balanced_difficulty(values, families)
        components = confirmatory_readout_components(matrix)
        names = ("missingness", "duplicate", "negative_discrimination", "subject_residual")
        output: dict[str, np.ndarray] = {}
        for omitted in names:
            structural = np.maximum.reduce(
                [components[name] for name in names if name != omitted]
            )
            output[f"WITHOUT_{omitted.upper()}"] = conditional_residualization(
                structural, difficulty, subjects
            )
        output["WITHOUT_DIFFICULTY_CORRECTION"] = np.maximum.reduce(
            [components[name] for name in names]
        )
        output["WITHOUT_FAMILY_BALANCING"] = conditional_residualization(
            output["WITHOUT_DIFFICULTY_CORRECTION"],
            1.0 - _safe_column_mean(values),
            subjects,
        )
        return output


def family_balanced_difficulty(values: np.ndarray, families: np.ndarray) -> np.ndarray:
    overall = _safe_column_mean(values)
    family_rates = np.vstack(
        [
            _safe_column_mean(values[families == family], fallback=overall)
            for family in sorted(set(families))
        ]
    )
    return 1.0 - np.mean(family_rates, axis=0)


def cross_fitted_family_difficulty(values: np.ndarray, families: np.ndarray) -> np.ndarray:
    unique = sorted(set(families))
    overall = _safe_column_mean(values)
    rates = {
        family: _safe_column_mean(values[families == family], fallback=overall)
        for family in unique
    }
    heldout_estimates = []
    for heldout in unique:
        heldout_estimates.append(
            1.0 - np.mean([rate for family, rate in rates.items() if family != heldout], axis=0)
        )
    return np.mean(heldout_estimates, axis=0)


def subject_conditioned_difficulty(difficulty: np.ndarray, subjects: np.ndarray) -> np.ndarray:
    output = np.zeros_like(difficulty, dtype=float)
    for subject in sorted(set(subjects.tolist())):
        indices = np.flatnonzero(subjects == subject)
        output[indices] = difficulty[indices] - np.nanmedian(difficulty[indices])
    return output


def family_disagreement(values: np.ndarray, families: np.ndarray) -> np.ndarray:
    overall = _safe_column_mean(values)
    family_rates = np.vstack(
        [
            _safe_column_mean(values[families == family], fallback=overall)
            for family in sorted(set(families))
        ]
    )
    return np.std(family_rates, axis=0)


def difficulty_matching(scores: np.ndarray, difficulty: np.ndarray, bins: int = 10) -> np.ndarray:
    groups = _quantile_groups(difficulty, bins)
    residual = np.zeros_like(scores, dtype=float)
    for group in sorted(set(groups.tolist())):
        indices = np.flatnonzero(groups == group)
        residual[indices] = np.clip(scores[indices] - np.nanmedian(scores[indices]), 0.0, None)
    return _unit_scale(residual)


def conditional_residualization(
    scores: np.ndarray,
    difficulty: np.ndarray,
    subjects: np.ndarray,
) -> np.ndarray:
    unique_subjects = sorted(set(subjects.tolist()))
    subject_columns = [
        (subjects == subject).astype(float) for subject in unique_subjects[1:]
    ]
    design = np.column_stack(
        [
            np.ones(len(scores)),
            difficulty,
            difficulty**2,
            *subject_columns,
        ]
    )
    finite = np.isfinite(scores) & np.all(np.isfinite(design), axis=1)
    fitted = np.full(len(scores), float(np.nanmedian(scores)))
    if finite.sum() > design.shape[1]:
        coefficients, *_ = np.linalg.lstsq(design[finite], scores[finite], rcond=None)
        fitted = design @ coefficients
    return _unit_scale(np.clip(scores - fitted, 0.0, None))


def difficulty_stratified_null(
    scores: np.ndarray, difficulty: np.ndarray, bins: int = 10
) -> np.ndarray:
    groups = _quantile_groups(difficulty, bins)
    output = np.zeros_like(scores, dtype=float)
    for group in sorted(set(groups.tolist())):
        indices = np.flatnonzero(groups == group)
        order = pd.Series(scores[indices]).rank(method="average", pct=True).to_numpy()
        output[indices] = order
    return output


def exploratory_stratified_p_values(
    scores: np.ndarray,
    difficulty: np.ndarray,
    subjects: Sequence[str],
    *,
    bins: int = 10,
) -> np.ndarray:
    groups = _quantile_groups(difficulty, bins)
    subjects_array = np.asarray(subjects, dtype=str)
    p_values = np.ones(len(scores), dtype=float)
    for subject in sorted(set(subjects_array.tolist())):
        for group in sorted(set(groups.tolist())):
            indices = np.flatnonzero((subjects_array == subject) & (groups == group))
            if not len(indices):
                continue
            ranks = pd.Series(scores[indices]).rank(method="max", ascending=False).to_numpy()
            p_values[indices] = (ranks + 1.0) / (len(indices) + 1.0)
    return p_values


def _families(
    model_ids: pd.Index,
    model_families: Sequence[str] | Mapping[str, str],
) -> np.ndarray:
    if isinstance(model_families, Mapping):
        missing = [model for model in model_ids if model not in model_families]
        if missing:
            raise ValueError(f"family mapping is missing {len(missing)} models")
        values = [str(model_families[model]) for model in model_ids]
    else:
        values = [str(value) for value in model_families]
        if len(values) != len(model_ids):
            raise ValueError("model_families must align with matrix rows")
    if any(not value for value in values):
        raise ValueError("empty family identifiers are not allowed")
    return np.asarray(values)


def _quantile_groups(values: np.ndarray, bins: int) -> np.ndarray:
    series = pd.Series(values).rank(method="average", pct=True)
    return np.minimum((series.to_numpy() * bins).astype(int), bins - 1)


def _unit_scale(values: np.ndarray) -> np.ndarray:
    finite = values[np.isfinite(values)]
    scale = float(np.quantile(finite, 0.95)) if len(finite) else 0.0
    if scale <= 0.0:
        return np.zeros_like(values, dtype=float)
    return np.clip(np.nan_to_num(values, nan=0.0) / scale, 0.0, 1.0)


def _safe_column_mean(
    values: np.ndarray, *, fallback: np.ndarray | None = None
) -> np.ndarray:
    finite = np.isfinite(values)
    count = finite.sum(axis=0)
    total = np.where(finite, values, 0.0).sum(axis=0)
    default = np.full(values.shape[1], 0.5) if fallback is None else fallback
    return np.divide(total, count, out=np.asarray(default, dtype=float).copy(), where=count > 0)
