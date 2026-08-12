from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import norm

from valideval.claims.contracts import (
    AnalysisPhase,
    ClaimType,
    DecisionDirection,
    InferentialUnit,
    PrimarySecondary,
    RankIntervalType,
)
from valideval.claims.evidence import ClaimEvidence
from valideval.claims.licensing import license_claim
from valideval.claims.policies import ClaimPolicy
from valideval.execution.manifest import atomic_write_json, canonical_json_bytes, sha256_bytes
from valideval.statistics.rank_inference_v7_1 import simultaneous_rank_confidence_sets
from valideval.statistics.rare_events import (
    monte_carlo_standard_error,
    simultaneous_wilson_interval,
    wilson_interval,
)
from valideval.transport.folds import build_fold_manifest
from valideval.validation.multiplicity import benjamini_hochberg, benjamini_yekutieli

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
GENERIC_V7_2_RESULT = "GENERIC_KNOWN_TRUTH_POLICY_CALIBRATION_PASS"
PUBLICATION_GRADE = "CLAIM_POLICY_CONFIRMATION_PUBLICATION_GRADE"
PARTIAL = "CLAIM_POLICY_CONFIRMATION_PARTIAL"
SUPPORTING_ONLY = "CLAIM_POLICY_CONFIRMATION_SUPPORTING_ONLY"
FAIL = "CLAIM_POLICY_CONFIRMATION_FAIL"


@dataclass(frozen=True, slots=True)
class NativePolicyCandidate:
    policy_id: str
    policy: ClaimPolicy

    def to_dict(self) -> dict[str, Any]:
        return {"policy_id": self.policy_id, **self.policy.to_dict()}


@dataclass(frozen=True, slots=True)
class NativeScenario:
    scenario_id: str
    split: str
    claim_family: str
    replicate: int
    seed: int
    generator: str
    critical_stratum: str
    truth_supported: bool
    strong_effect: bool
    effective_n: int
    family_count: int
    family_correlation: float
    family_imbalance: float
    multiplicity: int
    measurement_noise: float


def load_native_policy_spec(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("native policy specification must be a mapping")
    required = {
        "schema_version",
        "evidence_class",
        "generic_v7_2_result",
        "split_seeds",
        "replicates_per_claim_family",
        "quick_replicates_per_claim_family",
        "minimum_confirmation_null_count_per_safety_cell",
        "family_false_license_bound",
        "critical_stratum_false_license_bound",
        "critical_strata",
        "split_generators",
        "candidates",
    }
    missing = sorted(required.difference(payload))
    if missing:
        raise ValueError(f"native policy specification missing fields: {missing}")
    if payload["generic_v7_2_result"] != GENERIC_V7_2_RESULT:
        raise ValueError("the frozen V7.2 generic result must remain explicitly preserved")
    generators = payload["split_generators"]
    generator_sets = [set(map(str, generators[split])) for split in generators]
    for left_index, left in enumerate(generator_sets):
        for right in generator_sets[left_index + 1 :]:
            if left.intersection(right):
                raise ValueError("development, validation, and confirmation generators overlap")
    if "gaussian_mixture" in generators[POLICY_CONFIRMATION]:
        payload["gaussian_mixture_implementation"] = "ACTUAL_TWO_COMPONENT_MIXTURE"
    return payload


def load_candidates(spec: Mapping[str, Any]) -> list[NativePolicyCandidate]:
    candidates: list[NativePolicyCandidate] = []
    for row in spec["candidates"]:
        values = dict(row)
        policy_id = str(values.pop("policy_id"))
        candidates.append(NativePolicyCandidate(policy_id, ClaimPolicy.from_dict(values)))
    if len({candidate.policy_id for candidate in candidates}) != len(candidates):
        raise ValueError("native policy candidate IDs must be unique")
    return candidates


def build_native_scenarios(
    spec: Mapping[str, Any],
    split: str,
    *,
    quick: bool = False,
) -> list[NativeScenario]:
    if split not in {POLICY_DEVELOPMENT, POLICY_VALIDATION, POLICY_CONFIRMATION}:
        raise ValueError(f"unknown policy split: {split}")
    count_key = {
        POLICY_DEVELOPMENT: "development",
        POLICY_VALIDATION: "validation",
        POLICY_CONFIRMATION: "confirmation",
    }[split]
    counts = (
        spec["quick_replicates_per_claim_family"] if quick else spec["replicates_per_claim_family"]
    )
    count = int(counts[count_key])
    generators = tuple(map(str, spec["split_generators"][split]))
    strata = tuple(map(str, spec["critical_strata"]))
    base_seed = int(spec["split_seeds"][split])
    scenarios: list[NativeScenario] = []
    for family_index, claim_family in enumerate(CLAIM_FAMILIES):
        for replicate in range(count):
            truth_supported = replicate % 2 == 1
            stratum = strata[(replicate // 2) % len(strata)]
            if claim_family == "REPAIR" and stratum == "DISCOVERY_VALIDATION_SHIFT":
                truth_supported = False
            if claim_family == "TRANSPORT" and stratum == "TRANSPORT_REVERSAL_RISK":
                truth_supported = False
            effective_n = (30, 60, 100, 250, 500)[(replicate // 20) % 5]
            family_count = (4, 5, 6, 8, 10)[(replicate // 40) % 5]
            family_correlation = (0.0, 0.35, 0.65, 0.85)[(replicate // 60) % 4]
            family_imbalance = (1.0, 2.0, 5.0)[(replicate // 80) % 3]
            multiplicity = (1, 10, 50, 200)[(replicate // 100) % 4]
            measurement_noise = (0.6, 1.0, 1.5)[(replicate // 120) % 3]
            if stratum == "LOW_EFFECTIVE_N":
                effective_n = 30
            elif stratum == "HIGH_FAMILY_CORRELATION":
                family_correlation = 0.9
            elif stratum == "LOW_FAMILY_COUNT":
                family_count = 4
            elif stratum == "HIGH_FAMILY_IMBALANCE":
                family_imbalance = 8.0
            elif stratum == "HIGH_MULTIPLICITY":
                multiplicity = 500
            elif stratum == "HIGH_MEASUREMENT_NOISE":
                measurement_noise = 1.8
            scenarios.append(
                NativeScenario(
                    scenario_id=f"{split}-{claim_family}-{replicate:06d}",
                    split=split,
                    claim_family=claim_family,
                    replicate=replicate,
                    seed=base_seed + family_index * 100_000 + replicate,
                    generator=generators[(replicate // (2 * len(strata))) % len(generators)],
                    critical_stratum=stratum,
                    truth_supported=truth_supported,
                    strong_effect=(replicate // (2 * len(strata))) % 2 == 1,
                    effective_n=effective_n,
                    family_count=family_count,
                    family_correlation=family_correlation,
                    family_imbalance=family_imbalance,
                    multiplicity=multiplicity,
                    measurement_noise=measurement_noise,
                )
            )
    return scenarios


def evaluate_native_policies(
    scenarios: Sequence[NativeScenario],
    candidates: Sequence[NativePolicyCandidate],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        for candidate in candidates:
            rows.append(_evaluate_scenario(scenario, candidate))
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("native policy evaluation produced no rows")
    return frame.sort_values(["policy_id", "scenario_id"]).reset_index(drop=True)


def aggregate_native_metrics(
    records: pd.DataFrame,
    group_columns: Sequence[str] = ("policy_id",),
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_key: str | list[str] = list(group_columns)
    if len(group_columns) == 1:
        group_key = str(group_columns[0])
    for key, group in records.groupby(group_key, dropna=False, sort=True):
        values = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_columns, values, strict=True))
        null = group.loc[~group["truth_supported"]]
        supported = group.loc[group["truth_supported"]]
        false_count = int(null["licensed"].sum())
        true_count = int(supported["licensed"].sum())
        interval = wilson_interval(false_count, len(null)) if len(null) else None
        row.update(
            {
                "scenario_count": int(len(group)),
                "null_count": int(len(null)),
                "supported_count": int(len(supported)),
                "false_license_count": false_count,
                "false_license_rate": false_count / len(null) if len(null) else None,
                "false_license_upper_95_wilson": interval.upper if interval else None,
                "true_license_count": true_count,
                "true_license_power": true_count / len(supported) if len(supported) else None,
                "abstention_rate": float((~group["licensed"]).mean()),
                "decision_regret": float(group["decision_regret"].mean()),
                "coverage": float(group["coverage"].mean()),
                "monte_carlo_se_false_license": (
                    monte_carlo_standard_error(false_count, len(null)) if len(null) else None
                ),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def select_native_policy(
    records: pd.DataFrame,
    candidates: Sequence[NativePolicyCandidate],
    *,
    allow_underpowered_fixture: bool = False,
) -> tuple[NativePolicyCandidate, dict[str, Any]]:
    validation = records.loc[records["split"] == POLICY_VALIDATION]
    overall = aggregate_native_metrics(validation)
    by_family = aggregate_native_metrics(validation, ("policy_id", "claim_family"))
    family_max = by_family.groupby("policy_id")["false_license_upper_95_wilson"].max()
    family_min_power = by_family.groupby("policy_id")["true_license_power"].min()
    overall = overall.set_index("policy_id")
    overall["maximum_family_false_license_upper_95"] = family_max
    overall["minimum_family_power"] = family_min_power
    overall["controlled_risk"] = overall["maximum_family_false_license_upper_95"] <= 0.05
    overall["nonvacuous"] = (overall["minimum_family_power"] > 0.0) & (
        overall["abstention_rate"] < 1.0
    )
    overall["selection_utility"] = (
        overall["true_license_power"]
        - 3.0 * overall["false_license_rate"]
        - 0.10 * overall["abstention_rate"]
        - overall["decision_regret"]
    )
    viable = overall.loc[overall["controlled_risk"] & overall["nonvacuous"]]
    if viable.empty and allow_underpowered_fixture:
        # Quick mode is explicitly NON_EVIDENCE_FIXTURE. It exercises the complete
        # route but cannot estimate rare-event safety with its small cell counts.
        viable = overall.loc[overall["nonvacuous"]]
    if viable.empty:
        raise ValueError("no native candidate passed the preregistered validation gates")
    selected_id = str(
        viable.sort_values(
            ["selection_utility", "maximum_family_false_license_upper_95"],
            ascending=[False, True],
        ).index[0]
    )
    selected = next(candidate for candidate in candidates if candidate.policy_id == selected_id)
    return selected, {
        "status": "CLAIM_POLICY_NATIVE_SELECTION_COMPLETE",
        "selected_policy_id": selected_id,
        "selection_split": POLICY_VALIDATION,
        "candidate_metrics": overall.reset_index().to_dict(orient="records"),
        "family_metrics": by_family.to_dict(orient="records"),
    }


def build_policy_freeze(
    selected: NativePolicyCandidate,
    selection: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "valideval.claim-policy-freeze.v7.2.1",
        "status": "CLAIM_POLICY_NATIVE_FROZEN_BEFORE_CONFIRMATION",
        "policy_id": selected.policy_id,
        "policy": selected.policy.to_dict(),
        "selection_split": POLICY_VALIDATION,
        "confirmation_split": POLICY_CONFIRMATION,
        "confirmation_generators": list(spec["split_generators"][POLICY_CONFIRMATION]),
        "critical_strata": list(spec["critical_strata"]),
        "minimum_confirmation_null_count_per_safety_cell": int(
            spec["minimum_confirmation_null_count_per_safety_cell"]
        ),
        "family_false_license_bound": float(spec["family_false_license_bound"]),
        "critical_stratum_false_license_bound": float(spec["critical_stratum_false_license_bound"]),
        "selection_summary_sha256": sha256_bytes(canonical_json_bytes(dict(selection))),
        "allowed_confirmation_inputs": [
            "configs/statistics/claim_policy_v7_2_1.yaml",
            "results/final_cpu_maxout/claim_policy/policy_freeze.json",
        ],
        "forbidden_confirmation_inputs": [
            "development_records.csv",
            "validation_records.csv",
            "selection_metrics.json",
        ],
    }
    payload["freeze_hash"] = sha256_bytes(canonical_json_bytes(payload))
    return payload


def validate_policy_freeze(freeze: Mapping[str, Any]) -> NativePolicyCandidate:
    payload = dict(freeze)
    observed = str(payload.pop("freeze_hash", ""))
    expected = sha256_bytes(canonical_json_bytes(payload))
    if observed != expected:
        raise ValueError("policy freeze hash mismatch")
    if payload.get("status") != "CLAIM_POLICY_NATIVE_FROZEN_BEFORE_CONFIRMATION":
        raise ValueError("policy is not frozen for confirmation")
    if payload.get("selection_split") == payload.get("confirmation_split"):
        raise ValueError("selection and confirmation split must be disjoint")
    return NativePolicyCandidate(
        policy_id=str(payload["policy_id"]),
        policy=ClaimPolicy.from_dict(dict(payload["policy"])),
    )


def confirm_native_policy(
    records: pd.DataFrame,
    freeze: Mapping[str, Any],
) -> dict[str, Any]:
    candidate = validate_policy_freeze(freeze)
    confirmation = records.loc[
        (records["split"] == POLICY_CONFIRMATION) & (records["policy_id"] == candidate.policy_id)
    ].copy()
    if confirmation.empty:
        raise ValueError("confirmation records are missing")
    family_metrics = aggregate_native_metrics(confirmation, ("policy_id", "claim_family"))
    family_safety: list[dict[str, Any]] = []
    for row in family_metrics.to_dict(orient="records"):
        interval = simultaneous_wilson_interval(
            int(row["false_license_count"]),
            int(row["null_count"]),
            family_size=len(CLAIM_FAMILIES),
        )
        row["simultaneous_false_license_upper"] = interval.upper
        row["safety_status"] = (
            "PASS" if interval.upper <= float(freeze["family_false_license_bound"]) else "FAIL"
        )
        row["power_status"] = "PASS" if float(row["true_license_power"] or 0.0) > 0.0 else "FAIL"
        family_safety.append(row)

    safety_cells = aggregate_native_metrics(
        confirmation,
        ("policy_id", "claim_family", "critical_stratum"),
    )
    critical_safety: list[dict[str, Any]] = []
    family_size = len(CLAIM_FAMILIES) * len(set(confirmation["critical_stratum"]))
    minimum_count = int(freeze["minimum_confirmation_null_count_per_safety_cell"])
    for row in safety_cells.to_dict(orient="records"):
        if int(row["null_count"]) < minimum_count:
            row["simultaneous_false_license_upper"] = None
            row["safety_status"] = "UNDERPOWERED_STRATUM"
        else:
            interval = simultaneous_wilson_interval(
                int(row["false_license_count"]),
                int(row["null_count"]),
                family_size=family_size,
            )
            row["simultaneous_false_license_upper"] = interval.upper
            row["safety_status"] = (
                "PASS"
                if interval.upper <= float(freeze["critical_stratum_false_license_bound"])
                else "FAIL"
            )
        critical_safety.append(row)

    overall = aggregate_native_metrics(confirmation).iloc[0].to_dict()
    convergence = _monte_carlo_convergence(confirmation)
    family_pass = all(
        row["safety_status"] == "PASS" and row["power_status"] == "PASS" for row in family_safety
    )
    critical_pass = all(row["safety_status"] == "PASS" for row in critical_safety)
    if family_pass and critical_pass:
        status = PUBLICATION_GRADE
    elif family_pass and not any(row["safety_status"] == "FAIL" for row in critical_safety):
        status = PARTIAL
    elif any(row["power_status"] == "PASS" for row in family_safety):
        status = SUPPORTING_ONLY
    else:
        status = FAIL
    return {
        "schema_version": "valideval.claim-policy-confirmation.v7.2.1",
        "status": status,
        "policy_id": candidate.policy_id,
        "freeze_hash": freeze["freeze_hash"],
        "evidence_class": "SYNTHETIC_KNOWN_TRUTH_CONFIRMATORY",
        "generic_v7_2_result_preserved": GENERIC_V7_2_RESULT,
        "confirmation_generators": sorted(set(confirmation["generator"].astype(str))),
        "confirmation_scenarios": int(len(confirmation)),
        "overall": overall,
        "claim_family_scope": family_safety,
        "critical_strata": critical_safety,
        "monte_carlo_convergence": convergence,
        "scope_boundary": (
            "Known-truth synthetic confirmation supports only the declared generators, claim "
            "families, safety strata, and production licensing implementation. It is not real GPU, "
            "transport, human-label, or benchmark-validity evidence."
        ),
    }


def native_policy_development(
    spec: Mapping[str, Any],
    *,
    quick: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    candidates = load_candidates(spec)
    scenarios = build_native_scenarios(spec, POLICY_DEVELOPMENT, quick=quick)
    scenarios.extend(build_native_scenarios(spec, POLICY_VALIDATION, quick=quick))
    records = evaluate_native_policies(scenarios, candidates)
    selected, selection = select_native_policy(
        records,
        candidates,
        allow_underpowered_fixture=quick,
    )
    selection["mode"] = "NON_EVIDENCE_FIXTURE" if quick else "REGISTERED_FULL"
    selection["development_scenarios"] = int(
        records.loc[records["split"] == POLICY_DEVELOPMENT, "scenario_id"].nunique()
    )
    selection["validation_scenarios"] = int(
        records.loc[records["split"] == POLICY_VALIDATION, "scenario_id"].nunique()
    )
    freeze = build_policy_freeze(selected, selection, spec)
    return records, selection, freeze


def native_policy_confirmation(
    spec: Mapping[str, Any],
    freeze: Mapping[str, Any],
    *,
    quick: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    candidate = validate_policy_freeze(freeze)
    scenarios = build_native_scenarios(spec, POLICY_CONFIRMATION, quick=quick)
    records = evaluate_native_policies(scenarios, [candidate])
    summary = confirm_native_policy(records, freeze)
    if quick:
        summary["status"] = "NON_EVIDENCE_FIXTURE"
        summary["evidence_class"] = "NON_EVIDENCE_FIXTURE"
    return records, summary


def _evaluate_scenario(
    scenario: NativeScenario,
    candidate: NativePolicyCandidate,
) -> dict[str, Any]:
    rng = np.random.default_rng(scenario.seed)
    if scenario.claim_family == "PRIMARY_PAIRWISE":
        outcome = _pairwise_outcome(scenario, candidate.policy, rng)
    elif scenario.claim_family == "TOP_K":
        outcome = _top_k_outcome(scenario, candidate.policy, rng)
    elif scenario.claim_family == "THRESHOLD_PASS":
        outcome = _threshold_outcome(scenario, candidate.policy, rng)
    elif scenario.claim_family == "ITEM_DIAGNOSTICS":
        outcome = _diagnostic_outcome(scenario, candidate.policy, rng)
    elif scenario.claim_family == "TRANSPORT":
        outcome = _transport_outcome(scenario, candidate.policy, rng)
    elif scenario.claim_family == "REPAIR":
        outcome = _repair_outcome(scenario, candidate.policy, rng)
    else:  # pragma: no cover - guarded by the registry.
        raise ValueError(f"unsupported claim family: {scenario.claim_family}")
    return {
        **asdict(scenario),
        "policy_id": candidate.policy_id,
        "licensed": bool(outcome["licensed"]),
        "license_status": str(outcome["license_status"]),
        "coverage": bool(outcome["coverage"]),
        "decision_regret": float(outcome["decision_regret"]),
        "point_estimate": float(outcome["point_estimate"]),
        "method": str(outcome["method"]),
    }


def _pairwise_outcome(
    scenario: NativeScenario,
    policy: ClaimPolicy,
    rng: np.random.Generator,
) -> dict[str, Any]:
    effect = (0.07 if scenario.strong_effect else 0.03) if scenario.truth_supported else 0.0
    scale = 0.18 * scenario.measurement_noise / math.sqrt(scenario.effective_n)
    scale *= math.sqrt(1.0 + scenario.family_correlation)
    estimate = effect + scale * _standard_noise(rng, scenario.generator)
    z = float(norm.ppf(0.5 + policy.confidence_level / 2.0))
    lower, upper = estimate - z * scale, estimate + z * scale
    regret_upper = float(norm.cdf(-abs(estimate) / max(scale, 1e-12)) * 0.05)
    evidence = _base_evidence(
        scenario,
        estimand_unit=InferentialUnit.ITEM,
        independence_unit=InferentialUnit.ITEM,
        confidence_lower=lower,
        confidence_upper=upper,
        point_estimate=estimate,
        effect_size=estimate,
        decision_regret_upper=regret_upper,
        multiplicity_controlled=True,
        q_value=min(1.0, 2.0 * norm.sf(abs(estimate / max(scale, 1e-12)))),
        hypothesis_family_id="PRESPECIFIED_PRIMARY_PAIR",
        multiplicity_scope="SINGLE_PRESPECIFIED_COMPARISON",
    )
    result = license_claim(ClaimType.MODEL_A_OUTPERFORMS_MODEL_B, evidence, policy)
    regret = abs(min(effect, 0.0)) if result.licensed else 0.0
    return _outcome(
        result.licensed,
        result.status.value,
        lower <= effect <= upper,
        regret,
        estimate,
        "STRICT_PAIRED_CI",
    )


def _top_k_outcome(
    scenario: NativeScenario,
    policy: ClaimPolicy,
    rng: np.random.Generator,
) -> dict[str, Any]:
    model_count, top_k, target = 10, 3, 2
    scores = (
        np.array([0.84, 0.76, 0.94, 0.54, 0.51, 0.48, 0.45, 0.42, 0.39, 0.36])
        if scenario.strong_effect
        else np.linspace(0.78, 0.58, model_count)
    )
    if not scenario.truth_supported:
        scores[target], scores[3] = scores[3], scores[target]
    if scenario.critical_stratum == "NEAR_TIE_TOP_K":
        scores[1:5] = np.array([0.704, 0.702, 0.700, 0.698])
        if not scenario.truth_supported:
            scores[target], scores[3] = scores[3], scores[target]
    true_ranks = pd.Series(scores).rank(ascending=False, method="average").to_numpy()
    family_ids = np.arange(model_count) % max(2, min(scenario.family_count, model_count))
    base_scale = 0.025 * scenario.measurement_noise / math.sqrt(scenario.effective_n / 30.0)
    family_noise = rng.normal(0.0, base_scale, int(family_ids.max()) + 1)
    observed = scores + math.sqrt(scenario.family_correlation) * family_noise[family_ids]
    observed += math.sqrt(max(0.0, 1.0 - scenario.family_correlation)) * rng.normal(
        0.0, base_scale, model_count
    )
    draw_count = 60
    draw_family = rng.normal(0.0, base_scale, (draw_count, int(family_ids.max()) + 1))
    draws = observed + math.sqrt(scenario.family_correlation) * draw_family[:, family_ids]
    draws += math.sqrt(max(0.0, 1.0 - scenario.family_correlation)) * rng.normal(
        0.0, base_scale, (draw_count, model_count)
    )
    columns = [f"model_{index}" for index in range(model_count)]
    intervals = simultaneous_rank_confidence_sets(
        pd.DataFrame(draws, columns=columns),
        observed_scores=pd.Series(observed, index=columns),
        confidence_level=policy.confidence_level,
        resampling_unit="family_correlated_joint_parametric_bootstrap",
    )
    target_interval = intervals.loc[intervals["model_id"] == columns[target]].iloc[0]
    draw_ranks = pd.DataFrame(draws, columns=columns).rank(
        axis=1, ascending=False, method="average"
    )
    regret_upper = float((draw_ranks[columns[target]] > top_k).mean() * 0.05)
    evidence = _base_evidence(
        scenario,
        estimand_unit=InferentialUnit.ITEM,
        independence_unit=InferentialUnit.ITEM,
        simultaneous_rank_lower=float(target_interval["simultaneous_rank_lower"]),
        simultaneous_rank_upper=float(target_interval["simultaneous_rank_upper"]),
        rank_interval_type=RankIntervalType.BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS,
        requested_top_k=top_k,
        decision_regret_upper=regret_upper,
        multiplicity_controlled=True,
        q_value=0.0,
        hypothesis_family_id="SIMULTANEOUS_TOP_K",
        multiplicity_scope="ALL_MODELS_TOP_K",
    )
    result = license_claim(ClaimType.MODEL_IN_TOP_K, evidence, policy)
    covered = (
        float(target_interval["simultaneous_rank_lower"])
        <= float(true_ranks[target])
        <= float(target_interval["simultaneous_rank_upper"])
    )
    regret = 0.05 if result.licensed and not scenario.truth_supported else 0.0
    return _outcome(
        result.licensed,
        result.status.value,
        covered,
        regret,
        observed[target],
        "BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS",
    )


def _threshold_outcome(
    scenario: NativeScenario,
    policy: ClaimPolicy,
    rng: np.random.Generator,
) -> dict[str, Any]:
    threshold = 0.50
    probability = (0.58 if scenario.strong_effect else 0.53) if scenario.truth_supported else 0.50
    if scenario.critical_stratum == "NEAR_MATERIALITY_BOUNDARY":
        probability = 0.515 if scenario.truth_supported else 0.50
    perturbation = 0.012 * _standard_noise(rng, scenario.generator)
    observed_probability = float(np.clip(probability + perturbation, 0.01, 0.99))
    successes = int(rng.binomial(scenario.effective_n, observed_probability))
    interval = wilson_interval(
        successes,
        scenario.effective_n,
        confidence_level=policy.confidence_level,
    )
    estimate = successes / scenario.effective_n
    regret_upper = max(0.0, threshold - interval.lower)
    evidence = _base_evidence(
        scenario,
        estimand_unit=InferentialUnit.ITEM,
        independence_unit=InferentialUnit.ITEM,
        point_estimate=estimate,
        confidence_lower=interval.lower,
        confidence_upper=interval.upper,
        decision_threshold=threshold,
        decision_direction=DecisionDirection.ABOVE,
        threshold_units="accuracy",
        decision_regret_upper=regret_upper,
    )
    result = license_claim(ClaimType.MODEL_CROSSES_THRESHOLD, evidence, policy)
    return _outcome(
        result.licensed,
        result.status.value,
        interval.lower <= probability <= interval.upper,
        max(0.0, threshold - probability) if result.licensed else 0.0,
        estimate,
        "STRICT_WILSON_LCB_THRESHOLD",
    )


def _diagnostic_outcome(
    scenario: NativeScenario,
    policy: ClaimPolicy,
    rng: np.random.Generator,
) -> dict[str, Any]:
    test_count = max(20, min(scenario.multiplicity, 500))
    signals = np.asarray(
        [_standard_noise(rng, scenario.generator) for _ in range(test_count)], dtype=float
    )
    if scenario.truth_supported:
        signals[0] += 4.8 if scenario.strong_effect else 3.6
    p_values = (2.0 * norm.sf(np.abs(signals))).tolist()
    q_values = benjamini_hochberg(p_values)
    by_values = benjamini_yekutieli(p_values)
    validation_signal = (
        (2.5 if scenario.truth_supported else 0.0)
        + _standard_noise(rng, "gaussian")
        - 0.6 * (scenario.critical_stratum == "DISCOVERY_VALIDATION_SHIFT")
    )
    external_validated = bool(validation_signal > norm.ppf(policy.minimum_human_precision))
    effect = float(abs(signals[0]) / 100.0)
    stability = float(np.clip(0.55 + 0.10 * abs(signals[0]), 0.0, 0.99))
    evidence = _base_evidence(
        scenario,
        estimand_unit=InferentialUnit.MODEL_FAMILY,
        independence_unit=InferentialUnit.MODEL_FAMILY,
        effective_n=scenario.family_count,
        raw_n=scenario.family_count * 3,
        cluster_count=scenario.family_count,
        q_value=float(q_values[0]),
        by_q_value=float(by_values[0]),
        multiplicity_controlled=True,
        hypothesis_family_id=f"ITEM_DIAGNOSTICS_{test_count}",
        multiplicity_scope="ALL_ITEMS_ONE_DIAGNOSTIC_FAMILY",
        bootstrap_stability=stability,
        effect_size=effect,
        external_validated=external_validated,
        human_precision_lower=0.80 if external_validated else 0.0,
    )
    result = license_claim(ClaimType.ITEM_IS_SUSPICIOUS, evidence, policy)
    return _outcome(
        result.licensed,
        result.status.value,
        True,
        0.02 if result.licensed and not scenario.truth_supported else 0.0,
        effect,
        "BH_FDR_STABILITY_EXTERNAL_VALIDATION",
    )


def _transport_outcome(
    scenario: NativeScenario,
    policy: ClaimPolicy,
    rng: np.random.Generator,
) -> dict[str, Any]:
    benchmark_count = max(3, min(8, scenario.effective_n // 30 + 3))
    true_effect = (0.09 if scenario.strong_effect else 0.05) if scenario.truth_supported else 0.0
    benchmark_effects = true_effect + 0.04 * np.asarray(
        [_standard_noise(rng, scenario.generator) for _ in range(benchmark_count)]
    )
    if scenario.critical_stratum == "TRANSPORT_REVERSAL_RISK":
        benchmark_effects[-1] = -abs(float(benchmark_effects[-1])) - 0.03
    estimate = float(np.mean(benchmark_effects))
    standard_error = float(np.std(benchmark_effects, ddof=1) / math.sqrt(benchmark_count))
    z = float(norm.ppf(0.5 + policy.confidence_level / 2.0))
    lower = estimate - z * standard_error
    fold = build_fold_manifest(
        fold_id=scenario.scenario_id,
        training_benchmarks=[f"benchmark_{index}" for index in range(benchmark_count - 1)],
        held_out_benchmark=f"benchmark_{benchmark_count - 1}",
        training_families=[f"family_{index}" for index in range(max(2, scenario.family_count - 1))],
        held_out_families=[f"family_{max(2, scenario.family_count - 1)}"],
        training_model_ids=[f"model_{index}" for index in range(8)],
        evaluation_model_ids=["held_out_model"],
        discovery_item_ids=["discovery_item"],
        evaluation_item_ids=["evaluation_item"],
        source_commit="a" * 40,
        config_hash="b" * 64,
        execution_status="EXECUTED",
        data_artifact_hashes={"synthetic_known_truth": "c" * 64},
    )
    direction_consistent = bool(np.all(benchmark_effects > 0.0))
    evidence = _base_evidence(
        scenario,
        estimand_unit=InferentialUnit.BENCHMARK,
        independence_unit=InferentialUnit.BENCHMARK,
        effective_n=benchmark_count,
        raw_n=benchmark_count,
        cluster_count=benchmark_count,
        point_estimate=estimate,
        confidence_lower=lower,
        exact_model_overlap=8,
        independent_model_families=scenario.family_count,
        transport_heterogeneity=float(np.std(benchmark_effects, ddof=1)),
        transport_direction_consistent=direction_consistent,
        transport_fold_manifest=fold,
    )
    result = license_claim(ClaimType.DIAGNOSTIC_TRANSFERS, evidence, policy)
    covered = lower <= true_effect
    return _outcome(
        result.licensed,
        result.status.value,
        covered,
        abs(true_effect) if result.licensed and not scenario.truth_supported else 0.0,
        estimate,
        "HELD_OUT_TRANSPORT_FOLD",
    )


def _repair_outcome(
    scenario: NativeScenario,
    policy: ClaimPolicy,
    rng: np.random.Generator,
) -> dict[str, Any]:
    effect = (0.07 if scenario.strong_effect else 0.035) if scenario.truth_supported else 0.0
    if scenario.critical_stratum == "DISCOVERY_VALIDATION_SHIFT":
        effect = -0.04
    scale = 0.08 * scenario.measurement_noise / math.sqrt(max(scenario.family_count, 1))
    estimate = effect + scale * _standard_noise(rng, scenario.generator)
    z = float(norm.ppf(0.5 + policy.confidence_level / 2.0))
    lower, upper = estimate - z * scale, estimate + z * scale
    regret_upper = float(norm.cdf(-abs(estimate) / max(scale, 1e-12)) * 0.05)
    evidence = _base_evidence(
        scenario,
        estimand_unit=InferentialUnit.MODEL_FAMILY,
        independence_unit=InferentialUnit.MODEL_FAMILY,
        effective_n=scenario.family_count,
        raw_n=scenario.family_count * 2,
        cluster_count=scenario.family_count,
        point_estimate=estimate,
        confidence_lower=lower,
        confidence_upper=upper,
        effect_size=estimate,
        external_validated=True,
        held_out_validated=True,
        decision_regret_upper=regret_upper,
    )
    result = license_claim(ClaimType.REPAIR_IMPROVES_DECISION, evidence, policy)
    regret = abs(min(effect, 0.0)) if result.licensed else 0.0
    return _outcome(
        result.licensed,
        result.status.value,
        lower <= effect <= upper,
        regret,
        estimate,
        "HELD_OUT_FAMILY_REPAIR_LICENSING",
    )


def _base_evidence(
    scenario: NativeScenario,
    *,
    estimand_unit: InferentialUnit,
    independence_unit: InferentialUnit,
    **changes: Any,
) -> ClaimEvidence:
    payload: dict[str, Any] = {
        "estimand_unit": estimand_unit,
        "independence_unit": independence_unit,
        "raw_n": scenario.effective_n * max(1, scenario.family_count),
        "cluster_count": scenario.family_count,
        "effective_n": scenario.effective_n,
        "dependence_structure": (
            f"known_truth_{scenario.generator};family_rho={scenario.family_correlation:.2f};"
            f"imbalance={scenario.family_imbalance:.1f}"
        ),
        "identity_verified": True,
        "leakage_guard_passed": True,
        "claim_family_id": scenario.claim_family,
        "primary_or_secondary": PrimarySecondary.PRIMARY,
        "confirmatory_or_exploratory": (
            AnalysisPhase.CONFIRMATORY
            if scenario.split == POLICY_CONFIRMATION
            else AnalysisPhase.EXPLORATORY
        ),
        "preregistered": True,
        "scope": (scenario.generator, scenario.critical_stratum),
    }
    payload.update(changes)
    return ClaimEvidence(**payload)


def _standard_noise(rng: np.random.Generator, generator: str) -> float:
    if generator == "gaussian":
        return float(rng.normal())
    if generator == "gaussian_mixture":
        component = int(rng.random() < 0.15)
        return float(rng.normal(0.0, 2.2 if component else 0.75))
    if generator == "student_t":
        return float(rng.standard_t(5) / math.sqrt(5 / 3))
    if generator == "skewed":
        return float((rng.lognormal(0.0, 0.55) - math.exp(0.55**2 / 2)) / 0.65)
    if generator == "heteroskedastic":
        return float(rng.normal(0.0, rng.choice([0.55, 1.45])))
    if generator == "contaminated_gaussian":
        return float(rng.normal(0.0, 4.0 if rng.random() < 0.04 else 0.85))
    if generator == "beta_binomial":
        return float((rng.beta(4.0, 4.0) - 0.5) / math.sqrt(1.0 / 36.0))
    if generator == "correlated_bernoulli":
        latent = rng.normal()
        values = rng.binomial(1, norm.cdf(0.6 * latent), size=8)
        return float((values.mean() - 0.5) / 0.25)
    if generator == "logistic_mixed_effects":
        value = rng.logistic(0.0, math.sqrt(3.0) / math.pi)
        return float(value)
    if generator == "latent_family_mixture":
        return float(0.7 * rng.normal() + 0.3 * rng.choice([-2.0, 2.0]))
    if generator == "nonlinear_benchmark_effect":
        value = rng.normal()
        return float((value + 0.15 * (value * value - 1.0)) / 1.05)
    raise ValueError(f"unknown simulator generator: {generator}")


def _outcome(
    licensed: bool,
    license_status: str,
    coverage: bool,
    decision_regret: float,
    point_estimate: float,
    method: str,
) -> dict[str, Any]:
    return {
        "licensed": licensed,
        "license_status": license_status,
        "coverage": coverage,
        "decision_regret": decision_regret,
        "point_estimate": point_estimate,
        "method": method,
    }


def _monte_carlo_convergence(records: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for claim_family, family in records.groupby("claim_family", sort=True):
        family = family.sort_values("replicate")
        for count in (100, 250, 500, 1000, 2500, 5000):
            subset = family.iloc[: min(count, len(family))]
            null = subset.loc[~subset["truth_supported"]]
            supported = subset.loc[subset["truth_supported"]]
            false_count = int(null["licensed"].sum())
            rows.append(
                {
                    "claim_family": claim_family,
                    "requested_replicates": count,
                    "used_replicates": int(len(subset)),
                    "false_license_rate": false_count / len(null) if len(null) else None,
                    "false_license_mcse": (
                        monte_carlo_standard_error(false_count, len(null)) if len(null) else None
                    ),
                    "power": float(supported["licensed"].mean()) if len(supported) else None,
                    "abstention": float((~subset["licensed"]).mean()),
                }
            )
    return rows


def records_sha256(records: pd.DataFrame) -> str:
    normalized = records.sort_values(["policy_id", "scenario_id"]).to_dict(orient="records")
    return hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()


def write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    return atomic_write_json(path, dict(payload))
