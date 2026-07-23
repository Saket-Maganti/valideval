from __future__ import annotations

from valideval.cross_benchmark.gates import (
    CROSS_BENCHMARK_BLOCKED_CONFIGURATION_MISMATCH,
    CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY,
    CROSS_BENCHMARK_BLOCKED_INSUFFICIENT_MODEL_OVERLAP,
    CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY,
    CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL,
    evaluate_cross_benchmark_gate,
)


def _payload(models: list[str], *, config: str = "common", integrity: str = "pass"):
    return {
        "model_ids": models,
        "model_family_by_id": {model: f"family-{model[-1]}" for model in models},
        "config_class": config,
        "usable_items": 20,
        "extraction_reliability": 1.0,
        "data_integrity": integrity,
        "study_id": "study-c",
    }


def _thresholds() -> dict[str, object]:
    return {
        "minimum_exact_common_models": 3,
        "minimum_independent_families": 3,
        "minimum_common_families_exploratory": 2,
        "minimum_usable_items_per_benchmark": 10,
        "minimum_extraction_reliability": 0.95,
        "require_common_config_class": True,
        "allow_family_level_exploratory": True,
    }


def test_exact_common_panel_passes_only_with_all_gates() -> None:
    models = ["m-a", "m-b", "m-c"]
    result = evaluate_cross_benchmark_gate(
        {"mmlu": _payload(models), "gsm8k": _payload(models)},
        thresholds=_thresholds(),
    )
    assert result["status"] == CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL
    assert result["exact_common_model_ids"] == models


def test_configuration_and_integrity_fail_closed() -> None:
    models = ["m-a", "m-b", "m-c"]
    mismatch = evaluate_cross_benchmark_gate(
        {"mmlu": _payload(models), "gsm8k": _payload(models, config="other")},
        thresholds=_thresholds(),
    )
    assert mismatch["status"] == CROSS_BENCHMARK_BLOCKED_CONFIGURATION_MISMATCH

    invalid = evaluate_cross_benchmark_gate(
        {"mmlu": _payload(models), "gsm8k": _payload(models, integrity="fail")},
        thresholds=_thresholds(),
    )
    assert invalid["status"] == CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY


def test_family_only_and_insufficient_overlap_are_distinct() -> None:
    left = _payload(["a-a", "b-b", "c-c"])
    right = _payload(["x-a", "y-b", "z-z"])
    family_only = evaluate_cross_benchmark_gate(
        {"mmlu": left, "gsm8k": right},
        thresholds=_thresholds(),
    )
    assert family_only["status"] == CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY

    blocked = evaluate_cross_benchmark_gate(
        {"mmlu": left, "gsm8k": _payload(["x-x", "y-y", "z-z"])},
        thresholds=_thresholds(),
    )
    assert blocked["status"] == CROSS_BENCHMARK_BLOCKED_INSUFFICIENT_MODEL_OVERLAP
