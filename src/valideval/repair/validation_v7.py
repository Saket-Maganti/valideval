from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

REPAIR_STATUSES = (
    "REPAIR_SUPPORTED",
    "REPAIR_PARTIAL",
    "REPAIR_NO_BENEFIT",
    "REPAIR_HARMS",
    "UNDERPOWERED",
    "BLOCKED",
)


def validate_repair_policy(
    original_draws: pd.DataFrame,
    repaired_draws: pd.DataFrame,
    matched_random_draws: Sequence[pd.DataFrame],
    *,
    cross_fitted: bool,
    held_out_labels: bool,
    held_out_families: bool,
    minimum_draws: int = 200,
) -> dict[str, object]:
    """License a repair only against a random-matched, fully held-out comparison."""

    if not cross_fitted or not held_out_labels or not held_out_families:
        return {"status": "BLOCKED", "reason": "held-out validation gates failed"}
    if len(original_draws) < minimum_draws or len(repaired_draws) < minimum_draws:
        return {"status": "UNDERPOWERED", "reason": "insufficient bootstrap draws"}
    if list(original_draws.columns) != list(repaired_draws.columns):
        raise ValueError("original and repaired draws must contain the same models")
    original_uncertainty = float(original_draws.rank(axis=1, ascending=False).std(axis=0).mean())
    repaired_uncertainty = float(repaired_draws.rank(axis=1, ascending=False).std(axis=0).mean())
    observed_improvement = original_uncertainty - repaired_uncertainty
    random_improvements = []
    for random_draws in matched_random_draws:
        if list(random_draws.columns) != list(original_draws.columns):
            raise ValueError("matched random draws must contain the same models")
        random_uncertainty = float(random_draws.rank(axis=1, ascending=False).std(axis=0).mean())
        random_improvements.append(original_uncertainty - random_uncertainty)
    if not random_improvements:
        return {"status": "BLOCKED", "reason": "matched random baseline missing"}
    random_array = np.asarray(random_improvements, dtype=float)
    exceeds_random = observed_improvement > float(np.quantile(random_array, 0.95))
    if observed_improvement < 0.0:
        status = "REPAIR_HARMS"
    elif observed_improvement <= float(np.median(random_array)):
        status = "REPAIR_NO_BENEFIT"
    elif exceeds_random:
        status = "REPAIR_SUPPORTED"
    else:
        status = "REPAIR_PARTIAL"
    return {
        "status": status,
        "rank_uncertainty_before": original_uncertainty,
        "rank_uncertainty_after": repaired_uncertainty,
        "observed_improvement": observed_improvement,
        "matched_random_median_improvement": float(np.median(random_array)),
        "matched_random_95th_percentile": float(np.quantile(random_array, 0.95)),
        "cross_fitted": cross_fitted,
        "held_out_labels": held_out_labels,
        "held_out_families": held_out_families,
    }
