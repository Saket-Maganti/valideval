from __future__ import annotations

import numpy as np
import pandas as pd

from valideval.measurement.hierarchical_subject import (
    fit_hierarchical_subject_model,
    heldout_subject_model_validation,
    panel_size_sensitivity,
    validate_measurement_model_plan,
)


def _adequate_matrix() -> tuple[pd.DataFrame, list[str]]:
    rng = np.random.default_rng(12)
    n_models = 10
    n_subjects = 3
    items_per_subject = 20
    abilities = np.linspace(-1.5, 1.5, n_models)
    easiness = np.array([-0.7, 0.0, 0.7])
    values = np.zeros((n_models, n_subjects * items_per_subject))
    subjects: list[str] = []
    for subject_index in range(n_subjects):
        subjects.extend([f"s{subject_index}"] * items_per_subject)
        for item_offset in range(items_per_subject):
            column = subject_index * items_per_subject + item_offset
            probabilities = 1 / (1 + np.exp(-(abilities + easiness[subject_index])))
            values[:, column] = rng.binomial(1, probabilities)
    return (
        pd.DataFrame(
            values,
            index=[f"m{index}" for index in range(n_models)],
            columns=[f"i{index}" for index in range(values.shape[1])],
        ),
        subjects,
    )


def test_hierarchical_subject_fit_is_transparent_and_centered():
    frame, subjects = _adequate_matrix()
    result = fit_hierarchical_subject_model(frame, subjects)
    assert result["status"] == "REPRODUCED"
    assert result["convergence_method"] == "closed_form_no_iteration"
    assert result["full_parametric_2pl"] is False
    assert abs(result["identifiability_constraints"]["mean_centered_model_effect"]) < 1e-12
    assert abs(result["identifiability_constraints"]["mean_centered_subject_effect"]) < 1e-12
    assert len(result["model_subject_interactions"]) == 30
    assert "additive_baseline_brier_score" in result["fit_summary"]


def test_hierarchical_subject_fit_fails_closed_on_small_panel():
    frame, subjects = _adequate_matrix()
    result = fit_hierarchical_subject_model(
        frame.iloc[:4, :20],
        subjects[:20],
    )
    assert result["status"] == "BLOCKED"
    assert result["parameters_computed"] is False
    assert result["blockers"]


def test_panel_size_sensitivity_is_seeded():
    frame, subjects = _adequate_matrix()
    first = panel_size_sensitivity(frame, subjects, panel_sizes=(5, 8), n_repeats=2, seed=10)
    second = panel_size_sensitivity(frame, subjects, panel_sizes=(5, 8), n_repeats=2, seed=10)
    pd.testing.assert_frame_equal(first, second)
    assert set(first["status"]) == {"REPRODUCED"}


def test_measurement_model_has_heldout_baselines_calibration_and_sensitivity():
    frame, subjects = _adequate_matrix()
    families = {model: f"f{index}" for index, model in enumerate(frame.index)}
    heldout = heldout_subject_model_validation(
        frame,
        subjects,
        model_families=families,
        n_uncertainty_bootstrap=10,
    )
    assert heldout["status"] == "REPRODUCED"
    assert "brier_score" in heldout["subject_conditioned"]
    assert "brier_score" in heldout["aggregate_model_baseline"]
    assert "expected_calibration_error" in heldout["calibration"]
    plan = validate_measurement_model_plan(
        frame,
        subjects,
        model_families=families,
        regularization_grid=(2.0, 10.0),
    )
    assert plan["status"] == "MEASUREMENT_MODEL_PLAN_DEFENSIBLE"
    assert len(plan["regularization_sensitivity"]) == 2
