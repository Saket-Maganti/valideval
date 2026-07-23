from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd

from valideval.importers.schemas import ImportIssue, ImportSummary, WidePredictionRow
from valideval.io.jsonl import read_jsonl, write_jsonl

TEXT_FIELDS = {
    "prompt",
    "question",
    "context",
    "input",
    "inputs",
    "text",
    "doc",
    "document",
}

ALIASES = {
    "benchmark": ("benchmark", "benchmark_id", "task", "dataset"),
    "subset": ("subset", "subject", "split", "task_name", "category"),
    "item_id": ("item_id", "doc_id", "sample_id", "question_id", "id", "instance_id"),
    "model_id": ("model_id", "model", "model_name", "system", "run_id"),
    "prediction": ("prediction", "pred", "answer", "filtered_resps", "completion", "output"),
    "gold": ("gold", "target", "correct_answer", "answer_key", "label"),
    "correct": ("correct", "is_correct", "exact_match", "acc", "score"),
}


def import_wide_predictions(
    input_path: str | Path,
    output_path: str | Path,
    *,
    benchmark: str | None = None,
    input_format: str = "auto",
    source: str = "local",
    include_text: bool = False,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    source_path = Path(input_path)
    destination = Path(output_path)
    records = list(_iter_input_records(source_path, input_format=input_format))
    normalized: list[WidePredictionRow] = []
    errors: list[ImportIssue] = []
    discarded_text_fields: set[str] = set()

    for row_number, record in records:
        rows, row_errors, discarded = _normalize_record(
            record,
            row_number=row_number,
            benchmark=benchmark,
            source=source,
            source_file=str(source_path),
            include_text=include_text,
        )
        normalized.extend(rows)
        errors.extend(row_errors)
        discarded_text_fields.update(discarded)

    if errors:
        summary = _summary(
            status="invalid",
            input_path=source_path,
            output_path=destination,
            rows_read=len(records),
            rows=normalized,
            errors=errors,
            discarded_text_fields=discarded_text_fields,
        )
        _write_import_report(summary, report_path)
        raise ValueError(_format_errors(errors))

    destination.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(destination, normalized)
    summary = _summary(
        status="ok",
        input_path=source_path,
        output_path=destination,
        rows_read=len(records),
        rows=normalized,
        errors=[],
        discarded_text_fields=discarded_text_fields,
    )
    _write_import_report(summary, report_path)
    return summary.model_dump(mode="json")


def build_matrix_from_wide_predictions(
    predictions_path: str | Path,
    output_path: str | Path,
    *,
    report_path: str | Path | None = None,
    allow_missing: bool = True,
) -> dict[str, Any]:
    source = Path(predictions_path)
    destination = Path(output_path)
    rows = [WidePredictionRow(**record) for record in read_jsonl(source)]
    if not rows:
        raise ValueError("Cannot build matrix from zero wide prediction rows.")

    keys = [(row.model_id, row.subset, row.item_id) for row in rows]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        preview = ", ".join("/".join(key) for key in duplicates[:5])
        raise ValueError(f"Duplicate model/subset/item rows prevent matrix construction: {preview}")

    frame = pd.DataFrame(
        [
            {
                "model_id": row.model_id,
                "item_key": f"{row.subset}::{row.item_id}",
                "correct": float(bool(row.correct)),
            }
            for row in rows
        ]
    )
    matrix = frame.pivot(index="model_id", columns="item_key", values="correct")
    matrix = matrix.sort_index().sort_index(axis=1)
    missing_cells = int(matrix.isna().sum().sum())
    if missing_cells and not allow_missing:
        raise ValueError(f"Matrix has {missing_cells} missing model/item cells.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(destination)
    metadata = {
        "schema_version": "0.1",
        "source_predictions": str(source),
        "matrix_csv": str(destination),
        "benchmark": sorted({row.benchmark for row in rows}),
        "n_models": int(matrix.shape[0]),
        "n_items": int(matrix.shape[1]),
        "n_rows": len(rows),
        "missing_cells": missing_cells,
        "model_order": [str(index) for index in matrix.index],
        "item_order": [str(column) for column in matrix.columns],
        "prediction_hash": _sha256(source),
        "warnings": [
            "Wide matrices contain scored correctness only; inspect normalized predictions for source metadata."
        ],
    }
    metadata_path = destination.with_suffix(destination.suffix + ".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        Path(report_path).write_text(_matrix_report(metadata), encoding="utf-8")
    return metadata


def normalize_records(
    records: Iterable[dict[str, Any]],
    *,
    benchmark: str | None,
    source_file: str,
    source: str = "local",
    include_text: bool = False,
) -> tuple[list[WidePredictionRow], list[ImportIssue], set[str]]:
    rows: list[WidePredictionRow] = []
    errors: list[ImportIssue] = []
    discarded: set[str] = set()
    for row_number, record in enumerate(records, start=1):
        next_rows, next_errors, next_discarded = _normalize_record(
            record,
            row_number=row_number,
            benchmark=benchmark,
            source=source,
            source_file=source_file,
            include_text=include_text,
        )
        rows.extend(next_rows)
        errors.extend(next_errors)
        discarded.update(next_discarded)
    return rows, errors, discarded


def _iter_input_records(path: Path, *, input_format: str) -> Iterable[tuple[int, dict[str, Any]]]:
    fmt = _resolve_format(path, input_format)
    if fmt == "jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for row_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if stripped:
                    yield row_number, json.loads(stripped)
        return
    if fmt == "json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload.get("records", payload) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise ValueError("JSON input must be a list or an object with a records list.")
        for row_number, record in enumerate(records, start=1):
            yield row_number, dict(record)
        return
    if fmt == "csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row_number, record in enumerate(reader, start=2):
                yield row_number, dict(record)
        return
    raise ValueError(f"Unsupported wide prediction input format: {input_format}")


def _resolve_format(path: Path, input_format: str) -> str:
    if input_format != "auto":
        mapping = {
            "generic_jsonl": "jsonl",
            "model_major_jsonl": "jsonl",
            "generic_csv": "csv",
        }
        return mapping.get(input_format, input_format)
    if path.suffix == ".jsonl":
        return "jsonl"
    if path.suffix == ".json":
        return "json"
    if path.suffix == ".csv":
        return "csv"
    raise ValueError(f"Cannot infer input format from extension: {path}")


def _normalize_record(
    record: dict[str, Any],
    *,
    row_number: int,
    benchmark: str | None,
    source: str,
    source_file: str,
    include_text: bool,
) -> tuple[list[WidePredictionRow], list[ImportIssue], set[str]]:
    if isinstance(record.get("predictions"), list):
        model_id = _pick(record, "model_id")
        rows: list[WidePredictionRow] = []
        errors: list[ImportIssue] = []
        discarded: set[str] = set()
        for offset, child in enumerate(record["predictions"], start=1):
            child_record = {**child, "model_id": child.get("model_id", model_id)}
            child_rows, child_errors, child_discarded = _normalize_record(
                child_record,
                row_number=row_number,
                benchmark=benchmark or _pick(record, "benchmark"),
                source=source,
                source_file=source_file,
                include_text=include_text,
            )
            for issue in child_errors:
                issue.message = f"prediction[{offset}]: {issue.message}"
            rows.extend(child_rows)
            errors.extend(child_errors)
            discarded.update(child_discarded)
        return rows, errors, discarded

    values = {field: _pick(record, field) for field in ALIASES}
    values["benchmark"] = values["benchmark"] or benchmark
    values["subset"] = values["subset"] or "default"
    errors = [
        ImportIssue(row_number=row_number, field=field, message=f"Missing required field: {field}")
        for field in ("benchmark", "item_id", "model_id", "prediction", "gold")
        if values.get(field) in (None, "")
    ]
    if errors:
        return [], errors, set()

    prediction = _stringify_prediction(values["prediction"])
    gold = _stringify_prediction(values["gold"])
    correct = _parse_correct(values.get("correct"), prediction=prediction, gold=gold)
    discarded = {field for field in record if field in TEXT_FIELDS and not include_text}
    metadata = {
        key: value
        for key, value in record.items()
        if key not in discarded and key not in _all_aliases()
    }
    if discarded:
        metadata["discarded_text_fields"] = sorted(discarded)

    return (
        [
            WidePredictionRow(
                benchmark=str(values["benchmark"]),
                subset=str(values["subset"]),
                item_id=str(values["item_id"]),
                model_id=str(values["model_id"]),
                prediction=prediction,
                gold=gold,
                correct=correct,
                source=source,
                source_file=source_file,
                metadata=metadata,
            )
        ],
        [],
        discarded,
    )


def _pick(record: dict[str, Any], field: str) -> Any:
    for key in ALIASES[field]:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def _all_aliases() -> set[str]:
    return {alias for aliases in ALIASES.values() for alias in aliases}


def _stringify_prediction(value: Any) -> str:
    if isinstance(value, list):
        if not value:
            return ""
        return _stringify_prediction(value[0])
    if isinstance(value, dict):
        for key in ("text", "answer", "prediction", "filtered_resps"):
            if key in value:
                return _stringify_prediction(value[key])
        return json.dumps(value, sort_keys=True)
    return str(value).strip()


def _parse_correct(value: Any, *, prediction: str, gold: str) -> bool | None:
    if value in (None, ""):
        return prediction.strip().lower() == gold.strip().lower()
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return float(value) >= 0.5
    text = str(value).strip().lower()
    if text in {"true", "t", "yes", "y", "1", "correct"}:
        return True
    if text in {"false", "f", "no", "n", "0", "incorrect"}:
        return False
    return prediction.strip().lower() == gold.strip().lower()


def _summary(
    *,
    status: str,
    input_path: Path,
    output_path: Path,
    rows_read: int,
    rows: list[WidePredictionRow],
    errors: list[ImportIssue],
    discarded_text_fields: set[str],
) -> ImportSummary:
    duplicate_count = sum(
        count - 1
        for count in Counter((row.model_id, row.subset, row.item_id) for row in rows).values()
        if count > 1
    )
    warnings = []
    if duplicate_count:
        warnings.append("Duplicate model/subset/item rows were detected and reported.")
    return ImportSummary(
        status=status,
        input_path=str(input_path),
        output_path=str(output_path),
        rows_read=rows_read,
        rows_written=len(rows) if status == "ok" else 0,
        duplicate_count=duplicate_count,
        missing_field_count=len(errors),
        model_count=len({row.model_id for row in rows}),
        item_count=len({row.item_id for row in rows}),
        subsets=sorted({row.subset for row in rows}),
        discarded_text_fields=sorted(discarded_text_fields),
        warnings=warnings,
        errors=errors,
    )


def _format_errors(errors: list[ImportIssue]) -> str:
    preview = "; ".join(
        f"row {issue.row_number} {issue.field}: {issue.message}" for issue in errors[:5]
    )
    suffix = "" if len(errors) <= 5 else f"; {len(errors) - 5} more"
    return f"Wide prediction import failed validation: {preview}{suffix}"


def _write_import_report(summary: ImportSummary, report_path: str | Path | None) -> None:
    if not report_path:
        return
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Wide Prediction Import Report",
        "",
        f"- Status: `{summary.status}`",
        f"- Input: `{summary.input_path}`",
        f"- Output: `{summary.output_path}`",
        f"- Rows read: {summary.rows_read}",
        f"- Rows written: {summary.rows_written}",
        f"- Models: {summary.model_count}",
        f"- Items: {summary.item_count}",
        f"- Duplicate rows: {summary.duplicate_count}",
        f"- Discarded text fields: {', '.join(summary.discarded_text_fields) or 'none'}",
    ]
    if summary.errors:
        lines.extend(["", "## Errors"])
        for issue in summary.errors:
            lines.append(f"- Row {issue.row_number}, `{issue.field}`: {issue.message}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _matrix_report(metadata: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "# Wide Response Matrix Report",
                "",
                f"- Matrix CSV: `{metadata['matrix_csv']}`",
                f"- Models: {metadata['n_models']}",
                f"- Items: {metadata['n_items']}",
                f"- Rows: {metadata['n_rows']}",
                f"- Missing cells: {metadata['missing_cells']}",
                "",
                "This matrix is suitable for later diagnostics only after panel-validity checks pass.",
            ]
        )
        + "\n"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
