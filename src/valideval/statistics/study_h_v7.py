from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.special import expit, logit

from valideval.statistics.rank_materiality import kendalls_w, tie_aware_ranks
from valideval.statistics.rank_nulls import (
    normalize_subject_ids,
    subject_accuracy_matrix,
    validate_binary_response_matrix,
)

NULL_SUITE = (
    "ADD_ABILITY_SUBJECT",
    "EMPIRICAL_BAYES_ADDITIVE",
    "SUBJECT_SIZE_ONLY",
    "FIXED_MARGIN_PERMUTATION",
    "FAMILY_CORRELATED_NULL",
    "LATENT_FACTOR_NULL",
    "MODEL_SUBJECT_RANDOM_EFFECT_NULL",
)


def nested_subject_item_bootstrap(
    matrix: pd.DataFrame,
    subjects: Sequence[str] | Mapping[str, str],
    *,
    n_bootstrap: int = 500,
    seed: int = 2027,
) -> pd.DataFrame:
    """Nested subject/item bootstrap returning equal-subject-weight model scores."""

    frame = validate_binary_response_matrix(matrix)
    subject_map = normalize_subject_ids(frame.columns, subjects)
    subject_names = np.asarray(sorted(subject_map.unique()))
    indices = {
        subject: np.flatnonzero(subject_map.to_numpy() == subject) for subject in subject_names
    }
    rng = np.random.default_rng(seed)
    values = frame.to_numpy(dtype=float)
    draws = np.empty((n_bootstrap, frame.shape[0]), dtype=float)
    for replicate in range(n_bootstrap):
        sampled_subjects = rng.choice(subject_names, size=len(subject_names), replace=True)
        subject_draws = []
        for subject in sampled_subjects:
            available = indices[str(subject)]
            sampled_items = rng.choice(available, size=len(available), replace=True)
            subject_draws.append(np.nanmean(values[:, sampled_items], axis=1))
        draws[replicate] = np.nanmean(np.column_stack(subject_draws), axis=1)
    return pd.DataFrame(draws, columns=frame.index.astype(str)).rename_axis("replicate")


def simulate_null_suite(
    matrix: pd.DataFrame,
    subjects: Sequence[str] | Mapping[str, str],
    model_families: Mapping[str, str],
    *,
    n_simulations: int = 200,
    seed: int = 2027,
) -> pd.DataFrame:
    """Calibrate rank dispersion under seven explicitly different subject-score nulls."""

    frame = validate_binary_response_matrix(matrix)
    subject_map = normalize_subject_ids(frame.columns, subjects)
    scores = subject_accuracy_matrix(frame, subject_map.to_dict())
    sizes = np.asarray([int(subject_map.eq(subject).sum()) for subject in scores.columns])
    families = pd.Series(
        [str(model_families[str(model)]) for model in scores.index], index=scores.index
    )
    probabilities = _null_probabilities(scores, sizes, families)
    rng = np.random.default_rng(seed)
    rows = []
    for method in NULL_SUITE:
        for simulation in range(n_simulations):
            if method == "FIXED_MARGIN_PERMUTATION":
                sampled_scores = np.empty(scores.shape, dtype=float)
                for model_index, model in enumerate(frame.index):
                    total_success = int(frame.loc[model].sum())
                    counts = rng.multivariate_hypergeometric(sizes, total_success)
                    sampled_scores[model_index] = counts / sizes
            else:
                probability = probabilities[method]
                counts = rng.binomial(sizes[None, :], probability)
                sampled_scores = counts / sizes[None, :]
            rank_frame = pd.DataFrame(sampled_scores, index=scores.index).rank(
                axis=0, ascending=False, method="average"
            )
            ranges = rank_frame.max(axis=1) - rank_frame.min(axis=1)
            rows.append(
                {
                    "method": method,
                    "simulation": simulation,
                    "median_rank_range": float(ranges.median()),
                    "maximum_rank_range": float(ranges.max()),
                    "kendalls_w": kendalls_w(rank_frame),
                    "evidence_role": "CALIBRATION_NULL",
                }
            )
    return pd.DataFrame(rows)


def null_suite_comparison(
    subject_scores: pd.DataFrame,
    simulations: pd.DataFrame,
) -> pd.DataFrame:
    observed_ranks = tie_aware_ranks(subject_scores)
    observed_ranges = observed_ranks.max(axis=1) - observed_ranks.min(axis=1)
    observed = {
        "median_rank_range": float(observed_ranges.median()),
        "maximum_rank_range": float(observed_ranges.max()),
        "kendalls_w": kendalls_w(observed_ranks),
    }
    rows = []
    for method, group in simulations.groupby("method", sort=True):
        count = len(group)
        rows.append(
            {
                "method": str(method),
                **{f"observed_{name}": value for name, value in observed.items()},
                "median_rank_range_exceedance": float(
                    (1 + (group["median_rank_range"] >= observed["median_rank_range"]).sum())
                    / (count + 1)
                ),
                "maximum_rank_range_exceedance": float(
                    (1 + (group["maximum_rank_range"] >= observed["maximum_rank_range"]).sum())
                    / (count + 1)
                ),
                "kendalls_w_lower_tail": float(
                    (1 + (group["kendalls_w"] <= observed["kendalls_w"]).sum()) / (count + 1)
                ),
                "simulations": count,
            }
        )
    return pd.DataFrame(rows)


def sensitivity_sweep(
    matrix: pd.DataFrame,
    subjects: Sequence[str] | Mapping[str, str],
    *,
    seed: int = 2027,
) -> pd.DataFrame:
    """One-factor-at-a-time panel/composition sensitivity with fixed deterministic subsets."""

    frame = validate_binary_response_matrix(matrix)
    subject_map = normalize_subject_ids(frame.columns, subjects)
    baseline_rank = frame.mean(axis=1).rank(ascending=False, method="average")
    rng = np.random.default_rng(seed)
    rows = []
    for model_count in (5, 10, 20, 30, frame.shape[0]):
        if model_count > frame.shape[0]:
            continue
        selected_models = rng.choice(frame.index, size=model_count, replace=False)
        selected = frame.loc[selected_models]
        rank = selected.mean(axis=1).rank(ascending=False, method="average")
        rows.append(
            {
                "dimension": "model_count",
                "value": model_count,
                "model_count": model_count,
                "subject_count": int(subject_map.nunique()),
                "item_count": frame.shape[1],
                "rank_spearman_with_full": float(
                    rank.corr(baseline_rank.loc[selected_models], method="spearman")
                ),
            }
        )
    subject_names = np.asarray(sorted(subject_map.unique()))
    for subject_count in (5, 10, 20, 40, len(subject_names)):
        if subject_count > len(subject_names):
            continue
        selected_subjects = rng.choice(subject_names, size=subject_count, replace=False)
        columns = subject_map.index[subject_map.isin(selected_subjects)]
        rank = frame.loc[:, columns].mean(axis=1).rank(ascending=False, method="average")
        rows.append(
            {
                "dimension": "subject_count",
                "value": subject_count,
                "model_count": frame.shape[0],
                "subject_count": subject_count,
                "item_count": len(columns),
                "rank_spearman_with_full": float(rank.corr(baseline_rank, method="spearman")),
            }
        )
    for item_count in (250, 500, 1000, 2500, 5000, 10000, frame.shape[1]):
        if item_count > frame.shape[1]:
            continue
        columns = rng.choice(frame.columns, size=item_count, replace=False)
        rank = frame.loc[:, columns].mean(axis=1).rank(ascending=False, method="average")
        rows.append(
            {
                "dimension": "item_count",
                "value": item_count,
                "model_count": frame.shape[0],
                "subject_count": int(subject_map.loc[columns].nunique()),
                "item_count": item_count,
                "rank_spearman_with_full": float(rank.corr(baseline_rank, method="spearman")),
            }
        )
    for removal_fraction in (0.01, 0.05, 0.10, 0.20, 0.40):
        retained = rng.choice(
            frame.columns,
            size=max(2, int(round(frame.shape[1] * (1.0 - removal_fraction)))),
            replace=False,
        )
        rank = frame.loc[:, retained].mean(axis=1).rank(ascending=False, method="average")
        rows.append(
            {
                "dimension": "random_item_removal",
                "value": removal_fraction,
                "model_count": frame.shape[0],
                "subject_count": int(subject_map.loc[retained].nunique()),
                "item_count": len(retained),
                "rank_spearman_with_full": float(rank.corr(baseline_rank, method="spearman")),
            }
        )
    return pd.DataFrame(rows)


def _null_probabilities(
    scores: pd.DataFrame,
    sizes: np.ndarray,
    families: pd.Series,
) -> dict[str, np.ndarray]:
    clipped = scores.clip(1e-5, 1.0 - 1e-5)
    global_rate = float(
        np.average(scores.to_numpy(), weights=np.repeat(sizes[None, :], len(scores), axis=0))
    )
    model_rate = np.average(scores.to_numpy(), axis=1, weights=sizes)
    subject_rate = scores.mean(axis=0).to_numpy(dtype=float)
    additive_eta = (
        logit(np.clip(model_rate, 1e-5, 1 - 1e-5))[:, None]
        + logit(np.clip(subject_rate, 1e-5, 1 - 1e-5))[None, :]
        - logit(np.clip(global_rate, 1e-5, 1 - 1e-5))
    )
    additive = expit(additive_eta)
    shrink = sizes / (sizes + 20.0)
    shrunk_subject = shrink * subject_rate + (1.0 - shrink) * global_rate
    eb = expit(
        logit(np.clip(model_rate, 1e-5, 1 - 1e-5))[:, None]
        + logit(np.clip(shrunk_subject, 1e-5, 1 - 1e-5))[None, :]
        - logit(np.clip(global_rate, 1e-5, 1 - 1e-5))
    )
    subject_size_only = np.repeat(model_rate[:, None], scores.shape[1], axis=1)
    residual = clipped.to_numpy(dtype=float) - additive
    family_residual = pd.DataFrame(residual, index=scores.index).groupby(families).mean()
    family_lookup = family_residual.loc[families].to_numpy(dtype=float)
    family_correlated = np.clip(additive + family_lookup, 1e-5, 1.0 - 1e-5)
    left, singular, right = np.linalg.svd(
        clipped.to_numpy(dtype=float) - global_rate, full_matrices=False
    )
    rank = min(2, len(singular))
    latent = np.clip(
        global_rate + (left[:, :rank] * singular[:rank]) @ right[:rank], 1e-5, 1 - 1e-5
    )
    residual_sd = float(np.std(logit(clipped.to_numpy(dtype=float)) - additive_eta))
    row_subject_effect = np.resize(
        np.linspace(-residual_sd, residual_sd, scores.size), scores.shape
    )
    random_effect = expit(additive_eta + row_subject_effect)
    return {
        "ADD_ABILITY_SUBJECT": additive,
        "EMPIRICAL_BAYES_ADDITIVE": eb,
        "SUBJECT_SIZE_ONLY": subject_size_only,
        "FAMILY_CORRELATED_NULL": family_correlated,
        "LATENT_FACTOR_NULL": latent,
        "MODEL_SUBJECT_RANDOM_EFFECT_NULL": random_effect,
    }
