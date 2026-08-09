from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import norm

TRANSPORT_ESTIMANDS = (
    "score_transport",
    "ranking_transport",
    "flag_transport",
    "calibration_transport",
    "decision_transport",
    "repair_transport",
)


def analyze_transportability(
    effects: pd.DataFrame,
    *,
    confidence_level: float = 0.95,
    heterogeneity_threshold: float = 0.50,
    minimum_benchmarks: int = 3,
    minimum_families: int = 5,
) -> dict[str, object]:
    """Random-effects transport analysis with fail-closed identity and holdout gates.

    Required columns: estimand, benchmark, estimate, standard_error, exact_identity,
    held_out, and independent_families.
    """

    required = {
        "estimand",
        "benchmark",
        "estimate",
        "standard_error",
        "exact_identity",
        "held_out",
        "independent_families",
    }
    if not required.issubset(effects.columns):
        raise ValueError(f"transport effects are missing {sorted(required - set(effects.columns))}")
    unknown = set(effects["estimand"]) - set(TRANSPORT_ESTIMANDS)
    if unknown:
        raise ValueError(f"unknown transport estimand(s): {sorted(unknown)}")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie in (0, 1)")
    rows = []
    for estimand, group in effects.groupby("estimand", sort=True):
        rows.append(
            _analyze_estimand(
                str(estimand),
                group,
                confidence_level=confidence_level,
                heterogeneity_threshold=heterogeneity_threshold,
                minimum_benchmarks=minimum_benchmarks,
                minimum_families=minimum_families,
            )
        )
    return {
        "schema_version": "v7",
        "estimands": rows,
        "overall_status": _overall_status([str(row["status"]) for row in rows]),
        "claim_boundary": (
            "Transport is licensed only for the exact benchmark, model, family, and holdout "
            "scope represented in these effects."
        ),
    }


def _analyze_estimand(
    estimand: str,
    frame: pd.DataFrame,
    *,
    confidence_level: float,
    heterogeneity_threshold: float,
    minimum_benchmarks: int,
    minimum_families: int,
) -> dict[str, object]:
    if not frame["exact_identity"].astype(bool).all():
        return {"estimand": estimand, "status": "BLOCKED", "reason": "identity"}
    benchmark_count = int(frame["benchmark"].nunique())
    families = int(frame["independent_families"].min())
    if benchmark_count < minimum_benchmarks or families < minimum_families:
        return {
            "estimand": estimand,
            "status": "UNDERPOWERED",
            "benchmark_count": benchmark_count,
            "minimum_independent_families": families,
        }
    if not frame["held_out"].astype(bool).all():
        return {"estimand": estimand, "status": "BLOCKED", "reason": "not held out"}
    estimate = frame["estimate"].to_numpy(dtype=float)
    standard_error = frame["standard_error"].to_numpy(dtype=float)
    if (
        np.any(~np.isfinite(estimate))
        or np.any(~np.isfinite(standard_error))
        or np.any(standard_error <= 0.0)
    ):
        raise ValueError("transport estimates and positive standard errors must be finite")
    fixed_weight = 1.0 / standard_error**2
    fixed_mean = float(np.sum(fixed_weight * estimate) / np.sum(fixed_weight))
    q = float(np.sum(fixed_weight * (estimate - fixed_mean) ** 2))
    degrees = len(estimate) - 1
    c = float(np.sum(fixed_weight) - np.sum(fixed_weight**2) / np.sum(fixed_weight))
    tau_squared = max((q - degrees) / c, 0.0) if c > 0.0 else 0.0
    random_weight = 1.0 / (standard_error**2 + tau_squared)
    pooled = float(np.sum(random_weight * estimate) / np.sum(random_weight))
    pooled_se = math.sqrt(1.0 / float(np.sum(random_weight)))
    z = float(norm.ppf(0.5 + confidence_level / 2.0))
    lower = pooled - z * pooled_se
    upper = pooled + z * pooled_se
    i_squared = max((q - degrees) / q, 0.0) if q > 0.0 else 0.0
    directions = np.sign(estimate[np.abs(estimate) > 1e-12])
    reversal = len(set(directions.tolist())) > 1
    if reversal:
        status = "TRANSFER_DIRECTION_REVERSES"
    elif lower > 0.0 and i_squared <= heterogeneity_threshold:
        status = "TRANSFER_SUPPORTED"
    elif lower > 0.0:
        status = "TRANSFER_PARTIAL"
    elif i_squared > heterogeneity_threshold:
        status = "TRANSFER_BENCHMARK_SPECIFIC"
    else:
        status = "TRANSFER_NOT_SUPPORTED"
    return {
        "estimand": estimand,
        "status": status,
        "benchmark_count": benchmark_count,
        "minimum_independent_families": families,
        "pooled_effect": pooled,
        "pooled_standard_error": pooled_se,
        "confidence_lower": lower,
        "confidence_upper": upper,
        "tau_squared": tau_squared,
        "i_squared": i_squared,
        "leave_one_benchmark_out_required": True,
        "leave_one_family_out_required": True,
    }


def _overall_status(statuses: list[str]) -> str:
    if statuses and all(status == "TRANSFER_SUPPORTED" for status in statuses):
        return "TRANSFER_SUPPORTED"
    if any(status == "BLOCKED" for status in statuses):
        return "BLOCKED"
    if any(status == "UNDERPOWERED" for status in statuses):
        return "UNDERPOWERED"
    return "TRANSFER_PARTIAL"
