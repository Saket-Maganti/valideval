from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from valideval.diagnostics.base import Diagnostic
from valideval.schemas import DiagnosticResult


class ReportSectionFactory(Protocol):
    def __call__(self, results: list[DiagnosticResult]) -> str: ...


@dataclass(frozen=True)
class ThreatSpec:
    name: str
    domain: str
    description: str
    diagnostic: str
    evidence: str
    repair: str
    limitations: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ThreatSpec:
        limitations = payload.get("limitations", [])
        return cls(
            name=str(payload["name"]),
            domain=str(payload["domain"]),
            description=str(payload["description"]),
            diagnostic=str(payload["diagnostic"]),
            evidence=str(payload["evidence"]),
            repair=str(payload["repair"]),
            limitations=[str(item) for item in limitations]
            if isinstance(limitations, list)
            else [],
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "diagnostic": self.diagnostic,
            "evidence": self.evidence,
            "repair": self.repair,
            "limitations": self.limitations,
        }


@dataclass(frozen=True)
class DiagnosticFactory:
    diagnostic_name: str
    description: str
    factory: Callable[[], Diagnostic]


@dataclass(frozen=True)
class RepairPolicy:
    policy_id: str
    description: str
    actions: list[str] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "description": self.description,
            "actions": self.actions,
        }


@dataclass(frozen=True)
class DomainPack:
    domain_id: str
    supported_item_types: list[str]
    threat_library: list[ThreatSpec]
    diagnostics: list[DiagnosticFactory]
    report_sections: list[ReportSectionFactory]
    repair_policies: list[RepairPolicy]
    description: str = ""

    @property
    def diagnostic_names(self) -> list[str]:
        return [diagnostic.diagnostic_name for diagnostic in self.diagnostics]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "domain_id": self.domain_id,
            "description": self.description,
            "supported_item_types": self.supported_item_types,
            "threat_library": [threat.to_json_dict() for threat in self.threat_library],
            "diagnostics": [
                {
                    "diagnostic_name": diagnostic.diagnostic_name,
                    "description": diagnostic.description,
                }
                for diagnostic in self.diagnostics
            ],
            "repair_policies": [policy.to_json_dict() for policy in self.repair_policies],
        }
