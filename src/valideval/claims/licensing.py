from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from valideval.claims.contracts import (
    ClaimClass,
    ClaimLicenseResult,
    ClaimStatus,
    ClaimType,
    DecisionDirection,
    InferentialUnit,
    RankIntervalType,
)
from valideval.claims.evidence import ClaimEvidence
from valideval.claims.policies import ClaimPolicy
from valideval.transport.folds import FoldManifestError, validate_fold_manifest

_EXTERNAL_CLAIMS = {ClaimType.ITEM_IS_SUSPICIOUS, ClaimType.REPAIR_IMPROVES_DECISION}
_TRANSPORT_CLAIMS = {ClaimType.DIAGNOSTIC_TRANSFERS}
_DECISION_CLAIMS = {
    ClaimType.MODEL_A_OUTPERFORMS_MODEL_B,
    ClaimType.MODEL_IN_TOP_K,
    ClaimType.MODEL_CROSSES_THRESHOLD,
    ClaimType.MODEL_FAMILY_BEST,
    ClaimType.REPAIR_IMPROVES_DECISION,
}
_MULTIPLE_TEST_CLAIMS = {ClaimType.ITEM_IS_SUSPICIOUS, ClaimType.SUBJECT_IS_UNSTABLE}
_INFERENTIAL_UNITS = {
    ClaimType.MODEL_A_OUTPERFORMS_MODEL_B: {InferentialUnit.ITEM, InferentialUnit.SUBJECT},
    ClaimType.MODEL_IN_TOP_K: {InferentialUnit.ITEM, InferentialUnit.SUBJECT},
    ClaimType.MODEL_CROSSES_THRESHOLD: {InferentialUnit.ITEM, InferentialUnit.SUBJECT},
    ClaimType.MODEL_FAMILY_BEST: {InferentialUnit.MODEL_FAMILY},
    ClaimType.ITEM_IS_SUSPICIOUS: {InferentialUnit.MODEL_FAMILY},
    ClaimType.SUBJECT_IS_UNSTABLE: {InferentialUnit.SUBJECT},
    ClaimType.BENCHMARK_RANKING_IS_STABLE: {InferentialUnit.SUBJECT},
    ClaimType.DIAGNOSTIC_TRANSFERS: {InferentialUnit.BENCHMARK, InferentialUnit.MODEL_FAMILY},
    ClaimType.REPAIR_IMPROVES_DECISION: {
        InferentialUnit.MODEL_FAMILY,
        InferentialUnit.BENCHMARK,
    },
}


def license_claim(
    claim: ClaimType | str,
    evidence: ClaimEvidence | Mapping[str, Any],
    policy: ClaimPolicy | Mapping[str, Any] | None = None,
) -> ClaimLicenseResult:
    """License a claim only when all claim-specific, predeclared conditions pass."""

    claim_type = ClaimType(claim)
    ev = evidence if isinstance(evidence, ClaimEvidence) else ClaimEvidence(**dict(evidence))
    if policy is None:
        resolved_policy = ClaimPolicy()
    else:
        resolved_policy = (
            policy if isinstance(policy, ClaimPolicy) else ClaimPolicy.from_dict(dict(policy))
        )

    checks: list[tuple[str, bool | None]] = []

    def result(status: ClaimStatus, reason: str, claim_class: ClaimClass = ClaimClass.BLOCKED):
        return ClaimLicenseResult(
            status=status,
            claim_class=claim_class,
            claim_type=claim_type,
            reasons=(reason,),
            scope=ev.scope,
            checks=tuple(checks),
        )

    checks.append(("identity_verified", ev.identity_verified))
    if not ev.identity_verified:
        return result(
            ClaimStatus.BLOCKED_BY_IDENTITY, "Exact item/model identity was not verified."
        )
    checks.append(("leakage_guard_passed", ev.leakage_guard_passed))
    if not ev.leakage_guard_passed:
        return result(ClaimStatus.BLOCKED_BY_LEAKAGE, "A preregistered leakage guard failed.")
    effective_n_pass, effective_n_reason = _effective_n_passes(claim_type, ev, resolved_policy)
    checks.append(("dependence_aware_effective_n", effective_n_pass))
    if not effective_n_pass:
        return result(ClaimStatus.UNDERPOWERED, effective_n_reason)
    power_pass = ev.power is None or ev.power >= resolved_policy.minimum_power
    checks.append(("minimum_power", power_pass if ev.power is not None else None))
    if ev.power is not None and not power_pass:
        return result(ClaimStatus.UNDERPOWERED, "Estimated power is below policy.")

    if _requires_multiplicity(claim_type, ev):
        q_value = ev.by_q_value if resolved_policy.require_by_sensitivity else ev.q_value
        multiple_pass = (
            ev.multiplicity_controlled
            and q_value is not None
            and q_value <= resolved_policy.fdr_level
            and bool(ev.hypothesis_family_id)
            and bool(ev.multiplicity_scope)
        )
        checks.append(("multiplicity", multiple_pass))
        if not multiple_pass:
            return result(
                ClaimStatus.BLOCKED_BY_MULTIPLICITY,
                "The multiplicity-adjusted result does not pass the configured FDR policy.",
            )

    uncertainty_pass = _uncertainty_passes(claim_type, ev, resolved_policy)
    checks.append(("uncertainty_and_materiality", uncertainty_pass))
    if not uncertainty_pass:
        return result(
            ClaimStatus.BLOCKED_BY_UNCERTAINTY,
            "The confidence bound or stability estimate does not clear the materiality policy.",
        )

    if claim_type in _EXTERNAL_CLAIMS or resolved_policy.external_validation_required:
        external_pass = ev.external_validated
        if ev.human_precision_lower is not None:
            external_pass = (
                external_pass
                and ev.human_precision_lower >= resolved_policy.minimum_human_precision
            )
        checks.append(("external_validation", external_pass))
        if not external_pass:
            return result(
                ClaimStatus.BLOCKED_BY_EXTERNAL_VALIDATION,
                "Required independent or human validation has not passed.",
            )

    if claim_type in _TRANSPORT_CLAIMS:
        overlap_pass = ev.exact_model_overlap >= resolved_policy.minimum_exact_model_overlap
        family_pass = (
            ev.independent_model_families >= resolved_policy.minimum_independent_model_families
        )
        heterogeneity_pass = (
            ev.transport_heterogeneity is not None
            and ev.transport_heterogeneity <= resolved_policy.transport_heterogeneity_threshold
        )
        direction_pass = ev.transport_direction_consistent is True
        fold_pass = False
        if ev.transport_fold_manifest is not None:
            try:
                fold = validate_fold_manifest(ev.transport_fold_manifest)
                fold_pass = fold["execution_status"] == "EXECUTED"
            except FoldManifestError:
                fold_pass = False
        transport_pass = (
            overlap_pass and family_pass and heterogeneity_pass and direction_pass and fold_pass
        )
        checks.extend(
            [
                ("exact_model_overlap", overlap_pass),
                ("independent_model_families", family_pass),
                ("transport_heterogeneity", heterogeneity_pass),
                ("transport_direction", direction_pass),
                ("transport_fold_manifest", fold_pass),
            ]
        )
        if not transport_pass:
            return result(
                ClaimStatus.BLOCKED_BY_TRANSPORT,
                "Held-out transport evidence does not pass overlap, family, direction, and heterogeneity gates.",
            )

    if (
        resolved_policy.held_out_validation_required
        or claim_type is ClaimType.REPAIR_IMPROVES_DECISION
    ):
        checks.append(("held_out_validation", ev.held_out_validated))
        if not ev.held_out_validated:
            return result(
                ClaimStatus.BLOCKED_BY_EXTERNAL_VALIDATION,
                "The claim requires held-out validation under this policy.",
            )

    claim_class = _licensed_class(claim_type)
    if claim_type in _DECISION_CLAIMS:
        regret_pass = (
            ev.decision_regret_upper is not None
            and ev.decision_regret_upper <= resolved_policy.decision_regret_bound
        )
        checks.append(("decision_regret", regret_pass))
        if not regret_pass:
            return result(
                ClaimStatus.BLOCKED_BY_UNCERTAINTY,
                "The upper confidence bound on decision regret exceeds policy.",
            )
    status = ClaimStatus.LICENSED_WITH_SCOPE if ev.scope else ClaimStatus.LICENSED
    return result(status, "All applicable predeclared gates passed.", claim_class)


def _uncertainty_passes(
    claim_type: ClaimType,
    evidence: ClaimEvidence,
    policy: ClaimPolicy,
) -> bool:
    if claim_type is ClaimType.MODEL_A_OUTPERFORMS_MODEL_B:
        return (
            evidence.confidence_lower is not None
            and evidence.confidence_lower > policy.effect_size_threshold
        )
    if claim_type is ClaimType.MODEL_IN_TOP_K:
        try:
            interval_type = RankIntervalType(evidence.rank_interval_type)
        except (TypeError, ValueError):
            interval_type = None
        return (
            evidence.simultaneous_rank_upper is not None
            and evidence.requested_top_k is not None
            and interval_type is RankIntervalType.BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS
            and evidence.simultaneous_rank_upper <= evidence.requested_top_k
        )
    if claim_type is ClaimType.MODEL_CROSSES_THRESHOLD:
        if evidence.decision_threshold is None:
            return False
        direction = DecisionDirection(evidence.decision_direction)
        if direction is DecisionDirection.ABOVE:
            return (
                evidence.confidence_lower is not None
                and evidence.confidence_lower > evidence.decision_threshold
            )
        return (
            evidence.confidence_upper is not None
            and evidence.confidence_upper < evidence.decision_threshold
        )
    if claim_type is ClaimType.ITEM_IS_SUSPICIOUS:
        return (
            evidence.bootstrap_stability is not None
            and evidence.bootstrap_stability >= policy.bootstrap_stability_threshold
            and evidence.effect_size is not None
            and abs(evidence.effect_size) >= policy.effect_size_threshold
        )
    if claim_type is ClaimType.BENCHMARK_RANKING_IS_STABLE:
        return (
            evidence.bootstrap_stability is not None
            and evidence.bootstrap_stability >= policy.bootstrap_stability_threshold
        )
    if claim_type is ClaimType.DIAGNOSTIC_TRANSFERS:
        return evidence.confidence_lower is not None and evidence.confidence_lower > 0.0
    return (
        evidence.confidence_lower is not None
        and evidence.effect_size is not None
        and abs(evidence.effect_size) >= policy.effect_size_threshold
        and evidence.confidence_lower > 0.0
    )


def _licensed_class(claim_type: ClaimType) -> ClaimClass:
    if claim_type in _TRANSPORT_CLAIMS:
        return ClaimClass.TRANSPORTABLE
    if claim_type in _DECISION_CLAIMS:
        return ClaimClass.DECISION_LICENSED
    if claim_type in _EXTERNAL_CLAIMS:
        return ClaimClass.EXTERNALLY_VALIDATED
    if claim_type in {ClaimType.BENCHMARK_RANKING_IS_STABLE, ClaimType.SUBJECT_IS_UNSTABLE}:
        return ClaimClass.STABLE
    return ClaimClass.MATERIAL


def _effective_n_passes(
    claim_type: ClaimType,
    evidence: ClaimEvidence,
    policy: ClaimPolicy,
) -> tuple[bool, str]:
    if evidence.effective_n is None or evidence.estimand_unit is None:
        return False, "Dependence-aware effective_n and estimand_unit are required."
    try:
        unit = InferentialUnit(evidence.estimand_unit)
    except ValueError:
        return False, "The estimand unit is not recognized."
    if unit not in _INFERENTIAL_UNITS[claim_type]:
        allowed = ", ".join(sorted(value.value for value in _INFERENTIAL_UNITS[claim_type]))
        return False, f"{claim_type.value} requires one of these inferential units: {allowed}."
    if not evidence.effective_n > 0:
        return False, "effective_n must be positive."
    if evidence.raw_n is not None and evidence.effective_n > evidence.raw_n:
        return False, "effective_n cannot exceed raw_n."
    if evidence.cluster_count is not None and evidence.cluster_count <= 0:
        return False, "cluster_count must be positive when supplied."
    minimum = policy.minimum_sample_size
    if unit in {InferentialUnit.MODEL_FAMILY, InferentialUnit.HUMAN_ANNOTATOR}:
        minimum = policy.minimum_independent_model_families
    elif unit is InferentialUnit.BENCHMARK:
        minimum = policy.minimum_transport_benchmarks
    if evidence.effective_n < minimum:
        return (
            False,
            f"The effective sample size {evidence.effective_n:g} is below the {unit.value} policy minimum {minimum}.",
        )
    if evidence.independence_unit is None or not evidence.dependence_structure:
        return False, "independence_unit and dependence_structure are required."
    return True, ""


def _requires_multiplicity(claim_type: ClaimType, evidence: ClaimEvidence) -> bool:
    if claim_type in _MULTIPLE_TEST_CLAIMS:
        return True
    scope = str(evidence.multiplicity_scope or "").upper()
    return claim_type in {
        ClaimType.MODEL_A_OUTPERFORMS_MODEL_B,
        ClaimType.MODEL_IN_TOP_K,
        ClaimType.MODEL_FAMILY_BEST,
    } and scope not in {"", "SINGLE_PRESPECIFIED_COMPARISON"}
