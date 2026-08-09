import pandas as pd

from valideval.measurement.regime_study import (
    evaluate_measurement_regime,
    simulate_measurement_regime,
)
from valideval.statistics.panel_power_v7 import paired_difference_power
from valideval.transport import analyze_transportability


def test_transport_supported_requires_heldout_exact_effects() -> None:
    frame = pd.DataFrame(
        {
            "estimand": ["score_transport"] * 3,
            "benchmark": ["mmlu", "gsm8k", "bbh"],
            "estimate": [0.4, 0.35, 0.45],
            "standard_error": [0.05] * 3,
            "exact_identity": [True] * 3,
            "held_out": [True] * 3,
            "independent_families": [6] * 3,
        }
    )
    assert analyze_transportability(frame)["overall_status"] == "TRANSFER_SUPPORTED"


def test_transport_blocks_identity_failure() -> None:
    frame = pd.DataFrame(
        {
            "estimand": ["score_transport"],
            "benchmark": ["mmlu"],
            "estimate": [0.4],
            "standard_error": [0.05],
            "exact_identity": [False],
            "held_out": [True],
            "independent_families": [6],
        }
    )
    assert analyze_transportability(frame)["overall_status"] == "BLOCKED"


def test_measurement_regime_is_deterministic() -> None:
    first = simulate_measurement_regime(
        model_count=12, family_count=3, item_count=80, subject_count=4, seed=8
    )
    second = simulate_measurement_regime(
        model_count=12, family_count=3, item_count=80, subject_count=4, seed=8
    )
    assert first[0].equals(second[0])
    result = evaluate_measurement_regime(*first, seed=9)
    assert result["regime"] in {"SUPPORTED", "CAUTION", "UNRELIABLE", "UNIDENTIFIABLE"}


def test_well_identified_one_dimensional_regime_recovers_ability_direction() -> None:
    matrix, subjects, truth = simulate_measurement_regime(
        model_count=80,
        family_count=12,
        item_count=600,
        subject_count=12,
        seed=1,
    )
    result = evaluate_measurement_regime(matrix, subjects, truth, seed=2)
    assert result["parameter_recovery"]["ability_rank_spearman"] > 0.8
    assert result["regime"] == "SUPPORTED"


def test_paired_power_increases_with_items_and_effect_size() -> None:
    low = paired_difference_power(
        item_count=200,
        baseline_accuracy=0.5,
        difference=0.01,
        response_correlation=0.25,
    )
    more_items = paired_difference_power(
        item_count=2000,
        baseline_accuracy=0.5,
        difference=0.01,
        response_correlation=0.25,
    )
    larger_effect = paired_difference_power(
        item_count=200,
        baseline_accuracy=0.5,
        difference=0.03,
        response_correlation=0.25,
    )
    assert low < more_items
    assert low < larger_effect
