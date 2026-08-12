from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EvidenceStateV72(StrEnum):
    PLANNED = "PLANNED"
    ENGINEERING_VALIDATED = "ENGINEERING_VALIDATED"
    EXPLORATORY_OBSERVED = "EXPLORATORY_OBSERVED"
    CONFIRMATORY_OBSERVED = "CONFIRMATORY_OBSERVED"
    HELD_OUT_VALIDATED = "HELD_OUT_VALIDATED"
    HUMAN_VALIDATED = "HUMAN_VALIDATED"
    TRANSPORT_VALIDATED = "TRANSPORT_VALIDATED"
    DECISION_LICENSED = "DECISION_LICENSED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class EvidenceTransitionV72:
    package_accepted: bool = False
    engineering_claim: bool = False
    exploratory_analysis_complete: bool = False
    confirmatory_analysis_complete: bool = False
    held_out_validation_complete: bool = False
    human_validation_complete: bool = False
    transport_validation_complete: bool = False
    claim_policy_licensed: bool = False
    blocker_present: bool = False


def evaluate_evidence_state_v7_2(
    evidence: EvidenceTransitionV72,
) -> dict[str, Any]:
    """Evaluate claim state without treating package existence as scientific evidence."""

    if evidence.blocker_present:
        state = EvidenceStateV72.BLOCKED
        reason = "An unresolved claim-specific blocker is present."
    elif evidence.claim_policy_licensed:
        prerequisites = (
            evidence.confirmatory_analysis_complete and evidence.held_out_validation_complete
        )
        if not prerequisites:
            state = EvidenceStateV72.BLOCKED
            reason = "Decision licensing requested without confirmatory and held-out validation."
        else:
            state = EvidenceStateV72.DECISION_LICENSED
            reason = "Frozen claim policy licensed evidence with required validation."
    elif evidence.transport_validation_complete:
        state = EvidenceStateV72.TRANSPORT_VALIDATED
        reason = "Transport validation is complete; decision licensing remains separate."
    elif evidence.human_validation_complete:
        state = EvidenceStateV72.HUMAN_VALIDATED
        reason = "Human validation is complete; decision licensing remains separate."
    elif evidence.held_out_validation_complete:
        state = EvidenceStateV72.HELD_OUT_VALIDATED
        reason = "Held-out validation is complete."
    elif evidence.confirmatory_analysis_complete:
        state = EvidenceStateV72.CONFIRMATORY_OBSERVED
        reason = "Confirmatory results exist but are not automatically licensed."
    elif evidence.exploratory_analysis_complete:
        state = EvidenceStateV72.EXPLORATORY_OBSERVED
        reason = "Exploratory results exist and remain non-confirmatory."
    elif evidence.package_accepted and evidence.engineering_claim:
        state = EvidenceStateV72.ENGINEERING_VALIDATED
        reason = "Accepted package supports only the declared engineering claim."
    else:
        state = EvidenceStateV72.PLANNED
        reason = "No claim-specific observational evidence has advanced this claim."
    return {
        "schema_version": "valideval.evidence-state.v7.2",
        "state": state.value,
        "reason": reason,
        "package_auto_promotion": False,
    }
