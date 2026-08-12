from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from valideval.statistics.rank_nulls import (
    normalize_subject_ids,
    subject_accuracy_matrix,
    validate_binary_response_matrix,
)


def estimate_variance_components(
    matrix: pd.DataFrame,
    subjects: Sequence[str] | Mapping[str, str],
    model_families: Mapping[str, str],
) -> dict[str, float | int | str]:
    """Estimate a transparent method-of-moments Study-H variance profile.

    Components are descriptive design quantities for this observed panel. Because family cells
    are unbalanced and checkpoints are not sampled randomly, they are not population variance
    estimates without additional assumptions.
    """

    frame = validate_binary_response_matrix(matrix)
    missing = [str(model) for model in frame.index if str(model) not in model_families]
    if missing:
        raise ValueError(f"model_families is missing {len(missing)} model(s)")
    subject_map = normalize_subject_ids(frame.columns, subjects)
    scores = subject_accuracy_matrix(frame, subject_map.to_dict())
    grand = float(scores.to_numpy().mean())
    model_mean = scores.mean(axis=1)
    subject_mean = scores.mean(axis=0)
    families = pd.Series(
        [str(model_families[str(model)]) for model in scores.index],
        index=scores.index,
        name="family",
    )
    family_mean = model_mean.groupby(families).mean()
    family_effect = families.map(family_mean).to_numpy(dtype=float) - grand
    model_effect = model_mean.to_numpy(dtype=float) - grand - family_effect
    subject_effect = subject_mean.to_numpy(dtype=float) - grand

    family_subject = scores.groupby(families).mean()
    family_subject_residual = (
        family_subject.to_numpy(dtype=float)
        - family_mean.to_numpy(dtype=float)[:, None]
        - subject_effect[None, :]
    )
    model_subject_residual = (
        scores.to_numpy(dtype=float)
        - model_mean.to_numpy(dtype=float)[:, None]
        - subject_effect[None, :]
        + grand
    )
    family_subject_lookup = {
        (family, subject): family_subject_residual[family_index, subject_index]
        for family_index, family in enumerate(family_subject.index)
        for subject_index, subject in enumerate(family_subject.columns)
    }
    adjusted_model_subject = model_subject_residual.copy()
    for row, model in enumerate(scores.index):
        family = families.loc[model]
        for column, subject in enumerate(scores.columns):
            adjusted_model_subject[row, column] -= family_subject_lookup[(family, subject)]

    item_difficulty = frame.mean(axis=0, skipna=True).to_numpy(dtype=float)
    predicted = np.column_stack(
        [scores.loc[:, str(subject)].to_numpy(dtype=float) for subject in subject_map]
    )
    residual = frame.to_numpy(dtype=float) - predicted
    return {
        "method": "descriptive_unbalanced_method_of_moments_v7",
        "model": _variance(model_effect),
        "family": _variance(family_effect),
        "subject": _variance(subject_effect),
        "item": _variance(item_difficulty),
        "model_x_subject": _variance(adjusted_model_subject.ravel()),
        "family_x_subject": _variance(family_subject_residual.ravel()),
        "residual": float(np.nanvar(residual, ddof=1)),
        "model_count": int(frame.shape[0]),
        "family_count": int(families.nunique()),
        "subject_count": int(scores.shape[1]),
        "item_count": int(frame.shape[1]),
    }


def _variance(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    return float(np.var(finite, ddof=1)) if len(finite) > 1 else 0.0
