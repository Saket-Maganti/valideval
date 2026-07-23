from __future__ import annotations

import pandas as pd
import pytest

from valideval.planning.panel_power import (
    PanelPowerConfig,
    approximate_auc_detection_probability,
    build_common_panel_plan,
    simulate_rank_correlation_power,
    wilson_interval_width,
    write_common_panel_plan,
)


def test_panel_power_is_seeded_and_explicitly_non_evidence():
    kwargs = {
        "n_models": 16,
        "target_correlation": 0.5,
        "n_simulations": 100,
        "seed": 11,
    }
    first = simulate_rank_correlation_power(**kwargs)
    second = simulate_rank_correlation_power(**kwargs)
    assert first == second
    assert first["evidence_status"] == "PLANNED"
    assert first["planning_only"] is True


def test_panel_plan_contains_scientific_boundary_and_writes_csv(tmp_path):
    config = PanelPowerConfig(
        panel_sizes=(8, 16),
        target_rank_correlations=(0.2, 0.8),
        n_simulations=80,
        seed=5,
    )
    frame = build_common_panel_plan(config)
    assert len(frame) == 4
    assert not frame["full_2pl_identifiability_established"].any()
    assert frame["planning_only"].all()
    assert (frame["external_auc_detection_probability_approx"] > 0).all()
    assert (frame["human_precision_95pct_wilson_width"] > 0).all()
    output = tmp_path / "plan.csv"
    written = write_common_panel_plan(output, config)
    pd.testing.assert_frame_equal(pd.read_csv(output), written, check_dtype=False)


def test_panel_power_rejects_underspecified_simulation():
    config = PanelPowerConfig(panel_sizes=(3,), n_simulations=10)
    with pytest.raises(ValueError):
        config.validate()


def test_wilson_interval_tightens_with_sample_size():
    assert wilson_interval_width(400, 0.5) < wilson_interval_width(40, 0.5)


def test_external_auc_detection_probability_increases_with_label_count():
    small = approximate_auc_detection_probability(anticipated_auc=0.7, n_positive=20, n_negative=20)
    large = approximate_auc_detection_probability(
        anticipated_auc=0.7, n_positive=100, n_negative=100
    )
    assert large > small
