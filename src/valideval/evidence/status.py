from __future__ import annotations

from enum import Enum


class EvidenceStatus(str, Enum):
    """Allowed V5 evidence states.

    These values deliberately separate observed evidence, planning artifacts, fixtures,
    and blocked or retired claims. They are not an ordinal scale.
    """

    REPRODUCED = "REPRODUCED"
    VERIFIED_FROM_PRIMARY_ARTIFACT = "VERIFIED_FROM_PRIMARY_ARTIFACT"
    REPORTED_BUT_NOT_REPRODUCED = "REPORTED_BUT_NOT_REPRODUCED"
    INFERRED = "INFERRED"
    NON_EVIDENCE_FIXTURE = "NON_EVIDENCE_FIXTURE"
    PLANNED = "PLANNED"
    BLOCKED = "BLOCKED"
    CONTRADICTED = "CONTRADICTED"
    STALE = "STALE"
    RETIRED = "RETIRED"
