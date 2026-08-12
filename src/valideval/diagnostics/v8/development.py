from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from valideval.diagnostics.v8.difficulty import DifficultyAdjustedDetectorV8
from valideval.validation.confirmatory_v7 import (
    fixed_confirmatory_readout,
    generate_confirmatory_matrix,
)
from valideval.validation.detector_metrics import (
    expected_precision_at_k,
    precision_recall_auc,
    roc_auc,
)


def run_v8_exploratory_development(
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    detector = DifficultyAdjustedDetectorV8()
    _assert_label_isolated_api(detector)
    rows: list[dict[str, Any]] = []
    ablations: list[dict[str, Any]] = []
    for scenario, (flaw_class, severity, seed) in enumerate(
        (str(flaw), float(severity), int(seed))
        for flaw in config["flaw_classes"]
        for severity in config["severities"]
        for seed in config["seeds"]
    ):
        matrix, sealed = generate_confirmatory_matrix(
            flaw_class=flaw_class,
            severity=severity,
            prevalence=float(config["prevalence"]),
            model_count=int(config["model_count"]),
            family_count=int(config["family_count"]),
            item_count=int(config["item_count"]),
            subject_count=int(config["subject_count"]),
            dependence=float(config["dependence"]),
            seed=seed + scenario * 1009,
        )
        families = [
            f"family_{index % int(config['family_count'])}"
            for index in range(int(config["model_count"]))
        ]
        scores = detector.score_methods(matrix, model_families=families)
        scores["V7_FROZEN"] = fixed_confirmatory_readout(matrix)
        labels = sealed["sealed_is_flawed"].to_numpy(dtype=bool)
        for method, values in scores.items():
            if method in {
                "RAW_DIFFICULTY",
                "FAMILY_BALANCED_DIFFICULTY_ESTIMATE",
                "FAMILY_DISAGREEMENT",
            }:
                continue
            rows.append(
                _metric_row(
                    control="TRUE_FLAW",
                    flaw_class=flaw_class,
                    severity=severity,
                    seed=seed,
                    method=method,
                    labels=labels,
                    scores=values,
                )
            )
        for name, values in detector.ablation_scores(matrix, model_families=families).items():
            ablations.append(
                _metric_row(
                    control="TRUE_FLAW_ABLATION",
                    flaw_class=flaw_class,
                    severity=severity,
                    seed=seed,
                    method=name,
                    labels=labels,
                    scores=values,
                )
            )

    for seed_index, seed in enumerate(config["seeds"]):
        matrix, sealed = generate_confirmatory_matrix(
            flaw_class="NO_FLAW",
            severity=0.0,
            prevalence=float(config["prevalence"]),
            model_count=int(config["model_count"]),
            family_count=int(config["family_count"]),
            item_count=int(config["item_count"]),
            subject_count=int(config["subject_count"]),
            dependence=float(config["dependence"]),
            seed=int(seed) + 900_000 + seed_index,
        )
        families = [
            f"family_{index % int(config['family_count'])}"
            for index in range(int(config["model_count"]))
        ]
        scores = detector.score_methods(matrix, model_families=families)
        scores["V7_FROZEN"] = fixed_confirmatory_readout(matrix)
        cutoff = float(sealed["true_difficulty"].quantile(1.0 - float(config["prevalence"])))
        difficulty_labels = sealed["true_difficulty"].to_numpy(dtype=float) >= cutoff
        for method, values in scores.items():
            if method in {
                "RAW_DIFFICULTY",
                "FAMILY_BALANCED_DIFFICULTY_ESTIMATE",
                "FAMILY_DISAGREEMENT",
            }:
                continue
            rows.append(
                _metric_row(
                    control="DIFFICULTY_CONDITIONED_NEGATIVE_CONTROL",
                    flaw_class="NO_FLAW_DIFFICULTY_LABEL_ONLY",
                    severity=0.0,
                    seed=int(seed),
                    method=method,
                    labels=difficulty_labels,
                    scores=values,
                )
            )

    metrics = pd.DataFrame(rows).sort_values(
        ["control", "flaw_class", "severity", "seed", "method"]
    )
    ablation_frame = pd.DataFrame(ablations).sort_values(
        ["flaw_class", "severity", "seed", "method"]
    )
    difficulty = metrics.loc[metrics["control"] == "DIFFICULTY_CONDITIONED_NEGATIVE_CONTROL"]
    true_flaw = metrics.loc[metrics["control"] == "TRUE_FLAW"]
    baseline_difficulty = float(difficulty.loc[difficulty["method"] == "V7_FROZEN", "AUPRC"].mean())
    v8_difficulty = float(difficulty.loc[difficulty["method"] == "V8_FULL", "AUPRC"].mean())
    baseline_flaw = float(true_flaw.loc[true_flaw["method"] == "V7_FROZEN", "AUPRC"].median())
    v8_flaw = float(true_flaw.loc[true_flaw["method"] == "V8_FULL", "AUPRC"].median())
    gate = config["development_gate"]
    confound_reduced = baseline_difficulty - v8_difficulty >= float(
        gate["difficulty_negative_auprc_reduction_minimum"]
    )
    signal_retained = v8_flaw >= (
        baseline_flaw * float(gate["true_flaw_median_auprc_retention_minimum"])
    )
    passed = confound_reduced and signal_retained
    normalized = metrics.round(12).to_dict(orient="records")
    summary = {
        "status": (
            "V8_EXPLORATORY_DEVELOPMENT_GATE_PASS"
            if passed
            else "V8_EXPLORATORY_DEVELOPMENT_GATE_FAIL"
        ),
        "evidence_role": "EXPLORATORY_DEVELOPMENT_ONLY",
        "v7_primary_status": "V7_SYNTHETIC_PRIMARY_GRID_FAILED_AND_PRESERVED",
        "historical_v7_1_difficulty_negative_auprc": 0.439069,
        "development_v7_frozen_difficulty_negative_auprc": baseline_difficulty,
        "development_v8_full_difficulty_negative_auprc": v8_difficulty,
        "difficulty_negative_auprc_reduction": baseline_difficulty - v8_difficulty,
        "development_v7_frozen_true_flaw_median_auprc": baseline_flaw,
        "development_v8_full_true_flaw_median_auprc": v8_flaw,
        "true_flaw_auprc_retention": v8_flaw / baseline_flaw if baseline_flaw else None,
        "difficulty_confound_reduced": confound_reduced,
        "true_flaw_signal_retained": signal_retained,
        "label_isolation": "PASS",
        "v8_confirmatory_status": "NOT_RUN_NOT_AUTHORIZED_IN_V7_2",
        "normalized_metrics_sha256": hashlib.sha256(
            json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "claim_boundary": (
            "V8 is exploratory development only. Passing this gate does not repair the frozen "
            "V7 failure or license V8 findings on MMLU."
        ),
    }
    return metrics, ablation_frame, summary


def _assert_label_isolated_api(detector: DifficultyAdjustedDetectorV8) -> None:
    forbidden = {"label", "labels", "truth", "sealed", "is_flawed", "flaw_class"}
    for method_name in ("score_methods", "ablation_scores"):
        parameters = set(inspect.signature(getattr(detector, method_name)).parameters)
        if parameters.intersection(forbidden):
            raise ValueError(f"V8 scoring API exposes sealed-label field: {method_name}")


def _metric_row(
    *,
    control: str,
    flaw_class: str,
    severity: float,
    seed: int,
    method: str,
    labels: np.ndarray,
    scores: np.ndarray,
) -> dict[str, Any]:
    positives = int(labels.sum())
    return {
        "control": control,
        "flaw_class": flaw_class,
        "severity": severity,
        "seed": seed,
        "method": method,
        "positive_count": positives,
        "AUPRC": precision_recall_auc(labels.tolist(), scores.tolist()),
        "AUROC": roc_auc(labels.tolist(), scores.tolist()),
        "precision_at_k": expected_precision_at_k(
            labels.tolist(), scores.tolist(), max(positives, 1)
        ),
        "interpretation": "EXPLORATORY_DEVELOPMENT_NOT_CONFIRMATORY_EVIDENCE",
    }
