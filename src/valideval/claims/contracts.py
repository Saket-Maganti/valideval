from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ClaimClass(str, Enum):
    DESCRIPTIVE = "DESCRIPTIVE"
    STABLE = "STABLE"
    MATERIAL = "MATERIAL"
    EXTERNALLY_VALIDATED = "EXTERNALLY_VALIDATED"
    TRANSPORTABLE = "TRANSPORTABLE"
    DECISION_LICENSED = "DECISION_LICENSED"
    BLOCKED = "BLOCKED"


class ClaimType(str, Enum):
    MODEL_A_OUTPERFORMS_MODEL_B = "MODEL_A_OUTPERFORMS_MODEL_B"
    MODEL_IN_TOP_K = "MODEL_IN_TOP_K"
    MODEL_CROSSES_THRESHOLD = "MODEL_CROSSES_THRESHOLD"
    MODEL_FAMILY_BEST = "MODEL_FAMILY_BEST"
    ITEM_IS_SUSPICIOUS = "ITEM_IS_SUSPICIOUS"
    SUBJECT_IS_UNSTABLE = "SUBJECT_IS_UNSTABLE"
    BENCHMARK_RANKING_IS_STABLE = "BENCHMARK_RANKING_IS_STABLE"
    DIAGNOSTIC_TRANSFERS = "DIAGNOSTIC_TRANSFERS"
    REPAIR_IMPROVES_DECISION = "REPAIR_IMPROVES_DECISION"


class InferentialUnit(str, Enum):
    ITEM = "ITEM"
    SUBJECT = "SUBJECT"
    MODEL_CHECKPOINT = "MODEL_CHECKPOINT"
    MODEL_FAMILY = "MODEL_FAMILY"
    BENCHMARK = "BENCHMARK"
    MODEL_BENCHMARK_PAIR = "MODEL_BENCHMARK_PAIR"
    HUMAN_ANNOTATOR = "HUMAN_ANNOTATOR"
    HUMAN_ITEM = "HUMAN_ITEM"


class DecisionDirection(str, Enum):
    ABOVE = "above"
    BELOW = "below"


class RankIntervalType(str, Enum):
    MARGINAL_BOOTSTRAP = "MARGINAL_BOOTSTRAP"
    BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS = "BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS"


class PrimarySecondary(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"


class AnalysisPhase(str, Enum):
    CONFIRMATORY = "CONFIRMATORY"
    EXPLORATORY = "EXPLORATORY"


class ClaimStatus(str, Enum):
    LICENSED = "LICENSED"
    LICENSED_WITH_SCOPE = "LICENSED_WITH_SCOPE"
    EXPLORATORY_ONLY = "EXPLORATORY_ONLY"
    UNDERPOWERED = "UNDERPOWERED"
    BLOCKED_BY_UNCERTAINTY = "BLOCKED_BY_UNCERTAINTY"
    BLOCKED_BY_MULTIPLICITY = "BLOCKED_BY_MULTIPLICITY"
    BLOCKED_BY_EXTERNAL_VALIDATION = "BLOCKED_BY_EXTERNAL_VALIDATION"
    BLOCKED_BY_TRANSPORT = "BLOCKED_BY_TRANSPORT"
    BLOCKED_BY_IDENTITY = "BLOCKED_BY_IDENTITY"
    BLOCKED_BY_LEAKAGE = "BLOCKED_BY_LEAKAGE"


@dataclass(frozen=True)
class ClaimLicenseResult:
    status: ClaimStatus
    claim_class: ClaimClass
    claim_type: ClaimType
    reasons: tuple[str, ...]
    scope: tuple[str, ...] = ()
    checks: tuple[tuple[str, bool | None], ...] = ()

    @property
    def licensed(self) -> bool:
        return self.status in {ClaimStatus.LICENSED, ClaimStatus.LICENSED_WITH_SCOPE}

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "licensed": self.licensed,
            "claim_class": self.claim_class.value,
            "claim_type": self.claim_type.value,
            "reasons": list(self.reasons),
            "scope": list(self.scope),
            "checks": {name: passed for name, passed in self.checks},
        }
