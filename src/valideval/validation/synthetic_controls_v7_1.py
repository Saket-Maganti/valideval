from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit

from valideval.validation.confirmatory_v7 import (
    confirmatory_readout_components,
    fixed_confirmatory_readout,
    generate_confirmatory_matrix,
)
from valideval.validation.detector_metrics import (
    expected_precision_at_k,
    precision_recall_auc,
    roc_auc,
)

CONTROL_STUDY_ID = "V7_1_SYNTHETIC_CONTROL_COMPLETION"
REQUIRED_CONTROLS = {
    "LABEL_PERMUTATION",
    "NO_FLAW",
    "UNSEEN_FLAW",
    "HELD_OUT_GENERATOR_FAMILY",
    "MIXED_FLAWS",
    "DIAGNOSTIC_ABLATION",
    "FAMILY_DEPENDENCE_STRESS",
    "DIFFICULTY_CONDITIONED_NEGATIVE_CONTROL",
}


def run_synthetic_control_completion(
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute controls omitted from V7 without relabeling the frozen V7 result."""

    seeds = [int(seed) for seed in config.get("seeds", (3101, 3102, 3103))]
    model_count = int(config.get("model_count", 32))
    family_count = int(config.get("family_count", 8))
    item_count = int(config.get("item_count", 200))
    subject_count = int(config.get("subject_count", 10))
    prevalence = float(config.get("prevalence", 0.15))
    severity = float(config.get("severity", 0.6))
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        clean_matrix, clean_truth = generate_confirmatory_matrix(
            flaw_class="NO_FLAW",
            severity=severity,
            prevalence=prevalence,
            model_count=model_count,
            family_count=family_count,
            item_count=item_count,
            subject_count=subject_count,
            dependence=0.4,
            seed=seed,
        )
        clean_scores = fixed_confirmatory_readout(clean_matrix)
        rows.append(_metric_row("NO_FLAW", seed, clean_truth, clean_scores, "V7_GENERATOR"))

        flawed_matrix, flawed_truth = generate_confirmatory_matrix(
            flaw_class="LABEL_ERROR",
            severity=severity,
            prevalence=prevalence,
            model_count=model_count,
            family_count=family_count,
            item_count=item_count,
            subject_count=subject_count,
            dependence=0.4,
            seed=seed + 101,
        )
        flawed_scores = fixed_confirmatory_readout(flawed_matrix)
        rng = np.random.default_rng(seed + 102)
        permuted = flawed_truth.copy()
        permuted["sealed_is_flawed"] = rng.permutation(
            permuted["sealed_is_flawed"].to_numpy(dtype=bool)
        )
        rows.append(_metric_row("LABEL_PERMUTATION", seed, permuted, flawed_scores, "V7_GENERATOR"))

        unseen_matrix, unseen_truth = generate_confirmatory_matrix(
            flaw_class="CORRELATED_MODEL_FAILURE",
            severity=severity,
            prevalence=prevalence,
            model_count=model_count,
            family_count=family_count,
            item_count=item_count,
            subject_count=subject_count,
            dependence=0.65,
            seed=seed + 201,
        )
        rows.append(
            _metric_row(
                "UNSEEN_FLAW",
                seed,
                unseen_truth,
                fixed_confirmatory_readout(unseen_matrix),
                "V7_CORRELATED_FAILURE_HELD_OUT_CLASS",
            )
        )

        heldout_matrix, heldout_truth = _heldout_generator_family(
            model_count=model_count,
            family_count=family_count,
            item_count=item_count,
            subject_count=subject_count,
            prevalence=prevalence,
            severity=severity,
            seed=seed + 301,
        )
        rows.append(
            _metric_row(
                "HELD_OUT_GENERATOR_FAMILY",
                seed,
                heldout_truth,
                fixed_confirmatory_readout(heldout_matrix),
                "V7_1_HELDOUT_HEAVY_TAIL_GENERATOR",
            )
        )

        mixed_matrix, mixed_truth = _mixed_flaw_matrix(
            model_count=model_count,
            family_count=family_count,
            item_count=item_count,
            subject_count=subject_count,
            prevalence=prevalence,
            severity=severity,
            seed=seed + 401,
        )
        rows.append(
            _metric_row(
                "MIXED_FLAWS",
                seed,
                mixed_truth,
                fixed_confirmatory_readout(mixed_matrix),
                "V7_1_MIXED_MISSINGNESS_DUPLICATE",
            )
        )

        components = confirmatory_readout_components(flawed_matrix)
        for omitted in sorted(components):
            ablated = np.maximum.reduce(
                [values for name, values in components.items() if name != omitted]
            )
            row = _metric_row(
                "DIAGNOSTIC_ABLATION",
                seed,
                flawed_truth,
                ablated,
                "V7_READOUT_COMPONENT_ABLATION",
            )
            row["omitted_component"] = omitted
            rows.append(row)

        for dependence in (0.0, 0.4, 0.8, 0.95):
            dependence_matrix, dependence_truth = generate_confirmatory_matrix(
                flaw_class="LABEL_ERROR",
                severity=severity,
                prevalence=prevalence,
                model_count=model_count,
                family_count=family_count,
                item_count=item_count,
                subject_count=subject_count,
                dependence=dependence,
                seed=seed + 501 + int(dependence * 100),
            )
            row = _metric_row(
                "FAMILY_DEPENDENCE_STRESS",
                seed,
                dependence_truth,
                fixed_confirmatory_readout(dependence_matrix),
                "V7_GENERATOR",
            )
            row["family_dependence"] = dependence
            rows.append(row)

        difficulty_truth = clean_truth.copy()
        cutoff = float(difficulty_truth["true_difficulty"].quantile(1.0 - prevalence))
        difficulty_truth["sealed_is_flawed"] = (
            difficulty_truth["true_difficulty"] >= cutoff
        ).to_numpy(dtype=bool)
        rows.append(
            _metric_row(
                "DIFFICULTY_CONDITIONED_NEGATIVE_CONTROL",
                seed,
                difficulty_truth,
                clean_scores,
                "V7_GENERATOR_NO_FLAW_DIFFICULTY_LABEL_ONLY",
            )
        )
    result = pd.DataFrame(rows)
    normalized = result.sort_values(
        ["control", "seed", "generator_family", "omitted_component", "family_dependence"],
        na_position="last",
        kind="stable",
    ).reset_index(drop=True)
    result_hash = hashlib.sha256(
        json.dumps(
            _normalized_records(normalized), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()
    observed_controls = set(normalized["control"])
    summary = {
        "study_id": CONTROL_STUDY_ID,
        "status": (
            "V7_1_SYNTHETIC_CONTROL_SUITE_COMPLETE"
            if observed_controls == REQUIRED_CONTROLS
            else "V7_1_SYNTHETIC_CONTROL_SUITE_PARTIAL"
        ),
        "v7_primary_result": "V7_SYNTHETIC_PRIMARY_GRID_FAILED_AND_PRESERVED",
        "controls": sorted(observed_controls),
        "row_count": len(normalized),
        "deterministic_normalized_result_sha256": result_hash,
        "rounding_decimals_for_hash": 12,
        "claim_boundary": (
            "This V7.1 control-completion study does not alter, replace, or re-label the failed "
            "frozen V7 primary grid. Control metrics are generator-scoped observations."
        ),
    }
    return normalized, summary


def _metric_row(
    control: str,
    seed: int,
    truth: pd.DataFrame,
    scores: np.ndarray,
    generator_family: str,
) -> dict[str, Any]:
    labels = truth["sealed_is_flawed"].to_numpy(dtype=bool)
    positives = int(labels.sum())
    return {
        "study_id": CONTROL_STUDY_ID,
        "control": control,
        "seed": seed,
        "generator_family": generator_family,
        "positive_count": positives,
        "prevalence": float(labels.mean()),
        "AUPRC": precision_recall_auc(labels.tolist(), scores.tolist()),
        "AUROC": roc_auc(labels.tolist(), scores.tolist()),
        "precision_at_k": (
            expected_precision_at_k(labels.tolist(), scores.tolist(), positives)
            if positives
            else None
        ),
        "precision_at_k_tie_policy": "EXPECTED_RANDOM_BOUNDARY_TIE",
        "omitted_component": None,
        "family_dependence": None,
        "interpretation": "CONTROL_OBSERVATION_NOT_CONFIRMATORY_SUCCESS_GATE",
    }


def _heldout_generator_family(
    *,
    model_count: int,
    family_count: int,
    item_count: int,
    subject_count: int,
    prevalence: float,
    severity: float,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    families = np.arange(model_count) % family_count
    family_ability = rng.standard_t(df=4, size=family_count) * 0.7
    ability = family_ability[families] + rng.standard_t(df=5, size=model_count) * 0.4
    difficulty = np.log(rng.lognormal(0.0, 0.9, item_count))
    discrimination = rng.gamma(2.5, 0.4, item_count)
    probability = expit(discrimination[None, :] * (ability[:, None] - difficulty[None, :]))
    matrix = rng.binomial(1, probability).astype(float)
    count = max(1, int(round(prevalence * item_count)))
    flawed_indices = rng.choice(item_count, size=count, replace=False)
    flip = rng.random((model_count, count)) < severity
    matrix[:, flawed_indices] = np.where(
        flip, 1.0 - matrix[:, flawed_indices], matrix[:, flawed_indices]
    )
    subjects = np.arange(item_count) % subject_count
    columns = [f"subject_{subjects[index]}::item_{index}" for index in range(item_count)]
    labels = np.zeros(item_count, dtype=bool)
    labels[flawed_indices] = True
    return (
        pd.DataFrame(
            matrix, index=[f"model_{index}" for index in range(model_count)], columns=columns
        ),
        pd.DataFrame(
            {
                "item_id": columns,
                "sealed_is_flawed": labels,
                "sealed_flaw_class": np.where(labels, "HEAVY_TAIL_LABEL_ERROR", "NO_FLAW"),
                "true_difficulty": difficulty,
            }
        ),
    )


def _mixed_flaw_matrix(**kwargs: Any) -> tuple[pd.DataFrame, pd.DataFrame]:
    seed = int(kwargs["seed"])
    matrix, truth = generate_confirmatory_matrix(
        flaw_class="MISSINGNESS",
        severity=float(kwargs["severity"]),
        prevalence=float(kwargs["prevalence"]) / 2.0,
        model_count=int(kwargs["model_count"]),
        family_count=int(kwargs["family_count"]),
        item_count=int(kwargs["item_count"]),
        subject_count=int(kwargs["subject_count"]),
        dependence=0.4,
        seed=seed,
    )
    rng = np.random.default_rng(seed + 1)
    clean = np.flatnonzero(~truth["sealed_is_flawed"].to_numpy(dtype=bool))
    count = max(1, int(round(float(kwargs["prevalence"]) * len(truth) / 2.0)))
    targets = rng.choice(clean, size=min(count, len(clean)), replace=False)
    for target in targets:
        source = int(rng.integers(0, max(1, int(target))))
        matrix.iloc[:, int(target)] = matrix.iloc[:, source].to_numpy()
    truth.loc[targets, "sealed_is_flawed"] = True
    truth.loc[targets, "sealed_flaw_class"] = "DUPLICATE_ITEM"
    return matrix, truth


def _normalized_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw in frame.to_dict(orient="records"):
        row = {}
        for key, value in raw.items():
            if value is None or (isinstance(value, float) and np.isnan(value)):
                row[key] = None
            elif isinstance(value, float):
                row[key] = round(value, 12)
            else:
                row[key] = value
        records.append(row)
    return records
