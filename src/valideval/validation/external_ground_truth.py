from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import Field

from valideval.io.jsonl import write_jsonl
from valideval.schemas import JsonModel

GROUND_TRUTH_ALIASES = {
    "benchmark": ("benchmark", "benchmark_id", "dataset"),
    "subset": ("subset", "subject", "split", "category"),
    "item_id": ("item_id", "doc_id", "sample_id", "question_id", "id"),
    "issue_type": ("issue_type", "flaw_type", "error_type", "category", "label"),
    "severity": ("severity", "priority", "level"),
    "source": ("source", "source_url", "paper", "reference"),
}

KNOWN_ISSUE_TYPES = {
    "ambiguous",
    "answer_error",
    "bad_question",
    "contamination",
    "duplicate",
    "incorrect_answer",
    "invalid",
    "low_quality",
    "mmlu_redux_flaw",
    "outdated",
    "shortcut",
    "unclear",
}


class ExternalIssue(JsonModel):
    schema_version: str = "0.1"
    benchmark: str
    subset: str = "default"
    item_id: str
    issue_type: str
    severity: str = "unknown"
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)


def import_ground_truth(
    input_path: str | Path,
    output_path: str | Path,
    *,
    benchmark: str | None = None,
    input_format: str = "auto",
    known_issue_types: set[str] | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    source = Path(input_path)
    destination = Path(output_path)
    records = list(_iter_records(source, input_format=input_format))
    rows: list[ExternalIssue] = []
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    known = known_issue_types or KNOWN_ISSUE_TYPES

    for row_number, record in records:
        values = {field: _pick(record, field) for field in GROUND_TRUTH_ALIASES}
        values["benchmark"] = values["benchmark"] or benchmark
        values["subset"] = values["subset"] or "default"
        missing = [
            field
            for field in ("benchmark", "item_id", "issue_type", "source")
            if values.get(field) in (None, "")
        ]
        if missing:
            for field in missing:
                errors.append(
                    {
                        "row_number": row_number,
                        "field": field,
                        "message": f"Missing required field: {field}",
                    }
                )
            continue
        issue_type = str(values["issue_type"]).strip()
        if issue_type not in known:
            warnings.append(
                f"Row {row_number}: unknown issue_type `{issue_type}` retained for analysis."
            )
        metadata = {
            key: value
            for key, value in record.items()
            if key not in _all_aliases() and key not in {"prompt", "question", "context", "text"}
        }
        rows.append(
            ExternalIssue(
                benchmark=str(values["benchmark"]),
                subset=str(values["subset"]),
                item_id=str(values["item_id"]),
                issue_type=issue_type,
                severity=str(values.get("severity") or "unknown"),
                source=str(values["source"]),
                metadata=metadata,
            )
        )

    duplicate_pairs = [
        key
        for key, count in Counter((row.subset, row.item_id, row.issue_type) for row in rows).items()
        if count > 1
    ]
    if duplicate_pairs:
        warnings.append(
            f"Detected {len(duplicate_pairs)} duplicate subset/item/issue pairs; rows retained."
        )

    summary = {
        "schema_version": "0.1",
        "status": "invalid" if errors else "ok",
        "input_path": str(source),
        "output_path": str(destination),
        "rows_read": len(records),
        "rows_written": 0 if errors else len(rows),
        "issue_count": len(rows),
        "item_count": len({row.item_id for row in rows}),
        "issue_types": sorted({row.issue_type for row in rows}),
        "duplicate_pair_count": len(duplicate_pairs),
        "warnings": warnings,
        "errors": errors,
    }
    if errors:
        _write_ground_truth_report(summary, report_path)
        raise ValueError(f"Ground-truth import failed with {len(errors)} validation errors.")

    write_jsonl(destination, rows)
    _write_ground_truth_report(summary, report_path)
    return summary


def load_ground_truth(path: str | Path) -> list[ExternalIssue]:
    records = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(ExternalIssue(**_normalize_ground_truth_record(json.loads(line))))
    return records


def _normalize_ground_truth_record(record: dict[str, Any]) -> dict[str, Any]:
    allowed = set(ExternalIssue.model_fields)
    if set(record) <= allowed:
        return record
    metadata = dict(record.get("metadata") or {})
    for key in sorted(set(record) - allowed):
        metadata[key] = record[key]
    normalized = {key: value for key, value in record.items() if key in allowed}
    if not normalized.get("subset") and record.get("subject"):
        normalized["subset"] = record["subject"]
    normalized["metadata"] = metadata
    return normalized


def _iter_records(path: Path, *, input_format: str) -> list[tuple[int, dict[str, Any]]]:
    fmt = input_format
    if fmt == "auto":
        fmt = "csv" if path.suffix == ".csv" else "jsonl" if path.suffix == ".jsonl" else "json"
    if fmt in {"mmlu_redux_jsonl", "jsonl"}:
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for row_number, line in enumerate(handle, start=1):
                if line.strip():
                    rows.append((row_number, json.loads(line)))
        return rows
    if fmt in {"mmlu_redux_csv", "csv"}:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [
                (row_number, dict(row))
                for row_number, row in enumerate(csv.DictReader(handle), start=2)
            ]
    if fmt == "json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload.get("records", payload) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise ValueError("Ground-truth JSON must be a list or an object with records.")
        return [(index, dict(record)) for index, record in enumerate(records, start=1)]
    raise ValueError(f"Unsupported ground-truth input format: {input_format}")


def _pick(record: dict[str, Any], field: str) -> Any:
    for key in GROUND_TRUTH_ALIASES[field]:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def _all_aliases() -> set[str]:
    return {alias for aliases in GROUND_TRUTH_ALIASES.values() for alias in aliases}


def _write_ground_truth_report(summary: dict[str, Any], report_path: str | Path | None) -> None:
    if not report_path:
        return
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# External Ground-Truth Import Report",
        "",
        f"- Status: `{summary['status']}`",
        f"- Rows read: {summary['rows_read']}",
        f"- Rows written: {summary['rows_written']}",
        f"- Items with issues: {summary['item_count']}",
        f"- Issue types: {', '.join(summary['issue_types']) or 'none'}",
        f"- Duplicate issue pairs: {summary['duplicate_pair_count']}",
    ]
    if summary["warnings"]:
        lines.extend(["", "## Warnings", *[f"- {warning}" for warning in summary["warnings"]]])
    if summary["errors"]:
        lines.extend(
            [
                "",
                "## Errors",
                *[
                    f"- Row {error['row_number']}, `{error['field']}`: {error['message']}"
                    for error in summary["errors"]
                ],
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
