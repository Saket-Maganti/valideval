"""Fail-closed importer for V5 blinded human labels."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from valideval.human.protocol_v5 import HUMAN_LABEL_TAXONOMY

REQUIRED_FIELDS = frozenset(
    {
        "anonymized_annotator",
        "blinded_task_id",
        "confidence",
        "duration_seconds",
        "expertise_attestation",
        "label",
    }
)
ALLOWED_FIELDS = REQUIRED_FIELDS | frozenset(
    {"rationale", "expertise_attestation", "exclusion_reason", "duration_seconds"}
)
_ANON_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,63}$")


class HumanLabelImportError(ValueError):
    """Raised when packet integrity fails before annotation validation can begin."""


def _load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HumanLabelImportError(f"expected JSON object: {path}")
    return value


def _load_rows(path: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source = Path(path)
    errors: list[dict[str, Any]] = []
    if source.suffix.lower() == ".csv":
        with source.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle)), errors
    if source.suffix.lower() in {".jsonl", ".ndjson"}:
        rows: list[dict[str, Any]] = []
        with source.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(
                        {"row": line_number, "error": "malformed_json", "detail": str(exc)}
                    )
                    continue
                if not isinstance(value, dict):
                    errors.append({"row": line_number, "error": "row_is_not_object"})
                    continue
                rows.append(value)
        return rows, errors
    raise HumanLabelImportError("human annotation input must be CSV, JSONL, or NDJSON")


def _packet_task_ids(path: str | Path) -> set[str]:
    rows, errors = _load_rows(path)
    if errors:
        raise HumanLabelImportError(f"blinded packet is malformed: {errors}")
    task_ids = {str(row.get("blinded_task_id") or "") for row in rows}
    if "" in task_ids or len(task_ids) != len(rows):
        raise HumanLabelImportError("blinded packet has missing or duplicate task ids")
    return task_ids


def _verify_packet(
    blinded_tasks_path: str | Path,
    private_manifest_path: str | Path,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = _load_json(private_manifest_path)
    digest = hashlib.sha256(Path(blinded_tasks_path).read_bytes()).hexdigest()
    if digest != manifest.get("packet_sha256"):
        raise HumanLabelImportError("blinded packet SHA-256 does not match private manifest")
    mapping_rows = manifest.get("mapping")
    if not isinstance(mapping_rows, list):
        raise HumanLabelImportError("private manifest is missing the randomization mapping")
    mapping = {str(row.get("blinded_task_id") or ""): row for row in mapping_rows}
    task_ids = _packet_task_ids(blinded_tasks_path)
    if set(mapping) != task_ids:
        raise HumanLabelImportError("private mapping task ids do not equal blinded packet task ids")
    return manifest, mapping


def _normalise_input_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key).strip(): value for key, value in row.items() if key is not None}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def import_human_labels_v5(
    annotations_path: str | Path,
    *,
    blinded_tasks_path: str | Path,
    private_manifest_path: str | Path,
    output_dir: str | Path,
    minimum_annotators: int | None = None,
    minimum_rationale_characters: int = 0,
    minimum_control_match_rate: float = 0.8,
) -> dict[str, Any]:
    """Validate a complete annotation batch and write private linked labels.

    Any malformed row invalidates the whole batch: no partially accepted label file is written.
    Protocol completion and scientific analysis remain separate downstream gates.
    """

    manifest, mapping = _verify_packet(blinded_tasks_path, private_manifest_path)
    minimum = minimum_annotators or int(manifest.get("minimum_annotators_per_task") or 2)
    if minimum < 2:
        raise HumanLabelImportError("minimum annotator count must be at least 2")
    if minimum_rationale_characters < 0:
        raise ValueError("minimum_rationale_characters must be non-negative")
    if not 0.0 <= minimum_control_match_rate <= 1.0:
        raise ValueError("minimum_control_match_rate must be between 0 and 1")
    rows, errors = _load_rows(annotations_path)
    validated: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for row_number, raw in enumerate(rows, start=1):
        row = _normalise_input_row(raw)
        missing = sorted(
            field for field in REQUIRED_FIELDS if not str(row.get(field) or "").strip()
        )
        extra = sorted(set(row) - ALLOWED_FIELDS)
        if missing:
            errors.append(
                {"row": row_number, "error": "missing_required_fields", "fields": missing}
            )
            continue
        if extra:
            errors.append(
                {"row": row_number, "error": "unexpected_or_unblinded_fields", "fields": extra}
            )
            continue
        task_id = str(row["blinded_task_id"]).strip()
        annotator = str(row["anonymized_annotator"]).strip()
        label = str(row["label"]).strip().upper()
        if task_id not in mapping:
            errors.append({"row": row_number, "error": "unknown_blinded_task_id", "value": task_id})
            continue
        if not _ANON_ID_RE.fullmatch(annotator) or "@" in annotator:
            errors.append({"row": row_number, "error": "invalid_anonymized_annotator_id"})
            continue
        if label not in HUMAN_LABEL_TAXONOMY:
            errors.append(
                {"row": row_number, "error": "label_outside_frozen_taxonomy", "value": label}
            )
            continue
        try:
            confidence = float(row["confidence"])
        except (TypeError, ValueError):
            errors.append({"row": row_number, "error": "invalid_confidence"})
            continue
        if not 0.0 <= confidence <= 1.0:
            errors.append({"row": row_number, "error": "confidence_out_of_range"})
            continue
        duplicate_key = (task_id, annotator)
        if duplicate_key in seen:
            errors.append({"row": row_number, "error": "duplicate_task_annotator_pair"})
            continue
        seen.add(duplicate_key)
        rationale = str(row.get("rationale") or "").strip()
        if (
            label not in {"NO_DETECTED_ISSUE", "UNSURE"}
            and len(rationale) < minimum_rationale_characters
        ):
            errors.append({"row": row_number, "error": "rationale_too_short"})
            continue
        duration_value = str(row.get("duration_seconds") or "").strip()
        duration_seconds: float | None = None
        if duration_value:
            try:
                duration_seconds = float(duration_value)
            except ValueError:
                errors.append({"row": row_number, "error": "invalid_duration_seconds"})
                continue
            if duration_seconds <= 0:
                errors.append({"row": row_number, "error": "invalid_duration_seconds"})
                continue
        private = mapping[task_id]
        validated.append(
            {
                "schema_version": "5.0",
                "packet_id": manifest["packet_id"],
                "blinded_task_id": task_id,
                "source_item_id": private["source_item_id"],
                "source_content_hash": private["source_content_hash"],
                "anonymized_annotator": annotator,
                "label": label,
                "confidence": confidence,
                "rationale": rationale,
                "expertise_attestation": str(row.get("expertise_attestation") or "").strip(),
                "exclusion_reason": str(row.get("exclusion_reason") or "").strip(),
                "duration_seconds": duration_seconds,
                "is_control": bool(private.get("control_type")),
            }
        )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "human_label_import_report_v5.json"
    accepted_path = output / "validated_human_labels_private_v5.jsonl"
    if errors:
        accepted_path.unlink(missing_ok=True)
        report = {
            "schema_version": "5.0",
            "status": "IMPORT_BLOCKED",
            "valid": False,
            "packet_id": manifest.get("packet_id"),
            "source_rows": len(rows),
            "accepted_rows": 0,
            "error_count": len(errors),
            "errors": errors,
            "protocol_complete": False,
            "claim_state": "RESULT_REQUIRED",
            "evidence_status": "BLOCKED",
        }
        _write_json(report_path, report)
        return {**report, "report_json": str(report_path), "validated_labels_jsonl": None}

    _write_jsonl(accepted_path, validated)
    analysis_rows = [row for row in validated if not row["exclusion_reason"]]
    annotators_by_task: dict[str, set[str]] = defaultdict(set)
    for row in analysis_rows:
        annotators_by_task[row["blinded_task_id"]].add(row["anonymized_annotator"])
    under_annotated = sorted(
        task_id for task_id in mapping if len(annotators_by_task[task_id]) < minimum
    )
    control_results = [
        row["label"] == mapping[row["blinded_task_id"]].get("control_expectation")
        for row in analysis_rows
        if mapping[row["blinded_task_id"]].get("control_type")
    ]
    control_types = {
        str(row.get("control_type")) for row in mapping.values() if row.get("control_type")
    }
    control_match_rate = sum(control_results) / len(control_results) if control_results else None
    control_gate_passed = (
        control_types == {"positive", "negative"}
        and control_match_rate is not None
        and control_match_rate >= minimum_control_match_rate
    )
    protocol_complete = not under_annotated and bool(analysis_rows) and control_gate_passed
    report = {
        "schema_version": "5.0",
        "status": "IMPORT_VALID_PROTOCOL_COMPLETE"
        if protocol_complete
        else "IMPORT_VALID_INCOMPLETE",
        "valid": True,
        "packet_id": manifest.get("packet_id"),
        "source_rows": len(rows),
        "accepted_rows": len(validated),
        "error_count": 0,
        "minimum_annotators_per_task": minimum,
        "under_annotated_task_count": len(under_annotated),
        "under_annotated_blinded_task_ids": under_annotated,
        "annotator_count": len({row["anonymized_annotator"] for row in validated}),
        "analysis_row_count": len(analysis_rows),
        "excluded_row_count": len(validated) - len(analysis_rows),
        "label_counts": dict(sorted(Counter(row["label"] for row in analysis_rows).items())),
        "control_judgment_count": len(control_results),
        "control_match_rate": control_match_rate,
        "minimum_control_match_rate": minimum_control_match_rate,
        "control_gate_passed": control_gate_passed,
        "protocol_complete": protocol_complete,
        "claim_state": "RESULT_REQUIRED",
        "evidence_status": "REPORTED_BUT_NOT_REPRODUCED",
        "limitations": [
            "A valid import is not agreement, adjudication, power, or endpoint analysis.",
            "Recall is not identified by a high-score-only review sample.",
        ],
    }
    _write_json(report_path, report)
    return {
        **report,
        "report_json": str(report_path),
        "validated_labels_jsonl": str(accepted_path),
    }
