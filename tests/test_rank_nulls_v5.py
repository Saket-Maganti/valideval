from __future__ import annotations

import numpy as np
import pandas as pd

from valideval.statistics.rank_nulls import (
    additive_probability_matrix,
    empirical_bayes_probability_matrix,
    sample_model_margin_permutation_null,
    simulate_rank_range_null,
)


def _matrix() -> tuple[pd.DataFrame, list[str]]:
    frame = pd.DataFrame(
        [
            [1, 1, 1, 0, 1, 0, 0, 0],
            [1, 0, 1, 0, 1, 1, 0, 0],
            [0, 0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
        ],
        index=["m1", "m2", "m3", "m4"],
        columns=[f"i{index}" for index in range(8)],
        dtype=float,
    )
    return frame, ["a"] * 4 + ["b"] * 4


def test_additive_null_probabilities_are_bounded_and_ability_ordered():
    frame, subjects = _matrix()
    probabilities = additive_probability_matrix(frame, subjects)
    assert probabilities.shape == frame.shape
    assert ((probabilities > 0) & (probabilities < 1)).all().all()
    assert probabilities.loc["m1"].mean() > probabilities.loc["m4"].mean()


def test_margin_permutation_preserves_each_model_total():
    frame, _ = _matrix()
    sampled = sample_model_margin_permutation_null(frame, rng=np.random.default_rng(7))
    pd.testing.assert_series_equal(sampled.sum(axis=1), frame.sum(axis=1))


def test_rank_range_null_is_seeded_and_labeled_fixture():
    frame, subjects = _matrix()
    first = simulate_rank_range_null(frame, subjects, n_simulations=12, seed=9)
    second = simulate_rank_range_null(frame, subjects, n_simulations=12, seed=9)
    pd.testing.assert_frame_equal(first, second)
    assert set(first["evidence_status"]) == {"REPRODUCED"}
    assert set(first["simulation_role"]) == {"calibration_null_not_observed_benchmark_output"}


def test_empirical_bayes_and_binomial_nulls_are_available():
    frame, subjects = _matrix()
    probabilities = empirical_bayes_probability_matrix(frame, subjects, prior_strength=10)
    assert ((probabilities > 0) & (probabilities < 1)).all().all()
    result = simulate_rank_range_null(
        frame,
        subjects,
        method="binomial_subject_size",
        n_simulations=4,
        seed=2,
    )
    assert set(result["method"]) == {"binomial_subject_size"}
