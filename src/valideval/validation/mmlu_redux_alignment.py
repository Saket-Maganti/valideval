from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from valideval.io.jsonl import read_jsonl, write_jsonl

RAW_TEXT_KEYS = {
    "answer",
    "choices",
    "context",
    "correct_answer",
    "input",
    "prompt",
    "question",
    "raw_input",
    "raw_output",
    "mmlu_redux_source",
    "source_document",
    "source_url",
    "text",
    "url",
}

ISSUE_TYPE_MAP = {
    "bad_options_clarity": "ambiguous_options",
    "bad_question_clarity": "ambiguous_question",
    "expert": "expert_flag",
    "multiple_correct_answers": "multiple_correct",
    "no_correct_answer": "answer_error",
    "wrong_groundtruth": "label_error",
}

SEVERITY_MAP = {
    "answer_error": "high",
    "label_error": "high",
    "multiple_correct": "high",
    "ambiguous_options": "medium",
    "ambiguous_question": "medium",
    "expert_flag": "medium",
}


def align_mmlu_redux(
    *,
    predictions_path: str | Path,
    redux_path: str | Path,
    output_path: str | Path,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    predictions = read_jsonl(predictions_path)
    redux_rows = read_jsonl(redux_path)
    index = _PredictionIndex.from_rows(predictions)

    aligned_rows: list[dict[str, Any]] = []
    skipped_duplicate_source_ids: list[str] = []
    seen_source_issue_ids: set[str] = set()
    for row in sorted(redux_rows, key=_redux_sort_key):
        source_issue_id = _source_issue_id(row)
        if source_issue_id in seen_source_issue_ids:
            skipped_duplicate_source_ids.append(source_issue_id)
            continue
        seen_source_issue_ids.add(source_issue_id)
        match = index.match(row)
        aligned_rows.append(_aligned_row(row, match))

    write_jsonl(output_path, aligned_rows)
    summary = _summary(
        aligned_rows,
        predictions_path=predictions_path,
        redux_path=redux_path,
        output_path=output_path,
        skipped_duplicate_source_ids=skipped_duplicate_source_ids,
    )
    _write_report(summary, report_path)
    return summary


def describe_alignment_schema(
    *,
    predictions_path: str | Path,
    redux_path: str | Path,
    external_predictions_path: str | Path | None = None,
    report_path: str | Path,
    json_path: str | Path,
) -> dict[str, Any]:
    predictions = read_jsonl(predictions_path)
    redux_rows = read_jsonl(redux_path)
    external_predictions = (
        read_jsonl(external_predictions_path) if external_predictions_path else []
    )
    pred_sample = predictions[0] if predictions else {}
    redux_sample = redux_rows[0] if redux_rows else {}
    external_sample = external_predictions[0] if external_predictions else {}
    pred_ids = {str(row.get("item_id")) for row in predictions}
    redux_ids = {str(row.get("item_id")) for row in redux_rows}
    pred_subjects = {str(row.get("subset") or row.get("subject") or "") for row in predictions}
    redux_subjects = {str(row.get("subset") or row.get("subject") or "") for row in redux_rows}
    payload = {
        "schema_version": "0.1",
        "predictions_path": str(predictions_path),
        "redux_path": str(redux_path),
        "external_predictions_path": str(external_predictions_path)
        if external_predictions_path
        else None,
        "redux_fields": sorted(redux_sample.keys()),
        "redux_metadata_fields": sorted((redux_sample.get("metadata") or {}).keys()),
        "helm_prediction_fields": sorted(pred_sample.keys()),
        "helm_prediction_metadata_fields": sorted((pred_sample.get("metadata") or {}).keys()),
        "external_prediction_fields": sorted(external_sample.keys()),
        "external_prediction_metadata_fields": sorted(
            (external_sample.get("metadata") or {}).keys()
        ),
        "redux_item_id_format": _describe_item_id(next(iter(redux_ids), "")),
        "helm_item_id_format": _describe_item_id(next(iter(pred_ids), "")),
        "redux_subject_count": len(redux_subjects - {""}),
        "helm_subject_count": len(pred_subjects - {""}),
        "direct_item_id_matches": len(pred_ids & redux_ids),
        "direct_item_id_match_possible": bool(pred_ids & redux_ids),
        "subject_overlap_count": len((pred_subjects - {""}) & (redux_subjects - {""})),
        "subject_index_match_possible": _subject_index_possible(predictions, redux_rows),
        "stable_metadata_match_possible": _stable_metadata_possible(predictions, redux_rows),
        "hash_match_possible": _hash_match_possible(predictions, redux_rows),
        "raw_text_fields_detected": {
            "redux_top_level": sorted(set(redux_sample) & RAW_TEXT_KEYS),
            "prediction_top_level": sorted(set(pred_sample) & RAW_TEXT_KEYS),
            "external_prediction_top_level": sorted(set(external_sample) & RAW_TEXT_KEYS),
        },
        "conclusion": (
            "Direct item_id matching is not available; sanitized subject plus source row index "
            "alignment is the available path for the current files."
        ),
    }
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    Path(json_path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    _write_schema_report(payload, report_path)
    return payload


class _PredictionIndex:
    def __init__(
        self,
        *,
        direct: dict[str, str],
        by_subject_order: dict[str, list[str]],
        metadata: dict[str, str],
        hashes: dict[str, str],
    ) -> None:
        self.direct = direct
        self.by_subject_order = by_subject_order
        self.metadata = metadata
        self.hashes = hashes

    @classmethod
    def from_rows(cls, rows: list[dict[str, Any]]) -> _PredictionIndex:
        direct: dict[str, str] = {}
        subject_items: dict[str, set[str]] = defaultdict(set)
        metadata: dict[str, str] = {}
        hashes: dict[str, str] = {}
        for row in rows:
            item_id = str(row.get("item_id") or "")
            subject = _subject(row)
            if not item_id:
                continue
            direct[item_id] = item_id
            if subject:
                subject_items[subject].add(item_id)
            for key in _stable_metadata_keys(row):
                metadata.setdefault(key, item_id)
            for key in _hash_keys(row):
                hashes.setdefault(key, item_id)
        by_subject_order = {
            subject: sorted(items, key=_item_sort_key) for subject, items in subject_items.items()
        }
        return cls(
            direct=direct, by_subject_order=by_subject_order, metadata=metadata, hashes=hashes
        )

    def match(self, redux_row: dict[str, Any]) -> dict[str, Any]:
        source_id = str(redux_row.get("item_id") or "")
        if source_id in self.direct:
            return {
                "item_id": self.direct[source_id],
                "method": "direct_item_id",
                "confidence": 1.0,
            }
        for key in _stable_metadata_keys(redux_row):
            if key in self.metadata:
                return {
                    "item_id": self.metadata[key],
                    "method": "stable_source_metadata",
                    "confidence": 0.95,
                }
        for key in _hash_keys(redux_row):
            if key in self.hashes:
                return {"item_id": self.hashes[key], "method": "hash_match", "confidence": 0.95}
        subject = _subject(redux_row)
        source_index = _source_row_index(redux_row)
        if subject and source_index is not None:
            subject_items = self.by_subject_order.get(subject) or []
            if 0 <= source_index < len(subject_items):
                return {
                    "item_id": subject_items[source_index],
                    "method": "subject_numeric_index",
                    "confidence": 0.85,
                }
        return {"item_id": source_id, "method": "unaligned", "confidence": 0.0}


def _aligned_row(row: dict[str, Any], match: dict[str, Any]) -> dict[str, Any]:
    metadata = _sanitized_metadata(row.get("metadata") or {})
    redux_error_type = str(metadata.get("mmlu_redux_error_type") or row.get("issue_type") or "")
    issue_type = ISSUE_TYPE_MAP.get(
        redux_error_type, str(row.get("issue_type") or "mmlu_redux_flaw")
    )
    subject = _subject(row)
    source_issue_id = _source_issue_id(row)
    alignment_method = str(match["method"])
    metadata.update(
        {
            "aligned": alignment_method != "unaligned",
            "alignment_input_item_id": row.get("item_id"),
            "original_benchmark": row.get("benchmark"),
            "original_issue_type": row.get("issue_type"),
            "source_issue_id": source_issue_id,
        }
    )
    return {
        "schema_version": "0.1",
        "benchmark": "mmlu",
        "subset": subject,
        "subject": subject,
        "item_id": str(match["item_id"]),
        "source_issue_id": source_issue_id,
        "issue_type": issue_type,
        "severity": _severity(row, issue_type),
        "alignment_method": alignment_method,
        "alignment_confidence": float(match["confidence"]),
        "source": "mmlu_redux",
        "metadata": metadata,
    }


def _summary(
    aligned_rows: list[dict[str, Any]],
    *,
    predictions_path: str | Path,
    redux_path: str | Path,
    output_path: str | Path,
    skipped_duplicate_source_ids: list[str],
) -> dict[str, Any]:
    total = len(aligned_rows)
    aligned = [row for row in aligned_rows if row["alignment_method"] != "unaligned"]
    method_counts = Counter(row["alignment_method"] for row in aligned_rows)
    subjects_aligned = sorted({row["subject"] for row in aligned})
    subjects_total = sorted({row["subject"] for row in aligned_rows})
    confidence_values = [float(row["alignment_confidence"]) for row in aligned_rows]
    confidence_counts = Counter(f"{value:.2f}" for value in confidence_values)
    return {
        "schema_version": "0.1",
        "status": "ok" if aligned else "blocked",
        "predictions_path": str(predictions_path),
        "redux_path": str(redux_path),
        "output_path": str(output_path),
        "total_redux_labels": total + len(skipped_duplicate_source_ids),
        "output_rows": total,
        "aligned_count": len(aligned),
        "unaligned_count": total - len(aligned),
        "aligned_fraction": len(aligned) / total if total else 0.0,
        "alignment_method_counts": dict(sorted(method_counts.items())),
        "subjects_aligned": subjects_aligned,
        "subjects_missing": sorted(set(subjects_total) - set(subjects_aligned)),
        "subject_count_aligned": len(subjects_aligned),
        "confidence_distribution": dict(sorted(confidence_counts.items())),
        "skipped_duplicate_source_issue_count": len(skipped_duplicate_source_ids),
        "warnings": _alignment_warnings(total, len(aligned), skipped_duplicate_source_ids),
    }


def _alignment_warnings(
    total: int,
    aligned_count: int,
    skipped_duplicate_source_ids: list[str],
) -> list[str]:
    warnings = [
        "No raw MMLU question text was used or written by this alignment report.",
        "Subject/index alignment assumes the MMLU-Redux source row order matches the HELM MMLU test item order within each subject.",
    ]
    fraction = aligned_count / total if total else 0.0
    if fraction < 0.8:
        warnings.append("Aligned fraction is below 0.80; do not run Redux validation as evidence.")
    if skipped_duplicate_source_ids:
        warnings.append("Duplicate source issue ids were skipped deterministically.")
    return warnings


def _write_report(summary: dict[str, Any], report_path: str | Path | None) -> None:
    if not report_path:
        return
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MMLU-Redux to HELM Alignment Report",
        "",
        "This report is sanitized. It uses item ids, subject names, source row indexes, hashes, and metadata only. It does not expose raw MMLU question text.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Total Redux labels: {summary['total_redux_labels']}",
        f"- Output rows: {summary['output_rows']}",
        f"- Aligned labels: {summary['aligned_count']}",
        f"- Unaligned labels: {summary['unaligned_count']}",
        f"- Aligned fraction: {summary['aligned_fraction']:.3f}",
        f"- Subjects aligned: {summary['subject_count_aligned']}",
        f"- Duplicate source issue ids skipped: {summary['skipped_duplicate_source_issue_count']}",
        "",
        "## Alignment Methods",
        "",
        *[f"- `{method}`: {count}" for method, count in summary["alignment_method_counts"].items()],
        "",
        "## Confidence Distribution",
        "",
        *[f"- `{bucket}`: {count}" for bucket, count in summary["confidence_distribution"].items()],
        "",
        "## Subjects Missing Alignment",
        "",
        *([f"- `{subject}`" for subject in summary["subjects_missing"]] or ["- none"]),
        "",
        "## Warnings",
        "",
        *[f"- {warning}" for warning in summary["warnings"]],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.with_suffix(".json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )


def _write_schema_report(payload: dict[str, Any], report_path: str | Path) -> None:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MMLU-Redux Alignment Schema Report",
        "",
        "This report is sanitized and does not expose raw MMLU question text.",
        "",
        "## Redux Labels",
        "",
        f"- Fields: {', '.join(payload['redux_fields'])}",
        f"- Metadata fields: {', '.join(payload['redux_metadata_fields'])}",
        f"- Item id format: `{payload['redux_item_id_format']}`",
        f"- Subject count: {payload['redux_subject_count']}",
        "",
        "## HELM Predictions",
        "",
        f"- Fields: {', '.join(payload['helm_prediction_fields'])}",
        f"- Metadata fields: {', '.join(payload['helm_prediction_metadata_fields'])}",
        f"- Item id format: `{payload['helm_item_id_format']}`",
        f"- Subject count: {payload['helm_subject_count']}",
        "",
        "## Alignment Feasibility",
        "",
        f"- Direct item_id matches: {payload['direct_item_id_matches']}",
        f"- Direct item_id match possible: `{payload['direct_item_id_match_possible']}`",
        f"- Subject overlap count: {payload['subject_overlap_count']}",
        f"- Subject + numeric index match possible: `{payload['subject_index_match_possible']}`",
        f"- Stable metadata match possible: `{payload['stable_metadata_match_possible']}`",
        f"- Hash match possible: `{payload['hash_match_possible']}`",
        "",
        "## Raw Text Field Check",
        "",
        f"- Redux top-level raw-text-like fields: {payload['raw_text_fields_detected']['redux_top_level']}",
        f"- Prediction top-level raw-text-like fields: {payload['raw_text_fields_detected']['prediction_top_level']}",
        f"- External prediction top-level raw-text-like fields: {payload['raw_text_fields_detected']['external_prediction_top_level']}",
        "",
        "## Conclusion",
        "",
        payload["conclusion"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _subject(row: dict[str, Any]) -> str:
    return str(row.get("subset") or row.get("subject") or "").strip()


def _source_issue_id(row: dict[str, Any]) -> str:
    return str(row.get("source_issue_id") or row.get("item_id") or "")


def _source_row_index(row: dict[str, Any]) -> int | None:
    metadata = row.get("metadata") or {}
    value = metadata.get("source_row_index")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    item_id = str(row.get("item_id") or "")
    match = re.search(r"_(\d+)$", item_id)
    return int(match.group(1)) if match else None


def _item_sort_key(item_id: str) -> tuple[str, int, str]:
    match = re.search(r"(\d+)$", item_id)
    return (re.sub(r"\d+$", "", item_id), int(match.group(1)) if match else -1, item_id)


def _redux_sort_key(row: dict[str, Any]) -> tuple[str, int, str]:
    index = _source_row_index(row)
    return (_subject(row), index if index is not None else 10**9, _source_issue_id(row))


def _stable_metadata_keys(row: dict[str, Any]) -> set[str]:
    metadata = row.get("metadata") or {}
    keys = set()
    for key in ("helm_instance_id", "source_instance_id", "original_item_id"):
        value = metadata.get(key) or row.get(key)
        if value:
            keys.add(f"{key}:{value}")
    subject = _subject(row)
    source_row_index = _source_row_index(row)
    if subject and source_row_index is not None and metadata.get("source_dataset") == "helm":
        keys.add(f"helm_source_row:{subject}:{source_row_index}")
    return keys


def _hash_keys(row: dict[str, Any]) -> set[str]:
    metadata = row.get("metadata") or {}
    keys = set()
    for key in ("question_hash", "choices_hash", "item_hash", "prompt_hash"):
        value = metadata.get(key) or row.get(key)
        if value:
            keys.add(f"{key}:{value}")
    return keys


def _sanitized_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metadata.items() if key not in RAW_TEXT_KEYS}


def _severity(row: dict[str, Any], issue_type: str) -> str:
    value = str(row.get("severity") or "").strip().lower()
    if value and value != "unknown":
        return value
    return SEVERITY_MAP.get(issue_type, "unknown")


def _describe_item_id(item_id: str) -> str:
    if not item_id:
        return "empty"
    if re.fullmatch(r"mmlu_redux2_[a-z0-9_]+_\d{4}", item_id):
        return "mmlu_redux2_{subject}_{zero_padded_source_row_index}"
    if re.fullmatch(r"mmlu_[a-z0-9_]+_id\d+", item_id):
        return "mmlu_{subject}_id{helm_instance_number}"
    return "other"


def _subject_index_possible(
    predictions: list[dict[str, Any]],
    redux_rows: list[dict[str, Any]],
) -> bool:
    prediction_subjects = {_subject(row) for row in predictions}
    return any(
        _subject(row) in prediction_subjects and _source_row_index(row) is not None
        for row in redux_rows
    )


def _stable_metadata_possible(
    predictions: list[dict[str, Any]],
    redux_rows: list[dict[str, Any]],
) -> bool:
    prediction_keys = set().union(*(_stable_metadata_keys(row) for row in predictions), set())
    redux_keys = set().union(*(_stable_metadata_keys(row) for row in redux_rows), set())
    return bool(prediction_keys & redux_keys)


def _hash_match_possible(
    predictions: list[dict[str, Any]],
    redux_rows: list[dict[str, Any]],
) -> bool:
    prediction_keys = set().union(*(_hash_keys(row) for row in predictions), set())
    redux_keys = set().union(*(_hash_keys(row) for row in redux_rows), set())
    return bool(prediction_keys & redux_keys)
