from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from valideval.diagnostics.v8.development import run_v8_exploratory_development
from valideval.diagnostics.v8.difficulty import DifficultyAdjustedDetectorV8
from valideval.validation.confirmatory_v7 import generate_confirmatory_matrix

ROOT = Path(__file__).resolve().parents[1]


def test_v8_scoring_api_has_no_label_or_truth_input() -> None:
    forbidden = {"label", "labels", "truth", "sealed", "is_flawed", "flaw_class"}
    for name in ("score_methods", "ablation_scores"):
        parameters = set(
            inspect.signature(getattr(DifficultyAdjustedDetectorV8(), name)).parameters
        )
        assert not parameters.intersection(forbidden)


def test_v8_scores_are_invariant_to_sealed_label_changes() -> None:
    matrix, sealed = generate_confirmatory_matrix(
        flaw_class="LABEL_ERROR",
        severity=0.6,
        prevalence=0.15,
        model_count=24,
        family_count=6,
        item_count=120,
        subject_count=10,
        dependence=0.5,
        seed=8801,
    )
    families = [f"family_{index % 6}" for index in range(24)]
    detector = DifficultyAdjustedDetectorV8()
    before = detector.score_methods(matrix, model_families=families)["V8_FULL"]
    sealed["sealed_is_flawed"] = ~sealed["sealed_is_flawed"]
    after = detector.score_methods(matrix, model_families=families)["V8_FULL"]
    np.testing.assert_array_equal(before, after)


def test_v8_handles_family_specific_all_missing_blocks_without_imputation_warnings() -> None:
    rng = np.random.default_rng(8802)
    values = rng.binomial(1, 0.5, size=(12, 40)).astype(float)
    values[:4, :3] = np.nan
    matrix = pd.DataFrame(
        values,
        index=[f"model_{index}" for index in range(12)],
        columns=[f"subject_{index % 4}::item_{index}" for index in range(40)],
    )
    scores = DifficultyAdjustedDetectorV8().score_methods(
        matrix, model_families=[f"family_{index // 4}" for index in range(12)]
    )
    assert np.isfinite(scores["V8_FULL"]).all()
    assert np.isfinite(scores["FAMILY_BALANCED_DIFFICULTY_ESTIMATE"]).all()


def test_v8_development_reduces_difficulty_control_without_destroying_signal() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/diagnostics/v8_exploratory_development.yaml").read_text(encoding="utf-8")
    )
    config["seeds"] = config["seeds"][:3]
    metrics, ablations, summary = run_v8_exploratory_development(config)
    assert summary["status"] == "V8_EXPLORATORY_DEVELOPMENT_GATE_PASS"
    assert summary["difficulty_confound_reduced"] is True
    assert summary["true_flaw_signal_retained"] is True
    assert summary["label_isolation"] == "PASS"
    assert summary["v8_confirmatory_status"] == "NOT_RUN_NOT_AUTHORIZED_IN_V7_2"
    assert set(metrics["control"]) == {
        "TRUE_FLAW",
        "DIFFICULTY_CONDITIONED_NEGATIVE_CONTROL",
    }
    assert not ablations.empty
