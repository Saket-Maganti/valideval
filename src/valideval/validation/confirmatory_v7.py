from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit

from valideval.validation.detector_metrics import (
    expected_precision_at_k,
    precision_recall_auc,
    roc_auc,
)

FLAW_CLASSES = (
    "NO_FLAW",
    "LABEL_ERROR",
    "MULTIPLE_LABEL_ERRORS",
    "AMBIGUITY",
    "DISTRACTOR_FAILURE",
    "SUBJECT_MISASSIGNMENT",
    "DUPLICATE_ITEM",
    "MISSINGNESS",
    "CORRELATED_MODEL_FAILURE",
)


def generate_confirmatory_matrix(
    *,
    flaw_class: str,
    severity: float,
    prevalence: float,
    model_count: int,
    family_count: int,
    item_count: int,
    subject_count: int,
    dependence: float,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate responses and sealed truth; the detector receives only the first output."""

    if flaw_class not in FLAW_CLASSES:
        raise ValueError(f"unknown flaw class: {flaw_class}")
    if not all(0.0 <= value <= 1.0 for value in (severity, prevalence, dependence)):
        raise ValueError("severity, prevalence, and dependence must be in [0, 1]")
    rng = np.random.default_rng(seed)
    families = np.arange(model_count) % family_count
    family_ability = rng.normal(0.0, 0.8, family_count)
    ability = np.sqrt(dependence) * family_ability[families] + np.sqrt(
        1.0 - dependence
    ) * rng.normal(0.0, 1.0, model_count)
    subjects = np.arange(item_count) % subject_count
    difficulty = rng.normal(0.0, 1.0, item_count)
    discrimination = rng.lognormal(-0.05, 0.2, item_count)
    probabilities = expit(discrimination[None, :] * (ability[:, None] - difficulty[None, :]))
    matrix = rng.binomial(1, probabilities).astype(float)
    flawed = np.zeros(item_count, dtype=bool)
    if flaw_class != "NO_FLAW":
        count = max(1, int(round(prevalence * item_count)))
        flawed[rng.choice(item_count, size=count, replace=False)] = True
    observed_subjects = subjects.copy()
    if flaw_class == "LABEL_ERROR":
        flip = rng.random((model_count, item_count)) < severity
        matrix[:, flawed] = np.where(flip[:, flawed], 1.0 - matrix[:, flawed], matrix[:, flawed])
    elif flaw_class == "MULTIPLE_LABEL_ERRORS":
        flip_probability = min(1.0, 0.35 + 0.65 * severity)
        flip = rng.random((model_count, item_count)) < flip_probability
        matrix[:, flawed] = np.where(flip[:, flawed], 1.0 - matrix[:, flawed], matrix[:, flawed])
    elif flaw_class == "AMBIGUITY":
        ambiguous = rng.binomial(1, 0.5, size=(model_count, flawed.sum()))
        replace = rng.random(ambiguous.shape) < severity
        matrix[:, flawed] = np.where(replace, ambiguous, matrix[:, flawed])
    elif flaw_class == "DISTRACTOR_FAILURE":
        floor = 0.25 + 0.65 * severity
        replacement = rng.binomial(1, floor, size=(model_count, flawed.sum()))
        matrix[:, flawed] = replacement
    elif flaw_class == "SUBJECT_MISASSIGNMENT":
        offset = max(1, int(round(severity * (subject_count - 1))))
        observed_subjects[flawed] = (observed_subjects[flawed] + offset) % subject_count
    elif flaw_class == "DUPLICATE_ITEM":
        targets = np.flatnonzero(flawed)
        for target in targets:
            upper = max(int(target), 1)
            source = int(rng.integers(0, upper))
            matrix[:, target] = matrix[:, source]
    elif flaw_class == "MISSINGNESS":
        missing = rng.random((model_count, flawed.sum())) < max(severity, 0.05)
        block = matrix[:, flawed]
        block[missing] = np.nan
        matrix[:, flawed] = block
    elif flaw_class == "CORRELATED_MODEL_FAILURE":
        target_family = int(rng.integers(0, family_count))
        affected = families == target_family
        for item in np.flatnonzero(flawed):
            flip = rng.random(affected.sum()) < severity
            matrix[np.flatnonzero(affected)[flip], item] = 0.0
    frame = pd.DataFrame(
        matrix,
        index=[f"model_{index}" for index in range(model_count)],
        columns=[
            f"subject_{observed_subjects[index]}::item_{index}" for index in range(item_count)
        ],
    )
    metadata = pd.DataFrame(
        {
            "item_id": frame.columns,
            "sealed_is_flawed": flawed,
            "sealed_flaw_class": np.where(flawed, flaw_class, "NO_FLAW"),
            "true_subject": [f"subject_{value}" for value in subjects],
            "observed_subject": [f"subject_{value}" for value in observed_subjects],
            "true_difficulty": difficulty,
        }
    )
    return frame, metadata


def fixed_confirmatory_readout(matrix: pd.DataFrame) -> np.ndarray:
    """Frozen flaw-agnostic readout based only on observable response behavior."""

    return np.maximum.reduce(list(confirmatory_readout_components(matrix).values()))


def confirmatory_readout_components(matrix: pd.DataFrame) -> dict[str, np.ndarray]:
    """Return the unchanged V7 readout components for V7.1 ablation accounting."""

    values = matrix.to_numpy(dtype=float)
    missing = np.mean(~np.isfinite(values), axis=0)
    observed_count = np.sum(np.isfinite(values), axis=0)
    global_rate = float(np.nanmean(values))
    column_rate = np.divide(
        np.nansum(values, axis=0),
        observed_count,
        out=np.full(matrix.shape[1], global_rate),
        where=observed_count > 0,
    )
    filled = np.where(np.isfinite(values), values, column_rate[None, :])
    ability = np.nanmean(values, axis=1)
    correlations = np.zeros(matrix.shape[1], dtype=float)
    for item in range(matrix.shape[1]):
        if np.std(filled[:, item]) > 0.0 and np.std(ability) > 0.0:
            correlations[item] = np.corrcoef(filled[:, item], ability)[0, 1]
    negative_discrimination = np.clip(-correlations, 0.0, 1.0)
    centered_difficulty = np.abs(column_rate - 0.5) * 2.0
    duplicate = np.zeros(matrix.shape[1], dtype=float)
    signatures: dict[bytes, int] = {}
    for item in range(matrix.shape[1]):
        signature = np.nan_to_num(values[:, item], nan=-1.0).astype(np.int8).tobytes()
        if signature in signatures:
            duplicate[item] = 1.0
            duplicate[signatures[signature]] = 1.0
        else:
            signatures[signature] = item
    subject_names = np.asarray([str(column).split("::", 1)[0] for column in matrix.columns])
    subject_residual = np.zeros(matrix.shape[1], dtype=float)
    for subject in sorted(set(subject_names.tolist())):
        indices = np.flatnonzero(subject_names == subject)
        expected = float(np.mean(filled[:, indices]))
        subject_residual[indices] = np.abs(np.mean(filled[:, indices], axis=0) - expected)
    return {
        "missingness": missing,
        "duplicate": duplicate,
        "negative_discrimination": negative_discrimination,
        "centered_difficulty": centered_difficulty * 0.35,
        "subject_residual": np.clip(subject_residual * 2.0, 0.0, 1.0),
    }


def run_confirmatory_validation(config: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    required = {
        "seeds",
        "flaw_classes",
        "severities",
        "prevalences",
        "model_count",
        "family_count",
        "item_count",
        "subject_count",
        "dependence",
        "target_fdr",
    }
    if not required.issubset(config):
        raise ValueError(f"confirmatory config is missing {sorted(required - set(config))}")
    rows = []
    clean_scores = []
    scenario_outputs = []
    for scenario, (flaw_class, severity, prevalence, seed) in enumerate(
        (str(flaw), float(severity), float(prevalence), int(seed))
        for flaw in config["flaw_classes"]
        for severity in config["severities"]
        for prevalence in config["prevalences"]
        for seed in config["seeds"]
    ):
        matrix, sealed = generate_confirmatory_matrix(
            flaw_class=flaw_class,
            severity=severity,
            prevalence=prevalence,
            model_count=int(config["model_count"]),
            family_count=int(config["family_count"]),
            item_count=int(config["item_count"]),
            subject_count=int(config["subject_count"]),
            dependence=float(config["dependence"]),
            seed=seed + scenario * 1009,
        )
        scores = fixed_confirmatory_readout(matrix)
        labels = sealed["sealed_is_flawed"].to_numpy(dtype=bool)
        scenario_outputs.append((flaw_class, severity, prevalence, seed, labels, scores))
        if flaw_class == "NO_FLAW":
            clean_scores.extend(scores.tolist())
    target_fdr = float(config["target_fdr"])
    threshold = float(np.quantile(clean_scores, 1.0 - target_fdr))
    for flaw_class, severity, prevalence, seed, labels, scores in scenario_outputs:
        selected = scores >= threshold
        true_positive = int(np.sum(selected & labels))
        false_positive = int(np.sum(selected & ~labels))
        positive = int(labels.sum())
        discoveries = int(selected.sum())
        k = max(1, positive)
        rows.append(
            {
                "flaw_class": flaw_class,
                "severity": severity,
                "prevalence": prevalence,
                "seed": seed,
                "AUPRC": precision_recall_auc(labels.tolist(), scores.tolist()),
                "AUROC": roc_auc(labels.tolist(), scores.tolist()),
                "precision_at_k": expected_precision_at_k(labels.tolist(), scores.tolist(), k),
                "precision_at_k_tie_policy": "EXPECTED_RANDOM_BOUNDARY_TIE",
                "FDR": false_positive / discoveries if discoveries else 0.0,
                "recall_at_fixed_FDR": true_positive / positive if positive else None,
                "power": true_positive / positive if positive else None,
                "discoveries": discoveries,
                "threshold": threshold,
            }
        )
    results = pd.DataFrame(rows)
    flawed_results = results[results["flaw_class"] != "NO_FLAW"]
    summary = {
        "status": "SYNTHETIC_CONFIRMATORY_COMPLETE",
        "evidence_class": "CPU_SYNTHETIC_CONFIRMATORY",
        "scenario_count": len(results),
        "threshold_from_no_flaw_controls": threshold,
        "median_AUPRC": float(flawed_results["AUPRC"].median()),
        "median_precision_at_k": float(flawed_results["precision_at_k"].median()),
        "median_FDR": float(flawed_results["FDR"].median()),
        "median_power": float(flawed_results["power"].median()),
        "claim_boundary": (
            "These are results under a frozen synthetic generator/readout protocol, not evidence "
            "that the same flaw classes or effect sizes occur in real benchmarks."
        ),
    }
    return results, summary
