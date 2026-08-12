from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def optimize_study_c_compute(
    candidates: Sequence[Mapping[str, Any]],
    *,
    measured_examples_per_second: float | None,
    target_power: float = 0.80,
    minimum_families: int = 5,
    minimum_benchmarks: int = 3,
) -> dict[str, Any]:
    """Minimize measured T4 hours subject to declared design constraints."""

    if measured_examples_per_second is None:
        return {
            "status": "COMPUTE_OPTIMIZATION_BLOCKED_PENDING_S2",
            "selected_design": None,
            "reason": (
                "Measured accepted S1/S2 throughput is required; V7 planning ranges are not "
                "substituted for real T4 measurements."
            ),
            "target_power": target_power,
        }
    if measured_examples_per_second <= 0:
        raise ValueError("measured_examples_per_second must be positive")
    feasible = []
    for raw in candidates:
        row = dict(raw)
        if (
            float(row["power"]) < target_power
            or int(row["family_count"]) < minimum_families
            or int(row["benchmark_count"]) < minimum_benchmarks
        ):
            continue
        examples = int(row["model_count"]) * int(row["item_count"]) * int(row["benchmark_count"])
        row["estimated_t4_hours_from_measured_throughput"] = (
            examples / measured_examples_per_second / 3600.0
        )
        feasible.append(row)
    if not feasible:
        return {
            "status": "COMPUTE_OPTIMIZATION_NO_ADEQUATE_DESIGN",
            "selected_design": None,
            "target_power": target_power,
        }
    selected = min(
        feasible,
        key=lambda row: (
            row["estimated_t4_hours_from_measured_throughput"],
            row["model_count"],
            row["item_count"],
        ),
    )
    return {
        "status": "COMPUTE_OPTIMIZATION_READY_FROM_MEASURED_S2",
        "selected_design": selected,
        "feasible_design_count": len(feasible),
        "target_power": target_power,
        "claim_boundary": "Runtime is conditional on the supplied accepted T4 throughput measurement.",
    }
