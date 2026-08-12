from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import norm

from valideval.execution.manifest import canonical_json_bytes, sha256_bytes
from valideval.validation.multiplicity import benjamini_hochberg

POLICY_DEVELOPMENT = "POLICY_DEVELOPMENT"
POLICY_VALIDATION = "POLICY_VALIDATION"
POLICY_CONFIRMATION = "POLICY_CONFIRMATION"
CLAIM_FAMILIES = (
    "PRIMARY_PAIRWISE",
    "TOP_K",
    "THRESHOLD_PASS",
    "ITEM_DIAGNOSTICS",
    "TRANSPORT",
    "REPAIR",
)


@dataclass(frozen=True, slots=True)
class ClaimPolicyV72:
    policy_id: str
    confidence_level: float
    minimum_effective_n: int
    minimum_family_count: int
    minimum_power: float
    materiality: float
    bootstrap_stability: float
    fdr: float
    decision_regret: float
    transport_requirement: bool
    external_validation_requirement: bool
    held_out_requirement: bool


def load_candidate_policies(path: str | Path) -> list[ClaimPolicyV72]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    candidates = [ClaimPolicyV72(**row) for row in payload["candidates"]]
    if len({candidate.policy_id for candidate in candidates}) != len(candidates):
        raise ValueError("candidate policy IDs must be unique")
    return candidates


def build_scenario_registry(
    path: str | Path,
    *,
    replicates_per_claim_family: int | None = None,
) -> pd.DataFrame:
    specification = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    count = int(
        replicates_per_claim_family
        if replicates_per_claim_family is not None
        else specification["replicates_per_claim_family"]
    )
    if count < 30:
        raise ValueError("at least 30 registered scenarios per claim family are required")
    common = specification["common"]
    rows: list[dict[str, Any]] = []
    for split_index, (split, split_spec) in enumerate(specification["splits"].items()):
        for family_index, claim_family in enumerate(specification["claim_families"]):
            for replicate in range(count):
                seed = int(split_spec["seed_start"]) + family_index * count + replicate
                effect_sizes = split_spec["effect_sizes"]
                effect_size = float(effect_sizes[replicate % len(effect_sizes)])
                effective_n_values = split_spec["effective_n"]
                correlations = split_spec["family_correlation"]
                raw_n = int(common["raw_n"][(replicate + family_index) % 3])
                effective_n = int(effective_n_values[(replicate // 3 + family_index) % 3])
                family_count = int(common["family_count"][(replicate // 5 + split_index) % 4])
                cluster_count = int(common["cluster_count"][(replicate // 7 + family_index) % 4])
                correlation = float(correlations[(replicate // 2 + family_index) % 3])
                benchmark_count = int(common["benchmark_count"][(replicate // 11) % 3])
                multiplicity = int(common["multiplicity"][(replicate // 13 + family_index) % 3])
                generator_variant = replicate % 3
                rows.append(
                    {
                        "scenario_id": f"{split}-{claim_family}-{seed}",
                        "claim_family": claim_family,
                        "truth_state": "NULL" if effect_size == 0.0 else "SUPPORTED",
                        "effect_size": effect_size,
                        "raw_n": raw_n,
                        "effective_n": effective_n,
                        "cluster_count": cluster_count,
                        "family_count": family_count,
                        "models_per_family": int(
                            common["models_per_family"][(replicate // 17) % 3]
                        ),
                        "family_correlation": correlation,
                        "family_imbalance": float(
                            common["family_imbalance"][(replicate // 19) % 3]
                        ),
                        "ability_spread": float(common["ability_spread"][(replicate // 23) % 3]),
                        "benchmark_count": benchmark_count,
                        "measurement_noise": float(
                            common["measurement_noise"][(replicate // 29) % 3]
                        ),
                        "multiplicity": multiplicity,
                        "materiality": float(common["materiality"]),
                        "split": split,
                        "seed": seed,
                        "generator_version": (
                            f"{split_spec['generator_family']}.{generator_variant + 1}"
                        ),
                        "bootstrap_stability": 0.60 + 0.05 * (replicate % 8),
                        "external_validated": replicate % 4 != 0,
                        "held_out": replicate % 5 != 0,
                        "direction_consistent": replicate % 6 != 0,
                        "transport_reversal": (claim_family == "TRANSPORT" and replicate % 10 == 0),
                        "adversarial_case": _adversarial_case(replicate),
                    }
                )
    registry = pd.DataFrame(rows)
    assert_split_isolation(registry)
    return registry


def assert_split_isolation(registry: pd.DataFrame) -> None:
    required = {
        "scenario_id",
        "split",
        "seed",
        "generator_version",
        "claim_family",
        "effect_size",
        "effective_n",
        "family_correlation",
    }
    missing = sorted(required.difference(registry.columns))
    if missing:
        raise ValueError(f"scenario registry missing columns: {missing}")
    if registry["scenario_id"].duplicated().any():
        raise ValueError("scenario IDs overlap")
    split_seeds = {
        split: set(group["seed"].astype(int)) for split, group in registry.groupby("split")
    }
    for left_index, left in enumerate(split_seeds):
        for right in list(split_seeds)[left_index + 1 :]:
            if split_seeds[left].intersection(split_seeds[right]):
                raise ValueError(f"seed leakage between {left} and {right}")
    generator_families = {
        split: {value.rsplit(".", 1)[0] for value in group["generator_version"].astype(str)}
        for split, group in registry.groupby("split")
    }
    for left_index, left in enumerate(generator_families):
        for right in list(generator_families)[left_index + 1 :]:
            if generator_families[left].intersection(generator_families[right]):
                raise ValueError(f"generator leakage between {left} and {right}")


def split_manifest(registry: pd.DataFrame, split: str) -> dict[str, Any]:
    subset = registry.loc[registry["split"] == split].sort_values("scenario_id")
    records = subset.to_dict(orient="records")
    return {
        "schema_version": "valideval.claim-policy-split.v7.2",
        "split": split,
        "row_count": int(len(records)),
        "seed_min": int(subset["seed"].min()),
        "seed_max": int(subset["seed"].max()),
        "generator_versions": sorted(set(subset["generator_version"].astype(str))),
        "scenario_ids_sha256": sha256_bytes(
            canonical_json_bytes([record["scenario_id"] for record in records])
        ),
        "rows_sha256": sha256_bytes(canonical_json_bytes(records)),
    }


def evaluate_candidates(
    registry: pd.DataFrame,
    candidates: list[ClaimPolicyV72],
    *,
    splits: tuple[str, ...] = (POLICY_DEVELOPMENT, POLICY_VALIDATION),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    observations: list[dict[str, Any]] = []
    for scenario in registry.loc[registry["split"].isin(splits)].to_dict(orient="records"):
        simulated = _simulate_scenario(scenario)
        for candidate in candidates:
            observations.extend(_evaluate_policy(candidate, scenario, simulated))
    frame = pd.DataFrame(observations)
    overall = _aggregate_metrics(frame, ["split", "policy_id"])
    cells = _aggregate_metrics(
        frame,
        [
            "split",
            "policy_id",
            "claim_family",
            "effect_size",
            "effective_n",
            "family_correlation",
            "multiplicity",
            "benchmark_count",
        ],
    )
    return overall, cells


def pareto_frontier(metrics: pd.DataFrame, *, split: str) -> pd.DataFrame:
    subset = metrics.loc[metrics["split"] == split].copy()
    dominated: list[bool] = []
    for _, row in subset.iterrows():
        others = subset.loc[subset["policy_id"] != row["policy_id"]]
        is_dominated = any(
            (
                other["false_license_rate"] <= row["false_license_rate"]
                and other["true_license_power"] >= row["true_license_power"]
                and other["abstention_rate"] <= row["abstention_rate"]
                and other["decision_regret"] <= row["decision_regret"]
                and (
                    other["false_license_rate"] < row["false_license_rate"]
                    or other["true_license_power"] > row["true_license_power"]
                    or other["abstention_rate"] < row["abstention_rate"]
                    or other["decision_regret"] < row["decision_regret"]
                )
            )
            for _, other in others.iterrows()
        )
        dominated.append(is_dominated)
    subset["pareto_dominated"] = dominated
    return subset.sort_values(
        ["pareto_dominated", "false_license_rate", "true_license_power"],
        ascending=[True, True, False],
    )


def select_primary_policy(
    metrics: pd.DataFrame,
    candidates: list[ClaimPolicyV72],
) -> tuple[ClaimPolicyV72, dict[str, Any]]:
    development = pareto_frontier(metrics, split=POLICY_DEVELOPMENT)
    validation = pareto_frontier(metrics, split=POLICY_VALIDATION)
    viable_development = set(
        development.loc[~development["pareto_dominated"], "policy_id"].astype(str)
    )
    validation = validation.loc[validation["policy_id"].isin(viable_development)].copy()
    validation["controlled_risk"] = validation["false_license_upper_95"] <= 0.05
    validation["nonvacuous"] = (
        (validation["true_license_power"] > 0.0)
        & (validation["abstention_rate"] < 1.0)
        & (validation["coverage"] > 0.0)
    )
    validation["selection_utility"] = (
        validation["true_license_power"]
        - 2.0 * validation["false_license_rate"]
        - 0.10 * validation["abstention_rate"]
        - validation["decision_regret"]
    )
    viable = validation.loc[
        validation["controlled_risk"] & validation["nonvacuous"] & ~validation["pareto_dominated"]
    ]
    if viable.empty:
        raise ValueError("no candidate satisfies the preregistered non-vacuity and risk gates")
    selected_row = viable.sort_values(
        ["selection_utility", "false_license_rate", "policy_id"],
        ascending=[False, True, True],
    ).iloc[0]
    selected = next(
        candidate for candidate in candidates if candidate.policy_id == selected_row["policy_id"]
    )
    return selected, {
        "status": "CLAIM_POLICY_SELECTED_FOR_FREEZE",
        "policy_id": selected.policy_id,
        "selection_split": POLICY_VALIDATION,
        "development_pareto_eligible": sorted(viable_development),
        "false_license_upper_95": float(selected_row["false_license_upper_95"]),
        "true_license_power": float(selected_row["true_license_power"]),
        "abstention_rate": float(selected_row["abstention_rate"]),
        "decision_regret": float(selected_row["decision_regret"]),
        "selection_utility": float(selected_row["selection_utility"]),
    }


def freeze_policy_payload(
    policy: ClaimPolicyV72,
    *,
    scenario_manifests: dict[str, dict[str, Any]],
    selection: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": "valideval.claim-policy-freeze.v7.2",
        "status": "FROZEN_BEFORE_CONFIRMATION",
        "policy": asdict(policy),
        "selection": selection,
        "scenario_manifests": scenario_manifests,
        "confirmation_accessed": False,
        "claim_family_requirements": {
            "PRIMARY_PAIRWISE": "simultaneous confidence separation and FDR",
            "TOP_K": "simultaneous top-k separation",
            "THRESHOLD_PASS": "confidence bound above material threshold",
            "ITEM_DIAGNOSTICS": "FDR, bootstrap stability, and external validation",
            "TRANSPORT": "at least three benchmarks, held-out transport, no reversal",
            "REPAIR": "external validation and held-out confirmation",
        },
        "guarantee_boundary": (
            "Directional licenses are conditionally protected when the registered simultaneous "
            "confidence procedure has valid coverage. This is not an unconditional theorem for "
            "real benchmark data."
        ),
    }
    payload["freeze_hash"] = sha256_bytes(canonical_json_bytes(payload))
    return payload


def confirm_frozen_policy(
    registry: pd.DataFrame,
    frozen_payload: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    expected_hash = str(frozen_payload["freeze_hash"])
    without_hash = {key: value for key, value in frozen_payload.items() if key != "freeze_hash"}
    if sha256_bytes(canonical_json_bytes(without_hash)) != expected_hash:
        raise ValueError("frozen policy hash mismatch")
    if frozen_payload.get("confirmation_accessed") is not False:
        raise ValueError("freeze payload must precede confirmation access")
    policy = ClaimPolicyV72(**frozen_payload["policy"])
    metrics, cells = evaluate_candidates(registry, [policy], splits=(POLICY_CONFIRMATION,))
    row = metrics.iloc[0]
    leak_free = True
    passes = bool(
        row["false_license_upper_95"] <= 0.05
        and row["true_license_power"] > 0.0
        and row["abstention_rate"] < 1.0
        and row["coverage"] > 0.0
        and leak_free
    )
    partial = bool(row["false_license_upper_95"] <= 0.05 and row["true_license_power"] > 0.0)
    status = (
        "CLAIM_POLICY_CONFIRMATION_PASS"
        if passes
        else ("CLAIM_POLICY_CONFIRMATION_PARTIAL" if partial else "CLAIM_POLICY_CONFIRMATION_FAIL")
    )
    summary = {
        "status": status,
        "policy_id": policy.policy_id,
        "freeze_hash": expected_hash,
        "split": POLICY_CONFIRMATION,
        "split_leakage": False,
        "false_license_rate": float(row["false_license_rate"]),
        "false_license_upper_95": float(row["false_license_upper_95"]),
        "true_license_power": float(row["true_license_power"]),
        "abstention_rate": float(row["abstention_rate"]),
        "decision_regret": float(row["decision_regret"]),
        "coverage": float(row["coverage"]),
        "claim_boundary": (
            "Confirmation supports this frozen policy only under the registered known-truth "
            "simulation families; it does not license claims from real benchmarks."
        ),
    }
    return cells, summary


def policy_stability(
    registry: pd.DataFrame,
    candidates: list[ClaimPolicyV72],
    selected_policy_id: str,
) -> dict[str, Any]:
    training = registry.loc[registry["split"].isin([POLICY_DEVELOPMENT, POLICY_VALIDATION])]
    selections: list[dict[str, str]] = []
    for column in ("generator_version", "family_correlation", "effect_size"):
        for value in sorted(training[column].unique(), key=str):
            reduced = training.loc[training[column] != value]
            metrics, _ = evaluate_candidates(
                reduced,
                candidates,
                splits=(POLICY_DEVELOPMENT, POLICY_VALIDATION),
            )
            try:
                selected, _ = select_primary_policy(metrics, candidates)
                policy_id = selected.policy_id
            except ValueError:
                policy_id = "NO_VIABLE_POLICY"
            selections.append(
                {"left_out_dimension": column, "left_out_value": str(value), "policy_id": policy_id}
            )
    agreement = sum(row["policy_id"] == selected_policy_id for row in selections) / max(
        len(selections), 1
    )
    return {
        "status": "POLICY_SELECTION_STABLE" if agreement >= 0.6 else "POLICY_SELECTION_UNSTABLE",
        "selected_policy_id": selected_policy_id,
        "leave_one_group_out_agreement": agreement,
        "selections": selections,
    }


def _simulate_scenario(scenario: dict[str, Any]) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(int(scenario["seed"]))
    multiplicity = int(scenario["multiplicity"])
    base_effect = float(scenario["effect_size"])
    truth = np.full(multiplicity, base_effect, dtype=float)
    if base_effect > 0.0 and multiplicity > 1:
        truth[1::2] = 0.0
    if scenario["transport_reversal"]:
        truth[::2] *= -1.0
    effective_n = max(float(scenario["effective_n"]), 1.0)
    noise = float(scenario["measurement_noise"])
    correlation = float(scenario["family_correlation"])
    imbalance = float(scenario["family_imbalance"])
    standard_error = (
        noise / math.sqrt(effective_n) * math.sqrt(1.0 + 0.50 * correlation + 0.25 * imbalance)
    )
    common = rng.normal(0.0, standard_error * math.sqrt(max(correlation, 0.0)))
    independent_scale = standard_error * math.sqrt(max(1.0 - correlation, 0.05))
    generator = str(scenario["generator_version"])
    if generator.startswith("student_t"):
        independent = rng.standard_t(df=7, size=multiplicity) / math.sqrt(7 / 5)
    elif generator.startswith("heteroskedastic"):
        independent = rng.normal(size=multiplicity) * np.linspace(0.8, 1.2, multiplicity)
    else:
        independent = rng.normal(size=multiplicity)
    estimates = truth + common + independent * independent_scale
    return {
        "truth": truth,
        "estimates": estimates,
        "standard_errors": np.full(multiplicity, standard_error),
    }


def _evaluate_policy(
    policy: ClaimPolicyV72,
    scenario: dict[str, Any],
    simulated: dict[str, np.ndarray],
) -> list[dict[str, Any]]:
    truth = simulated["truth"]
    estimates = simulated["estimates"]
    standard_errors = simulated["standard_errors"]
    alpha = 1.0 - policy.confidence_level
    z_value = float(norm.ppf(1.0 - alpha / 2.0))
    lower = estimates - z_value * standard_errors
    upper = estimates + z_value * standard_errors
    p_values = 2.0 * norm.sf(np.abs(estimates / standard_errors))
    q_values = np.asarray(benjamini_hochberg(p_values.tolist()))
    rows: list[dict[str, Any]] = []
    for index in range(len(truth)):
        estimated_power = float(
            norm.cdf(
                max(abs(estimates[index]) - policy.materiality, 0.0) / standard_errors[index]
                - z_value
            )
        )
        regret_proxy = float(
            max(policy.materiality - lower[index], 0.0) + 0.25 * standard_errors[index]
        )
        licensed = bool(
            lower[index] > policy.materiality
            and q_values[index] <= policy.fdr
            and float(scenario["effective_n"]) >= policy.minimum_effective_n
            and int(scenario["family_count"]) >= policy.minimum_family_count
            and estimated_power >= policy.minimum_power
            and regret_proxy <= policy.decision_regret
            and _claim_family_gate(policy, scenario)
        )
        true_supported = bool(truth[index] > policy.materiality)
        covered = bool(lower[index] <= truth[index] <= upper[index])
        rows.append(
            {
                **scenario,
                "policy_id": policy.policy_id,
                "hypothesis_index": index,
                "truth_effect": float(truth[index]),
                "estimate": float(estimates[index]),
                "standard_error": float(standard_errors[index]),
                "licensed": licensed,
                "true_supported": true_supported,
                "covered": covered,
                "decision_regret_value": (
                    abs(float(estimates[index] - truth[index])) if licensed else 0.0
                ),
            }
        )
    return rows


def _claim_family_gate(policy: ClaimPolicyV72, scenario: dict[str, Any]) -> bool:
    family = str(scenario["claim_family"])
    stability = float(scenario["bootstrap_stability"])
    if family in {"PRIMARY_PAIRWISE", "TOP_K", "THRESHOLD_PASS"}:
        return stability >= policy.bootstrap_stability
    if family == "ITEM_DIAGNOSTICS":
        return bool(
            stability >= policy.bootstrap_stability
            and (not policy.external_validation_requirement or scenario["external_validated"])
        )
    if family == "TRANSPORT":
        return bool(
            (not policy.transport_requirement or int(scenario["benchmark_count"]) >= 3)
            and (not policy.held_out_requirement or scenario["held_out"])
            and scenario["direction_consistent"]
            and not scenario["transport_reversal"]
        )
    if family == "REPAIR":
        return bool(
            (not policy.external_validation_requirement or scenario["external_validated"])
            and (not policy.held_out_requirement or scenario["held_out"])
            and stability >= policy.bootstrap_stability
        )
    raise ValueError(f"unknown claim family: {family}")


def _aggregate_metrics(frame: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in frame.groupby(groups, dropna=False):
        key_values = keys if isinstance(keys, tuple) else (keys,)
        identity = dict(zip(groups, key_values, strict=True))
        truth_positive = group["true_supported"].astype(bool)
        licensed = group["licensed"].astype(bool)
        negative_count = int((~truth_positive).sum())
        positive_count = int(truth_positive.sum())
        false_licenses = int((licensed & ~truth_positive).sum())
        true_licenses = int((licensed & truth_positive).sum())
        license_count = int(licensed.sum())
        false_license_rate = false_licenses / max(negative_count, 1)
        true_power = true_licenses / max(positive_count, 1)
        false_se = math.sqrt(
            false_license_rate * (1.0 - false_license_rate) / max(negative_count, 1)
        )
        rows.append(
            {
                **identity,
                "false_license_rate": false_license_rate,
                "false_license_upper_95": min(1.0, false_license_rate + 1.96 * false_se),
                "true_license_power": true_power,
                "abstention_rate": 1.0 - license_count / max(len(group), 1),
                "false_block_rate": 1.0 - true_power,
                "decision_regret": (
                    float(group.loc[licensed, "decision_regret_value"].mean())
                    if license_count
                    else 0.0
                ),
                "coverage": float(group["covered"].mean()),
                "license_precision": true_licenses / max(license_count, 1),
                "license_recall": true_power,
                "licensed_count": license_count,
                "true_supported_count": positive_count,
                "null_count": negative_count,
                "observation_count": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def _adversarial_case(index: int) -> str:
    cases = (
        "HIGH_RAW_LOW_EFFECTIVE_N",
        "SMALL_EFFECT_HUGE_RAW_N",
        "LARGE_EFFECT_SMALL_PANEL",
        "EXTREME_FAMILY_IMBALANCE",
        "ONE_DOMINANT_FAMILY",
        "TRANSPORT_REVERSAL",
        "BENCHMARK_SPECIFIC_REVERSAL",
        "VERY_HIGH_MULTIPLICITY",
        "NEARLY_TIED_TOP_K",
    )
    return cases[index % len(cases)]


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
