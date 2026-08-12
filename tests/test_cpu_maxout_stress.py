from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from valideval.statistics.cpu_maxout_stress import (
    benchmark_effective_count,
    expanded_human_planning,
    power_uncertainty_summary,
    run_benchmark_dependence_stress,
    run_cpu_maxout_stress_suite,
    run_pairwise_multiplicity_stress,
)
from valideval.statistics.rank_inference_v7_1 import simulate_simultaneous_rank_coverage


def test_effective_benchmark_count_respects_dependence() -> None:
    assert benchmark_effective_count(np.eye(5)) == pytest.approx(5.0)
    redundant = np.full((5, 5), 0.9)
    np.fill_diagonal(redundant, 1.0)
    assert 1.0 < benchmark_effective_count(redundant) < 2.0


def test_odd_model_tie_rank_stress_is_shape_safe() -> None:
    result = simulate_simultaneous_rank_coverage(
        simulations=50,
        bootstrap_draws=100,
        model_count=5,
        family_count=2,
        family_correlation=0.6,
        tied_truth=True,
    )
    assert result["model_count"] == 5
    assert 0.0 <= result["joint_coverage"] <= 1.0


def test_benchmark_dependence_stress_is_bounded() -> None:
    rows = run_benchmark_dependence_stress()
    assert (rows["effective_benchmark_count_approximation"] >= 1.0).all()
    assert (rows["effective_benchmark_count_approximation"] <= rows["raw_benchmark_count"]).all()


def test_pairwise_scenario_labels_survive_csv_roundtrip(tmp_path) -> None:
    rows = run_pairwise_multiplicity_stress()
    output = tmp_path / "pairwise.csv"
    rows.to_csv(output, index=False)
    restored = pd.read_csv(output)
    assert restored["scenario"].notna().all()
    assert "GLOBAL_NULL" in set(restored["scenario"])


def test_human_planning_expands_annotators_and_adjudication() -> None:
    plans = expanded_human_planning()
    assert set(plans["annotators_per_item"]) == {2, 3}
    assert set(plans["adjudication_fraction"]) == {0.10, 0.25, 0.50}
    assert set(plans["design"]) == {
        "pilot",
        "minimum_confirmatory",
        "recommended",
        "high_precision",
    }
    assert (plans["total_labels"] >= plans["primary_labels"]).all()


def test_power_uncertainty_is_ordered() -> None:
    grid = pd.DataFrame(
        {"stage": ["S2"] * 4, "estimand": ["PAIR"] * 4, "power": [0.1, 0.2, 0.3, 0.4]}
    )
    row = power_uncertainty_summary(grid).iloc[0]
    assert row["worst_plausible"] <= row["conservative"] <= row["central"] <= row["optimistic"]


def test_quick_stress_is_separate_non_evidence_fixture(tmp_path) -> None:
    root = Path(__file__).resolve().parents[1]
    payload = run_cpu_maxout_stress_suite(
        confirmation_records_path=root
        / "results/final_cpu_maxout/claim_policy/confirmation_records.csv",
        power_grid_path=root / "results/v7_1/planning/power/primary_estimand_power_grid.csv",
        output_root=tmp_path / "fixture",
        quick=True,
    )
    assert payload["mode"] == "NON_EVIDENCE_FIXTURE"
    assert payload["evidence_class"] == "NON_EVIDENCE_FIXTURE"
    assert payload["monte_carlo_replicates"] < 10_000
