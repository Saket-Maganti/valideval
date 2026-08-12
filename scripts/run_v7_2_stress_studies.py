from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import norm


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7.2 effective-N and decision stresses.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("results/v7_2/claim_policy/simulation_scenario_registry.csv"),
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("results/v7_2/claim_policy/claim_policy_v7_2_frozen.yaml"),
    )
    parser.add_argument("--output", type=Path, default=Path("results/v7_2/stress"))
    args = parser.parse_args()
    started = time.perf_counter()
    registry = pd.read_csv(args.registry)
    frozen = yaml.safe_load(args.policy.read_text(encoding="utf-8"))
    policy = frozen["policy"]
    inference_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    for scenario in registry.loc[
        registry["split"].isin(["POLICY_DEVELOPMENT", "POLICY_VALIDATION"])
    ].to_dict(orient="records"):
        rng = np.random.default_rng(int(scenario["seed"]) + 77)
        truth = float(scenario["effect_size"])
        noise = float(scenario["measurement_noise"])
        raw_se = noise / math.sqrt(max(float(scenario["raw_n"]), 1.0))
        proper_se = noise / math.sqrt(max(float(scenario["effective_n"]), 1.0)) * math.sqrt(
            1.0
            + 0.5 * float(scenario["family_correlation"])
            + 0.25 * float(scenario["family_imbalance"])
        )
        estimate = truth + rng.normal(0.0, proper_se)
        family_se = noise / math.sqrt(max(float(scenario["family_count"]), 1.0))
        methods = {
            "NAIVE_CHECKPOINT": (raw_se, 1.96, True),
            "FAMILY_CLUSTER_BOOTSTRAP": (proper_se, 1.96, True),
            "FAMILY_BALANCED": (proper_se * 0.95, 1.96, True),
            "ONE_MODEL_PER_FAMILY": (family_se, 1.96, True),
            "VALIDEVAL_LICENSING": (
                proper_se,
                float(
                    norm.ppf(
                        1.0
                        - float(policy["fdr"])
                        / (2.0 * max(int(scenario["multiplicity"]), 1))
                    )
                ),
                _policy_prerequisites(policy, scenario),
            ),
        }
        for method, (standard_error, critical, prerequisites) in methods.items():
            lower = estimate - critical * standard_error
            upper = estimate + critical * standard_error
            licensed = bool(
                prerequisites and lower > float(policy["materiality"])
            )
            true_supported = truth > float(policy["materiality"])
            inference_rows.append(
                {
                    **scenario,
                    "method": method,
                    "estimate": estimate,
                    "standard_error": standard_error,
                    "licensed": licensed,
                    "true_supported": true_supported,
                    "false_directional_decision": bool(licensed and not true_supported),
                    "CI_coverage": bool(lower <= truth <= upper),
                    "inflated_significance": bool(
                        method == "NAIVE_CHECKPOINT"
                        and licensed
                        and not (estimate - 1.96 * proper_se > float(policy["materiality"]))
                    ),
                    "false_transport": bool(
                        scenario["claim_family"] == "TRANSPORT"
                        and licensed
                        and not true_supported
                    ),
                    "power_event": bool(licensed and true_supported),
                    "stress_case": _stress_case(scenario),
                }
            )

        decision_methods = {
            "FORCED_LEADERBOARD": True,
            "CI_AWARE_RANKING": abs(estimate) > 1.96 * proper_se,
            "MULTIPLICITY_AWARE_RANKING": abs(estimate)
            > float(norm.ppf(1.0 - 0.05 / (2 * max(int(scenario["multiplicity"]), 1))))
            * proper_se,
            "VALIDEVAL_SELECTIVE_LICENSING": methods["VALIDEVAL_LICENSING"][2]
            and estimate - methods["VALIDEVAL_LICENSING"][1] * proper_se
            > float(policy["materiality"]),
        }
        truth_direction = 0 if abs(truth) <= float(policy["materiality"]) else 1
        estimate_direction = 1 if estimate > 0 else -1
        for method, decided in decision_methods.items():
            directional_error = bool(decided and estimate_direction != truth_direction)
            decision_rows.append(
                {
                    **scenario,
                    "method": method,
                    "directional_error": directional_error,
                    "abstained": not decided,
                    "regret": abs(estimate - truth) if decided else 0.0,
                    "top_k_error": directional_error,
                    "coverage": bool(abs(estimate - truth) <= 1.96 * proper_se),
                }
            )

    inference = pd.DataFrame(inference_rows)
    decisions = pd.DataFrame(decision_rows)
    args.output.mkdir(parents=True, exist_ok=True)
    family_stress = _aggregate_inference(
        inference,
        [
            "method",
            "family_count",
            "models_per_family",
            "family_correlation",
            "family_imbalance",
            "ability_spread",
        ],
    )
    effective_stress = _aggregate_inference(
        inference,
        ["method", "stress_case", "raw_n", "effective_n", "family_count"],
    )
    selective = (
        decisions.groupby("method", as_index=False)
        .agg(
            directional_error=("directional_error", "mean"),
            abstention=("abstained", "mean"),
            regret=("regret", "mean"),
            top_k_error=("top_k_error", "mean"),
            coverage=("coverage", "mean"),
        )
        .sort_values("method")
    )
    family_stress.to_csv(args.output / "family_dependence_stress.csv", index=False)
    effective_stress.to_csv(args.output / "effective_n_stress.csv", index=False)
    selective.to_csv(args.output / "selective_decision_study.csv", index=False)
    inference.to_csv(args.output / "stress_observations.csv", index=False)
    summary = _summary(inference, selective, frozen["freeze_hash"])
    summary["runtime_seconds"] = time.perf_counter() - started
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"{summary['status']}: effective-N={summary['effective_n_stress_status']} "
        f"family={summary['family_dependence_status']}"
    )
    return 0


def _policy_prerequisites(policy: dict[str, Any], scenario: dict[str, Any]) -> bool:
    base = bool(
        float(scenario["effective_n"]) >= float(policy["minimum_effective_n"])
        and int(scenario["family_count"]) >= int(policy["minimum_family_count"])
        and float(scenario["bootstrap_stability"]) >= float(policy["bootstrap_stability"])
    )
    family = str(scenario["claim_family"])
    if family == "ITEM_DIAGNOSTICS":
        base = base and bool(scenario["external_validated"])
    elif family == "TRANSPORT":
        base = base and bool(
            int(scenario["benchmark_count"]) >= 3
            and scenario["held_out"]
            and scenario["direction_consistent"]
            and not scenario["transport_reversal"]
        )
    elif family == "REPAIR":
        base = base and bool(scenario["external_validated"] and scenario["held_out"])
    return base


def _stress_case(scenario: dict[str, Any]) -> str:
    if float(scenario["raw_n"]) >= 10_000 and float(scenario["effective_n"]) <= 24:
        return "HUGE_RAW_N_TINY_EFFECTIVE_N"
    if (
        float(scenario["raw_n"]) <= 10_000
        and float(scenario["effective_n"]) >= 54
        and int(scenario["family_count"]) >= 6
        and float(scenario["family_correlation"]) <= 0.6
    ):
        return "MODERATE_RAW_N_STRONG_INDEPENDENT_EVIDENCE"
    if int(scenario["models_per_family"]) >= 8 and int(scenario["family_count"]) <= 4:
        return "MANY_CHECKPOINTS_FEW_FAMILIES"
    if float(scenario["family_imbalance"]) >= 0.9:
        return "ONE_DOMINANT_FAMILY"
    return "GENERAL_STRESS"


def _aggregate_inference(frame: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    rows = []
    for keys, group in frame.groupby(groups, dropna=False):
        values = keys if isinstance(keys, tuple) else (keys,)
        truth = group["true_supported"].astype(bool)
        licensed = group["licensed"].astype(bool)
        rows.append(
            {
                **dict(zip(groups, values, strict=True)),
                "false_directional_decisions": float(
                    group["false_directional_decision"].mean()
                ),
                "CI_undercoverage": 1.0 - float(group["CI_coverage"].mean()),
                "inflated_significance": float(group["inflated_significance"].mean()),
                "false_transport": float(group["false_transport"].mean()),
                "power": float((licensed & truth).sum() / max(int(truth.sum()), 1)),
                "abstention": 1.0 - float(licensed.mean()),
                "observations": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def _summary(
    inference: pd.DataFrame, selective: pd.DataFrame, freeze_hash: str
) -> dict[str, Any]:
    huge = inference.loc[
        (inference["stress_case"] == "HUGE_RAW_N_TINY_EFFECTIVE_N")
        & (inference["method"].isin(["NAIVE_CHECKPOINT", "VALIDEVAL_LICENSING"]))
    ]
    false_by_method = huge.groupby("method")["false_directional_decision"].mean()
    strong = inference.loc[
        (inference["stress_case"] == "MODERATE_RAW_N_STRONG_INDEPENDENT_EVIDENCE")
        & (inference["method"] == "VALIDEVAL_LICENSING")
    ]
    strong_truth = strong["true_supported"].astype(bool)
    strong_power = float(
        (strong["licensed"].astype(bool) & strong_truth).sum() / max(int(strong_truth.sum()), 1)
    )
    valid_false = float(false_by_method.get("VALIDEVAL_LICENSING", 1.0))
    naive_false = float(false_by_method.get("NAIVE_CHECKPOINT", 0.0))
    effective_pass = valid_false <= naive_false and strong_power > 0.0
    family_subset = inference.loc[inference["method"] == "VALIDEVAL_LICENSING"]
    family_pass = bool(
        family_subset["false_directional_decision"].mean()
        < inference.loc[inference["method"] == "NAIVE_CHECKPOINT", "false_directional_decision"].mean()
    )
    valid_decision = selective.loc[
        selective["method"] == "VALIDEVAL_SELECTIVE_LICENSING"
    ].iloc[0]
    selective_pass = bool(valid_decision["abstention"] < 1.0)
    return {
        "status": "V7_2_STRESS_STUDIES_COMPLETE",
        "policy_freeze_hash": freeze_hash,
        "effective_n_stress_status": (
            "EFFECTIVE_N_STRESS_PASS" if effective_pass else "EFFECTIVE_N_STRESS_PARTIAL"
        ),
        "family_dependence_status": (
            "FAMILY_DEPENDENCE_STRESS_PASS"
            if family_pass
            else "FAMILY_DEPENDENCE_STRESS_PARTIAL"
        ),
        "selective_decision_status": (
            "SELECTIVE_DECISION_USEFUL_FRONTIER"
            if selective_pass
            else "SELECTIVE_DECISION_VACUOUS"
        ),
        "huge_raw_tiny_effective_false_directional": {
            "naive": naive_false,
            "valideval": valid_false,
        },
        "strong_independent_evidence_power": strong_power,
        "claim_boundary": (
            "Known-truth CPU stress behavior is conditional on this registered simulator and "
            "does not prove error control for arbitrary benchmark data."
        ),
    }


if __name__ == "__main__":
    raise SystemExit(main())
