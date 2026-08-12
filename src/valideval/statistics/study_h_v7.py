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
    "FIXED_PRIOR_SHRUNK_ADDITIVE",
    "SUBJECT_SIZE_ONLY",
    "MODEL_TOTAL_SUBJECT_SIZE_HYPERGEOMETRIC",
    "FAMILY_CORRELATED_NULL",
    "LATENT_FACTOR_NULL",
    "DETERMINISTIC_MODEL_SUBJECT_PERTURBATION_NULL",
)

NULL_MODEL_CONTRACTS = {
    "ADD_ABILITY_SUBJECT": {
        "fixed": "observed model and subject aggregate rates plus subject sample sizes",
        "randomized": "binomial subject-level success counts",
        "estimated": "additive logit model and subject effects",
        "hypothesis": "no model-by-subject interaction beyond additive ability and difficulty",
    },
    "FIXED_PRIOR_SHRUNK_ADDITIVE": {
        "fixed": "prior strength 20 and observed subject sample sizes",
        "randomized": "binomial subject-level success counts",
        "estimated": "model rates and fixed-prior shrunk subject rates",
        "hypothesis": "additive effects after prespecified shrinkage; not empirical Bayes",
    },
    "SUBJECT_SIZE_ONLY": {
        "fixed": "model aggregate rates and subject sample sizes",
        "randomized": "binomial subject-level success counts",
        "estimated": "model aggregate rates",
        "hypothesis": "no subject effect",
    },
    "MODEL_TOTAL_SUBJECT_SIZE_HYPERGEOMETRIC": {
        "fixed": "each model total successes and subject item counts",
        "randomized": "allocation of model successes across subject-size blocks",
        "estimated": "nothing beyond observed margins",
        "hypothesis": "responses are exchangeable across subjects within model",
    },
    "FAMILY_CORRELATED_NULL": {
        "fixed": "observed family membership",
        "randomized": "binomial counts from additive plus family residual probabilities",
        "estimated": "additive rates and family mean residuals",
        "hypothesis": "family-correlated deviations explain observed subject dispersion",
    },
    "LATENT_FACTOR_NULL": {
        "fixed": "rank-two latent approximation",
        "randomized": "binomial counts from latent probabilities",
        "estimated": "two singular components",
        "hypothesis": "low-rank model-subject structure explains dispersion",
    },
    "DETERMINISTIC_MODEL_SUBJECT_PERTURBATION_NULL": {
        "fixed": "deterministic perturbation grid scaled by observed residual spread",
        "randomized": "binomial counts from perturbed probabilities",
        "estimated": "residual spread only",
        "hypothesis": "structured perturbation sensitivity; not a random-effects model",
    },
}


def nested_subject_item_bootstrap(
    matrix: pd.DataFrame,
    subjects: Sequence[str] | Mapping[str, str],
    *,
    n_bootstrap: int = 500,
    seed: int = 2027,
    estimand: str = "BALANCED_SUBJECT_WEIGHTED",
) -> pd.DataFrame:
    """Nested bootstrap for one explicitly named MMLU score estimand."""

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
        subject_weights = []
        for subject in sampled_subjects:
            available = indices[str(subject)]
            sampled_items = rng.choice(available, size=len(available), replace=True)
            subject_draws.append(np.nanmean(values[:, sampled_items], axis=1))
            subject_weights.append(len(sampled_items))
        stacked = np.column_stack(subject_draws)
        if estimand == "BALANCED_SUBJECT_WEIGHTED":
            draws[replicate] = np.nanmean(stacked, axis=1)
        elif estimand == "CANONICAL_ITEM_WEIGHTED":
            draws[replicate] = np.average(stacked, axis=1, weights=subject_weights)
        else:
            raise ValueError(
                "estimand must be CANONICAL_ITEM_WEIGHTED or BALANCED_SUBJECT_WEIGHTED"
            )
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
            if method == "MODEL_TOTAL_SUBJECT_SIZE_HYPERGEOMETRIC":
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
    replicates: int = 100,
) -> pd.DataFrame:
    """Monte Carlo panel/composition sensitivity with uncertainty per grid point."""

    frame = validate_binary_response_matrix(matrix)
    subject_map = normalize_subject_ids(frame.columns, subjects)
    baseline_rank = frame.mean(axis=1).rank(ascending=False, method="average")
    if replicates < 2:
        raise ValueError("replicates must be at least two")
    rows = []

    def summarize(dimension: str, value: float | int, draws: list[float], **metadata: int):
        values = np.asarray(draws, dtype=float)
        rows.append(
            {
                "dimension": dimension,
                "value": value,
                **metadata,
                "replicates": replicates,
                "rank_spearman_mean": float(np.nanmean(values)),
                "rank_spearman_monte_carlo_se": float(
                    np.nanstd(values, ddof=1) / np.sqrt(np.isfinite(values).sum())
                ),
                "rank_spearman_q025": float(np.nanquantile(values, 0.025)),
                "rank_spearman_q975": float(np.nanquantile(values, 0.975)),
                "sweep_type": "STOCHASTIC_MONTE_CARLO",
            }
        )

    for model_count in (5, 10, 20, 30, frame.shape[0]):
        if model_count > frame.shape[0]:
            continue
        draws = []
        for replicate in range(replicates):
            rng = np.random.default_rng(seed + model_count * 10_000 + replicate)
            selected_models = rng.choice(frame.index, size=model_count, replace=False)
            rank = frame.loc[selected_models].mean(axis=1).rank(ascending=False, method="average")
            draws.append(float(rank.corr(baseline_rank.loc[selected_models], method="spearman")))
        summarize(
            "model_count",
            model_count,
            draws,
            model_count=model_count,
            subject_count=int(subject_map.nunique()),
            item_count=frame.shape[1],
        )
    subject_names = np.asarray(sorted(subject_map.unique()))
    for subject_count in (5, 10, 20, 40, len(subject_names)):
        if subject_count > len(subject_names):
            continue
        draws = []
        item_counts = []
        for replicate in range(replicates):
            rng = np.random.default_rng(seed + subject_count * 20_000 + replicate)
            selected_subjects = rng.choice(subject_names, size=subject_count, replace=False)
            columns = subject_map.index[subject_map.isin(selected_subjects)]
            rank = frame.loc[:, columns].mean(axis=1).rank(ascending=False, method="average")
            draws.append(float(rank.corr(baseline_rank, method="spearman")))
            item_counts.append(len(columns))
        summarize(
            "subject_count",
            subject_count,
            draws,
            model_count=frame.shape[0],
            subject_count=subject_count,
            item_count=int(round(np.mean(item_counts))),
        )
    for item_count in (250, 500, 1000, 2500, 5000, 10000, frame.shape[1]):
        if item_count > frame.shape[1]:
            continue
        draws = []
        subject_counts = []
        for replicate in range(replicates):
            rng = np.random.default_rng(seed + item_count * 30_000 + replicate)
            columns = rng.choice(frame.columns, size=item_count, replace=False)
            rank = frame.loc[:, columns].mean(axis=1).rank(ascending=False, method="average")
            draws.append(float(rank.corr(baseline_rank, method="spearman")))
            subject_counts.append(int(subject_map.loc[columns].nunique()))
        summarize(
            "item_count",
            item_count,
            draws,
            model_count=frame.shape[0],
            subject_count=int(round(np.mean(subject_counts))),
            item_count=item_count,
        )
    for removal_fraction in (0.01, 0.05, 0.10, 0.20, 0.40):
        retained_count = max(2, int(round(frame.shape[1] * (1.0 - removal_fraction))))
        draws = []
        for replicate in range(replicates):
            rng = np.random.default_rng(seed + int(removal_fraction * 1000) * 40_000 + replicate)
            retained = rng.choice(frame.columns, size=retained_count, replace=False)
            rank = frame.loc[:, retained].mean(axis=1).rank(ascending=False, method="average")
            draws.append(float(rank.corr(baseline_rank, method="spearman")))
        summarize(
            "random_item_removal",
            removal_fraction,
            draws,
            model_count=frame.shape[0],
            subject_count=int(subject_map.nunique()),
            item_count=retained_count,
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
        "FIXED_PRIOR_SHRUNK_ADDITIVE": eb,
        "SUBJECT_SIZE_ONLY": subject_size_only,
        "FAMILY_CORRELATED_NULL": family_correlated,
        "LATENT_FACTOR_NULL": latent,
        "DETERMINISTIC_MODEL_SUBJECT_PERTURBATION_NULL": random_effect,
    }
