from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

from valideval.diagnostics.multiplicity import benjamini_hochberg
from valideval.diagnostics.v8.development import run_v8_exploratory_development
from valideval.diagnostics.v8.difficulty import (
    DifficultyAdjustedDetectorV8,
    exploratory_stratified_p_values,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exploratory V8 difficulty correction.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/diagnostics/v8_exploratory_development.yaml"),
    )
    parser.add_argument("--matrix", type=Path, default=Path("cache/mmlu/wide/matrix.csv"))
    parser.add_argument(
        "--families",
        type=Path,
        default=Path("configs/models/study_h_family_map_v5.csv"),
    )
    parser.add_argument("--output", type=Path, default=Path("results/v7_2/v8"))
    args = parser.parse_args()
    started = time.perf_counter()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    metrics, ablations, summary = run_v8_exploratory_development(config)
    args.output.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.output / "synthetic_development_metrics.csv", index=False)
    ablations.to_csv(args.output / "synthetic_ablation_metrics.csv", index=False)

    matrix = pd.read_csv(args.matrix, index_col=0)
    family_frame = pd.read_csv(args.families)
    family_map = dict(
        zip(family_frame["model_id"], family_frame["model_family"], strict=True)
    )
    detector = DifficultyAdjustedDetectorV8()
    scores = detector.score_methods(matrix, model_families=family_map)
    subjects = [str(item).split("::", 1)[0] for item in matrix.columns]
    p_values = exploratory_stratified_p_values(
        scores["V8_FULL"],
        scores["FAMILY_BALANCED_DIFFICULTY_ESTIMATE"],
        subjects,
    )
    q_values = benjamini_hochberg(p_values)
    item_scores = pd.DataFrame(
        {
            "item_id": matrix.columns.astype(str),
            "subject": subjects,
            **{name.lower(): values for name, values in scores.items()},
            "exploratory_stratified_p_value": p_values,
            "exploratory_BH_q_value": q_values,
            "claim_status": "EXPLORATORY_ONLY_NO_EXTERNAL_LABEL_VALIDATION",
        }
    )
    item_scores.to_csv(args.output / "mmlu_difficulty_adjusted_item_scores.csv", index=False)
    confound_rows = []
    for method in (
        "V8_FULL",
        "CONDITIONAL_RESIDUALIZATION",
        "DIFFICULTY_MATCHING",
    ):
        confound_rows.append(
            {
                "method": method,
                "difficulty_spearman": _safe_spearman(
                    scores[method], scores["FAMILY_BALANCED_DIFFICULTY_ESTIMATE"]
                ),
                "family_disagreement_spearman": _safe_spearman(
                    scores[method], scores["FAMILY_DISAGREEMENT"]
                ),
                "subject_eta_squared": _subject_eta_squared(scores[method], subjects),
                "answer_position_association": None,
                "item_length_association": None,
                "unavailable_covariates": "answer position and item length absent from matrix",
            }
        )
    confound = pd.DataFrame(confound_rows)
    confound.to_csv(args.output / "mmlu_diagnostic_confound_audit.csv", index=False)
    mmlu_summary = {
        "status": "MMLU_V8_DIFFICULTY_ADJUSTED_EXPLORATORY_COMPLETE",
        "models": int(matrix.shape[0]),
        "items": int(matrix.shape[1]),
        "families": len(set(family_map.values())),
        "exploratory_BH_q_le_0_05": int(np.sum(q_values <= 0.05)),
        "licensed_discoveries": 0,
        "external_label_validation": "NOT_AVAILABLE",
        "claim_boundary": (
            "Difficulty-adjusted MMLU scores and q-values are exploratory associations under "
            "this response-matrix null. They do not identify causes or license item claims."
        ),
    }
    summary["runtime_seconds"] = time.perf_counter() - started
    summary["mmlu"] = mmlu_summary
    summary["historical_v7_1_difficulty_control"] = {
        "AUPRC": 0.439069,
        "AUROC": 0.822549,
        "precision_at_k": 0.396296,
        "status": "FROZEN_FAILURE_SIGNAL_PRESERVED",
    }
    (args.output / "development_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output / "mmlu_summary.json").write_text(
        json.dumps(mmlu_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"{summary['status']}: difficulty AUPRC "
        f"{summary['development_v8_full_difficulty_negative_auprc']:.4f}; "
        f"true-flaw median AUPRC {summary['development_v8_full_true_flaw_median_auprc']:.4f}"
    )
    return 0


def _safe_spearman(left: np.ndarray, right: np.ndarray) -> float | None:
    value = float(spearmanr(left, right).statistic)
    return value if np.isfinite(value) else None


def _subject_eta_squared(scores: np.ndarray, subjects: list[str]) -> float:
    values = np.asarray(scores, dtype=float)
    grand = float(np.mean(values))
    total = float(np.sum((values - grand) ** 2))
    if total <= 0.0:
        return 0.0
    between = 0.0
    subject_array = np.asarray(subjects)
    for subject in sorted(set(subjects)):
        group = values[subject_array == subject]
        between += len(group) * (float(np.mean(group)) - grand) ** 2
    return between / total


if __name__ == "__main__":
    raise SystemExit(main())
