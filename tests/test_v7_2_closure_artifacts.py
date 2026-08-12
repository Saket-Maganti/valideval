from __future__ import annotations

import json
from pathlib import Path

from valideval.evidence.state_v7_2 import (
    EvidenceTransitionV72,
    evaluate_evidence_state_v7_2,
)
from valideval.execution.authorization_v7_2 import (
    S1V72RunReadiness,
    assess_s1_v7_2_run_authorization,
)

ROOT = Path(__file__).resolve().parents[1]


def test_package_acceptance_does_not_promote_scientific_claim() -> None:
    scientific = evaluate_evidence_state_v7_2(
        EvidenceTransitionV72(package_accepted=True, engineering_claim=False)
    )
    engineering = evaluate_evidence_state_v7_2(
        EvidenceTransitionV72(package_accepted=True, engineering_claim=True)
    )
    assert scientific["state"] == "PLANNED"
    assert engineering["state"] == "ENGINEERING_VALIDATED"
    assert scientific["package_auto_promotion"] is False


def test_decision_license_requires_confirmation_and_heldout_validation() -> None:
    blocked = evaluate_evidence_state_v7_2(
        EvidenceTransitionV72(claim_policy_licensed=True)
    )
    licensed = evaluate_evidence_state_v7_2(
        EvidenceTransitionV72(
            claim_policy_licensed=True,
            confirmatory_analysis_complete=True,
            held_out_validation_complete=True,
        )
    )
    assert blocked["state"] == "BLOCKED"
    assert licensed["state"] == "DECISION_LICENSED"


def test_s1_authorization_requires_every_execution_gate() -> None:
    ready = S1V72RunReadiness(**{field: True for field in S1V72RunReadiness.__dataclass_fields__})
    authorized = assess_s1_v7_2_run_authorization(ready)
    blocked = assess_s1_v7_2_run_authorization(
        S1V72RunReadiness(exact_final_source=True)
    )
    assert authorized["status"] == "S1_V7_2_AUTHORIZED"
    assert authorized["s2"] == "S2_BLOCKED_PENDING_ACCEPTED_S1"
    assert blocked["status"] == "S1_V7_2_BLOCKED"
    assert "native_end_to_end" in blocked["missing_requirements"]


def test_required_v7_2_reports_and_machine_keys_exist() -> None:
    report_names = {
        path.name for path in (ROOT / "reports/v7_2").glob("*.md")
    }
    assert len(report_names) == 17
    machine = json.loads((ROOT / "VALID_EVAL_V7_2_MACHINE_STATE.json").read_text())
    required = {
        "baseline_commit",
        "final_source_commit",
        "final_source_tag",
        "metadata_commit",
        "git_dirty",
        "ci",
        "s1_v7_2_bridge",
        "claim_policy_confirmation",
        "difficulty_confound_status",
        "v8_development_status",
        "s2_authorization",
        "tests",
        "release",
        "remaining_blockers",
        "exact_next_action",
    }
    assert required.issubset(machine)
    assert (ROOT / "VALID_EVAL_V7_2_KAGGLE_S1_RUNBOOK.md").is_file()
    assert (ROOT / "VALID_EVAL_V7_2_FINAL_PRE_KAGGLE_HANDOFF.md").is_file()
