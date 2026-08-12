from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

from valideval.claims import (
    ClaimEvidence,
    ClaimPolicy,
    ClaimType,
    InferentialUnit,
    license_claim,
)
from valideval.validation.multiplicity import benjamini_hochberg

CALIBRATION_METHODS = (
    "NAIVE_POINT_ESTIMATE",
    "CI_ONLY",
    "FDR_ONLY",
    "VALIDEVAL_FULL_LICENSING",
)


def run_claim_policy_calibration(
    *,
    simulations: int = 200,
    seed: int = 7201,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Estimate operating characteristics under known simulation truth."""

    if simulations < 100:
        raise ValueError("claim calibration requires at least 100 replicates per cell")
    alpha = 0.05
    materiality = 0.01
    rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    cell = 0
    for effect_size in (0.0, 0.01, 0.03):
        for raw_n in (1_000, 10_000):
            for effective_n in (10, 100, 500):
                if effective_n > raw_n:
                    continue
                for family_dependence in (0.0, 0.5, 0.9):
                    for multiplicity in (1, 20):
                        for heterogeneity in (0.0, 0.2):
                            rng = np.random.default_rng(seed + cell)
                            cell += 1
                            outcomes: dict[str, list[tuple[bool, bool]]] = {
                                method: [] for method in CALIBRATION_METHODS
                            }
                            directional = {
                                method: {"wrong": 0, "abstain": 0, "regret": 0.0}
                                for method in CALIBRATION_METHODS
                            }
                            coverages = []
                            for _ in range(simulations):
                                truth = np.full(multiplicity, effect_size, dtype=float)
                                if multiplicity > 1:
                                    truth[::2] = 0.0
                                design_effect = math.sqrt(
                                    1.0 + family_dependence * max(raw_n / effective_n - 1.0, 0.0)
                                )
                                standard_error = (
                                    0.08
                                    * design_effect
                                    * math.sqrt(100.0 / effective_n)
                                    * math.sqrt(1.0 + heterogeneity**2)
                                )
                                estimates = rng.normal(truth, standard_error)
                                lower = estimates - 1.96 * standard_error
                                upper = estimates + 1.96 * standard_error
                                p_values = 2.0 * norm.sf(np.abs(estimates / standard_error))
                                q_values = np.asarray(benjamini_hochberg(p_values.tolist()))
                                coverages.extend(((lower <= truth) & (truth <= upper)).tolist())
                                for index, true_effect in enumerate(truth):
                                    truth_positive = true_effect > materiality
                                    licenses = {
                                        "NAIVE_POINT_ESTIMATE": estimates[index] > materiality,
                                        "CI_ONLY": lower[index] > materiality,
                                        "FDR_ONLY": q_values[index] <= alpha
                                        and estimates[index] > 0.0,
                                    }
                                    full = license_claim(
                                        ClaimType.MODEL_A_OUTPERFORMS_MODEL_B,
                                        ClaimEvidence(
                                            point_estimate=float(estimates[index]),
                                            confidence_lower=float(lower[index]),
                                            confidence_upper=float(upper[index]),
                                            estimand_unit=InferentialUnit.ITEM,
                                            raw_n=raw_n,
                                            cluster_count=max(1, int(effective_n)),
                                            effective_n=float(effective_n),
                                            independence_unit=InferentialUnit.ITEM,
                                            dependence_structure=(
                                                f"family_dependence={family_dependence:.2f}; "
                                                f"design_effect={design_effect:.6f}"
                                            ),
                                            q_value=float(q_values[index]),
                                            multiplicity_controlled=True,
                                            hypothesis_family_id="CALIBRATION_ALL_PAIRS",
                                            multiplicity_scope=(
                                                "SINGLE_PRESPECIFIED_COMPARISON"
                                                if multiplicity == 1
                                                else "ALL_PAIRS_LEADERBOARD"
                                            ),
                                            decision_regret_upper=float(1.96 * standard_error),
                                        ),
                                        ClaimPolicy(effect_size_threshold=materiality),
                                    )
                                    licenses["VALIDEVAL_FULL_LICENSING"] = full.licensed
                                    for method, licensed in licenses.items():
                                        outcomes[method].append((truth_positive, bool(licensed)))
                                        if licensed and estimates[index] * true_effect < 0.0:
                                            directional[method]["wrong"] += 1
                                        if not licensed:
                                            directional[method]["abstain"] += 1
                                        if licensed:
                                            directional[method]["regret"] += abs(
                                                float(estimates[index] - true_effect)
                                            )
                            total_tests = simulations * multiplicity
                            for method, values in outcomes.items():
                                truth_positive_count = sum(truth for truth, _ in values)
                                truth_negative_count = len(values) - truth_positive_count
                                false_license = sum(
                                    (not truth) and licensed for truth, licensed in values
                                )
                                false_block = sum(
                                    truth and (not licensed) for truth, licensed in values
                                )
                                true_license = sum(truth and licensed for truth, licensed in values)
                                false_license_rate = false_license / max(truth_negative_count, 1)
                                power = true_license / max(truth_positive_count, 1)
                                rows.append(
                                    {
                                        "method": method,
                                        "effect_size": effect_size,
                                        "raw_n": raw_n,
                                        "effective_n": effective_n,
                                        "family_dependence": family_dependence,
                                        "measurement_noise": 0.08,
                                        "multiplicity": multiplicity,
                                        "transport_heterogeneity": heterogeneity,
                                        "false_license_rate": false_license_rate,
                                        "false_block_rate": false_block
                                        / max(truth_positive_count, 1),
                                        "coverage": float(np.mean(coverages)),
                                        "power": power,
                                        "false_license_monte_carlo_se": math.sqrt(
                                            false_license_rate
                                            * (1.0 - false_license_rate)
                                            / max(truth_negative_count, 1)
                                        ),
                                        "power_monte_carlo_se": math.sqrt(
                                            power * (1.0 - power) / max(truth_positive_count, 1)
                                        ),
                                        "replicates": simulations,
                                        "evidence_role": "KNOWN_TRUTH_CPU_SIMULATION",
                                    }
                                )
                                decision_rows.append(
                                    {
                                        "method": method,
                                        "effect_size": effect_size,
                                        "effective_n": effective_n,
                                        "family_dependence": family_dependence,
                                        "multiplicity": multiplicity,
                                        "wrong_directional_decision_rate": directional[method][
                                            "wrong"
                                        ]
                                        / total_tests,
                                        "abstention_rate": directional[method]["abstain"]
                                        / total_tests,
                                        "mean_decision_regret": directional[method]["regret"]
                                        / total_tests,
                                        "guarantee_type": "EMPIRICAL_NOT_THEOREM",
                                    }
                                )
    calibration = pd.DataFrame(rows)
    decisions = pd.DataFrame(decision_rows)
    summary = {
        "status": "CLAIM_POLICY_CALIBRATION_READY",
        "simulation_cells": int(len(calibration) / len(CALIBRATION_METHODS)),
        "simulations_per_cell": simulations,
        "methods": list(CALIBRATION_METHODS),
        "v7_primary_synthetic_result": "FAILED_AND_UNCHANGED",
        "claim_boundary": (
            "Operating characteristics are conditional on the declared simulation family and "
            "do not prove calibration on real benchmark claims."
        ),
    }
    return calibration, decisions, summary
