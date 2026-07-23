from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from valideval.execution.manifest import NON_EVIDENCE_FIXTURE

CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL = "CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL"
CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY = "CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY"
CROSS_BENCHMARK_BLOCKED_INSUFFICIENT_MODEL_OVERLAP = (
    "CROSS_BENCHMARK_BLOCKED_INSUFFICIENT_MODEL_OVERLAP"
)
CROSS_BENCHMARK_BLOCKED_CONFIGURATION_MISMATCH = "CROSS_BENCHMARK_BLOCKED_CONFIGURATION_MISMATCH"
CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY = "CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY"

POSITIVE_EXACT_GATE = CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL


@dataclass(frozen=True, slots=True)
class CrossBenchmarkGateThresholds:
    minimum_exact_common_models: int = 8
    minimum_independent_families: int = 3
    minimum_common_families_exploratory: int = 3
    minimum_usable_items_per_benchmark: int = 100
    minimum_extraction_reliability: float = 0.95
    require_common_config_class: bool = True
    allow_family_level_exploratory: bool = True

    def __post_init__(self) -> None:
        for name in (
            "minimum_exact_common_models",
            "minimum_independent_families",
            "minimum_common_families_exploratory",
            "minimum_usable_items_per_benchmark",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if not 0.0 <= self.minimum_extraction_reliability <= 1.0:
            raise ValueError("minimum_extraction_reliability must be in [0, 1]")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> CrossBenchmarkGateThresholds:
        if payload is None:
            return cls()
        known = {field for field in cls.__dataclass_fields__}
        unknown = sorted(set(payload).difference(known))
        if unknown:
            raise ValueError(f"Unknown cross-benchmark gate thresholds: {unknown}")
        return cls(**dict(payload))


@dataclass(frozen=True, slots=True)
class BenchmarkGateInput:
    benchmark_id: str
    model_ids: frozenset[str]
    model_family_by_id: dict[str, str]
    config_class: str
    usable_items: int
    extraction_reliability: float
    data_integrity: str = "pass"
    evidence_state: str = "RESULT_REQUIRED"
    study_id: str | None = None

    @property
    def model_families(self) -> frozenset[str]:
        return frozenset(self.model_family_by_id.values())

    @classmethod
    def from_mapping(
        cls,
        benchmark_id: str,
        payload: Mapping[str, Any],
    ) -> BenchmarkGateInput:
        model_records = payload.get("models", [])
        model_ids_raw = payload.get("model_ids")
        if (
            model_ids_raw is None
            and isinstance(model_records, Sequence)
            and not isinstance(model_records, str | bytes)
        ):
            model_ids_raw = [
                model.get("model_id") if isinstance(model, Mapping) else model
                for model in model_records
            ]
        if model_ids_raw is None:
            model_ids_raw = []
        if not isinstance(model_ids_raw, Sequence) or isinstance(model_ids_raw, str | bytes):
            raise ValueError(f"{benchmark_id}: model_ids must be a sequence")
        model_ids = frozenset(str(value) for value in model_ids_raw)
        family_mapping = payload.get("model_family_by_id", payload.get("model_families", {}))
        if (not isinstance(family_mapping, Mapping) or not family_mapping) and isinstance(
            model_records, Sequence
        ):
            family_mapping = {
                str(model["model_id"]): str(model.get("model_family", model.get("family", "")))
                for model in model_records
                if isinstance(model, Mapping) and model.get("model_id") is not None
            }
        if not isinstance(family_mapping, Mapping):
            raise ValueError(
                f"{benchmark_id}: model_family_by_id must map exact model IDs to families"
            )
        normalized_families = {str(key): str(value) for key, value in family_mapping.items()}
        return cls(
            benchmark_id=benchmark_id,
            model_ids=model_ids,
            model_family_by_id=normalized_families,
            config_class=str(payload.get("config_class", "")),
            usable_items=int(payload.get("usable_items", payload.get("usable_item_count", 0))),
            extraction_reliability=float(payload.get("extraction_reliability", 0.0)),
            data_integrity=_normalize_integrity(payload.get("data_integrity", "fail")),
            evidence_state=str(payload.get("evidence_state", "RESULT_REQUIRED")),
            study_id=(str(payload["study_id"]) if payload.get("study_id") is not None else None),
        )


def evaluate_cross_benchmark_gate(
    benchmarks: Mapping[str, BenchmarkGateInput | Mapping[str, Any]],
    *,
    thresholds: CrossBenchmarkGateThresholds | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    gate_thresholds = (
        thresholds
        if isinstance(thresholds, CrossBenchmarkGateThresholds)
        else CrossBenchmarkGateThresholds.from_mapping(thresholds)
    )
    inputs = {
        benchmark_id: value
        if isinstance(value, BenchmarkGateInput)
        else BenchmarkGateInput.from_mapping(benchmark_id, value)
        for benchmark_id, value in benchmarks.items()
    }
    if len(inputs) < 2:
        return _gate_result(
            CROSS_BENCHMARK_BLOCKED_INSUFFICIENT_MODEL_OVERLAP,
            inputs,
            gate_thresholds,
            reasons=["At least two benchmark inputs are required."],
        )

    integrity_reasons = _integrity_reasons(inputs, gate_thresholds)
    if integrity_reasons:
        return _gate_result(
            CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY,
            inputs,
            gate_thresholds,
            reasons=integrity_reasons,
        )

    config_classes = {value.config_class for value in inputs.values()}
    if gate_thresholds.require_common_config_class and len(config_classes) != 1:
        return _gate_result(
            CROSS_BENCHMARK_BLOCKED_CONFIGURATION_MISMATCH,
            inputs,
            gate_thresholds,
            reasons=[
                "Exact-model analysis requires one common configuration class; "
                f"observed {sorted(config_classes)}."
            ],
        )

    common_models = set.intersection(*(set(value.model_ids) for value in inputs.values()))
    family_conflicts: list[str] = []
    common_model_families: dict[str, str] = {}
    for model_id in sorted(common_models):
        families = {value.model_family_by_id[model_id] for value in inputs.values()}
        if len(families) != 1:
            family_conflicts.append(f"{model_id}: {sorted(families)}")
        else:
            common_model_families[model_id] = next(iter(families))
    if family_conflicts:
        return _gate_result(
            CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY,
            inputs,
            gate_thresholds,
            reasons=[
                "Exact model IDs have inconsistent family metadata across benchmarks: "
                + "; ".join(family_conflicts)
            ],
        )

    independent_families = set(common_model_families.values())
    common_families = set.intersection(*(set(value.model_families) for value in inputs.values()))
    details = {
        "exact_common_model_ids": sorted(common_models),
        "exact_common_model_count": len(common_models),
        "exact_common_model_families": common_model_families,
        "independent_family_count": len(independent_families),
        "common_family_ids": sorted(common_families),
        "common_family_count": len(common_families),
        "common_config_class": next(iter(config_classes)) if len(config_classes) == 1 else None,
    }
    if (
        len(common_models) >= gate_thresholds.minimum_exact_common_models
        and len(independent_families) >= gate_thresholds.minimum_independent_families
    ):
        return _gate_result(
            CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL,
            inputs,
            gate_thresholds,
            reasons=["All preregistered exact-common-panel gates passed."],
            details=details,
        )
    if (
        gate_thresholds.allow_family_level_exploratory
        and len(common_families) >= gate_thresholds.minimum_common_families_exploratory
    ):
        return _gate_result(
            CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY,
            inputs,
            gate_thresholds,
            reasons=[
                "Exact checkpoint overlap is below threshold; only family-level exploratory analysis is allowed."
            ],
            details=details,
        )
    return _gate_result(
        CROSS_BENCHMARK_BLOCKED_INSUFFICIENT_MODEL_OVERLAP,
        inputs,
        gate_thresholds,
        reasons=[
            "Exact common models or independent families are below the preregistered minimum."
        ],
        details=details,
    )


evaluate_overlap_gate = evaluate_cross_benchmark_gate


def gate_allows_exact_analysis(gate: Mapping[str, Any]) -> bool:
    return gate.get("status") == CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL


def _integrity_reasons(
    inputs: Mapping[str, BenchmarkGateInput],
    thresholds: CrossBenchmarkGateThresholds,
) -> list[str]:
    reasons: list[str] = []
    study_ids = {value.study_id for value in inputs.values() if value.study_id is not None}
    if len(study_ids) > 1:
        reasons.append(
            f"Benchmark inputs mix study IDs and cannot form a controlled panel: {sorted(study_ids)}."
        )
    for benchmark_id, value in sorted(inputs.items()):
        if value.data_integrity != "pass":
            reasons.append(f"{benchmark_id}: data_integrity={value.data_integrity!r}.")
        missing_family_models = sorted(value.model_ids.difference(value.model_family_by_id))
        unknown_family_models = sorted(set(value.model_family_by_id).difference(value.model_ids))
        if missing_family_models or unknown_family_models:
            reasons.append(
                f"{benchmark_id}: family metadata mismatch; missing={missing_family_models}, "
                f"unknown={unknown_family_models}."
            )
        if value.usable_items < thresholds.minimum_usable_items_per_benchmark:
            reasons.append(
                f"{benchmark_id}: usable_items={value.usable_items} below "
                f"{thresholds.minimum_usable_items_per_benchmark}."
            )
        if value.extraction_reliability < thresholds.minimum_extraction_reliability:
            reasons.append(
                f"{benchmark_id}: extraction_reliability={value.extraction_reliability:.6f} "
                f"below {thresholds.minimum_extraction_reliability:.6f}."
            )
        if not value.config_class:
            reasons.append(f"{benchmark_id}: config_class is missing.")
    return reasons


def _gate_result(
    status: str,
    inputs: Mapping[str, BenchmarkGateInput],
    thresholds: CrossBenchmarkGateThresholds,
    *,
    reasons: list[str],
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    fixture_only = bool(inputs) and all(
        value.evidence_state == NON_EVIDENCE_FIXTURE for value in inputs.values()
    )
    mixed_fixture = (
        any(value.evidence_state == NON_EVIDENCE_FIXTURE for value in inputs.values())
        and not fixture_only
    )
    if mixed_fixture:
        status = CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY
        reasons = [
            "Fixture and non-fixture inputs cannot be combined in one cross-benchmark analysis."
        ]
    payload = {
        "schema_version": "valideval.cross_benchmark_gate.v5",
        "status": status,
        "ready_for_exact_analysis": status == CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL,
        "family_level_exploratory_only": status == CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY,
        "benchmark_ids": sorted(inputs),
        "thresholds": asdict(thresholds),
        "reasons": reasons,
        "inputs": {
            benchmark_id: {
                "model_count": len(value.model_ids),
                "model_ids": sorted(value.model_ids),
                "model_family_by_id": dict(sorted(value.model_family_by_id.items())),
                "config_class": value.config_class,
                "usable_items": value.usable_items,
                "extraction_reliability": value.extraction_reliability,
                "data_integrity": value.data_integrity,
                "evidence_state": value.evidence_state,
                "study_id": value.study_id,
            }
            for benchmark_id, value in sorted(inputs.items())
        },
        "evidence_state": NON_EVIDENCE_FIXTURE if fixture_only else "ARTIFACT_GATED",
        "claim_state": "NON_EVIDENCE_FIXTURE_ONLY" if fixture_only else "GATE_SCOPED",
    }
    payload.update(details or {})
    return payload


def _normalize_integrity(value: Any) -> str:
    if value is True:
        return "pass"
    if value is False:
        return "fail"
    normalized = str(value).strip().lower()
    return "pass" if normalized in {"pass", "passed", "ok", "valid"} else normalized
