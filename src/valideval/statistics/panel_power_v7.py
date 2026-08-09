from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm


def paired_difference_power(
    *,
    item_count: int,
    baseline_accuracy: float,
    difference: float,
    response_correlation: float,
    alpha: float = 0.05,
) -> float:
    """Two-sided paired-normal power under explicit Bernoulli planning assumptions."""

    if item_count <= 1:
        raise ValueError("item_count must exceed one")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    if not -1.0 <= response_correlation <= 1.0:
        raise ValueError("response_correlation must lie in [-1, 1]")
    p_left = float(baseline_accuracy)
    p_right = p_left + float(difference)
    if not 0.0 < p_left < 1.0 or not 0.0 < p_right < 1.0:
        raise ValueError("planned accuracies must lie in (0, 1)")
    left_variance = p_left * (1.0 - p_left)
    right_variance = p_right * (1.0 - p_right)
    paired_variance = (
        left_variance
        + right_variance
        - 2.0 * response_correlation * np.sqrt(left_variance * right_variance)
    )
    standard_error = np.sqrt(max(paired_variance, 1e-12) / item_count)
    noncentrality = abs(difference) / standard_error
    critical = float(norm.ppf(1.0 - alpha / 2.0))
    return float(norm.cdf(-critical - noncentrality) + 1.0 - norm.cdf(critical - noncentrality))


def panel_power_grid(config: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for stage, panel in config["panels"].items():
        for benchmark, benchmark_config in config["benchmarks"].items():
            item_key = "pilot_items" if stage == "S2" else "scientific_items"
            for correlation in config["paired_response_correlations"]:
                for difference in config["effect_sizes"]:
                    power = paired_difference_power(
                        item_count=int(benchmark_config[item_key]),
                        baseline_accuracy=float(config["baseline_accuracy"]),
                        difference=float(difference),
                        response_correlation=float(correlation),
                        alpha=float(config["alpha"]),
                    )
                    rows.append(
                        {
                            "stage": stage,
                            "benchmark": benchmark,
                            "models": int(panel["model_count"]),
                            "families": int(panel["family_count"]),
                            "items": int(benchmark_config[item_key]),
                            "pairwise_difference": float(difference),
                            "response_correlation": float(correlation),
                            "power": power,
                            "power_gate": "PASS" if power >= 0.80 else "UNDERPOWERED",
                            "evidence_role": "PLANNING_ONLY",
                        }
                    )
    return pd.DataFrame(rows)
