"""Deterministic, non-evidence planning utilities for future ValidEval studies."""

from valideval.planning.panel_power import (
    PanelPowerConfig,
    approximate_auc_detection_probability,
    auc_standard_error,
    build_common_panel_plan,
    simulate_rank_correlation_power,
    write_common_panel_plan,
)
from valideval.planning.runtime_estimator import (
    CpuRuntimeScenario,
    GpuRuntimeScenario,
    calibrate_items_per_second_from_smoke,
    estimate_cpu_runtime,
    estimate_gpu_runtime,
)

__all__ = [
    "CpuRuntimeScenario",
    "GpuRuntimeScenario",
    "PanelPowerConfig",
    "approximate_auc_detection_probability",
    "auc_standard_error",
    "build_common_panel_plan",
    "calibrate_items_per_second_from_smoke",
    "estimate_cpu_runtime",
    "estimate_gpu_runtime",
    "simulate_rank_correlation_power",
    "write_common_panel_plan",
]
