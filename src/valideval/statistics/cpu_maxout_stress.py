from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from valideval.execution.manifest import atomic_write_json, atomic_write_text
from valideval.statistics.claim_policy_v7_2_1 import aggregate_native_metrics
from valideval.statistics.rank_inference_v7_1 import (
    pairwise_multiplicity_analysis,
    simulate_simultaneous_rank_coverage,
)
from valideval.statistics.rare_events import wilson_interval
from valideval.validation.multiplicity import correct_p_values


def benchmark_effective_count(correlation: np.ndarray) -> float:
    """Participation-ratio approximation to independent benchmark information."""

    matrix = np.asarray(correlation, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0:
        raise ValueError("benchmark correlation must be a non-empty square matrix")
    if not np.allclose(matrix, matrix.T) or not np.allclose(np.diag(matrix), 1.0):
        raise ValueError("benchmark correlation must be symmetric with unit diagonal")
    eigenvalues = np.linalg.eigvalsh(matrix)
    if eigenvalues.min() < -1e-8:
        raise ValueError("benchmark correlation must be positive semidefinite")
    return float(np.trace(matrix) ** 2 / np.trace(matrix @ matrix))


def run_rank_stress(*, simulations: int = 50, bootstrap_draws: int = 100) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scenario_index = 0
    for model_count in (5, 10, 20, 30, 40, 50):
        for tied_truth in (False, True):
            for correlation in (0.0, 0.6, 0.9):
                scenario_index += 1
                result = simulate_simultaneous_rank_coverage(
                    simulations=simulations,
                    bootstrap_draws=bootstrap_draws,
                    model_count=model_count,
                    family_count=min(10, max(2, model_count // 3)),
                    family_correlation=correlation,
                    tied_truth=tied_truth,
                    seed=7_215_000 + scenario_index,
                )
                rows.append(result)
    return pd.DataFrame(rows)


def run_pairwise_multiplicity_stress(*, draws_per_scenario: int = 400) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for model_count in (5, 10, 20, 30, 40, 50):
        for scenario_index, scenario in enumerate(
            ("GLOBAL_NULL", "ONE_CLEAR_WINNER", "DENSE_NEAR_TIES")
        ):
            rng = np.random.default_rng(7_216_000 + model_count * 10 + scenario_index)
            if scenario == "GLOBAL_NULL":
                truth = np.zeros(model_count)
            elif scenario == "ONE_CLEAR_WINNER":
                truth = np.zeros(model_count)
                truth[0] = 0.08
            else:
                truth = np.linspace(0.025, -0.025, model_count)
            families = np.arange(model_count) % min(10, max(2, model_count // 3))
            family_noise = rng.normal(0.0, 0.025, (draws_per_scenario, int(families.max()) + 1))
            independent = rng.normal(0.0, 0.02, (draws_per_scenario, model_count))
            draws = truth + math.sqrt(0.6) * family_noise[:, families]
            draws += math.sqrt(0.4) * independent
            columns = [f"model_{index:02d}" for index in range(model_count)]
            analysis = pairwise_multiplicity_analysis(pd.DataFrame(draws, columns=columns))
            methods = {
                "NONE": analysis["p_value_two_sided"].to_numpy() <= 0.05,
                "BH": analysis["reject_bh"].to_numpy(dtype=bool),
                "BY": np.asarray(
                    correct_p_values(analysis["p_value_two_sided"].tolist(), method="by")
                )
                <= 0.05,
                "HOLM": analysis["reject_holm"].to_numpy(dtype=bool),
            }
            index_by_model = {model: index for index, model in enumerate(columns)}
            true_differences = np.asarray(
                [
                    truth[index_by_model[str(row.model_a)]]
                    - truth[index_by_model[str(row.model_b)]]
                    for row in analysis.itertuples()
                ]
            )
            material = np.abs(true_differences) > 0.01
            estimated = analysis["mean_difference"].to_numpy(dtype=float)
            for method, rejected in methods.items():
                false_count = int(np.sum(rejected & ~material))
                discovery_count = int(np.sum(rejected))
                rows.append(
                    {
                        "model_count": model_count,
                        "scenario": scenario,
                        "method": method,
                        "pair_count": int(len(analysis)),
                        "discoveries": discovery_count,
                        "decision_density": discovery_count / len(analysis),
                        "false_discoveries": false_count,
                        "fdr": false_count / max(discovery_count, 1),
                        "fwer": float(false_count > 0),
                        "power": float(np.sum(rejected & material) / max(np.sum(material), 1)),
                        "directional_error": float(
                            np.sum(
                                rejected
                                & material
                                & (np.sign(estimated) != np.sign(true_differences))
                            )
                            / max(np.sum(rejected & material), 1)
                        ),
                        "materiality_threshold": 0.01,
                    }
                )
    return pd.DataFrame(rows)


def run_benchmark_dependence_stress() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for count in (3, 5, 10, 20):
        for regime in (
            "INDEPENDENT",
            "SHARED_LATENT_ABILITY",
            "BENCHMARK_CLUSTERS",
            "NEAR_REDUNDANT",
            "SPECIALIZATION",
            "REVERSAL",
        ):
            matrix = np.eye(count)
            if regime == "SHARED_LATENT_ABILITY":
                matrix[:] = 0.4
                np.fill_diagonal(matrix, 1.0)
            elif regime == "BENCHMARK_CLUSTERS":
                for left in range(count):
                    for right in range(count):
                        if left != right and left // 3 == right // 3:
                            matrix[left, right] = 0.7
            elif regime == "NEAR_REDUNDANT":
                matrix[:] = 0.9
                np.fill_diagonal(matrix, 1.0)
            elif regime == "SPECIALIZATION":
                matrix[:] = 0.2
                np.fill_diagonal(matrix, 1.0)
            elif regime == "REVERSAL":
                rho = max(-0.05, -0.95 / max(count - 1, 1))
                matrix[:] = rho
                np.fill_diagonal(matrix, 1.0)
            effective = benchmark_effective_count(matrix)
            rows.append(
                {
                    "regime": regime,
                    "raw_benchmark_count": count,
                    "effective_benchmark_count_approximation": effective,
                    "redundancy_fraction": 1.0 - effective / count,
                    "semantics": "EFFECTIVE_N_APPROXIMATION",
                }
            )
    return pd.DataFrame(rows)


def finite_sample_calibration(confirmation_records: pd.DataFrame) -> pd.DataFrame:
    return aggregate_native_metrics(
        confirmation_records,
        ("policy_id", "claim_family", "effective_n"),
    ).assign(effective_n_semantics="EFFECTIVE_N_APPROXIMATION")


def materiality_calibration(confirmation_records: pd.DataFrame) -> pd.DataFrame:
    return aggregate_native_metrics(
        confirmation_records,
        ("policy_id", "claim_family", "strong_effect"),
    ).rename(columns={"strong_effect": "strong_effect_band"})


def expanded_human_planning() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    designs = {"pilot": 50, "minimum_confirmatory": 100, "recommended": 200, "high_precision": 400}
    for design, per_stratum in designs.items():
        unique_items = per_stratum * 4
        for annotators in (2, 3):
            for adjudication_fraction in (0.10, 0.25, 0.50):
                adjudication = math.ceil(unique_items * adjudication_fraction)
                rows.append(
                    {
                        "design": design,
                        "items_per_stratum": per_stratum,
                        "strata": 4,
                        "unique_items": unique_items,
                        "annotators_per_item": annotators,
                        "adjudication_fraction": adjudication_fraction,
                        "primary_labels": unique_items * annotators,
                        "adjudication_labels": adjudication,
                        "total_labels": unique_items * annotators + adjudication,
                        "planning_only": True,
                    }
                )
    return pd.DataFrame(rows)


def annotator_noise_stress(replicates: int = 1_000) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for prevalence in (0.05, 0.20):
        for sensitivity in (0.70, 0.80, 0.90):
            for specificity in (0.70, 0.80, 0.90):
                for correlation in (0.0, 0.30):
                    seed = int(
                        7_217_000
                        + prevalence * 10_000
                        + sensitivity * 1_000
                        + specificity * 100
                        + correlation * 10
                    )
                    rng = np.random.default_rng(seed)
                    truth = rng.random(replicates) < prevalence
                    shared = rng.random(replicates)
                    votes = []
                    for _ in range(3):
                        positive_probability = np.where(truth, sensitivity, 1.0 - specificity)
                        independent_vote = rng.random(replicates) < positive_probability
                        shared_vote = shared < positive_probability
                        votes.append(
                            np.where(
                                rng.random(replicates) < correlation, shared_vote, independent_vote
                            )
                        )
                    majority = np.sum(votes, axis=0) >= 2
                    true_positive = int(np.sum(majority & truth))
                    false_positive = int(np.sum(majority & ~truth))
                    predicted_positive = int(np.sum(majority))
                    precision = true_positive / max(predicted_positive, 1)
                    interval = (
                        wilson_interval(true_positive, predicted_positive)
                        if predicted_positive
                        else None
                    )
                    rows.append(
                        {
                            "prevalence": prevalence,
                            "annotator_sensitivity": sensitivity,
                            "annotator_specificity": specificity,
                            "correlated_error_probability": correlation,
                            "replicates": replicates,
                            "majority_vote_precision": precision,
                            "majority_vote_precision_lower_95": interval.lower
                            if interval
                            else None,
                            "majority_vote_recall": true_positive / max(int(np.sum(truth)), 1),
                            "false_positive_count": false_positive,
                            "license_at_precision_0_70": bool(
                                interval is not None and interval.lower >= 0.70
                            ),
                            "evidence_role": "PLANNING_SIMULATION_ONLY",
                        }
                    )
    return pd.DataFrame(rows)


def power_uncertainty_summary(power_grid: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (stage, estimand), group in power_grid.groupby(["stage", "estimand"], sort=True):
        values = group["power"].astype(float)
        rows.append(
            {
                "stage": stage,
                "estimand": estimand,
                "worst_plausible": float(values.min()),
                "conservative": float(values.quantile(0.25)),
                "central": float(values.median()),
                "optimistic": float(values.max()),
                "source": "DECLARED_V7_1_PLANNING_GRID",
                "replace_after_s2": True,
            }
        )
    return pd.DataFrame(rows)


def run_cpu_maxout_stress_suite(
    *,
    confirmation_records_path: str | Path,
    power_grid_path: str | Path,
    output_root: str | Path,
    quick: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    confirmation = pd.read_csv(confirmation_records_path)
    confirmation["truth_supported"] = confirmation["truth_supported"].astype(bool)
    confirmation["licensed"] = confirmation["licensed"].astype(bool)
    artifacts = {
        "rank_stress": run_rank_stress(
            simulations=50,
            bootstrap_draws=100,
        ),
        "pairwise_multiplicity": run_pairwise_multiplicity_stress(
            draws_per_scenario=100 if quick else 400
        ),
        "benchmark_dependence": run_benchmark_dependence_stress(),
        "finite_sample": finite_sample_calibration(confirmation),
        "materiality": materiality_calibration(confirmation),
        "human_planning": expanded_human_planning(),
        "annotator_noise": annotator_noise_stress(100 if quick else 1_000),
        "power_uncertainty": power_uncertainty_summary(pd.read_csv(power_grid_path)),
    }
    for name, frame in artifacts.items():
        atomic_write_text(output / f"{name}.csv", frame.to_csv(index=False, lineterminator="\n"))
    rank = artifacts["rank_stress"]
    pairwise = artifacts["pairwise_multiplicity"]
    summary = {
        "schema_version": "valideval.cpu-maxout-stress.v7.2.1",
        "status": "CPU_MAXOUT_STATISTICAL_STRESS_COMPLETE",
        "mode": "NON_EVIDENCE_FIXTURE" if quick else "FULL_REGISTERED",
        "evidence_class": "NON_EVIDENCE_FIXTURE" if quick else "SYNTHETIC_STRESS",
        "rank_scenarios": int(len(rank)),
        "rank_minimum_joint_coverage": float(rank["joint_coverage"].min()),
        "rank_scope_status": (
            "RANK_SCOPE_SUPPORTED_IN_STRESSED_REGIMES"
            if float(rank["joint_coverage"].min()) >= 0.93
            else "RANK_SCOPE_RESTRICTION_REQUIRED"
        ),
        "pairwise_scenarios": int(len(pairwise)),
        "benchmark_dependence_scenarios": int(len(artifacts["benchmark_dependence"])),
        "human_plans": int(len(artifacts["human_planning"])),
        "annotator_noise_scenarios": int(len(artifacts["annotator_noise"])),
        "cpu_runs": len(artifacts),
        "monte_carlo_replicates": int(rank["simulations"].sum())
        + int(artifacts["annotator_noise"]["replicates"].sum()),
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": (
            "All results are known-truth or planning simulations. Effective benchmark count and "
            "effective N are approximations, not observed independence counts."
        ),
    }
    atomic_write_json(output / "summary.json", summary)
    return summary
