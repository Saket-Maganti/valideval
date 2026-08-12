import pandas as pd

from valideval.measurement.regime_study import (
    evaluate_measurement_regime,
    simulate_measurement_regime,
)
from valideval.statistics.panel_power_v7 import paired_difference_power
from valideval.transport import analyze_transportability, build_fold_manifest


def _fold(benchmark: str) -> dict[str, object]:
    return build_fold_manifest(
        fold_id=f"lobo-{benchmark}",
        training_benchmarks=[name for name in ("mmlu", "gsm8k", "bbh") if name != benchmark],
        held_out_benchmark=benchmark,
        training_families=["f1", "f2", "f3", "f4", "f5"],
        held_out_families=[],
        training_model_ids=["train-1"],
        evaluation_model_ids=["eval-1"],
        discovery_item_ids=["discover-1"],
        evaluation_item_ids=["eval-item-1"],
        source_commit="a" * 40,
        config_hash="b" * 64,
        execution_status="EXECUTED",
        data_artifact_hashes={"effects.csv": "c" * 64},
    )


def test_transport_supported_requires_heldout_exact_effects() -> None:
    frame = pd.DataFrame(
        {
            "estimand": ["score_transport"] * 3,
            "benchmark": ["mmlu", "gsm8k", "bbh"],
            "estimate": [0.4, 0.35, 0.45],
            "standard_error": [0.05] * 3,
            "exact_identity": [True] * 3,
            "fold_manifest": [_fold(name) for name in ("mmlu", "gsm8k", "bbh")],
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
            "fold_manifest": [_fold("mmlu")],
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
