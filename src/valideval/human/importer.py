from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from valideval.human.common import (
    bool_from_value,
    load_annotation_tasks,
    stable_json_hash,
    write_json,
)
from valideval.io.jsonl import write_jsonl
from valideval.schemas import HumanJudgment

REQUIRED_FIELDS = {"task_id", "item_id", "label", "confidence"}


def import_annotations(
    path: str | Path,
    *,
    output_dir: str | Path,
    benchmark_id: str,
    panel_id: str,
) -> dict[str, Any]:
    rows, parse_errors = _load_rows(path)
    tasks = load_annotation_tasks(output_dir)
    known_task_ids = {task.task_id for task in tasks}
    known_item_ids = {task.item_id for task in tasks}
    judgments: list[HumanJudgment] = []
    errors: list[dict[str, Any]] = list(parse_errors)
    seen: set[tuple[str, str, str | None, str]] = set()

    for index, row in enumerate(rows, start=1):
        normalized = _normalize_row(row)
        missing = sorted(field for field in REQUIRED_FIELDS if not normalized.get(field))
        annotator = normalized.get("anonymized_annotator")
        if not annotator:
            missing.append("anonymized_annotator")
        if missing:
            errors.append({"row": index, "error": "missing_required_fields", "fields": missing})
            continue

        if known_task_ids and normalized["task_id"] not in known_task_ids:
            errors.append(
                {
                    "row": index,
                    "error": "unknown_task_id",
                    "task_id": normalized["task_id"],
                }
            )
            continue
        if known_item_ids and normalized["item_id"] not in known_item_ids:
            errors.append(
                {
                    "row": index,
                    "error": "unknown_item_id",
                    "item_id": normalized["item_id"],
                }
            )
            continue

        try:
            confidence = float(normalized["confidence"])
        except (TypeError, ValueError):
            errors.append(
                {
                    "row": index,
                    "error": "invalid_confidence",
                    "value": normalized.get("confidence"),
                }
            )
            continue

        duplicate_key: tuple[str, str, str | None, str] = (
            str(normalized["task_id"]),
            str(normalized["item_id"]),
            str(normalized["model_id"]) if normalized.get("model_id") else None,
            str(annotator),
        )
        if duplicate_key in seen:
            errors.append(
                {
                    "row": index,
                    "error": "duplicate_annotation",
                    "key": "::".join(value or "" for value in duplicate_key),
                }
            )
            continue
        seen.add(duplicate_key)

        payload = {
            "task_id": normalized["task_id"],
            "item_id": normalized["item_id"],
            "model_id": normalized.get("model_id") or None,
            "anonymized_annotator": annotator,
            "label": str(normalized["label"]).strip(),
            "confidence": confidence,
            "rationale": normalized.get("rationale") or None,
            "ambiguity_flag": bool_from_value(normalized.get("ambiguity_flag")),
            "invalid_item_flag": bool_from_value(normalized.get("invalid_item_flag")),
            "metadata": {
                "source_path": str(path),
                "source_row": index,
            },
        }
        payload["version_hash"] = stable_json_hash(payload)
        try:
            judgments.append(HumanJudgment(**payload))
        except ValidationError as exc:
            errors.append({"row": index, "error": "schema_validation", "details": str(exc)})

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    judgments_path = output / "human_judgments.jsonl"
    report_path = output / "annotation_import_report.json"
    write_jsonl(judgments_path, judgments)
    report = {
        "schema_version": "0.1",
        "benchmark_id": benchmark_id,
        "panel_id": panel_id,
        "source_path": str(path),
        "valid": not errors,
        "n_rows": len(rows),
        "n_imported": len(judgments),
        "n_errors": len(errors),
        "errors": errors,
        "warnings": [
            "Imported human labels are evidence under this protocol and may still require adjudication."
        ],
        "artifacts": {"human_judgments_jsonl": str(judgments_path)},
    }
    write_json(report_path, report)
    return {
        **report,
        "human_judgments_jsonl": str(judgments_path),
        "annotation_import_report_json": str(report_path),
    }


def _load_rows(path: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        with source.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle)), []
    if suffix in {".jsonl", ".ndjson"}:
        rows: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        with source.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    errors.append({"row": index, "error": "malformed_jsonl", "details": str(exc)})
                    continue
                if not isinstance(record, dict):
                    errors.append({"row": index, "error": "row_is_not_object"})
                    continue
                rows.append(record)
        return rows, errors
    raise ValueError("Annotation import supports CSV, JSONL, and NDJSON files.")


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = {str(key).strip(): value for key, value in row.items()}
    if not normalized.get("anonymized_annotator"):
        normalized["anonymized_annotator"] = normalized.get("annotator_id") or normalized.get(
            "annotator"
        )
    return normalized
