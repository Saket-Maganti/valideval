from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ClaimPolicy:
    confidence_level: float = 0.95
    fdr_level: float = 0.05
    bootstrap_stability_threshold: float = 0.80
    effect_size_threshold: float = 0.01
    minimum_exact_model_overlap: int = 8
    minimum_independent_model_families: int = 5
    minimum_transport_benchmarks: int = 3
    minimum_sample_size: int = 100
    minimum_power: float = 0.80
    external_validation_required: bool = False
    held_out_validation_required: bool = False
    minimum_human_precision: float = 0.70
    transport_heterogeneity_threshold: float = 0.50
    decision_regret_bound: float = 0.01
    require_by_sensitivity: bool = False

    def __post_init__(self) -> None:
        probabilities = {
            "confidence_level": self.confidence_level,
            "fdr_level": self.fdr_level,
            "bootstrap_stability_threshold": self.bootstrap_stability_threshold,
            "minimum_power": self.minimum_power,
            "minimum_human_precision": self.minimum_human_precision,
        }
        for name, value in probabilities.items():
            if not 0.0 < value < 1.0:
                raise ValueError(f"{name} must be strictly between 0 and 1")
        nonnegative = {
            "effect_size_threshold": self.effect_size_threshold,
            "transport_heterogeneity_threshold": self.transport_heterogeneity_threshold,
            "decision_regret_bound": self.decision_regret_bound,
        }
        for name, value in nonnegative.items():
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        counts = {
            "minimum_exact_model_overlap": self.minimum_exact_model_overlap,
            "minimum_independent_model_families": self.minimum_independent_model_families,
            "minimum_transport_benchmarks": self.minimum_transport_benchmarks,
            "minimum_sample_size": self.minimum_sample_size,
        }
        for name, value in counts.items():
            if value < 1:
                raise ValueError(f"{name} must be positive")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ClaimPolicy:
        unknown = set(payload) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"unknown claim-policy field(s): {sorted(unknown)}")
        return cls(**payload)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
