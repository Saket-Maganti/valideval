from __future__ import annotations

from pathlib import Path

import pandas as pd

from valideval.cross_benchmark.analysis import run_cross_benchmark_analysis


def _matrix(reverse: bool = False) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "model_id": ["m-a", "m-b", "m-c", "m-d"],
            "i1": [1, 1, 0, 0],
            "i2": [1, 0, 1, 0],
            "i3": [1, 1, 1, 0],
            "i4": [1, 0, 0, 0],
        }
    )
    if reverse:
        for column in ["i1", "i2", "i3", "i4"]:
            frame[column] = 1 - frame[column]
    return frame


def _metadata() -> dict[str, object]:
    return {
        "model_family_by_id": {
            "m-a": "family-a",
            "m-b": "family-b",
            "m-c": "family-c",
            "m-d": "family-d",
        },
        "config_class": "common-v5",
        "usable_items": 4,
        "extraction_reliability": 1.0,
        "data_integrity": "pass",
        "study_id": "study-c",
        "evidence_state": "NON_EVIDENCE_FIXTURE",
    }


def test_exact_analysis_uses_intersection_and_writes_artifacts(tmp_path: Path) -> None:
    metadata = {"mmlu": _metadata(), "gsm8k": _metadata()}
    payload = run_cross_benchmark_analysis(
        {"mmlu": _matrix(), "gsm8k": _matrix(reverse=True)},
        output_dir=tmp_path,
        benchmark_metadata=metadata,
        gate_thresholds={
            "minimum_exact_common_models": 4,
            "minimum_independent_families": 4,
            "minimum_common_families_exploratory": 2,
            "minimum_usable_items_per_benchmark": 4,
            "minimum_extraction_reliability": 1.0,
            "require_common_config_class": True,
            "allow_family_level_exploratory": True,
        },
        analysis_config={
            "top_k": 2,
            "bootstrap_iterations": 20,
            "permutation_iterations": 20,
            "random_seed": 7,
            "alpha": 0.05,
            "multiple_testing_method": "bh",
            "minimum_models_for_inference": 4,
            "transfer_supported_spearman": 0.7,
            "transfer_partial_spearman": 0.4,
            "benchmark_specific_range": 0.35,
        },
        execute=True,
    )

    assert payload["status"] == "ok"
    assert payload["exact_common_model_count"] == 4
    assert payload["evidence_state"] == "NON_EVIDENCE_FIXTURE"
    assert payload["transfer_conclusion"] == "UNDERPOWERED"
    assert (tmp_path / "rank_transfer_v5.csv").exists()
    assert (tmp_path / "model_benchmark_interaction_v5.json").exists()


def test_analysis_stops_when_exact_and_family_gates_fail(tmp_path: Path) -> None:
    right = _matrix().query("model_id in ['m-a', 'm-b']")
    metadata = {"mmlu": _metadata(), "gsm8k": _metadata()}
    metadata["gsm8k"]["model_family_by_id"] = {
        "m-a": "family-a",
        "m-b": "family-b",
    }
    payload = run_cross_benchmark_analysis(
        {"mmlu": _matrix(), "gsm8k": right},
        output_dir=tmp_path,
        benchmark_metadata=metadata,
        gate_thresholds={
            "minimum_exact_common_models": 4,
            "minimum_independent_families": 3,
            "minimum_common_families_exploratory": 3,
            "minimum_usable_items_per_benchmark": 4,
            "minimum_extraction_reliability": 1.0,
            "require_common_config_class": True,
            "allow_family_level_exploratory": True,
        },
        execute=True,
    )
    assert payload["status"] == "blocked"
    assert not (tmp_path / "rank_transfer_v5.csv").exists()
