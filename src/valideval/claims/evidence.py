from __future__ import annotations

from dataclasses import dataclass


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
    requested_top_k: int | None = None
    p_value: float | None = None
    q_value: float | None = None
    by_q_value: float | None = None
    bootstrap_stability: float | None = None
    effect_size: float | None = None
    exact_model_overlap: int = 0
    independent_model_families: int = 0
    sample_size: int = 0
    power: float | None = None
    external_validated: bool = False
    held_out_validated: bool = False
    human_precision_lower: float | None = None
    transport_heterogeneity: float | None = None
    transport_direction_consistent: bool | None = None
    decision_regret_upper: float | None = None
    identity_verified: bool = True
    leakage_guard_passed: bool = True
    multiplicity_controlled: bool = False
    scope: tuple[str, ...] = ()
