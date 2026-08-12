from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from valideval.validation.multiplicity import correct_p_values

SIMULTANEOUS_METHOD = "BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS"
MARGINAL_METHOD = "MARGINAL_BOOTSTRAP"


def simultaneous_rank_confidence_sets(
    score_draws: pd.DataFrame,
    *,
    observed_scores: pd.Series | None = None,
    confidence_level: float = 0.95,
    resampling_unit: str = "items_with_model_dependence_preserved",
) -> pd.DataFrame:
    """Construct joint rank bands with a bootstrap maximum-deviation critical value.

    Each bootstrap row must be a joint draw for every model. The maximum rank
    deviation is therefore calibrated across the entire leaderboard rather than
    separately per model. Correlation among checkpoints is retained within every
    joint draw.
    """

    frame = _validate_draws(score_draws)
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie in (0, 1)")
    point_scores = frame.mean(axis=0) if observed_scores is None else observed_scores.astype(float)
    point_scores.index = point_scores.index.astype(str)
    frame.columns = frame.columns.astype(str)
    if set(point_scores.index) != set(frame.columns):
        raise ValueError("observed_scores identifiers must match score_draws")
    point_scores = point_scores.reindex(frame.columns)
    point_ranks = point_scores.rank(ascending=False, method="average")
    draw_ranks = frame.rank(axis=1, ascending=False, method="average")
    max_deviation = draw_ranks.sub(point_ranks, axis=1).abs().max(axis=1)
    critical = float(np.quantile(max_deviation, confidence_level, method="higher"))
    model_count = frame.shape[1]
    return pd.DataFrame(
        {
            "model_id": frame.columns.astype(str),
            "point_rank": point_ranks.to_numpy(dtype=float),
            "simultaneous_rank_lower": np.maximum(
                1.0, point_ranks.to_numpy(dtype=float) - critical
            ),
            "simultaneous_rank_upper": np.minimum(
                float(model_count), point_ranks.to_numpy(dtype=float) + critical
            ),
            "interval_type": SIMULTANEOUS_METHOD,
            "confidence_level": confidence_level,
            "joint_critical_rank_deviation": critical,
            "resampling_unit": resampling_unit,
            "joint_draw_count": frame.shape[0],
        }
    )


def marginal_rank_intervals(
    score_draws: pd.DataFrame,
    *,
    confidence_level: float = 0.95,
) -> pd.DataFrame:
    frame = _validate_draws(score_draws)
    alpha = 1.0 - confidence_level
    ranks = frame.rank(axis=1, ascending=False, method="average")
    return pd.DataFrame(
        {
            "model_id": frame.columns.astype(str),
            "median_rank": ranks.median(axis=0).to_numpy(dtype=float),
            "marginal_rank_lower": ranks.quantile(alpha / 2.0, axis=0).to_numpy(dtype=float),
            "marginal_rank_upper": ranks.quantile(1.0 - alpha / 2.0, axis=0).to_numpy(dtype=float),
            "interval_type": MARGINAL_METHOD,
            "confidence_level": confidence_level,
        }
    )


def pairwise_multiplicity_analysis(
    score_draws: pd.DataFrame,
    *,
    confidence_level: float = 0.95,
    hypothesis_family_id: str = "ALL_MODEL_PAIRS",
    multiplicity_scope: str = "ALL_PAIRS_LEADERBOARD",
    methods: Sequence[str] = ("bh", "holm"),
) -> pd.DataFrame:
    """Test all unordered directional pairs with family-level FDR/FWER control."""

    frame = _validate_draws(score_draws)
    if not hypothesis_family_id or not multiplicity_scope:
        raise ValueError("hypothesis family ID and multiplicity scope are required")
    alpha = 1.0 - confidence_level
    rows: list[dict[str, Any]] = []
    columns = list(frame.columns)
    for left, model_a in enumerate(columns):
        for model_b in columns[left + 1 :]:
            difference = frame[model_a].to_numpy(dtype=float) - frame[model_b].to_numpy(dtype=float)
            nonpositive = int(np.sum(difference <= 0.0))
            nonnegative = int(np.sum(difference >= 0.0))
            p_value = min(1.0, 2.0 * min(nonpositive + 1, nonnegative + 1) / (len(difference) + 1))
            lower, upper = np.quantile(difference, [alpha / 2.0, 1.0 - alpha / 2.0])
            rows.append(
                {
                    "model_a": str(model_a),
                    "model_b": str(model_b),
                    "mean_difference": float(np.mean(difference)),
                    "confidence_lower_marginal": float(lower),
                    "confidence_upper_marginal": float(upper),
                    "p_value_two_sided": float(p_value),
                    "hypothesis_family_id": hypothesis_family_id,
                    "multiplicity_scope": multiplicity_scope,
                    "prespecified_single_comparison": False,
                }
            )
    result = pd.DataFrame(rows)
    p_values = result["p_value_two_sided"].tolist()
    for method in methods:
        normalized = method.lower()
        if normalized not in {"bh", "holm"}:
            raise ValueError("pairwise methods must be bh (FDR) or holm (FWER)")
        result[f"adjusted_p_{normalized}"] = correct_p_values(p_values, method=normalized)
        result[f"reject_{normalized}"] = result[f"adjusted_p_{normalized}"] <= alpha
    result["primary_control"] = "FDR_CONTROLLED_PAIRWISE_BH"
    result["sensitivity_control"] = "FWER_CONTROLLED_PAIRWISE_HOLM"
    return result


def prespecified_pair_test(
    difference_draws: Sequence[float],
    *,
    model_a: str,
    model_b: str,
    confidence_level: float = 0.95,
) -> dict[str, Any]:
    values = np.asarray(difference_draws, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("difference_draws must contain at least two finite draws")
    alpha = 1.0 - confidence_level
    lower, upper = np.quantile(values, [alpha / 2.0, 1.0 - alpha / 2.0])
    p_value = min(
        1.0,
        2.0
        * min(int(np.sum(values <= 0.0)) + 1, int(np.sum(values >= 0.0)) + 1)
        / (len(values) + 1),
    )
    return {
        "model_a": model_a,
        "model_b": model_b,
        "mean_difference": float(np.mean(values)),
        "confidence_lower": float(lower),
        "confidence_upper": float(upper),
        "p_value_two_sided": float(p_value),
        "hypothesis_family_id": "PRESPECIFIED_SINGLE_PAIR",
        "multiplicity_scope": "SINGLE_PRESPECIFIED_COMPARISON",
        "prespecified_single_comparison": True,
    }


def simulate_simultaneous_rank_coverage(
    *,
    simulations: int = 200,
    bootstrap_draws: int = 300,
    model_count: int = 8,
    family_count: int = 4,
    family_correlation: float = 0.6,
    tied_truth: bool = False,
    confidence_level: float = 0.95,
    seed: int = 7301,
) -> dict[str, Any]:
    """Known-truth coverage check with family-correlated model errors."""

    if simulations < 50 or bootstrap_draws < 100:
        raise ValueError("coverage simulation requires >=50 simulations and >=100 bootstraps")
    if not 0.0 <= family_correlation < 1.0:
        raise ValueError("family_correlation must lie in [0, 1)")
    rng = np.random.default_rng(seed)
    true_scores = np.linspace(0.75, 0.55, model_count)
    if tied_truth:
        true_scores[::2] = true_scores[1::2]
    true_ranks = pd.Series(true_scores).rank(ascending=False, method="average").to_numpy()
    families = np.arange(model_count) % family_count
    joint_covered = 0
    average_widths = []
    for _ in range(simulations):
        family_error = rng.normal(0.0, 0.018, family_count)
        independent_error = rng.normal(0.0, 0.018, model_count)
        observed = (
            true_scores
            + np.sqrt(family_correlation) * family_error[families]
            + np.sqrt(1.0 - family_correlation) * independent_error
        )
        family_bootstrap = rng.normal(0.0, 0.018, (bootstrap_draws, family_count))
        independent_bootstrap = rng.normal(0.0, 0.018, (bootstrap_draws, model_count))
        draws = observed[None, :] + np.sqrt(family_correlation) * family_bootstrap[:, families]
        draws += np.sqrt(1.0 - family_correlation) * independent_bootstrap
        columns = [f"model_{index}" for index in range(model_count)]
        intervals = simultaneous_rank_confidence_sets(
            pd.DataFrame(draws, columns=columns),
            observed_scores=pd.Series(observed, index=columns),
            confidence_level=confidence_level,
            resampling_unit="known_truth_family_correlated_parametric_bootstrap",
        )
        covered = (intervals["simultaneous_rank_lower"].to_numpy() <= true_ranks) & (
            true_ranks <= intervals["simultaneous_rank_upper"].to_numpy()
        )
        joint_covered += int(covered.all())
        average_widths.append(
            float(
                np.mean(intervals["simultaneous_rank_upper"] - intervals["simultaneous_rank_lower"])
            )
        )
    coverage = joint_covered / simulations
    mcse = float(np.sqrt(coverage * (1.0 - coverage) / simulations))
    return {
        "status": "SIMULTANEOUS_RANK_COVERAGE_SIMULATION_COMPLETE",
        "simulations": simulations,
        "bootstrap_draws": bootstrap_draws,
        "model_count": model_count,
        "family_count": family_count,
        "family_correlation": family_correlation,
        "tied_truth": tied_truth,
        "target_coverage": confidence_level,
        "joint_coverage": coverage,
        "joint_coverage_monte_carlo_se": mcse,
        "mean_interval_width": float(np.mean(average_widths)),
        "method": SIMULTANEOUS_METHOD,
        "claim_boundary": "Coverage is conditional on this known-truth simulation family.",
    }


def _validate_draws(score_draws: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(score_draws, pd.DataFrame) or score_draws.shape[0] < 2:
        raise ValueError("score_draws must contain at least two joint draws")
    if score_draws.shape[1] < 2 or score_draws.columns.has_duplicates:
        raise ValueError("score_draws must contain at least two uniquely named models")
    frame = score_draws.astype(float)
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError("score_draws must be finite")
    return frame
