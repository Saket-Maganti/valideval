from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.no_run_preflight import (
    NO_RUN_FORBIDDEN_ACTIONS,
    inspect_structured_schema,
    manifest_status,
    path_status,
    require_dry_run,
    write_manifest,
)

PLANNED_FINDING_TYPES = [
    "accuracy_only_vs_validity_adjusted_ranking_disagreement",
    "diagnostic_vs_diagnostic_disagreement",
    "subject_specific_validity_instability",
    "suspicious_item_subset_ranking_sensitivity",
    "multiple_diagnostic_flagged_item_sets",
    "mmlu_redux_weak_negative_blocked_claim_case",
]

PLANNED_OUTPUTS = {
    "real_panel_ranking_audit": [
        "real_panel_ranking_audit.json",
        "real_panel_ranking_audit.md",
        "accuracy_vs_validity_rank_shift.csv",
    ],
    "diagnostic_disagreement_audit": [
        "diagnostic_disagreement_audit.json",
        "diagnostic_disagreement_audit.md",
        "diagnostic_disagreement_matrix.csv",
    ],
    "subject_instability_audit": [
        "subject_instability_audit.json",
        "subject_instability_audit.md",
        "subject_instability_matrix.csv",
    ],
}


def build_real_panel_dry_run_manifest(
    *,
    audit_name: str,
    matrix: str | Path | None,
    predictions: str | Path | None,
    results_dir: str | Path | None,
    mmlu_redux: str | Path | None,
    output: str | Path,
    dry_run: bool,
    execute_confirmatory_real_panel: bool = False,
) -> dict[str, Any]:
    require_dry_run(
        dry_run=dry_run,
        execute=execute_confirmatory_real_panel,
        execute_flag="--execute-confirmatory-real-panel",
        action=audit_name,
    )
    matrix_check = inspect_structured_schema(
        matrix,
        required_fields=[],
        accepted_id_fields=[
            "item_id",
            "question_id",
            "instance_id",
            "subject_numeric_index",
            "model_id",
        ],
    )
    predictions_check = inspect_structured_schema(
        predictions,
        required_fields=[],
        accepted_id_fields=["item_id", "question_id", "instance_id", "subject_numeric_index"],
    )
    results_check = path_status(results_dir, required=False, kind="dir")
    redux_check = inspect_structured_schema(
        mmlu_redux,
        required_fields=[],
        accepted_id_fields=["item_id", "question_id", "stable_hash", "subject_numeric_index"],
    )
    checks = [matrix_check, predictions_check, results_check, redux_check]
    payload: dict[str, Any] = {
        "mode": "dry_run_only",
        "audit_name": audit_name,
        "status": manifest_status(*checks),
        "evidence_state": "RESULT_REQUIRED",
        "claim_state": "blocked_until_authorized_real_panel_finding_exists",
        "planned_finding_types": PLANNED_FINDING_TYPES,
        "planned_metrics": [
            "rank_correlation_delta",
            "top_k_disagreement",
            "per_subject_rank_shift",
            "diagnostic_flag_overlap",
            "flagged_subset_ranking_sensitivity",
        ],
        "planned_outputs": PLANNED_OUTPUTS[audit_name],
        "input_checks": {
            "matrix": matrix_check,
            "predictions": predictions_check,
            "results_dir": results_check,
            "mmlu_redux": redux_check,
        },
        "forbidden_actions": NO_RUN_FORBIDDEN_ACTIONS,
        "notes": [
            "This manifest validates path/schema readiness only.",
            "It does not compute rankings, diagnostic disagreements, subject effects, or metrics.",
            "MMLU-Redux remains weak/negative and is included only as a blocked-claim case.",
        ],
    }
    manifest_path = write_manifest(output, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload


def refuse_real_panel_execution() -> None:
    raise NotImplementedError(
        "Real-panel finding computation is RESULT_REQUIRED and must be implemented only after "
        "explicit future authorization."
    )
