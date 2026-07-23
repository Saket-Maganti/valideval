from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import spearmanr

from valideval.statistics.rank_nulls import (
    normalize_subject_ids,
    validate_binary_response_matrix,
)

METHOD_NAME = "regularized_subject_conditioned_logit_decomposition"


def _smoothed_logit(successes: float, observations: float, smoothing: float) -> float:
    probability = (successes + smoothing) / (observations + 2.0 * smoothing)
    return float(logit(np.clip(probability, 1e-8, 1.0 - 1e-8)))


def check_measurement_assumptions(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
    *,
    model_families: Mapping[Any, str] | None = None,
    min_models: int = 8,
    min_items: int = 40,
    min_subjects: int = 2,
    min_items_per_subject: int = 5,
    max_missing_fraction: float = 0.10,
    min_ability_spread: float = 0.05,
    max_family_fraction: float = 0.50,
) -> dict[str, Any]:
    """Evaluate explicit adequacy assumptions without claiming psychometric validity."""

    frame = validate_binary_response_matrix(matrix)
    subjects = normalize_subject_ids(frame.columns, subject_ids)
    blockers: list[str] = []
    warnings: list[str] = []
    n_models, n_items = frame.shape
    subject_counts = subjects.value_counts()
    missing_fraction = float(frame.isna().to_numpy().mean())
    model_accuracy = frame.mean(axis=1, skipna=True)
    ability_spread = float(model_accuracy.max() - model_accuracy.min())
    if n_models < min_models:
        blockers.append(f"model_count_below_{min_models}")
    if n_items < min_items:
        blockers.append(f"item_count_below_{min_items}")
    if subject_counts.shape[0] < min_subjects:
        blockers.append(f"subject_count_below_{min_subjects}")
    if (subject_counts < min_items_per_subject).any():
        blockers.append(f"subject_item_count_below_{min_items_per_subject}")
    if missing_fraction > max_missing_fraction:
        blockers.append("missingness_too_high")
    if ability_spread < min_ability_spread:
        blockers.append("ability_spread_too_narrow")
    saturated_models = int(((model_accuracy <= 0.01) | (model_accuracy >= 0.99)).sum())
    if saturated_models:
        warnings.append(f"{saturated_models} model(s) are near floor or ceiling.")
    family_summary: dict[str, Any] | None = None
    if model_families is not None:
        missing_models = [model for model in frame.index if model not in model_families]
        if missing_models:
            blockers.append("model_family_mapping_incomplete")
        else:
            counts = Counter(str(model_families[model]) for model in frame.index)
            largest_fraction = max(counts.values()) / n_models
            family_summary = {
                "n_families": len(counts),
                "family_counts": dict(sorted(counts.items())),
                "largest_family_fraction": largest_fraction,
            }
            if largest_fraction > max_family_fraction:
                blockers.append("model_family_concentration_too_high")
    return {
        "schema_version": "0.1",
        "diagnostic_name": "measurement_model_assumptions_v5",
        "status": "pass" if not blockers else "blocked",
        "n_models": n_models,
        "n_items": n_items,
        "n_subjects": int(subject_counts.shape[0]),
        "subject_item_counts": {str(k): int(v) for k, v in subject_counts.items()},
        "missing_fraction": missing_fraction,
        "ability_spread": ability_spread,
        "saturated_model_count": saturated_models,
        "family_summary": family_summary,
        "blockers": blockers,
        "warnings": warnings,
        "exploratory_measurement_analysis_permitted": not blockers,
        "psychometric_validity_established": False,
        "full_parametric_2pl_identified": False,
        "interpretation": (
            "Passing these minimum assumptions permits this exploratory regularized model; it "
            "does not validate unidimensionality, local independence, invariance, or construct validity."
        ),
    }


def fit_hierarchical_subject_model(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
    *,
    model_families: Mapping[Any, str] | None = None,
    interaction_shrinkage: float = 10.0,
    smoothing: float = 0.5,
    assumption_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fit a closed-form regularized subject-conditioned logistic decomposition.

    This is a transparent exploratory measurement model, not a full mixed-effects
    likelihood fit, Bayesian hierarchical model, Rasch model, or 2PL model.
    """

    frame = validate_binary_response_matrix(matrix)
    subjects = normalize_subject_ids(frame.columns, subject_ids)
    if interaction_shrinkage <= 0 or smoothing <= 0:
        raise ValueError("interaction_shrinkage and smoothing must be positive")
    assumptions = check_measurement_assumptions(
        frame,
        subjects.to_dict(),
        model_families=model_families,
        **dict(assumption_overrides or {}),
    )
    base_payload: dict[str, Any] = {
        "schema_version": "0.1",
        "method": METHOD_NAME,
        "model_class": "exploratory_regularized_logit_decomposition",
        "full_parametric_2pl": False,
        "assumption_check": assumptions,
        "claim_boundary": (
            "Parameters summarize this matrix under a regularized additive-plus-interaction "
            "decomposition. They do not establish latent-trait validity or causal subject effects."
        ),
    }
    if assumptions["status"] != "pass":
        return {
            **base_payload,
            "status": "BLOCKED",
            "converged": False,
            "parameters_computed": False,
            "blockers": assumptions["blockers"],
        }

    observed = frame.notna().astype(float)
    successes = frame.fillna(0.0)
    total_successes = float(successes.to_numpy().sum())
    total_observations = float(observed.to_numpy().sum())
    intercept = _smoothed_logit(total_successes, total_observations, smoothing)

    raw_model_logits = pd.Series(
        {
            model: _smoothed_logit(
                float(successes.loc[model].sum()), float(observed.loc[model].sum()), smoothing
            )
            for model in frame.index
        }
    )
    model_effects = raw_model_logits - raw_model_logits.mean()
    raw_subject_logits = pd.Series(
        {
            subject: _smoothed_logit(
                float(successes.loc[:, subjects.eq(subject).to_numpy()].to_numpy().sum()),
                float(observed.loc[:, subjects.eq(subject).to_numpy()].to_numpy().sum()),
                smoothing,
            )
            for subject in sorted(subjects.unique())
        }
    )
    subject_effects = raw_subject_logits - raw_subject_logits.mean()

    model_rows: list[dict[str, Any]] = []
    for model in frame.index:
        n = float(observed.loc[model].sum())
        probability = float((successes.loc[model].sum() + smoothing) / (n + 2 * smoothing))
        standard_error = math.sqrt(1.0 / max(n * probability * (1.0 - probability), 1e-8))
        model_rows.append(
            {
                "model_id": str(model),
                "ability_logit": float(intercept + model_effects.loc[model]),
                "centered_model_effect": float(model_effects.loc[model]),
                "standard_error_approx": standard_error,
                "n_observed": int(n),
                "model_family": (
                    str(model_families[model]) if model_families is not None else None
                ),
            }
        )

    subject_rows: list[dict[str, Any]] = []
    interaction_rows: list[dict[str, Any]] = []
    predicted = pd.DataFrame(index=frame.index, columns=frame.columns, dtype=float)
    additive_predicted = pd.DataFrame(index=frame.index, columns=frame.columns, dtype=float)
    for subject in sorted(subjects.unique()):
        subject_item_ids = subjects.index[subjects.eq(subject)]
        n_subject = float(observed.loc[:, subject_item_ids].to_numpy().sum())
        subject_rows.append(
            {
                "subject_id": str(subject),
                "centered_subject_easiness": float(subject_effects.loc[subject]),
                "difficulty_logit": float(-subject_effects.loc[subject]),
                "n_observed": int(n_subject),
                "n_items": int(len(subject_item_ids)),
            }
        )
        for model in frame.index:
            model_values = frame.loc[model, subject_item_ids]
            n_cell = int(model_values.notna().sum())
            successes_cell = float(model_values.sum(skipna=True))
            baseline_eta = float(
                intercept + model_effects.loc[model] + subject_effects.loc[subject]
            )
            cell_eta = _smoothed_logit(successes_cell, n_cell, smoothing)
            raw_interaction = cell_eta - baseline_eta
            shrinkage_weight = n_cell / (n_cell + interaction_shrinkage)
            interaction = raw_interaction * shrinkage_weight
            probability = float(expit(baseline_eta + interaction))
            predicted.loc[model, subject_item_ids] = probability
            additive_predicted.loc[model, subject_item_ids] = float(expit(baseline_eta))
            interaction_rows.append(
                {
                    "model_id": str(model),
                    "subject_id": str(subject),
                    "n_observed": n_cell,
                    "observed_accuracy": successes_cell / n_cell if n_cell else None,
                    "raw_interaction_logit": float(raw_interaction),
                    "shrinkage_weight": float(shrinkage_weight),
                    "regularized_interaction_logit": float(interaction),
                    "predicted_probability": probability,
                }
            )

    mask = frame.notna().to_numpy()
    observed_values = frame.to_numpy()[mask]
    predicted_values = np.clip(predicted.to_numpy()[mask], 1e-8, 1.0 - 1e-8)
    brier = float(np.square(observed_values - predicted_values).mean())
    log_loss = float(
        -np.mean(
            observed_values * np.log(predicted_values)
            + (1.0 - observed_values) * np.log(1.0 - predicted_values)
        )
    )
    additive_values = np.clip(additive_predicted.to_numpy()[mask], 1e-8, 1.0 - 1e-8)
    additive_brier = float(np.square(observed_values - additive_values).mean())
    additive_log_loss = float(
        -np.mean(
            observed_values * np.log(additive_values)
            + (1.0 - observed_values) * np.log(1.0 - additive_values)
        )
    )
    family_ability_summary: list[dict[str, Any]] = []
    if model_families is not None:
        parameter_frame = pd.DataFrame(model_rows)
        family_ability_summary = (
            parameter_frame.groupby("model_family")["centered_model_effect"]
            .agg(["mean", "std", "count"])
            .reset_index()
            .fillna({"std": 0.0})
            .to_dict(orient="records")
        )
    return {
        **base_payload,
        "status": "REPRODUCED",
        "converged": True,
        "convergence_method": "closed_form_no_iteration",
        "parameters_computed": True,
        "interaction_shrinkage": interaction_shrinkage,
        "smoothing": smoothing,
        "global_intercept": intercept,
        "identifiability_constraints": {
            "mean_centered_model_effect": float(model_effects.mean()),
            "mean_centered_subject_effect": float(subject_effects.mean()),
        },
        "fit_summary": {
            "brier_score": brier,
            "log_loss": log_loss,
            "additive_baseline_brier_score": additive_brier,
            "additive_baseline_log_loss": additive_log_loss,
            "brier_improvement_over_additive": additive_brier - brier,
            "log_loss_improvement_over_additive": additive_log_loss - log_loss,
        },
        "model_parameters": model_rows,
        "subject_parameters": subject_rows,
        "model_subject_interactions": interaction_rows,
        "family_ability_summary": family_ability_summary,
    }


def panel_size_sensitivity(
    matrix: pd.DataFrame,
    subject_ids: Sequence[str] | Mapping[Any, str],
    *,
    panel_sizes: Sequence[int],
    n_repeats: int = 20,
    seed: int = 2027,
    interaction_shrinkage: float = 10.0,
    assumption_overrides: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    """Compare recovered ability ordering across seeded panel-size subsets."""

    frame = validate_binary_response_matrix(matrix)
    subjects = normalize_subject_ids(frame.columns, subject_ids)
    if not panel_sizes or any(size < 3 or size > frame.shape[0] for size in panel_sizes):
        raise ValueError("panel_sizes must lie between 3 and the available model count")
    if n_repeats <= 0:
        raise ValueError("n_repeats must be positive")
    shared_overrides = {
        "min_models": 3,
        "min_items": 2,
        "min_subjects": 2,
        "min_items_per_subject": 1,
        **dict(assumption_overrides or {}),
    }
    full = fit_hierarchical_subject_model(
        frame,
        subjects.to_dict(),
        interaction_shrinkage=interaction_shrinkage,
        assumption_overrides=shared_overrides,
    )
    if full["status"] != "REPRODUCED":
        raise ValueError(f"full panel failed assumption gate: {full.get('blockers', [])}")
    full_ability = pd.Series(
        {row["model_id"]: row["centered_model_effect"] for row in full["model_parameters"]}
    )
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for panel_size in sorted(set(panel_sizes)):
        for repeat in range(n_repeats):
            selected = rng.choice(frame.index.to_numpy(), size=panel_size, replace=False)
            subset = fit_hierarchical_subject_model(
                frame.loc[selected],
                subjects.to_dict(),
                interaction_shrinkage=interaction_shrinkage,
                assumption_overrides=shared_overrides,
            )
            if subset["status"] != "REPRODUCED":
                rows.append(
                    {
                        "panel_size": panel_size,
                        "repeat": repeat,
                        "status": "BLOCKED",
                        "ability_spearman_with_full": None,
                    }
                )
                continue
            subset_ability = pd.Series(
                {
                    row["model_id"]: row["centered_model_effect"]
                    for row in subset["model_parameters"]
                }
            )
            rows.append(
                {
                    "panel_size": panel_size,
                    "repeat": repeat,
                    "status": "REPRODUCED",
                    "ability_spearman_with_full": float(
                        full_ability.loc[subset_ability.index].corr(
                            subset_ability, method="spearman"
                        )
                    ),
                }
            )
    return pd.DataFrame(rows)


def synthetic_recovery_check(
    *,
    n_models: int = 16,
    n_subjects: int = 4,
    items_per_subject: int = 40,
    seed: int = 2027,
) -> dict[str, Any]:
    """Run a deterministic non-evidence recovery fixture for the model implementation."""

    if n_models < 8 or n_subjects < 2 or items_per_subject < 10:
        raise ValueError("recovery fixture needs >=8 models, >=2 subjects, and >=10 items/subject")
    rng = np.random.default_rng(seed)
    true_ability = np.linspace(-1.5, 1.5, n_models)
    true_subject_easiness = np.linspace(-0.8, 0.8, n_subjects)
    subject_labels = [
        f"s{subject}" for subject in range(n_subjects) for _ in range(items_per_subject)
    ]
    values = np.empty((n_models, len(subject_labels)), dtype=float)
    for model_index in range(n_models):
        for item_index, subject in enumerate(subject_labels):
            subject_index = int(subject[1:])
            probability = expit(true_ability[model_index] + true_subject_easiness[subject_index])
            values[model_index, item_index] = rng.binomial(1, probability)
    frame = pd.DataFrame(
        values,
        index=[f"m{index}" for index in range(n_models)],
        columns=[f"i{index}" for index in range(len(subject_labels))],
    )
    result = fit_hierarchical_subject_model(
        frame,
        subject_labels,
        assumption_overrides={
            "min_models": 8,
            "min_items": 40,
            "min_items_per_subject": 10,
        },
    )
    if result["status"] != "REPRODUCED":
        return {
            "status": "BLOCKED",
            "evidence_status": "NON_EVIDENCE_FIXTURE",
            "blockers": result.get("blockers", []),
        }
    recovered_ability = [row["centered_model_effect"] for row in result["model_parameters"]]
    recovered_subject = [row["centered_subject_easiness"] for row in result["subject_parameters"]]
    ability_correlation = float(spearmanr(true_ability, recovered_ability).statistic)
    subject_correlation = float(spearmanr(true_subject_easiness, recovered_subject).statistic)
    return {
        "status": "PASS" if ability_correlation >= 0.8 and subject_correlation >= 0.8 else "FAIL",
        "evidence_status": "NON_EVIDENCE_FIXTURE",
        "seed": seed,
        "ability_spearman": ability_correlation,
        "subject_easiness_spearman": subject_correlation,
        "claim_boundary": "Synthetic recovery checks implementation behavior only.",
    }
