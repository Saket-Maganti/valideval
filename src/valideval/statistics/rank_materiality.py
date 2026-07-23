from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from valideval.statistics.rank_nulls import (
    compare_observed_rank_ranges_to_null,
    normalize_subject_ids,
    simulate_rank_range_null,
    subject_accuracy_matrix,
    subject_rank_ranges,
    validate_binary_response_matrix,
)


def tie_aware_ranks(scores: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Rank higher scores first using average ranks for ties."""

    if isinstance(scores, pd.Series):
        return scores.rank(method="average", ascending=False, na_option="bottom")
    return scores.rank(axis=0, method="average", ascending=False, na_option="bottom")


def normalized_rank_entropy(ranks: pd.Series, n_models: int) -> float:
    if ranks.empty or n_models <= 1:
        return 0.0
    probabilities = ranks.value_counts(normalize=True).to_numpy(dtype=float)
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    return entropy / math.log(max(min(n_models, len(ranks)), 2))


def kendalls_w(rank_matrix: pd.DataFrame) -> float:
    """Tie-corrected Kendall's W across subject ranking columns."""

    if rank_matrix.shape[0] < 2 or rank_matrix.shape[1] < 2:
        return 0.0
    values = rank_matrix.to_numpy(dtype=float)
    n_objects, n_judges = values.shape
    rank_sums = values.sum(axis=1)
    squared_deviation = float(np.square(rank_sums - rank_sums.mean()).sum())
    tie_correction = 0.0
    for column in rank_matrix.columns:
        counts = rank_matrix[column].value_counts().to_numpy(dtype=float)
        tie_correction += float(np.sum(counts**3 - counts))
    denominator = n_judges**2 * (n_objects**3 - n_objects) - n_judges * tie_correction
    if denominator <= 0:
        return 0.0
    return float(np.clip(12.0 * squared_deviation / denominator, 0.0, 1.0))


def bootstrap_subject_ranks(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
    *,
    n_bootstrap: int = 500,
    seed: int = 2027,
) -> pd.DataFrame:
    """Bootstrap items within each subject and retain tie-aware ranks."""

    frame = validate_binary_response_matrix(matrix)
    subjects = normalize_subject_ids(frame.columns, subject_ids)
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be positive")
    rng = np.random.default_rng(seed)
    values = frame.to_numpy(dtype=float)
    subject_names = sorted(subjects.unique())
    subject_indices = [np.flatnonzero(subjects.to_numpy() == subject) for subject in subject_names]
    n_models = frame.shape[0]
    n_subjects = len(subject_names)
    record_count = n_bootstrap * n_models * n_subjects
    replicate_column = np.repeat(np.arange(n_bootstrap), n_models * n_subjects)
    model_column = np.tile(np.repeat(frame.index.astype(str).to_numpy(), n_subjects), n_bootstrap)
    subject_column = np.tile(np.tile(subject_names, n_models), n_bootstrap)
    rank_column = np.empty(record_count, dtype=float)
    for replicate in range(n_bootstrap):
        score_columns = []
        for indices in subject_indices:
            sampled_indices = rng.choice(indices, size=len(indices), replace=True)
            with np.errstate(invalid="ignore"):
                score_columns.append(np.nanmean(values[:, sampled_indices], axis=1))
        score_frame = pd.DataFrame(
            np.column_stack(score_columns), index=frame.index, columns=subject_names
        )
        rank_values = tie_aware_ranks(score_frame).to_numpy(dtype=float).reshape(-1)
        start = replicate * n_models * n_subjects
        rank_column[start : start + n_models * n_subjects] = rank_values
    return pd.DataFrame(
        {
            "replicate": replicate_column,
            "model_id": model_column,
            "subject_id": subject_column,
            "rank": rank_column,
        }
    )


def rank_confidence_sets(
    bootstrap_ranks: pd.DataFrame,
    *,
    lower_quantile: float = 0.025,
    upper_quantile: float = 0.975,
) -> pd.DataFrame:
    if bootstrap_ranks.empty:
        raise ValueError("bootstrap_ranks must not be empty")
    if not 0.0 <= lower_quantile < upper_quantile <= 1.0:
        raise ValueError("quantiles must satisfy 0 <= lower < upper <= 1")
    grouped = bootstrap_ranks.groupby(["model_id", "subject_id"])["rank"]
    return grouped.agg(
        median_rank="median",
        lower_rank=lambda values: float(values.quantile(lower_quantile)),
        upper_rank=lambda values: float(values.quantile(upper_quantile)),
    ).reset_index()


def pairwise_outranking_probabilities(bootstrap_ranks: pd.DataFrame) -> pd.DataFrame:
    if bootstrap_ranks.empty:
        raise ValueError("bootstrap_ranks must not be empty")
    rows: list[dict[str, Any]] = []
    for subject, subject_frame in bootstrap_ranks.groupby("subject_id"):
        pivot = subject_frame.pivot(index="replicate", columns="model_id", values="rank")
        models = sorted(pivot.columns)
        for model_a in models:
            for model_b in models:
                if model_a == model_b:
                    continue
                difference = pivot[model_a] - pivot[model_b]
                probability = float((difference < 0).mean() + 0.5 * (difference == 0).mean())
                rows.append(
                    {
                        "subject_id": str(subject),
                        "model_a": str(model_a),
                        "model_b": str(model_b),
                        "outranking_probability": probability,
                    }
                )
    return pd.DataFrame(rows)


def top_k_membership_probabilities(
    bootstrap_ranks: pd.DataFrame,
    *,
    top_ks: Sequence[int] = (1, 3, 5, 10),
) -> pd.DataFrame:
    if bootstrap_ranks.empty:
        raise ValueError("bootstrap_ranks must not be empty")
    if any(k <= 0 for k in top_ks):
        raise ValueError("top-k values must be positive")
    rows: list[dict[str, Any]] = []
    grouped = bootstrap_ranks.groupby(["model_id", "subject_id"])["rank"]
    for (model_id, subject_id), ranks in grouped:
        for k in sorted(set(top_ks)):
            rows.append(
                {
                    "model_id": str(model_id),
                    "subject_id": str(subject_id),
                    "k": int(k),
                    "membership_probability": float((ranks <= k).mean()),
                }
            )
    return pd.DataFrame(rows)


def bootstrap_benchmark_composition_ranks(
    subject_scores: pd.DataFrame,
    *,
    n_bootstrap: int = 500,
    seed: int = 2027,
) -> pd.DataFrame:
    """Resample subjects to quantify benchmark-composition sensitivity."""

    if subject_scores.shape[1] < 2 or n_bootstrap <= 0:
        raise ValueError("at least two subjects and a positive bootstrap count are required")
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    subject_names = subject_scores.columns.to_numpy()
    for replicate in range(n_bootstrap):
        sampled = rng.choice(subject_names, size=len(subject_names), replace=True)
        aggregate = subject_scores.loc[:, sampled].mean(axis=1)
        ranks = tie_aware_ranks(aggregate)
        for model_id, rank in ranks.items():
            rows.append(
                {
                    "replicate": replicate,
                    "model_id": str(model_id),
                    "rank": float(rank),
                }
            )
    return pd.DataFrame(rows)


def top_k_jaccard_stability(
    subject_ranks: pd.DataFrame,
    *,
    top_ks: Sequence[int] = (1, 3, 5, 10),
) -> pd.DataFrame:
    """Compute pairwise subject top-k overlap with ties included at the boundary."""

    rows: list[dict[str, Any]] = []
    subjects = sorted(str(column) for column in subject_ranks.columns)
    for index, subject_a in enumerate(subjects):
        for subject_b in subjects[index + 1 :]:
            for k in sorted(set(top_ks)):
                if k <= 0:
                    raise ValueError("top-k values must be positive")
                set_a = set(subject_ranks.index[subject_ranks[subject_a] <= k].astype(str))
                set_b = set(subject_ranks.index[subject_ranks[subject_b] <= k].astype(str))
                union = set_a | set_b
                rows.append(
                    {
                        "subject_a": subject_a,
                        "subject_b": subject_b,
                        "k": k,
                        "jaccard": len(set_a & set_b) / len(union) if union else 1.0,
                        "ties_included_at_boundary": True,
                    }
                )
    return pd.DataFrame(rows)


def leave_one_subject_out_sensitivity(subject_scores: pd.DataFrame) -> pd.DataFrame:
    """Compare aggregate ranks after removing each subject in turn."""

    if subject_scores.shape[1] < 2:
        raise ValueError("at least two subjects are required")
    full_ranks = tie_aware_ranks(subject_scores.mean(axis=1))
    rows: list[dict[str, Any]] = []
    for held_out in subject_scores.columns:
        reduced_ranks = tie_aware_ranks(subject_scores.drop(columns=held_out).mean(axis=1))
        rows.append(
            {
                "held_out_subject": str(held_out),
                "spearman_with_full_ranking": float(
                    full_ranks.corr(reduced_ranks, method="spearman")
                ),
                "maximum_absolute_rank_change": float((full_ranks - reduced_ranks).abs().max()),
            }
        )
    return pd.DataFrame(rows)


def effect_size_filtered_reversals(
    subject_scores: pd.DataFrame,
    *,
    practical_effect_threshold: float = 0.01,
) -> pd.DataFrame:
    """List subject-level order reversals where both differences exceed a fixed threshold."""

    if practical_effect_threshold < 0:
        raise ValueError("practical_effect_threshold must be non-negative")
    score_values = subject_scores.to_numpy(dtype=float)
    aggregate = np.nanmean(score_values, axis=1)
    models = list(subject_scores.index)
    subjects = list(subject_scores.columns)
    rows: list[dict[str, Any]] = []
    for first_index, model_a in enumerate(models):
        for second_index in range(first_index + 1, len(models)):
            model_b = models[second_index]
            aggregate_difference = float(aggregate[first_index] - aggregate[second_index])
            if abs(aggregate_difference) < practical_effect_threshold:
                continue
            subject_differences = score_values[first_index] - score_values[second_index]
            reversal_indices = np.flatnonzero(
                (np.abs(subject_differences) >= practical_effect_threshold)
                & (np.sign(subject_differences) != np.sign(aggregate_difference))
            )
            for subject_index in reversal_indices:
                rows.append(
                    {
                        "model_a": str(model_a),
                        "model_b": str(model_b),
                        "subject_id": str(subjects[subject_index]),
                        "aggregate_accuracy_difference": aggregate_difference,
                        "subject_accuracy_difference": float(subject_differences[subject_index]),
                        "practical_effect_threshold": practical_effect_threshold,
                    }
                )
    return pd.DataFrame(rows)


def family_deduplicated_ranking(
    subject_scores: pd.DataFrame,
    model_families: Mapping[Any, str],
) -> pd.DataFrame:
    """Collapse checkpoints to family means before ranking family-level performance."""

    missing = [model for model in subject_scores.index if model not in model_families]
    if missing:
        raise ValueError(f"model_families is missing {len(missing)} model(s)")
    family_labels = pd.Series(
        [str(model_families[model]) for model in subject_scores.index],
        index=subject_scores.index,
    )
    family_scores = subject_scores.groupby(family_labels).mean()
    aggregate = family_scores.mean(axis=1)
    ranks = tie_aware_ranks(aggregate)
    return pd.DataFrame(
        {
            "model_family": family_scores.index.astype(str),
            "family_mean_accuracy": aggregate.to_numpy(dtype=float),
            "family_rank": ranks.to_numpy(dtype=float),
            "member_count": [int(family_labels.eq(family).sum()) for family in family_scores.index],
        }
    )


def leave_one_family_out_sensitivity(
    subject_scores: pd.DataFrame,
    model_families: Mapping[Any, str],
) -> pd.DataFrame:
    """Measure ranking stability among remaining models after dropping each family."""

    missing = [model for model in subject_scores.index if model not in model_families]
    if missing:
        raise ValueError(f"model_families is missing {len(missing)} model(s)")
    full_ranks = tie_aware_ranks(subject_scores.mean(axis=1))
    families = sorted({str(model_families[model]) for model in subject_scores.index})
    rows: list[dict[str, Any]] = []
    for family in families:
        remaining = [
            model for model in subject_scores.index if str(model_families[model]) != family
        ]
        if len(remaining) < 2:
            rows.append(
                {
                    "held_out_family": family,
                    "status": "BLOCKED",
                    "remaining_models": len(remaining),
                    "spearman_with_full_ranking": None,
                }
            )
            continue
        reduced = tie_aware_ranks(subject_scores.loc[remaining].mean(axis=1))
        rows.append(
            {
                "held_out_family": family,
                "status": "REPRODUCED",
                "remaining_models": len(remaining),
                "spearman_with_full_ranking": float(
                    full_ranks.loc[remaining].corr(reduced, method="spearman")
                ),
            }
        )
    return pd.DataFrame(rows)


def _model_rank_materiality(
    matrix: pd.DataFrame,
    subject_scores: pd.DataFrame,
    subject_ranks: pd.DataFrame,
) -> pd.DataFrame:
    aggregate_accuracy = matrix.mean(axis=1, skipna=True)
    aggregate_rank = tie_aware_ranks(aggregate_accuracy)
    rows: list[dict[str, Any]] = []
    denominator = max(matrix.shape[0] - 1, 1)
    for model_id in matrix.index:
        ranks = subject_ranks.loc[model_id]
        rows.append(
            {
                "model_id": str(model_id),
                "aggregate_accuracy": float(aggregate_accuracy.loc[model_id]),
                "aggregate_rank": float(aggregate_rank.loc[model_id]),
                "minimum_subject_rank": float(ranks.min()),
                "maximum_subject_rank": float(ranks.max()),
                "rank_range": float(ranks.max() - ranks.min()),
                "normalized_rank_range": float((ranks.max() - ranks.min()) / denominator),
                "rank_entropy": normalized_rank_entropy(ranks, matrix.shape[0]),
                "subject_accuracy_std": float(subject_scores.loc[model_id].std(ddof=0)),
            }
        )
    return pd.DataFrame(rows)


def _subject_rank_correlations(subject_ranks: pd.DataFrame) -> pd.DataFrame:
    correlations = subject_ranks.corr(method="spearman")
    rows: list[dict[str, Any]] = []
    for subject_a in correlations.index:
        for subject_b in correlations.columns:
            if str(subject_a) >= str(subject_b):
                continue
            rows.append(
                {
                    "subject_a": str(subject_a),
                    "subject_b": str(subject_b),
                    "spearman_rank_correlation": float(correlations.loc[subject_a, subject_b]),
                }
            )
    return pd.DataFrame(rows)


def analyze_rank_materiality(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
    *,
    n_bootstrap: int = 500,
    n_null_simulations: int = 500,
    null_method: str = "additive",
    seed: int = 2027,
    model_families: Mapping[Any, str] | None = None,
    practical_effect_threshold: float = 0.01,
) -> dict[str, Any]:
    """Run a deterministic, uncertainty-aware rank-materiality analysis."""

    frame = validate_binary_response_matrix(matrix)
    subjects = normalize_subject_ids(frame.columns, subject_ids)
    subject_counts = subjects.value_counts()
    blockers: list[str] = []
    if frame.shape[0] < 3:
        blockers.append("fewer_than_three_models")
    if subject_counts.shape[0] < 2:
        blockers.append("fewer_than_two_subjects")
    if (subject_counts < 2).any():
        blockers.append("subject_with_fewer_than_two_items")
    if blockers:
        return {
            "schema_version": "0.1",
            "status": "BLOCKED",
            "blockers": blockers,
            "empirical_metrics_computed": False,
            "claim_boundary": "Dependent rank-materiality claims remain blocked.",
        }

    scores = subject_accuracy_matrix(frame, subjects.to_dict())
    ranks = tie_aware_ranks(scores)
    model_summary = _model_rank_materiality(frame, scores, ranks)
    bootstrap = bootstrap_subject_ranks(
        frame, subjects.to_dict(), n_bootstrap=n_bootstrap, seed=seed
    )
    confidence_sets = rank_confidence_sets(bootstrap)
    outranking = pairwise_outranking_probabilities(bootstrap)
    top_k = top_k_membership_probabilities(
        bootstrap, top_ks=tuple(k for k in (1, 3, 5, 10) if k <= frame.shape[0])
    )
    nulls = simulate_rank_range_null(
        frame,
        subjects.to_dict(),
        method=null_method,
        n_simulations=n_null_simulations,
        seed=seed + 1,
    )
    ranges = subject_rank_ranges(frame, subjects.to_dict())
    null_comparison = compare_observed_rank_ranges_to_null(ranges, nulls)
    correlations = _subject_rank_correlations(ranks)
    composition_bootstrap = bootstrap_benchmark_composition_ranks(
        scores, n_bootstrap=n_bootstrap, seed=seed + 2
    )
    composition_confidence = (
        composition_bootstrap.groupby("model_id")["rank"]
        .agg(
            median_rank="median",
            lower_rank=lambda values: float(values.quantile(0.025)),
            upper_rank=lambda values: float(values.quantile(0.975)),
        )
        .reset_index()
    )
    top_k_jaccard = top_k_jaccard_stability(
        ranks, top_ks=tuple(k for k in (1, 3, 5, 10) if k <= frame.shape[0])
    )
    leave_subject_out = leave_one_subject_out_sensitivity(scores)
    practical_reversals = effect_size_filtered_reversals(
        scores, practical_effect_threshold=practical_effect_threshold
    )
    if model_families is None:
        family_analysis: dict[str, Any] = {
            "status": "BLOCKED",
            "blockers": ["exact_model_family_registry_not_supplied"],
            "family_deduplicated_ranking": [],
            "leave_one_family_out_sensitivity": [],
        }
    else:
        family_analysis = {
            "status": "REPRODUCED",
            "blockers": [],
            "family_deduplicated_ranking": family_deduplicated_ranking(
                scores, model_families
            ).to_dict(orient="records"),
            "leave_one_family_out_sensitivity": leave_one_family_out_sensitivity(
                scores, model_families
            ).to_dict(orient="records"),
        }
    return {
        "schema_version": "0.1",
        "status": "REPRODUCED",
        "analysis_name": "rank_materiality_v5",
        "n_models": int(frame.shape[0]),
        "n_items": int(frame.shape[1]),
        "n_subjects": int(subject_counts.shape[0]),
        "n_bootstrap": n_bootstrap,
        "n_null_simulations": n_null_simulations,
        "null_method": null_method,
        "seed": seed,
        "severity_threshold_used": False,
        "practical_effect_threshold": practical_effect_threshold,
        "kendalls_w": kendalls_w(ranks),
        "null_comparison": null_comparison,
        "model_rank_materiality": model_summary.to_dict(orient="records"),
        "rank_confidence_sets": confidence_sets.to_dict(orient="records"),
        "pairwise_outranking_probabilities": outranking.to_dict(orient="records"),
        "top_k_membership_probabilities": top_k.to_dict(orient="records"),
        "subject_rank_correlations": correlations.to_dict(orient="records"),
        "top_k_jaccard_stability": top_k_jaccard.to_dict(orient="records"),
        "leave_one_subject_out_sensitivity": leave_subject_out.to_dict(orient="records"),
        "benchmark_composition_rank_confidence": composition_confidence.to_dict(orient="records"),
        "effect_size_filtered_reversals": practical_reversals.to_dict(orient="records"),
        "family_analysis": family_analysis,
        "null_simulations": nulls.to_dict(orient="records"),
        "claim_boundary": (
            "Evidence is conditional on this response matrix, bootstrap, and null protocol; "
            "rank dispersion alone does not establish benchmark invalidity."
        ),
    }
