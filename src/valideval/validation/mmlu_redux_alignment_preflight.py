from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.no_run_preflight import (
    NO_RUN_FORBIDDEN_ACTIONS,
    inspect_structured_schema,
    manifest_status,
    require_dry_run,
    write_manifest,
)

DIRECT_OR_HASH_FIELDS = ["item_id", "question_id", "stable_hash", "content_hash", "prompt_hash"]


def build_mmlu_redux_alignment_preflight(
    *,
    predictions: str | Path,
    redux: str | Path,
    output: str | Path,
    dry_run: bool,
    execute_alignment: bool = False,
) -> dict[str, Any]:
    require_dry_run(
        dry_run=dry_run,
        execute=execute_alignment,
        execute_flag="--execute-alignment",
        action="MMLU-Redux direct/hash alignment preflight",
    )
    predictions_check = inspect_structured_schema(
        predictions,
        required_fields=[],
        accepted_id_fields=DIRECT_OR_HASH_FIELDS,
    )
    redux_check = inspect_structured_schema(
        redux,
        required_fields=[],
        accepted_id_fields=DIRECT_OR_HASH_FIELDS,
    )
    direct_or_hash_ready = bool(
        predictions_check.get("accepted_id_field_present")
        and redux_check.get("accepted_id_field_present")
    )
    payload: dict[str, Any] = {
        "mode": "dry_run_only",
        "status": "direct_or_hash_fields_present"
        if direct_or_hash_ready
        and manifest_status(predictions_check, redux_check) == "dry_run_ready"
        else "blocked_direct_hash_alignment_missing",
        "claim_state": "BLOCKED_UNTIL_DIRECT_HASH_ALIGNMENT",
        "predictions_schema": predictions_check,
        "mmlu_redux_schema": redux_check,
        "accepted_direct_or_hash_fields": DIRECT_OR_HASH_FIELDS,
        "raw_text_exposed": False,
        "alignment_run": False,
        "forbidden_actions": NO_RUN_FORBIDDEN_ACTIONS,
        "notes": [
            "This preflight reports field names only, not raw MMLU question text or answer choices.",
            "It does not rerun MMLU-Redux validation or compute validation metrics.",
        ],
    }
    manifest_path = write_manifest(output, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload
