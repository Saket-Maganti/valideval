from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class S1V72RunReadiness:
    exact_final_source: bool = False
    exact_panel: bool = False
    exact_contracts: bool = False
    exact_subsets: bool = False
    native_end_to_end: bool = False
    oom_recovery_tests: bool = False
    provenance_negative_tests: bool = False
    package_import_tests: bool = False
    acceptance_negative_tests: bool = False
    unresolved_p0_execution_blocker_absent: bool = False


def assess_s1_v7_2_run_authorization(
    readiness: S1V72RunReadiness,
) -> dict[str, Any]:
    evidence = asdict(readiness)
    missing = [name for name, passed in evidence.items() if not passed]
    return {
        "schema_version": "valideval.s1-run-authorization.v7.2",
        "status": "S1_V7_2_AUTHORIZED" if not missing else "S1_V7_2_BLOCKED",
        "missing_requirements": missing,
        "evidence": evidence,
        "authorization_boundary": (
            "This authorizes the exact Kaggle engineering smoke only. It is not an accepted "
            "real S1 result and licenses no scientific claim."
        ),
        "s2": "S2_BLOCKED_PENDING_ACCEPTED_S1",
        "s3": "S3_BLOCKED_PENDING_S2",
        "s4": "S4_BLOCKED_PENDING_S3",
    }
