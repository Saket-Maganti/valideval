from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from valideval.claims.contracts import (
    AnalysisPhase,
    DecisionDirection,
    InferentialUnit,
    PrimarySecondary,
    RankIntervalType,
)


@dataclass(frozen=True)
class ClaimEvidence:
    """Evidence supplied to the claim gate.

    Optional fields are intentionally not imputed. Missing evidence is different from
    evidence of absence and causes the relevant inferential claim to abstain.
    """

    point_estimate: float | None = None
    confidence_lower: float | None = None
    confidence_upper: float | None = None
    simultaneous_rank_lower: float | None = None
    simultaneous_rank_upper: float | None = None
    rank_interval_type: RankIntervalType | None = None
    requested_top_k: int | None = None
    p_value: float | None = None
    q_value: float | None = None
    by_q_value: float | None = None
    bootstrap_stability: float | None = None
    effect_size: float | None = None
    decision_threshold: float | None = None
    decision_direction: DecisionDirection = DecisionDirection.ABOVE
    threshold_units: str | None = None
    exact_model_overlap: int = 0
    independent_model_families: int = 0
    # ``sample_size`` remains readable for V7 ledger compatibility but is never
    # used to license a V7.1 inferential claim.
    sample_size: int = 0
    estimand_unit: InferentialUnit | None = None
    raw_n: int | None = None
    cluster_count: int | None = None
    effective_n: float | None = None
    independence_unit: InferentialUnit | None = None
    dependence_structure: str | None = None
    power: float | None = None
    external_validated: bool = False
    held_out_validated: bool = False
    transport_fold_manifest: dict[str, Any] | None = None
    human_precision_lower: float | None = None
    transport_heterogeneity: float | None = None
    transport_direction_consistent: bool | None = None
    decision_regret_upper: float | None = None
    identity_verified: bool = True
    leakage_guard_passed: bool = True
    multiplicity_controlled: bool = False
    hypothesis_family_id: str | None = None
    multiplicity_scope: str | None = None
    claim_family_id: str | None = None
    primary_or_secondary: PrimarySecondary | None = None
    confirmatory_or_exploratory: AnalysisPhase | None = None
    preregistered: bool | None = None
    scope: tuple[str, ...] = ()
