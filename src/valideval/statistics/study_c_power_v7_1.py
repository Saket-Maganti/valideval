from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

ESTIMANDS = (
    "PAIRWISE_ACCURACY_DIFFERENCE",
    "MODEL_RANK_CORRELATION",
    "MODEL_BENCHMARK_INTERACTION",
    "FAMILY_BENCHMARK_INTERACTION",
    "DIAGNOSTIC_TRANSPORT_EFFECT",
    "TOP_K_DECISION_STABILITY",
    "CLAIM_LICENSE_RATE",
    "REPAIR_EFFECT",
)


def study_c_power_redesign(config: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Monte Carlo planning around the eight actual Study-C estimand families.

    This is a design simulator, not empirical power. Every simulated estimator is
    explicitly affected by model/family/benchmark counts and the declared
    dependence and measurement-error assumptions.
    """

    simulations = int(config.get("simulations", 500))
    alpha = float(config.get("alpha", 0.05))
    target_power = float(config.get("target_power", 0.80))
    if simulations < 100:
        raise ValueError("power redesign requires at least 100 Monte Carlo simulations")
    rows: list[dict[str, Any]] = []
    seed = int(config.get("seed", 7101))
    for stage_index, (stage, design_raw) in enumerate(config["designs"].items()):
        design = dict(design_raw)
        for estimand_index, estimand in enumerate(ESTIMANDS):
            for effect_index, effect_size in enumerate(config["effect_sizes"]):
                rng = np.random.default_rng(
                    seed + stage_index * 100_000 + estimand_index * 1_000 + effect_index
                )
                power, standard_error = _simulate_estimand_power(
                    estimand,
                    design,
                    effect_size=float(effect_size),
                    alpha=alpha,
                    simulations=simulations,
                    rng=rng,
                )
                mcse = math.sqrt(max(power * (1.0 - power), 0.0) / simulations)
                rows.append(
                    {
                        "stage": str(stage),
                        "estimand": estimand,
                        "effect_size": float(effect_size),
                        "model_count": int(design["model_count"]),
                        "family_count": int(design["family_count"]),
                        "models_per_family": float(design["model_count"] / design["family_count"]),
                        "family_correlation": float(design["family_correlation"]),
                        "benchmark_count": int(design["benchmark_count"]),
                        "item_count": int(design["item_count"]),
                        "measurement_error": float(design["measurement_error"]),
                        "transport_heterogeneity": float(design["transport_heterogeneity"]),
                        "held_out_benchmark": str(design["held_out_benchmark"]),
                        "held_out_family": str(design["held_out_family"]),
                        "simulated_standard_error": standard_error,
                        "power": power,
                        "monte_carlo_se": mcse,
                        "power_ci_lower": max(0.0, power - 1.96 * mcse),
                        "power_ci_upper": min(1.0, power + 1.96 * mcse),
                        "target_power": target_power,
                        "design_adequacy": "ADEQUATE" if power >= target_power else "UNDERPOWERED",
                        "evidence_role": "PLANNING_SIMULATION_ONLY",
                    }
                )
    frame = pd.DataFrame(rows)
    primary = set(map(str, config.get("primary_estimands", ESTIMANDS)))
    material_effect = float(config.get("material_effect", config["effect_sizes"][0]))
    material = frame[np.isclose(frame["effect_size"], material_effect)]
    stage_summary: dict[str, Any] = {}
    for stage, group in material.groupby("stage", sort=True):
        primary_group = group[group["estimand"].isin(primary)]
        stage_summary[str(stage)] = {
            "primary_estimands": sorted(primary),
            "adequate_primary_estimands": sorted(
                primary_group.loc[
                    primary_group["design_adequacy"] == "ADEQUATE", "estimand"
                ].tolist()
            ),
            "all_primary_estimands_adequate": bool(
                len(primary_group) == len(primary)
                and primary_group["design_adequacy"].eq("ADEQUATE").all()
            ),
        }
    summary = {
        "status": "PRIMARY_ESTIMAND_POWER_PLANNING_READY",
        "empirical_power_claimed": False,
        "estimands": list(ESTIMANDS),
        "simulations_per_cell": simulations,
        "stage_design_adequacy": stage_summary,
        "s3_minimum_scientific_label_permitted": bool(
            stage_summary.get("S3", {}).get("all_primary_estimands_adequate", False)
        ),
        "claim_boundary": (
            "Power is simulated under declared planning distributions. S2 measurements must "
            "replace throughput, heterogeneity, and measurement-error assumptions before S3 authorization."
        ),
    }
    return frame, summary


def _simulate_estimand_power(
    estimand: str,
    design: Mapping[str, Any],
    *,
    effect_size: float,
    alpha: float,
    simulations: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    models = int(design["model_count"])
    families = int(design["family_count"])
    benchmarks = int(design["benchmark_count"])
    items = int(design["item_count"])
    family_correlation = float(design["family_correlation"])
    measurement_error = float(design["measurement_error"])
    heterogeneity = float(design["transport_heterogeneity"])
    effective_models = families + max(models - families, 0) * (1.0 - family_correlation)
    critical = float(norm.ppf(1.0 - alpha / 2.0))
    if estimand == "PAIRWISE_ACCURACY_DIFFERENCE":
        standard_error = math.sqrt(
            max(2.0 * 0.25 * (1.0 - float(design["paired_response_correlation"])), 1e-9) / items
        )
    elif estimand == "MODEL_RANK_CORRELATION":
        effective = max(effective_models, 4.0)
        standard_error = (1.0 + measurement_error) / math.sqrt(effective - 3.0)
    elif estimand == "MODEL_BENCHMARK_INTERACTION":
        standard_error = measurement_error / math.sqrt(max(effective_models * benchmarks, 1.0))
    elif estimand == "FAMILY_BENCHMARK_INTERACTION":
        standard_error = measurement_error / math.sqrt(max(families * benchmarks, 1.0))
    elif estimand == "DIAGNOSTIC_TRANSPORT_EFFECT":
        effective = max((benchmarks - 1) * (families - 1), 1)
        standard_error = math.sqrt(measurement_error**2 + heterogeneity**2) / math.sqrt(effective)
    elif estimand == "TOP_K_DECISION_STABILITY":
        standard_error = measurement_error / math.sqrt(
            max(math.log1p(items) * effective_models, 1.0)
        )
    elif estimand == "CLAIM_LICENSE_RATE":
        effective = max(families * benchmarks, 1)
        standard_error = math.sqrt(0.25 / effective) * (1.0 + family_correlation)
    elif estimand == "REPAIR_EFFECT":
        effective = max((families - 1) * (benchmarks - 1) * math.sqrt(items), 1.0)
        standard_error = math.sqrt(measurement_error**2 + heterogeneity**2) / math.sqrt(effective)
    else:
        raise ValueError(f"unknown Study-C estimand: {estimand}")
    standard_error = max(float(standard_error), 1e-9)
    estimates = rng.normal(effect_size, standard_error, size=simulations)
    reject = np.abs(estimates / standard_error) > critical
    return float(np.mean(reject)), standard_error
