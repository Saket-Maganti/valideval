from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StudyCAuthorizationEvidence:
    production_smoke_path_ready: bool = False
    exact_source_verified: bool = False
    end_to_end_passed: bool = False
    t4_preflight_passed: bool = False
    accepted_s1: bool = False
    measured_throughput: bool = False
    extraction_reliable: bool = False
    identity_drift_absent: bool = False
    blocking_oom_absent: bool = False
    accepted_s2: bool = False
    primary_power_recalibrated: bool = False
    family_coverage_adequate: bool = False
    runtime_acceptable: bool = False
    preregistration_frozen: bool = False
    unresolved_p0_absent: bool = False
    s3_results_available: bool = False
    added_scientific_value_documented: bool = False
    incremental_power_or_robustness: bool = False


def assess_study_c_authorization(
    evidence: StudyCAuthorizationEvidence,
) -> dict[str, Any]:
    """Evaluate the sequential Study-C authorization hierarchy without imputation."""

    values = asdict(evidence)
    requirements = {
        "S1": (
            "production_smoke_path_ready",
            "exact_source_verified",
            "end_to_end_passed",
            "t4_preflight_passed",
        ),
        "S2": (
            "accepted_s1",
            "measured_throughput",
            "extraction_reliable",
            "identity_drift_absent",
            "blocking_oom_absent",
        ),
        "S3": (
            "accepted_s2",
            "primary_power_recalibrated",
            "family_coverage_adequate",
            "runtime_acceptable",
            "preregistration_frozen",
            "unresolved_p0_absent",
        ),
        "S4": (
            "s3_results_available",
            "added_scientific_value_documented",
            "incremental_power_or_robustness",
        ),
    }
    statuses: dict[str, Any] = {}
    for stage, fields in requirements.items():
        missing = [field for field in fields if not values[field]]
        if not missing:
            status = f"{stage}_AUTHORIZED"
        elif stage == "S3" and not evidence.accepted_s2:
            status = "S3_BLOCKED_PENDING_S2"
        elif stage == "S4" and not evidence.s3_results_available:
            status = "S4_BLOCKED_PENDING_S3"
        else:
            status = f"{stage}_BLOCKED"
        statuses[stage.lower()] = {"status": status, "missing_requirements": missing}
    return {
        "status": "STUDY_C_AUTHORIZATION_EVALUATED",
        "stages": statuses,
        "evidence": values,
    }
