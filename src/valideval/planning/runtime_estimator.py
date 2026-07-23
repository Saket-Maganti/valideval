from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class GpuRuntimeScenario:
    scenario_id: str
    benchmark: str
    model_id: str
    model_parameters_billions: float
    item_count: int
    average_input_tokens: float
    average_output_tokens: float
    gpu_count: int = 2
    dual_gpu_utilization: float = 0.80
    prefill_token_weight: float = 0.15
    throughput_tps_optimistic: float = 20.0
    throughput_tps_expected: float = 12.0
    throughput_tps_conservative: float = 6.0
    load_minutes_optimistic: float = 2.0
    load_minutes_expected: float = 5.0
    load_minutes_conservative: float = 10.0
    retry_fraction_optimistic: float = 0.02
    retry_fraction_expected: float = 0.08
    retry_fraction_conservative: float = 0.20
    download_size_gb: float = 0.0
    download_mbps_optimistic: float = 400.0
    download_mbps_expected: float = 150.0
    download_mbps_conservative: float = 50.0
    output_bytes_per_item: int = 4_096
    quantization: str = "unspecified"

    def validate(self) -> None:
        if not self.scenario_id or not self.benchmark or not self.model_id:
            raise ValueError("scenario_id, benchmark, and model_id are required")
        if self.model_parameters_billions <= 0 or self.item_count <= 0:
            raise ValueError("model size and item_count must be positive")
        if self.average_input_tokens < 0 or self.average_output_tokens <= 0:
            raise ValueError("token assumptions must be non-negative with positive output tokens")
        if self.gpu_count not in {1, 2}:
            raise ValueError("the T4 planner supports one or two GPUs")
        if not 0.0 < self.dual_gpu_utilization <= 1.0:
            raise ValueError("dual_gpu_utilization must lie in (0, 1]")
        throughputs = (
            self.throughput_tps_optimistic,
            self.throughput_tps_expected,
            self.throughput_tps_conservative,
        )
        if any(value <= 0 for value in throughputs) or not (
            throughputs[0] >= throughputs[1] >= throughputs[2]
        ):
            raise ValueError(
                "throughput must be positive and optimistic >= expected >= conservative"
            )
        loads = (
            self.load_minutes_optimistic,
            self.load_minutes_expected,
            self.load_minutes_conservative,
        )
        if any(value < 0 for value in loads) or not loads[0] <= loads[1] <= loads[2]:
            raise ValueError("load minutes must satisfy optimistic <= expected <= conservative")
        retries = (
            self.retry_fraction_optimistic,
            self.retry_fraction_expected,
            self.retry_fraction_conservative,
        )
        if any(not 0.0 <= value < 1.0 for value in retries) or not (
            retries[0] <= retries[1] <= retries[2]
        ):
            raise ValueError(
                "retry fractions must satisfy 0 <= optimistic <= expected <= conservative < 1"
            )
        if self.download_size_gb < 0 or self.output_bytes_per_item < 0:
            raise ValueError("download size and output bytes must be non-negative")


@dataclass(frozen=True)
class CpuRuntimeScenario:
    scenario_id: str
    operation: str
    work_units: int
    units_per_second_optimistic: float
    units_per_second_expected: float
    units_per_second_conservative: float
    fixed_minutes_optimistic: float = 0.0
    fixed_minutes_expected: float = 0.0
    fixed_minutes_conservative: float = 0.0

    def validate(self) -> None:
        if not self.scenario_id or not self.operation or self.work_units <= 0:
            raise ValueError("scenario_id, operation, and positive work_units are required")
        rates = (
            self.units_per_second_optimistic,
            self.units_per_second_expected,
            self.units_per_second_conservative,
        )
        if any(value <= 0 for value in rates) or not rates[0] >= rates[1] >= rates[2]:
            raise ValueError("CPU rates must satisfy optimistic >= expected >= conservative > 0")
        fixed = (
            self.fixed_minutes_optimistic,
            self.fixed_minutes_expected,
            self.fixed_minutes_conservative,
        )
        if any(value < 0 for value in fixed) or not fixed[0] <= fixed[1] <= fixed[2]:
            raise ValueError("fixed minutes must satisfy optimistic <= expected <= conservative")


def _download_hours(size_gb: float, megabits_per_second: float) -> float:
    return size_gb * 8_000.0 / megabits_per_second / 3_600.0


def estimate_gpu_runtime(scenario: GpuRuntimeScenario) -> dict[str, Any]:
    """Estimate a planning range without representing it as measured runtime."""

    scenario.validate()
    weighted_tokens = scenario.item_count * (
        scenario.average_output_tokens
        + scenario.prefill_token_weight * scenario.average_input_tokens
    )
    effective_workers = scenario.gpu_count * (
        scenario.dual_gpu_utilization if scenario.gpu_count == 2 else 1.0
    )
    values: dict[str, float] = {}
    for label in ("optimistic", "expected", "conservative"):
        throughput = getattr(scenario, f"throughput_tps_{label}")
        load_hours = getattr(scenario, f"load_minutes_{label}") / 60.0
        retry_fraction = getattr(scenario, f"retry_fraction_{label}")
        inference_hours = weighted_tokens / (throughput * effective_workers) / 3_600.0
        inference_with_retries = inference_hours / (1.0 - retry_fraction)
        download_hours = _download_hours(
            scenario.download_size_gb, getattr(scenario, f"download_mbps_{label}")
        )
        values[f"inference_hours_{label}"] = inference_with_retries
        values[f"download_hours_{label}"] = download_hours
        values[f"wall_hours_excluding_download_{label}"] = load_hours + inference_with_retries
        values[f"wall_hours_including_download_{label}"] = (
            load_hours + inference_with_retries + download_hours
        )
    return {
        **asdict(scenario),
        **values,
        "weighted_tokens": weighted_tokens,
        "effective_parallel_workers": effective_workers,
        "estimated_output_gb": scenario.item_count * scenario.output_bytes_per_item / 1e9,
        "evidence_status": "PLANNED",
        "planning_only": True,
        "calibration_state": "UNMEASURED_ASSUMPTIONS",
        "claim_boundary": (
            "Planning range only. Replace throughput assumptions with an imported S1 smoke "
            "measurement before scheduling scientific runs."
        ),
    }


def estimate_cpu_runtime(scenario: CpuRuntimeScenario) -> dict[str, Any]:
    scenario.validate()
    values: dict[str, float] = {}
    for label in ("optimistic", "expected", "conservative"):
        work_hours = scenario.work_units / getattr(scenario, f"units_per_second_{label}") / 3_600.0
        values[f"wall_hours_{label}"] = (
            work_hours + getattr(scenario, f"fixed_minutes_{label}") / 60.0
        )
    return {
        **asdict(scenario),
        **values,
        "evidence_status": "PLANNED",
        "planning_only": True,
        "calibration_state": "UNMEASURED_ASSUMPTIONS",
    }


def calibrate_items_per_second_from_smoke(
    *,
    completed_items: int,
    elapsed_seconds: float,
    failed_items: int = 0,
) -> dict[str, float | int | str | bool]:
    """Create a measured calibration record from an imported engineering smoke."""

    if completed_items <= 0 or elapsed_seconds <= 0 or failed_items < 0:
        raise ValueError(
            "completed_items and elapsed_seconds must be positive; failures non-negative"
        )
    total_attempted = completed_items + failed_items
    return {
        "completed_items": completed_items,
        "failed_items": failed_items,
        "elapsed_seconds": elapsed_seconds,
        "completed_items_per_second": completed_items / elapsed_seconds,
        "attempted_items_per_second": total_attempted / elapsed_seconds,
        "observed_failure_fraction": failed_items / total_attempted,
        "evidence_status": "NON_EVIDENCE_FIXTURE",
        "planning_only": True,
        "calibration_state": "S1_ENGINEERING_SMOKE_MEASURED",
    }


def recalibrate_gpu_scenario(
    scenario: GpuRuntimeScenario,
    *,
    completed_items: int,
    elapsed_seconds: float,
    uncertainty_fraction: float = 0.30,
) -> GpuRuntimeScenario:
    """Replace throughput assumptions using an S1 smoke, retaining a wide range."""

    if not 0.0 < uncertainty_fraction < 1.0:
        raise ValueError("uncertainty_fraction must lie in (0, 1)")
    calibration = calibrate_items_per_second_from_smoke(
        completed_items=completed_items, elapsed_seconds=elapsed_seconds
    )
    weighted_tokens_per_item = (
        scenario.average_output_tokens
        + scenario.prefill_token_weight * scenario.average_input_tokens
    )
    effective_workers = scenario.gpu_count * (
        scenario.dual_gpu_utilization if scenario.gpu_count == 2 else 1.0
    )
    observed_per_gpu_tps = (
        float(calibration["completed_items_per_second"])
        * weighted_tokens_per_item
        / effective_workers
    )
    return replace(
        scenario,
        throughput_tps_optimistic=observed_per_gpu_tps * (1.0 + uncertainty_fraction),
        throughput_tps_expected=observed_per_gpu_tps,
        throughput_tps_conservative=observed_per_gpu_tps * (1.0 - uncertainty_fraction),
    )


def write_runtime_estimates(
    output: str | Path,
    *,
    gpu_scenarios: Iterable[GpuRuntimeScenario] = (),
    cpu_scenarios: Iterable[CpuRuntimeScenario] = (),
) -> pd.DataFrame:
    rows = [estimate_gpu_runtime(scenario) for scenario in gpu_scenarios]
    rows.extend(estimate_cpu_runtime(scenario) for scenario in cpu_scenarios)
    if not rows:
        raise ValueError("at least one explicit runtime scenario is required")
    frame = pd.DataFrame(rows)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)
    return frame
