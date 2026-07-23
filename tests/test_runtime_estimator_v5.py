from __future__ import annotations

import pytest

from valideval.planning.runtime_estimator import (
    GpuRuntimeScenario,
    calibrate_items_per_second_from_smoke,
    estimate_gpu_runtime,
    recalibrate_gpu_scenario,
)


def _scenario() -> GpuRuntimeScenario:
    return GpuRuntimeScenario(
        scenario_id="smoke-plan",
        benchmark="toy",
        model_id="example/model@revision",
        model_parameters_billions=1.0,
        item_count=100,
        average_input_tokens=100,
        average_output_tokens=20,
        throughput_tps_optimistic=20,
        throughput_tps_expected=10,
        throughput_tps_conservative=5,
        download_size_gb=1.0,
    )


def test_runtime_range_is_ordered_and_non_evidence():
    result = estimate_gpu_runtime(_scenario())
    assert (
        result["wall_hours_including_download_optimistic"]
        < result["wall_hours_including_download_expected"]
    )
    assert (
        result["wall_hours_including_download_expected"]
        < result["wall_hours_including_download_conservative"]
    )
    assert result["download_hours_expected"] > 0
    assert result["evidence_status"] == "PLANNED"
    assert result["calibration_state"] == "UNMEASURED_ASSUMPTIONS"


def test_smoke_calibration_is_mechanical_and_recalibrates_range():
    calibration = calibrate_items_per_second_from_smoke(
        completed_items=100, elapsed_seconds=50, failed_items=5
    )
    assert calibration["completed_items_per_second"] == 2.0
    assert calibration["evidence_status"] == "NON_EVIDENCE_FIXTURE"
    recalibrated = recalibrate_gpu_scenario(
        _scenario(), completed_items=100, elapsed_seconds=50, uncertainty_fraction=0.2
    )
    assert recalibrated.throughput_tps_optimistic > recalibrated.throughput_tps_expected
    assert recalibrated.throughput_tps_expected > recalibrated.throughput_tps_conservative


def test_runtime_estimator_rejects_reversed_throughput_range():
    scenario = _scenario()
    invalid = GpuRuntimeScenario(
        **{
            **scenario.__dict__,
            "throughput_tps_optimistic": 5,
            "throughput_tps_expected": 10,
        }
    )
    with pytest.raises(ValueError):
        estimate_gpu_runtime(invalid)
