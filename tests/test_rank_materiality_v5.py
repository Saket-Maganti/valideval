from __future__ import annotations

import pandas as pd

from valideval.statistics.rank_materiality import (
    analyze_rank_materiality,
    kendalls_w,
    tie_aware_ranks,
)


def _matrix() -> tuple[pd.DataFrame, list[str]]:
    frame = pd.DataFrame(
        [
            [1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],
            [1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0],
            [0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1],
            [0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1],
        ],
        index=["m1", "m2", "m3", "m4"],
        columns=[f"i{index}" for index in range(12)],
        dtype=float,
    )
    return frame, ["a"] * 4 + ["b"] * 4 + ["c"] * 4


def test_tie_aware_ranks_use_average_positions():
    ranks = tie_aware_ranks(pd.Series([0.8, 0.8, 0.2], index=["a", "b", "c"]))
    assert ranks.loc["a"] == 1.5
    assert ranks.loc["b"] == 1.5
    assert ranks.loc["c"] == 3.0


def test_rank_materiality_returns_uncertainty_and_null_outputs():
    frame, subjects = _matrix()
    result = analyze_rank_materiality(
        frame,
        subjects,
        n_bootstrap=20,
        n_null_simulations=20,
        seed=3,
        model_families={"m1": "f1", "m2": "f1", "m3": "f2", "m4": "f3"},
    )
    assert result["status"] == "REPRODUCED"
    assert result["severity_threshold_used"] is False
    assert len(result["model_rank_materiality"]) == 4
    assert result["rank_confidence_sets"]
    assert result["pairwise_outranking_probabilities"]
    assert result["null_comparison"]["n_null_simulations"] == 20
    assert result["top_k_jaccard_stability"]
    assert result["leave_one_subject_out_sensitivity"]
    assert result["benchmark_composition_rank_confidence"]
    assert result["family_analysis"]["status"] == "REPRODUCED"
    assert "does not establish benchmark invalidity" in result["claim_boundary"]


def test_kendalls_w_is_one_for_identical_rankings():
    ranks = pd.DataFrame({"a": [1, 2, 3], "b": [1, 2, 3]}, index=["x", "y", "z"])
    assert kendalls_w(ranks) == 1.0
