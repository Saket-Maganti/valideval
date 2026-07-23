from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr


@dataclass(frozen=True)
class PanelPowerConfig:
    """Configuration for a deterministic planning simulation.

    Outputs from this module are design aids. They are never benchmark evidence and
    do not establish that a planned panel is scientifically adequate.
    """

    panel_sizes: tuple[int, ...] = (4, 8, 12, 16, 24, 30, 40)
    target_rank_correlations: tuple[float, ...] = (0.3, 0.5, 0.7)
    n_simulations: int = 1_000
    alpha: float = 0.05
    seed: int = 2027
    minimum_independent_families: int = 4
    external_label_positive_count: int = 50
    external_label_negative_count: int = 150
    anticipated_external_auc: float = 0.70
    human_review_sample_size: int = 200
    anticipated_human_precision: float = 0.50

    def validate(self) -> None:
        if not self.panel_sizes or any(size < 4 for size in self.panel_sizes):
            raise ValueError("panel_sizes must contain integers of at least 4")
        if len(set(self.panel_sizes)) != len(self.panel_sizes):
            raise ValueError("panel_sizes must be unique")
        if not self.target_rank_correlations or any(
            not 0.0 < correlation < 1.0 for correlation in self.target_rank_correlations
        ):
            raise ValueError("target_rank_correlations must lie strictly between 0 and 1")
        if self.n_simulations < 20:
            raise ValueError("n_simulations must be at least 20 for a useful planning estimate")
        if not 0.0 < self.alpha < 0.5:
            raise ValueError("alpha must lie strictly between 0 and 0.5")
        if self.minimum_independent_families < 2:
            raise ValueError("minimum_independent_families must be at least 2")
        if self.external_label_positive_count <= 0 or self.external_label_negative_count <= 0:
            raise ValueError("external-label positive and negative counts must be positive")
        if not 0.5 < self.anticipated_external_auc < 1.0:
            raise ValueError("anticipated_external_auc must lie strictly between 0.5 and 1")
        if self.human_review_sample_size <= 0:
            raise ValueError("human_review_sample_size must be positive")
        if not 0.0 <= self.anticipated_human_precision <= 1.0:
            raise ValueError("anticipated_human_precision must lie between 0 and 1")


def simulate_rank_correlation_power(
    *,
    n_models: int,
    target_correlation: float,
    n_simulations: int = 1_000,
    alpha: float = 0.05,
    seed: int = 2027,
) -> dict[str, float | int | str | bool]:
    """Estimate rank-correlation detection probability using seeded simulation.

    A Gaussian copula supplies paired latent abilities. Spearman correlation is then
    tested in every replicate. The result quantifies only this stated planning model.
    """

    config = PanelPowerConfig(
        panel_sizes=(n_models,),
        target_rank_correlations=(target_correlation,),
        n_simulations=n_simulations,
        alpha=alpha,
        seed=seed,
    )
    config.validate()
    rng = np.random.default_rng(seed)
    covariance = np.array([[1.0, target_correlation], [target_correlation, 1.0]])
    detected = 0
    estimates: list[float] = []
    top_k_jaccards: list[float] = []
    top_k = max(1, min(5, n_models // 4))
    for _ in range(n_simulations):
        sample = rng.multivariate_normal(np.zeros(2), covariance, size=n_models)
        result = spearmanr(sample[:, 0], sample[:, 1])
        estimate = float(result.statistic)
        p_value = float(result.pvalue)
        estimates.append(estimate)
        detected += int(p_value < alpha and estimate > 0.0)
        first_top = set(np.argsort(sample[:, 0])[-top_k:])
        second_top = set(np.argsort(sample[:, 1])[-top_k:])
        top_k_jaccards.append(len(first_top & second_top) / len(first_top | second_top))
    probability = detected / n_simulations
    return {
        "panel_size": n_models,
        "target_rank_correlation": target_correlation,
        "n_simulations": n_simulations,
        "alpha": alpha,
        "estimated_detection_probability": probability,
        "monte_carlo_standard_error": math.sqrt(probability * (1.0 - probability) / n_simulations),
        "median_estimated_rank_correlation": float(np.median(estimates)),
        "top_k": top_k,
        "median_top_k_jaccard": float(np.median(top_k_jaccards)),
        "evidence_status": "PLANNED",
        "planning_only": True,
        "simulation_model": "gaussian_copula_spearman",
    }


def fisher_correlation_ci_width(
    n_models: int,
    target_correlation: float,
    *,
    confidence: float = 0.95,
) -> float:
    """Approximate correlation interval width for planning, on the Fisher-z scale."""

    if n_models <= 3:
        raise ValueError("n_models must be greater than 3")
    if not -1.0 < target_correlation < 1.0:
        raise ValueError("target_correlation must lie strictly between -1 and 1")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between 0 and 1")
    z = math.atanh(target_correlation)
    delta = float(norm.ppf(0.5 + confidence / 2.0)) / math.sqrt(n_models - 3)
    return math.tanh(z + delta) - math.tanh(z - delta)


def wilson_interval_width(
    n: int,
    anticipated_proportion: float,
    *,
    confidence: float = 0.95,
) -> float:
    """Wilson interval width used for human-precision and prevalence planning."""

    if n <= 0:
        raise ValueError("n must be positive")
    if not 0.0 <= anticipated_proportion <= 1.0:
        raise ValueError("anticipated_proportion must be between 0 and 1")
    z = float(norm.ppf(0.5 + confidence / 2.0))
    denominator = 1.0 + z**2 / n
    center = (anticipated_proportion + z**2 / (2.0 * n)) / denominator
    half_width = (
        z
        * math.sqrt(
            anticipated_proportion * (1.0 - anticipated_proportion) / n + z**2 / (4.0 * n**2)
        )
        / denominator
    )
    return min(1.0, center + half_width) - max(0.0, center - half_width)


def auc_standard_error(
    *,
    anticipated_auc: float,
    n_positive: int,
    n_negative: int,
) -> float:
    """Hanley-McNeil approximation for explicit external-validation planning."""

    if not 0.5 < anticipated_auc < 1.0:
        raise ValueError("anticipated_auc must lie strictly between 0.5 and 1")
    if n_positive <= 0 or n_negative <= 0:
        raise ValueError("positive and negative sample counts must be positive")
    q1 = anticipated_auc / (2.0 - anticipated_auc)
    q2 = 2.0 * anticipated_auc**2 / (1.0 + anticipated_auc)
    variance = (
        anticipated_auc * (1.0 - anticipated_auc)
        + (n_positive - 1) * (q1 - anticipated_auc**2)
        + (n_negative - 1) * (q2 - anticipated_auc**2)
    ) / (n_positive * n_negative)
    return math.sqrt(max(variance, 0.0))


def approximate_auc_detection_probability(
    *,
    anticipated_auc: float,
    n_positive: int,
    n_negative: int,
    alpha: float = 0.05,
) -> float:
    """Normal-approximation planning probability for testing AUC above 0.5."""

    standard_error = auc_standard_error(
        anticipated_auc=anticipated_auc,
        n_positive=n_positive,
        n_negative=n_negative,
    )
    critical_value = float(norm.ppf(1.0 - alpha))
    signal_to_noise = (anticipated_auc - 0.5) / max(standard_error, 1e-12)
    return float(norm.cdf(signal_to_noise - critical_value))


def build_common_panel_plan(config: PanelPowerConfig) -> pd.DataFrame:
    """Build a non-evidence planning table across candidate panel sizes."""

    config.validate()
    rows: list[dict[str, Any]] = []
    external_auc_standard_error = auc_standard_error(
        anticipated_auc=config.anticipated_external_auc,
        n_positive=config.external_label_positive_count,
        n_negative=config.external_label_negative_count,
    )
    external_auc_detection_probability = approximate_auc_detection_probability(
        anticipated_auc=config.anticipated_external_auc,
        n_positive=config.external_label_positive_count,
        n_negative=config.external_label_negative_count,
        alpha=config.alpha,
    )
    human_precision_width = wilson_interval_width(
        config.human_review_sample_size,
        config.anticipated_human_precision,
    )
    scenario_index = 0
    for panel_size in sorted(config.panel_sizes):
        for target in sorted(config.target_rank_correlations):
            result = simulate_rank_correlation_power(
                n_models=panel_size,
                target_correlation=target,
                n_simulations=config.n_simulations,
                alpha=config.alpha,
                seed=config.seed + scenario_index,
            )
            scenario_index += 1
            independent_families_required = min(
                panel_size, max(config.minimum_independent_families, math.ceil(panel_size / 4))
            )
            rows.append(
                {
                    **result,
                    "approximate_95pct_correlation_ci_width": fisher_correlation_ci_width(
                        panel_size, target
                    ),
                    "minimum_independent_families_assumption": independent_families_required,
                    "model_pair_count": panel_size * (panel_size - 1) // 2,
                    "item_difficulty_se_at_probability_half": math.sqrt(0.25 / panel_size),
                    "model_by_benchmark_interaction_plannable": panel_size >= 8,
                    "diagnostic_transfer_plannable": panel_size >= 12,
                    "regularized_item_discrimination_plannable": panel_size >= 20,
                    "full_2pl_identifiability_established": False,
                    "external_label_positive_count_assumption": (
                        config.external_label_positive_count
                    ),
                    "external_label_negative_count_assumption": (
                        config.external_label_negative_count
                    ),
                    "anticipated_external_auc_assumption": config.anticipated_external_auc,
                    "external_auc_standard_error_approx": external_auc_standard_error,
                    "external_auc_detection_probability_approx": (
                        external_auc_detection_probability
                    ),
                    "human_review_sample_size_assumption": config.human_review_sample_size,
                    "anticipated_human_precision_assumption": (config.anticipated_human_precision),
                    "human_precision_95pct_wilson_width": human_precision_width,
                    "claim_boundary": (
                        "Simulation supports design comparison only; adequacy requires exact-family, "
                        "item-count, missingness, and execution-quality checks."
                    ),
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["panel_size", "target_rank_correlation"], ignore_index=True
    )


def write_common_panel_plan(
    output: str | Path,
    config: PanelPowerConfig,
) -> pd.DataFrame:
    """Write a deterministic CSV with explicit non-evidence labeling."""

    frame = build_common_panel_plan(config)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)
    return frame


def parse_numeric_sequence(values: str, *, cast: type[int] | type[float]) -> tuple[Any, ...]:
    """Parse a comma-separated CLI value with fail-closed validation."""

    parsed = tuple(cast(value.strip()) for value in values.split(",") if value.strip())
    if not parsed:
        raise ValueError("at least one value is required")
    return parsed


def unique_preserving_order(values: Iterable[Any]) -> tuple[Any, ...]:
    """Return deterministic unique values without sorting caller-defined tiers."""

    return tuple(dict.fromkeys(values))
