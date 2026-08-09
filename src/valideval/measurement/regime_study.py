from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import spearmanr

ABILITY_DISTRIBUTIONS = (
    "gaussian",
    "skewed",
    "multimodal",
    "family_clustered",
    "heavy_tailed",
)


def simulate_measurement_regime(
    *,
    model_count: int,
    family_count: int,
    item_count: int,
    subject_count: int,
    ability_distribution: str = "gaussian",
    family_correlation: float = 0.4,
    latent_dimensions: int = 1,
    missingness: float = 0.0,
    saturation: float = 0.0,
    seed: int = 2027,
) -> tuple[pd.DataFrame, list[str], dict[str, Any]]:
    if ability_distribution not in ABILITY_DISTRIBUTIONS:
        raise ValueError(f"unknown ability distribution: {ability_distribution}")
    if min(model_count, family_count, item_count, subject_count, latent_dimensions) <= 0:
        raise ValueError("regime counts must be positive")
    if family_count > model_count or subject_count > item_count:
        raise ValueError("families cannot exceed models and subjects cannot exceed items")
    if not 0.0 <= family_correlation < 1.0 or not 0.0 <= missingness < 0.9:
        raise ValueError("family_correlation and missingness are outside supported ranges")
    rng = np.random.default_rng(seed)
    families = np.arange(model_count) % family_count
    family_latent = rng.normal(size=(family_count, latent_dimensions))
    individual = _ability_draws(rng, model_count, latent_dimensions, ability_distribution)
    ability = (
        np.sqrt(family_correlation) * family_latent[families]
        + np.sqrt(1.0 - family_correlation) * individual
    )
    subjects = np.arange(item_count) % subject_count
    item_loading = rng.normal(size=(item_count, latent_dimensions))
    item_loading /= np.maximum(np.linalg.norm(item_loading, axis=1, keepdims=True), 1e-8)
    difficulty = rng.normal(0.0, 0.9, size=item_count)
    if saturation > 0.0:
        difficulty -= float(saturation) * 2.5
    logits = ability @ item_loading.T - difficulty[None, :]
    probabilities = expit(logits)
    responses = rng.binomial(1, probabilities).astype(float)
    if missingness > 0.0:
        responses[rng.random(responses.shape) < missingness] = np.nan
    columns = [f"s{subjects[index]}::i{index}" for index in range(item_count)]
    matrix = pd.DataFrame(
        responses,
        index=[f"m{index}" for index in range(model_count)],
        columns=columns,
    )
    truth = {
        "true_scalar_ability": ability.mean(axis=1).tolist(),
        "true_ability": ability.tolist(),
        "true_difficulty": difficulty.tolist(),
        "model_families": {f"m{index}": f"f{families[index]}" for index in range(model_count)},
        "parameters": {
            "model_count": model_count,
            "family_count": family_count,
            "item_count": item_count,
            "subject_count": subject_count,
            "ability_distribution": ability_distribution,
            "family_correlation": family_correlation,
            "latent_dimensions": latent_dimensions,
            "missingness": missingness,
            "saturation": saturation,
            "seed": seed,
        },
    }
    return matrix, [f"s{value}" for value in subjects], truth


def evaluate_measurement_regime(
    matrix: pd.DataFrame,
    subjects: Sequence[str],
    truth: dict[str, Any],
    *,
    holdout_fraction: float = 0.2,
    seed: int = 2027,
) -> dict[str, Any]:
    """Grouped cell holdout comparison for aggregate, additive, subject, and low-rank models."""

    if len(subjects) != matrix.shape[1]:
        raise ValueError("subjects must have one entry per item")
    rng = np.random.default_rng(seed)
    values = matrix.to_numpy(dtype=float)
    train = values.copy()
    holdout = np.zeros(values.shape, dtype=bool)
    for model in range(values.shape[0]):
        available = np.flatnonzero(np.isfinite(values[model]))
        count = max(1, int(round(len(available) * holdout_fraction)))
        selected = rng.choice(available, size=count, replace=False)
        holdout[model, selected] = True
        train[model, selected] = np.nan
    aggregate = _aggregate_prediction(train)
    additive = _additive_prediction(train, subjects)
    subject_conditioned = _subject_conditioned_prediction(train, subjects, shrinkage=10.0)
    low_rank = _low_rank_prediction(train, rank=min(3, values.shape[0] - 1))
    metrics = {
        "aggregate_ability": _metrics(values[holdout], aggregate[holdout]),
        "additive_subject_difficulty": _metrics(values[holdout], additive[holdout]),
        "regularized_subject_conditioned": _metrics(values[holdout], subject_conditioned[holdout]),
        "low_rank_factor": _metrics(values[holdout], low_rank[holdout]),
    }
    recovered = np.nanmean(train, axis=1)
    true_ability = np.asarray(truth["true_scalar_ability"], dtype=float)
    recovery = float(spearmanr(true_ability, recovered).statistic)
    parameters = truth["parameters"]
    best = min(metrics, key=lambda name: metrics[name]["log_loss"])
    regime = _regime_class(
        model_count=int(parameters["model_count"]),
        family_count=int(parameters["family_count"]),
        latent_dimensions=int(parameters["latent_dimensions"]),
        rank_recovery=recovery,
        best_log_loss=float(metrics[best]["log_loss"]),
    )
    return {
        "status": "COMPLETE",
        "regime": regime,
        "best_predictive_model": best,
        "metrics": metrics,
        "parameter_recovery": {
            "ability_rank_spearman": recovery,
            "latent_parameter_claim_permitted": regime == "SUPPORTED",
        },
        "heldout_observations": int(holdout.sum()),
        "parameters": parameters,
        "claim_boundary": (
            "Simulation recovery supports estimator behavior only under the stated generator; "
            "it does not establish a latent trait in any real benchmark."
        ),
    }


def run_regime_study(
    *,
    model_counts: Sequence[int] = (5, 10, 20, 30, 40, 80, 120),
    seed: int = 2027,
) -> pd.DataFrame:
    scenarios: list[dict[str, Any]] = []
    for model_count in model_counts:
        scenarios.append(
            {
                "model_count": model_count,
                "family_count": min(max(2, model_count // 4), 12),
                "item_count": 600,
                "subject_count": 12,
                "ability_distribution": "gaussian",
                "family_correlation": 0.4,
                "latent_dimensions": 1,
                "missingness": 0.0,
                "saturation": 0.0,
            }
        )
    for distribution in ABILITY_DISTRIBUTIONS[1:]:
        scenarios.append({**scenarios[4], "ability_distribution": distribution})
    for latent_dimensions in (2, 4):
        scenarios.append({**scenarios[4], "latent_dimensions": latent_dimensions})
    for missingness in (0.1, 0.3):
        scenarios.append({**scenarios[4], "missingness": missingness})
    for saturation in (0.4, 0.8):
        scenarios.append({**scenarios[4], "saturation": saturation})
    for family_correlation in (0.0, 0.8):
        scenarios.append({**scenarios[4], "family_correlation": family_correlation})
    rows = []
    for index, scenario in enumerate(scenarios):
        matrix, subjects, truth = simulate_measurement_regime(**scenario, seed=seed + index)
        result = evaluate_measurement_regime(matrix, subjects, truth, seed=seed + 10_000 + index)
        rows.append(
            {
                "scenario": index,
                **scenario,
                "regime": result["regime"],
                "best_predictive_model": result["best_predictive_model"],
                "ability_rank_spearman": result["parameter_recovery"]["ability_rank_spearman"],
                **{
                    f"{model}_{metric}": value
                    for model, model_metrics in result["metrics"].items()
                    for metric, value in model_metrics.items()
                },
            }
        )
    return pd.DataFrame(rows)


def _ability_draws(
    rng: np.random.Generator,
    count: int,
    dimensions: int,
    distribution: str,
) -> np.ndarray:
    if distribution == "gaussian" or distribution == "family_clustered":
        return rng.normal(size=(count, dimensions))
    if distribution == "skewed":
        values = rng.lognormal(0.0, 0.7, size=(count, dimensions))
        return (values - values.mean(axis=0)) / values.std(axis=0)
    if distribution == "multimodal":
        modes = rng.choice([-1.2, 1.2], size=(count, 1))
        return rng.normal(modes, 0.45, size=(count, dimensions))
    return rng.standard_t(df=3, size=(count, dimensions)) / np.sqrt(3.0)


def _aggregate_prediction(train: np.ndarray) -> np.ndarray:
    model_rate = np.nanmean(train, axis=1)
    global_rate = float(np.nanmean(train))
    model_rate = np.where(np.isfinite(model_rate), model_rate, global_rate)
    return np.repeat(model_rate[:, None], train.shape[1], axis=1)


def _additive_prediction(train: np.ndarray, subjects: Sequence[str]) -> np.ndarray:
    aggregate = _aggregate_prediction(train)
    global_rate = float(np.clip(np.nanmean(train), 1e-5, 1.0 - 1e-5))
    model_eta = logit(np.clip(aggregate[:, 0], 1e-5, 1.0 - 1e-5))
    subject_values = np.asarray(subjects)
    output = np.empty(train.shape, dtype=float)
    for subject in sorted(set(subject_values.tolist())):
        columns = np.flatnonzero(subject_values == subject)
        subject_rate = float(np.clip(np.nanmean(train[:, columns]), 1e-5, 1.0 - 1e-5))
        output[:, columns] = expit(model_eta[:, None] + logit(subject_rate) - logit(global_rate))
    return output


def _subject_conditioned_prediction(
    train: np.ndarray,
    subjects: Sequence[str],
    *,
    shrinkage: float,
) -> np.ndarray:
    additive = _additive_prediction(train, subjects)
    subject_values = np.asarray(subjects)
    output = additive.copy()
    for subject in sorted(set(subject_values.tolist())):
        columns = np.flatnonzero(subject_values == subject)
        for model in range(train.shape[0]):
            observed = train[model, columns]
            count = int(np.isfinite(observed).sum())
            if count == 0:
                continue
            rate = float(np.clip((np.nansum(observed) + 0.5) / (count + 1.0), 1e-5, 1 - 1e-5))
            baseline = float(np.clip(additive[model, columns[0]], 1e-5, 1 - 1e-5))
            weight = count / (count + shrinkage)
            probability = expit(logit(baseline) + weight * (logit(rate) - logit(baseline)))
            output[model, columns] = probability
    return output


def _low_rank_prediction(train: np.ndarray, *, rank: int) -> np.ndarray:
    global_rate = float(np.nanmean(train))
    filled = np.where(np.isfinite(train), train, global_rate)
    observed = np.isfinite(train)
    for _ in range(10):
        row_mean = filled.mean(axis=1, keepdims=True)
        centered = filled - row_mean
        left, singular, right = np.linalg.svd(centered, full_matrices=False)
        reconstructed = row_mean + (left[:, :rank] * singular[:rank]) @ right[:rank]
        filled = np.where(observed, train, reconstructed)
    return np.clip(reconstructed, 1e-5, 1.0 - 1e-5)


def _metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    mask = np.isfinite(observed) & np.isfinite(predicted)
    actual = observed[mask]
    probability = np.clip(predicted[mask], 1e-8, 1.0 - 1e-8)
    return {
        "brier": float(np.mean((actual - probability) ** 2)),
        "log_loss": float(
            -np.mean(actual * np.log(probability) + (1.0 - actual) * np.log(1.0 - probability))
        ),
        "calibration_error": float(abs(np.mean(actual) - np.mean(probability))),
    }


def _regime_class(
    *,
    model_count: int,
    family_count: int,
    latent_dimensions: int,
    rank_recovery: float,
    best_log_loss: float,
) -> str:
    if model_count < max(8, 2 * latent_dimensions + 2) or family_count < 2:
        return "UNIDENTIFIABLE"
    if model_count >= 30 and family_count >= 5 and rank_recovery >= 0.80 and best_log_loss < 0.70:
        return "SUPPORTED"
    if model_count >= 20 and family_count >= 4 and rank_recovery >= 0.60:
        return "CAUTION"
    return "UNRELIABLE"
