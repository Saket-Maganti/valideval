from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.importers.lm_eval_mmlu import (
    extract_mmlu_gold,
    extract_mmlu_prediction,
    first_present,
    first_scalar,
    model_id_from_results,
    task_from_sample_filename,
)
from valideval.importers.schemas import ImportIssue, ImportSummary, WidePredictionRow
from valideval.importers.wide_matrix import _write_import_report
from valideval.io.jsonl import write_jsonl

LM_EVAL_TEXT_FIELDS = {"doc", "arguments", "prompt", "input", "ctx", "question"}


def import_lm_eval_samples(
    input_path: str | Path,
    *,
    benchmark: str,
    output_path: str | Path,
    mapping_report: str | Path | None = None,
    include_text: bool = False,
    model_id: str | None = None,
) -> dict[str, Any]:
    source = Path(input_path)
    sample_files = _discover_sample_files(source)
    rows: list[WidePredictionRow] = []
    errors: list[ImportIssue] = []
    discarded_text_fields: set[str] = set()

    for sample_file in sample_files:
        inferred_model = model_id or _infer_model_id(sample_file, source)
        with sample_file.open("r", encoding="utf-8") as handle:
            for row_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(
                        ImportIssue(
                            row_number=row_number,
                            field=str(sample_file),
                            message=f"Invalid JSON: {exc}",
                        )
                    )
                    continue
                row, row_errors, discarded = _normalize_lm_eval_record(
                    record,
                    row_number=row_number,
                    source_file=sample_file,
                    benchmark=benchmark,
                    model_id=inferred_model,
                    include_text=include_text,
                )
                if row is not None:
                    rows.append(row)
                errors.extend(row_errors)
                discarded_text_fields.update(discarded)

    destination = Path(output_path)
    duplicate_count = _duplicate_count(rows)
    if not errors and duplicate_count:
        rows = _dedupe_rows(rows)
    status = "invalid" if errors else "ok"
    summary = ImportSummary(
        status=status,
        input_path=str(source),
        output_path=str(destination),
        rows_read=sum(
            1
            for file in sample_files
            for line in file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ),
        rows_written=0 if errors else len(rows),
        duplicate_count=duplicate_count,
        missing_field_count=len(errors),
        model_count=len({row.model_id for row in rows}),
        item_count=len({row.item_id for row in rows}),
        subsets=sorted({row.subset for row in rows}),
        discarded_text_fields=sorted(discarded_text_fields),
        warnings=[
            *(
                [
                    "Duplicate lm-eval rows were dropped by first-seen model/subset/item key; inspect source paths before evidence claims."
                ]
                if duplicate_count
                else []
            ),
            *(
                [
                    "lm-eval sample prompts/docs are discarded by default; pass --include-text only for private inspection."
                ]
                if discarded_text_fields
                else []
            ),
        ],
        errors=errors,
    )
    _write_import_report(summary, mapping_report)
    if errors:
        raise ValueError(_format_lm_eval_errors(errors))
    write_jsonl(destination, rows)
    _write_summary_json(destination, summary.model_dump(mode="json"), sample_files)
    return summary.model_dump(mode="json") | {
        "format": "lm_eval",
        "sample_files": [str(path) for path in sample_files],
    }


def _discover_sample_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if not source.exists():
        raise ValueError(f"lm-eval input path does not exist: {source}")
    candidates = sorted(
        path
        for path in source.rglob("*.jsonl")
        if path.name.startswith("samples_") or "sample" in path.name.lower()
    )
    if not candidates:
        candidates = sorted(source.rglob("*.jsonl"))
    if not candidates:
        raise ValueError(f"No lm-eval JSONL sample files found under {source}")
    return candidates


def _normalize_lm_eval_record(
    record: dict[str, Any],
    *,
    row_number: int,
    source_file: Path,
    benchmark: str,
    model_id: str,
    include_text: bool,
) -> tuple[WidePredictionRow | None, list[ImportIssue], set[str]]:
    item_id = first_present(record, ["doc_id", "item_id", "sample_id", "id", "idx"])
    task_name = str(
        first_present(record, ["task", "task_name", "dataset", "subset"])
        or _task_from_filename(source_file)
    )
    prediction, prediction_metadata = _extract_prediction(record)
    gold, gold_metadata = _extract_gold(record)
    correct = _extract_correct(record)
    if correct is None and prediction not in (None, "") and gold not in (None, ""):
        correct = str(prediction) == str(gold)
    errors = []
    for field, value in {
        "item_id": item_id,
        "model_id": model_id,
        "prediction": prediction,
        "gold": gold,
    }.items():
        if value in (None, ""):
            errors.append(
                ImportIssue(
                    row_number=row_number,
                    field=field,
                    message=f"lm-eval sample is missing required field: {field}",
                )
            )
    if errors:
        return None, errors, set()

    discarded = {field for field in record if field in LM_EVAL_TEXT_FIELDS and not include_text}
    metadata = {
        key: value
        for key, value in record.items()
        if key not in discarded
        and key
        not in {
            "doc_id",
            "item_id",
            "sample_id",
            "id",
            "idx",
            "task",
            "task_name",
            "dataset",
            "subset",
            "filtered_resps",
            "resps",
            "target",
            "gold",
            "answer",
            "correct_answer",
            "acc",
            "exact_match",
            "metrics",
        }
    }
    metadata["lm_eval_task"] = task_name
    metadata["lm_eval_source_file"] = str(source_file)
    metadata.update(prediction_metadata)
    metadata.update(gold_metadata)
    metadata["raw_prediction"] = _safe_raw_prediction(record)
    if discarded:
        metadata["discarded_text_fields"] = sorted(discarded)

    return (
        WidePredictionRow(
            benchmark=benchmark,
            subset=task_name,
            item_id=str(item_id),
            model_id=model_id,
            prediction=str(prediction),
            gold=str(gold),
            correct=correct,
            source="lm_eval:log_samples",
            source_file=str(source_file),
            metadata=metadata,
        ),
        [],
        discarded,
    )


def _extract_prediction(record: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    return extract_mmlu_prediction(record)


def _extract_gold(record: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    return extract_mmlu_gold(record)


def _extract_correct(record: dict[str, Any]) -> bool | None:
    value = first_present(record, ["acc", "exact_match", "correct", "is_correct"])
    if value is None and isinstance(record.get("metrics"), dict):
        value = first_present(record["metrics"], ["acc", "exact_match", "correct"])
    if isinstance(value, list):
        value = first_scalar(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return float(value) >= 0.5
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "correct"}:
            return True
        if lowered in {"0", "false", "no", "incorrect"}:
            return False
    return None


def _infer_model_id(sample_file: Path, root: Path) -> str:
    result_model = model_id_from_results(sample_file)
    if result_model:
        return result_model
    if root.is_file():
        parent = sample_file.parent.name
        return parent if parent not in {"", "."} else "lm_eval_model"
    try:
        relative = sample_file.relative_to(root)
    except ValueError:
        relative = sample_file
    if len(relative.parts) > 1:
        return relative.parts[0]
    parent = sample_file.parent.name
    return parent if parent not in {"", "."} else "lm_eval_model"


def _task_from_filename(path: Path) -> str:
    return task_from_sample_filename(path)


def _safe_raw_prediction(record: dict[str, Any]) -> Any:
    value = first_present(record, ["filtered_resps", "resps", "prediction", "pred", "answer"])
    return value


def _duplicate_count(rows: list[WidePredictionRow]) -> int:
    seen: set[tuple[str, str, str]] = set()
    duplicates = 0
    for row in rows:
        key = (row.model_id, row.subset, row.item_id)
        if key in seen:
            duplicates += 1
        seen.add(key)
    return duplicates


def _dedupe_rows(rows: list[WidePredictionRow]) -> list[WidePredictionRow]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[WidePredictionRow] = []
    for row in rows:
        key = (row.model_id, row.subset, row.item_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _format_lm_eval_errors(errors: list[ImportIssue]) -> str:
    preview = "; ".join(
        f"row {issue.row_number} {issue.field}: {issue.message}" for issue in errors[:5]
    )
    suffix = "" if len(errors) <= 5 else f"; {len(errors) - 5} more"
    return f"lm-eval sample import failed validation: {preview}{suffix}"


def _write_summary_json(
    output_path: Path,
    summary: dict[str, Any],
    sample_files: list[Path],
) -> None:
    summary["sample_files"] = [str(path) for path in sample_files]
    output_path.with_suffix(output_path.suffix + ".summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
