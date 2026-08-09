from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.optimize import linprog


def subject_weight_fragility(subject_scores: pd.DataFrame) -> dict[str, object]:
    """Minimum total-variation change to equal subject weights that flips the winner."""

    if subject_scores.shape[0] < 2 or subject_scores.shape[1] < 2:
        raise ValueError("subject_scores must contain at least two models and subjects")
    aggregate = subject_scores.mean(axis=1)
    winner = str(aggregate.idxmax())
    best: dict[str, object] | None = None
    n_subjects = subject_scores.shape[1]
    baseline = np.full(n_subjects, 1.0 / n_subjects)
    for challenger in subject_scores.index:
        if str(challenger) == winner:
            continue
        difference = subject_scores.loc[winner].to_numpy(dtype=float) - subject_scores.loc[
            challenger
        ].to_numpy(dtype=float)
        # Variables are subject weights followed by absolute deviations from equal weights.
        objective = np.r_[np.zeros(n_subjects), np.ones(n_subjects) * 0.5]
        upper = np.c_[np.eye(n_subjects), -np.eye(n_subjects)]
        lower = np.c_[-np.eye(n_subjects), -np.eye(n_subjects)]
        result = linprog(
            objective,
            A_ub=np.vstack([np.r_[difference, np.zeros(n_subjects)], upper, lower]),
            b_ub=np.r_[0.0, baseline, -baseline],
            A_eq=np.asarray([np.r_[np.ones(n_subjects), np.zeros(n_subjects)]]),
            b_eq=np.asarray([1.0]),
            bounds=[(0.0, 1.0)] * n_subjects + [(0.0, None)] * n_subjects,
            method="highs",
        )
        if not result.success:
            continue
        candidate = {
            "winner": winner,
            "challenger": str(challenger),
            "minimum_total_variation": float(result.fun),
            "flipped_weights": result.x[:n_subjects].tolist(),
            "subjects": [str(subject) for subject in subject_scores.columns],
        }
        if best is None or float(candidate["minimum_total_variation"]) < float(
            best["minimum_total_variation"]
        ):
            best = candidate
    return best or {
        "winner": winner,
        "challenger": None,
        "minimum_total_variation": None,
        "status": "NO_FEASIBLE_REVERSAL",
    }


def item_removal_fragility(
    matrix: pd.DataFrame,
    *,
    difficulty: Sequence[float] | None = None,
    difficulty_bins: int = 10,
) -> dict[str, object]:
    """Smallest greedy item removal that reverses the observed winner.

    The exact pairwise solution removes items in decreasing winner advantage. The optional
    matched-difficulty result removes complete quantile-matched blocks and is conservative.
    """

    if matrix.shape[0] < 2 or matrix.shape[1] < 2:
        raise ValueError("matrix must contain at least two models and items")
    scores = matrix.mean(axis=1)
    winner = str(scores.idxmax())
    best: dict[str, object] | None = None
    for challenger in matrix.index:
        if str(challenger) == winner:
            continue
        delta = matrix.loc[winner].to_numpy(dtype=float) - matrix.loc[challenger].to_numpy(
            dtype=float
        )
        order = np.argsort(delta)[::-1]
        total = float(np.nansum(delta))
        removed_sum = np.nancumsum(np.nan_to_num(delta[order], nan=0.0))
        feasible = np.flatnonzero(total - removed_sum <= 0.0)
        if not len(feasible):
            continue
        count = int(feasible[0] + 1)
        candidate = {
            "winner": winner,
            "challenger": str(challenger),
            "items_removed": count,
            "removal_fraction": count / matrix.shape[1],
            "removed_item_ids": [str(matrix.columns[index]) for index in order[:count]],
        }
        if best is None or float(candidate["removal_fraction"]) < float(best["removal_fraction"]):
            best = candidate
    output = best or {
        "winner": winner,
        "challenger": None,
        "items_removed": None,
        "removal_fraction": None,
        "status": "NO_FEASIBLE_REVERSAL",
    }
    if difficulty is not None and best is not None:
        difficulty_values = np.asarray(difficulty, dtype=float)
        if len(difficulty_values) != matrix.shape[1]:
            raise ValueError("difficulty must have one value per item")
        bins = pd.qcut(difficulty_values, q=difficulty_bins, labels=False, duplicates="drop")
        selected = set(best["removed_item_ids"])
        counts = pd.Series(
            [bins[index] for index, item in enumerate(matrix.columns) if str(item) in selected]
        ).value_counts()
        output["matched_difficulty_bin_counts"] = {
            str(int(key)): int(value) for key, value in counts.items()
        }
    return output
