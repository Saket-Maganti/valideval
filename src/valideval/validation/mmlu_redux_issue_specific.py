from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from valideval.config import load_yaml
from valideval.diagnostics.panel_validity import load_matrix_csv
from valideval.io.jsonl import read_jsonl
from valideval.psychometrics.irt_models import estimate_irt_proxy
from valideval.schemas import ResponseMatrix
from valideval.validation.detector_metrics import precision_recall_auc, roc_auc
from valideval.validation.external_ground_truth import ExternalIssue, load_ground_truth

TEXT_KEYS = {
    "prompt",
    "question",
    "context",
    "text",
    "choices",
    "answer_choices",
    "raw_output",
}

AVAILABLE_DIAGNOSTICS = {
    "high_disagreement",
    "correct_answer_rarely_selected",
    "negative_discrimination",
    "low_discrimination",
    "extreme_difficulty",
    "option_selection_anomaly",
    "bimodal_model_choices",
}

SUBJECT_NORMALIZED_BASE_DIAGNOSTICS = {
    "correct_answer_rarely_selected",
    "high_disagreement",
    "option_selection_anomaly",
    "negative_discrimination",
    "low_discrimination",
    "extreme_difficulty",
}

SUBJECT_NORMALIZED_DIAGNOSTICS = {
    f"{diagnostic}_subject_z" for diagnostic in SUBJECT_NORMALIZED_BASE_DIAGNOSTICS
}

AVAILABLE_DIAGNOSTICS.update(SUBJECT_NORMALIZED_DIAGNOSTICS)

BLOCKED_DIAGNOSTICS = {
    "extraction_sensitivity": "blocked_missing_strict_lenient_extraction_metadata",
    "prompt_sensitivity": "blocked_no_complete_prompt_variant_matrix",
}

DEFAULT_TOP_K = (10, 25, 50)
NORMALIZED_SUFFIX = "_subject_z"
SCORE_DIRECTION = "higher_is_more_suspicious"


def write_issue_taxonomy(
    *,
    aligned_ground_truth_path: str | Path,
    output_dir: str | Path,
    normalized_ground_truth_path: str | Path | None = None,
    min_positive_count: int = 20,
) -> dict[str, Any]:
    aligned_records = read_jsonl(aligned_ground_truth_path)
    normalized_records = (
        read_jsonl(normalized_ground_truth_path) if normalized_ground_truth_path else []
    )
    taxonomy = build_issue_taxonomy(
        aligned_records,
        normalized_records=normalized_records,
        min_positive_count=min_positive_count,
        aligned_path=str(aligned_ground_truth_path),
        normalized_path=str(normalized_ground_truth_path) if normalized_ground_truth_path else None,
    )
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "issue_taxonomy.json").write_text(
        json.dumps(taxonomy, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "issue_taxonomy.md").write_text(
        render_issue_taxonomy(taxonomy),
        encoding="utf-8",
    )
    return taxonomy


def build_issue_taxonomy(
    aligned_records: list[dict[str, Any]],
    *,
    normalized_records: list[dict[str, Any]] | None = None,
    min_positive_count: int = 20,
    aligned_path: str | None = None,
    normalized_path: str | None = None,
) -> dict[str, Any]:
    normalized_records = normalized_records or []
    sanitized = [_sanitize_issue_record(row) for row in aligned_records]
    issue_counts = Counter(row["issue_type"] for row in sanitized)
    severity_counts = Counter(row["severity"] for row in sanitized)
    subject_counts = Counter(row["subject"] for row in sanitized)
    issue_subject: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    issue_severity: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in sanitized:
        issue_subject[row["issue_type"]][row["subject"]] += 1
        issue_severity[row["issue_type"]][row["severity"]] += 1

    issue_type_status = {}
    for issue_type, count in sorted(issue_counts.items()):
        issue_type_status[issue_type] = {
            "positive_count": int(count),
            "status": "evaluable" if count >= min_positive_count else "underpowered",
            "underpowered": bool(count < min_positive_count),
            "min_positive_count": int(min_positive_count),
            "power_note": "sparse; expect wide uncertainty"
            if count < 50
            else "adequate for preliminary ranking metrics",
        }

    normalized_summary = {
        "path": normalized_path,
        "row_count": len(normalized_records),
        "issue_type_counts": dict(
            sorted(Counter(_value(row, "issue_type") for row in normalized_records).items())
        ),
        "severity_counts": dict(
            sorted(Counter(_value(row, "severity") for row in normalized_records).items())
        ),
        "note": (
            "Normalized Redux rows collapse the taxonomy before HELM alignment."
            if normalized_records
            else "No normalized Redux file supplied."
        ),
    }

    return {
        "schema_version": "0.1",
        "status": "ok" if sanitized else "empty",
        "aligned_path": aligned_path,
        "normalized_summary": normalized_summary,
        "row_count": len(sanitized),
        "issue_type_counts": dict(sorted(issue_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "subject_counts": dict(sorted(subject_counts.items())),
        "issue_type_by_subject": {
            issue_type: dict(sorted(subjects.items()))
            for issue_type, subjects in sorted(issue_subject.items())
        },
        "issue_type_by_severity": {
            issue_type: dict(sorted(severities.items()))
            for issue_type, severities in sorted(issue_severity.items())
        },
        "issue_type_status": issue_type_status,
        "warnings": [
            "Taxonomy uses aligned MMLU-Redux labels and no raw MMLU question text.",
            "Alignment is structural and should be treated as confidence 0.85 unless upgraded.",
        ],
    }


def run_mmlu_redux_issue_validation(
    *,
    predictions_path: str | Path,
    matrix_path: str | Path,
    ground_truth_path: str | Path,
    mapping_path: str | Path,
    output_dir: str | Path,
    restrict_to_ground_truth_subjects: bool = False,
    severities: list[str] | None = None,
    issue_types: list[str] | None = None,
    diagnostics: list[str] | None = None,
    subject_normalize: bool = False,
    subject_matched_null: int = 0,
    min_positive_count: int = 20,
    bootstrap_samples: int = 200,
    seed: int = 0,
) -> dict[str, Any]:
    mapping = load_issue_mapping(mapping_path)
    issues = _filter_issues(
        load_ground_truth(ground_truth_path),
        severities=severities,
        issue_types=issue_types,
    )
    observed_issue_types = sorted({issue.issue_type for issue in issues})
    mapping_warnings = validate_issue_mapping(mapping, observed_issue_types)
    scores = compute_issue_specific_scores(
        predictions_path=predictions_path,
        matrix_path=matrix_path,
        subject_normalize=subject_normalize,
    )
    if restrict_to_ground_truth_subjects:
        allowed_subjects = {issue.subset for issue in issues}
        scores = [row for row in scores if row["subject"] in allowed_subjects]

    metrics: dict[str, dict[str, Any]] = {}
    matrix_rows: list[dict[str, Any]] = []
    top_rows: list[dict[str, Any]] = []
    issue_items_by_type: dict[str, set[str]] = defaultdict(set)
    issue_meta_by_item_type: dict[tuple[str, str], list[ExternalIssue]] = defaultdict(list)
    for issue in issues:
        issue_items_by_type[issue.issue_type].add(issue.item_id)
        issue_meta_by_item_type[(issue.issue_type, issue.item_id)].append(issue)

    for issue_type in observed_issue_types:
        issue_metrics = {}
        plausible = _select_diagnostics(
            mapping["issue_type_mapping"].get(issue_type, {}).get("plausible_diagnostics", []),
            diagnostics=diagnostics,
            subject_normalize=subject_normalize,
        )
        for diagnostic in plausible:
            if diagnostic in BLOCKED_DIAGNOSTICS:
                row = _blocked_metric(
                    issue_type=issue_type,
                    diagnostic=diagnostic,
                    reason=BLOCKED_DIAGNOSTICS[diagnostic],
                    positives=len(issue_items_by_type[issue_type]),
                    min_positive_count=min_positive_count,
                )
            elif diagnostic not in AVAILABLE_DIAGNOSTICS:
                row = _blocked_metric(
                    issue_type=issue_type,
                    diagnostic=diagnostic,
                    reason="unsupported_diagnostic",
                    positives=len(issue_items_by_type[issue_type]),
                    min_positive_count=min_positive_count,
                )
            else:
                row = _metrics_for_issue_type(
                    scores,
                    issue_type=issue_type,
                    diagnostic=diagnostic,
                    positive_items=issue_items_by_type[issue_type],
                    issue_meta_by_item_type=issue_meta_by_item_type,
                    min_positive_count=min_positive_count,
                    bootstrap_samples=bootstrap_samples,
                    seed=seed,
                )
                top_rows.extend(row.pop("top_rows", []))
            issue_metrics[diagnostic] = row
            matrix_rows.append(_matrix_row(issue_type, diagnostic, row))
        metrics[issue_type] = issue_metrics

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "0.1",
        "status": "ok" if metrics else "empty",
        "inputs": {
            "predictions": str(predictions_path),
            "matrix": str(matrix_path),
            "ground_truth": str(ground_truth_path),
            "mapping": str(mapping_path),
        },
        "filters": {
            "restrict_to_ground_truth_subjects": restrict_to_ground_truth_subjects,
            "severities": severities or [],
            "issue_types": issue_types or [],
            "diagnostics": diagnostics or [],
            "subject_normalize": subject_normalize,
            "subject_matched_null": subject_matched_null,
            "min_positive_count": min_positive_count,
        },
        "diagnostic_availability": {
            "available": sorted(AVAILABLE_DIAGNOSTICS),
            "blocked": BLOCKED_DIAGNOSTICS,
            "subject_normalized": sorted(SUBJECT_NORMALIZED_DIAGNOSTICS),
        },
        "mapping_warnings": mapping_warnings,
        "issue_type_metrics": metrics,
        "warnings": [
            "Issue-specific validation is preliminary and protocol-scoped.",
            "No raw MMLU question text or answer choices are exported.",
            "MMLU-Redux alignment is structural with confidence 0.85.",
        ],
    }
    (destination / "issue_type_metrics.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "issue_type_metrics.md").write_text(
        render_issue_validation_report(payload),
        encoding="utf-8",
    )
    _write_matrix_outputs(destination, matrix_rows)
    _write_top_items(destination, top_rows)
    if subject_normalize:
        _write_subject_normalized_item_scores(destination, scores)
        _write_raw_vs_subject_normalized_comparison(destination, payload)
    if subject_matched_null > 0:
        null_payload = _subject_matched_null_payload(
            score_rows=scores,
            metrics=metrics,
            issue_items_by_type=issue_items_by_type,
            iterations=subject_matched_null,
            seed=seed,
        )
        _write_subject_matched_null(destination, null_payload)
        payload["subject_matched_null"] = {
            "iterations": subject_matched_null,
            "path_json": str(destination / "subject_matched_null.json"),
            "path_md": str(destination / "subject_matched_null.md"),
        }
        (destination / "issue_type_metrics.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return payload


def load_issue_mapping(mapping_path: str | Path) -> dict[str, Any]:
    mapping = load_yaml(mapping_path)
    if not isinstance(mapping.get("issue_type_mapping"), dict):
        raise ValueError("Issue mapping must contain issue_type_mapping.")
    for issue_type, spec in mapping["issue_type_mapping"].items():
        if not isinstance(spec, dict):
            raise ValueError(f"Mapping for {issue_type} must be an object.")
        if not isinstance(spec.get("plausible_diagnostics"), list):
            raise ValueError(f"Mapping for {issue_type} must list plausible_diagnostics.")
        spec.setdefault("excluded_diagnostics", [])
    return mapping


def validate_issue_mapping(mapping: dict[str, Any], issue_types: list[str]) -> list[str]:
    warnings: list[str] = []
    mapped = set(mapping.get("issue_type_mapping", {}))
    observed = set(issue_types)
    for issue_type in sorted(observed - mapped):
        warnings.append(f"Observed issue type `{issue_type}` is missing from mapping.")
    for issue_type in sorted(mapped - observed):
        warnings.append(f"Mapped issue type `{issue_type}` is absent after current filters.")
    for issue_type, spec in sorted(mapping.get("issue_type_mapping", {}).items()):
        for diagnostic in spec.get("plausible_diagnostics", []):
            if diagnostic not in AVAILABLE_DIAGNOSTICS and diagnostic not in BLOCKED_DIAGNOSTICS:
                warnings.append(
                    f"Mapping references unsupported diagnostic `{diagnostic}` for `{issue_type}`."
                )
    return warnings


def _select_diagnostics(
    plausible: list[str],
    *,
    diagnostics: list[str] | None,
    subject_normalize: bool,
) -> list[str]:
    selected = list(plausible)
    if diagnostics:
        requested = set(diagnostics)
        selected = [diagnostic for diagnostic in selected if diagnostic in requested]
        for diagnostic in diagnostics:
            if diagnostic not in selected and diagnostic in AVAILABLE_DIAGNOSTICS:
                selected.append(diagnostic)
    if subject_normalize:
        expanded = []
        for diagnostic in selected:
            expanded.append(diagnostic)
            normalized = _subject_normalized_name(diagnostic)
            if normalized in AVAILABLE_DIAGNOSTICS:
                expanded.append(normalized)
        selected = expanded
    return _dedupe(selected)


def _subject_normalized_name(diagnostic: str) -> str:
    if diagnostic.endswith(NORMALIZED_SUFFIX):
        return diagnostic
    if diagnostic in SUBJECT_NORMALIZED_BASE_DIAGNOSTICS:
        return f"{diagnostic}{NORMALIZED_SUFFIX}"
    return diagnostic


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def compute_issue_specific_scores(
    *,
    predictions_path: str | Path,
    matrix_path: str | Path,
    subject_normalize: bool = False,
) -> list[dict[str, Any]]:
    frame = load_matrix_csv(matrix_path)
    prediction_stats = _load_prediction_stats(predictions_path)
    proxy = estimate_irt_proxy(
        ResponseMatrix.from_dataframe(frame, metadata={"source_matrix": str(matrix_path)})
    )
    rows = []
    for item_key in frame.columns:
        subject, item_id = _split_item_key(str(item_key))
        values = frame[item_key].dropna().astype(float)
        correct_rate = float(values.mean()) if not values.empty else None
        stats = prediction_stats.get(item_id, {})
        option_counts: Counter[str] = stats.get("option_counts", Counter())
        valid_option_n = int(sum(option_counts.values()))
        gold = str(stats.get("gold") or "")
        option_fractions = {
            option: (option_counts.get(option, 0) / valid_option_n if valid_option_n else 0.0)
            for option in ("A", "B", "C", "D")
        }
        majority_fraction = max(option_fractions.values()) if valid_option_n else None
        gold_fraction = option_fractions.get(gold) if gold in option_fractions else correct_rate
        entropy = _normalized_entropy(list(option_fractions.values())) if valid_option_n else None
        item_proxy = proxy["item_stats"].get(str(item_key), {})
        discrimination = _float_or_none(item_proxy.get("discrimination"))
        proportion_correct = _float_or_none(item_proxy.get("proportion_correct"))
        if correct_rate is None:
            correct_rate = proportion_correct
        diagnostics = {
            "high_disagreement": _none_if_none(
                None if majority_fraction is None else 1.0 - majority_fraction
            ),
            "correct_answer_rarely_selected": _none_if_none(
                None if correct_rate is None else 1.0 - correct_rate
            ),
            "negative_discrimination": _none_if_none(
                None if discrimination is None else max(0.0, -discrimination)
            ),
            "low_discrimination": _low_discrimination_score(discrimination),
            "extreme_difficulty": _none_if_none(
                None if correct_rate is None else abs(correct_rate - 0.5) * 2.0
            ),
            "option_selection_anomaly": _option_selection_anomaly(
                entropy=entropy,
                gold_fraction=gold_fraction,
            ),
            "bimodal_model_choices": _bimodal_choice_score(
                option_fractions,
                gold=gold,
                valid_option_n=valid_option_n,
            ),
        }
        rows.append(
            {
                "item_key": str(item_key),
                "item_id": item_id,
                "subject": subject,
                "diagnostics": diagnostics,
                "diagnostic_details": {
                    diagnostic: {
                        "raw_score": score,
                        "score": score,
                        "direction": SCORE_DIRECTION,
                    }
                    for diagnostic, score in diagnostics.items()
                },
                "metadata": {
                    "valid_option_fraction": valid_option_n / max(int(stats.get("n", 0)), 1)
                    if stats
                    else 0.0,
                    "gold_option_available": gold in {"A", "B", "C", "D"},
                },
            }
        )
    if subject_normalize:
        _add_subject_normalized_scores(rows)
    return rows


def _add_subject_normalized_scores(rows: list[dict[str, Any]]) -> None:
    for diagnostic in sorted(SUBJECT_NORMALIZED_BASE_DIAGNOSTICS):
        by_subject: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            score = row["diagnostics"].get(diagnostic)
            if score is not None and np.isfinite(float(score)):
                by_subject[row["subject"]].append(float(score))

        stats_by_subject = {}
        for subject, values in by_subject.items():
            mean = float(np.mean(values)) if values else 0.0
            std = float(np.std(values)) if values else 0.0
            stats_by_subject[subject] = {
                "mean": mean,
                "std": std if np.isfinite(std) else 0.0,
            }

        normalized_name = _subject_normalized_name(diagnostic)
        for row in rows:
            raw_score = row["diagnostics"].get(diagnostic)
            subject_stats = stats_by_subject.get(row["subject"], {"mean": 0.0, "std": 0.0})
            mean = subject_stats["mean"]
            std = subject_stats["std"]
            if raw_score is None or not np.isfinite(float(raw_score)):
                normalized_score = None
            elif std <= 0.0:
                normalized_score = 0.0
            else:
                normalized_score = (float(raw_score) - mean) / std
            row["diagnostics"][normalized_name] = normalized_score
            row.setdefault("diagnostic_details", {})[normalized_name] = {
                "diagnostic": normalized_name,
                "raw_diagnostic": diagnostic,
                "raw_score": raw_score,
                "subject_mean": mean,
                "subject_std": std,
                "score": normalized_score,
                "direction": SCORE_DIRECTION,
                "normalization": "subject_z",
                "zero_variance_subject": bool(std <= 0.0),
            }


def render_issue_taxonomy(taxonomy: dict[str, Any]) -> str:
    lines = [
        "# MMLU-Redux Issue Taxonomy",
        "",
        "Preliminary, protocol-scoped taxonomy. No raw MMLU question text or answer choices are included.",
        "",
        f"- Rows: {taxonomy['row_count']}",
        f"- Issue types: {len(taxonomy['issue_type_counts'])}",
        f"- Subjects: {len(taxonomy['subject_counts'])}",
        "",
        "## Issue Type Counts",
        "",
        "| Issue type | Count | Status |",
        "|---|---:|---|",
    ]
    for issue_type, count in taxonomy["issue_type_counts"].items():
        status = taxonomy["issue_type_status"][issue_type]["status"]
        lines.append(f"| `{issue_type}` | {count} | `{status}` |")
    lines.extend(["", "## Severity Counts", "", "| Severity | Count |", "|---|---:|"])
    for severity, count in taxonomy["severity_counts"].items():
        lines.append(f"| `{severity}` | {count} |")
    lines.extend(
        ["", "## Issue Type x Severity", "", "| Issue type | Severity counts |", "|---|---|"]
    )
    for issue_type, counts in taxonomy["issue_type_by_severity"].items():
        rendered = ", ".join(f"{key}: {value}" for key, value in counts.items())
        lines.append(f"| `{issue_type}` | {rendered} |")
    lines.extend(
        ["", "## Issue Type x Subject", "", "| Issue type | Subject counts |", "|---|---|"]
    )
    for issue_type, counts in taxonomy["issue_type_by_subject"].items():
        rendered = ", ".join(f"{key}: {value}" for key, value in counts.items())
        lines.append(f"| `{issue_type}` | {rendered} |")
    lines.extend(["", "## Subject Counts", "", "| Subject | Count |", "|---|---:|"])
    for subject, count in taxonomy["subject_counts"].items():
        lines.append(f"| `{subject}` | {count} |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Evaluable means the issue type has at least the configured minimum positive count.",
            "- Sparse issue types can still have wide uncertainty even when technically evaluable.",
            "- Alignment remains structural (`subject_numeric_index`, confidence 0.85).",
        ]
    )
    return "\n".join(lines) + "\n"


def render_issue_validation_report(payload: dict[str, Any]) -> str:
    lines = [
        "# MMLU-Redux Issue-Specific Validation Metrics",
        "",
        "Preliminary, protocol-scoped metrics. No raw MMLU question text or answer choices are included.",
        "",
        f"- Status: `{payload['status']}`",
        f"- Restrict to Redux subjects: `{payload['filters']['restrict_to_ground_truth_subjects']}`",
        f"- Severity filters: {payload['filters']['severities'] or 'none'}",
        f"- Issue-type filters: {payload['filters'].get('issue_types') or 'none'}",
        f"- Diagnostic filters: {payload['filters'].get('diagnostics') or 'none'}",
        f"- Subject normalize: `{payload['filters'].get('subject_normalize', False)}`",
        f"- Min positive count: {payload['filters']['min_positive_count']}",
        "",
        "| Issue type | Diagnostic | Positives | AUROC | AUPRC | P@10 | P@25 | P@50 | R@10 | R@25 | R@50 | Enrich@10 | Enrich@25 | Enrich@50 | Status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for issue_type, diagnostics in payload["issue_type_metrics"].items():
        for diagnostic, row in diagnostics.items():
            precision_at = row.get("precision_at", {})
            recall_at = row.get("recall_at", {})
            enrichment_at = row.get("enrichment_at", {})
            lines.append(
                f"| `{issue_type}` | `{diagnostic}` | {row.get('positive_count', 0)} | "
                f"{_fmt(row.get('auroc'))} | {_fmt(row.get('auprc'))} | "
                f"{_fmt(precision_at.get('10'))} | {_fmt(precision_at.get('25'))} | "
                f"{_fmt(precision_at.get('50'))} | {_fmt(recall_at.get('10'))} | "
                f"{_fmt(recall_at.get('25'))} | {_fmt(recall_at.get('50'))} | "
                f"{_fmt(enrichment_at.get('10'))} | {_fmt(enrichment_at.get('25'))} | "
                f"{_fmt(enrichment_at.get('50'))} | `{row.get('status')}` |"
            )
    if payload.get("mapping_warnings"):
        lines.extend(["", "## Mapping Warnings", ""])
        lines.extend(f"- {warning}" for warning in payload["mapping_warnings"])
    lines.extend(
        [
            "",
            "Use cautious language: these metrics test logical issue-type mappings under structural alignment; they do not establish generic benchmark-error detection.",
        ]
    )
    return "\n".join(lines) + "\n"


def _metrics_for_issue_type(
    score_rows: list[dict[str, Any]],
    *,
    issue_type: str,
    diagnostic: str,
    positive_items: set[str],
    issue_meta_by_item_type: dict[tuple[str, str], list[ExternalIssue]],
    min_positive_count: int,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, Any]:
    rows = [
        row
        for row in score_rows
        if row["diagnostics"].get(diagnostic) is not None
        and np.isfinite(float(row["diagnostics"][diagnostic]))
    ]
    y_true = [row["item_id"] in positive_items for row in rows]
    scores = [float(row["diagnostics"][diagnostic]) for row in rows]
    positive_count = int(sum(y_true))
    negative_count = int(len(rows) - positive_count)
    precision_at, recall_at, enrichment_at, effective_k = _topk_metrics(y_true, scores, rows)
    status = "ok"
    warnings = []
    if positive_count == 0:
        status = "no_positives"
        warnings.append("No positives remain for this issue type after filters.")
    elif positive_count < min_positive_count:
        status = "underpowered"
        warnings.append(
            f"Positive count {positive_count} is below min_positive_count {min_positive_count}."
        )
    elif negative_count == 0:
        status = "degenerate_labels"
        warnings.append("No negatives remain for this issue type after filters.")
    return {
        "status": status,
        "issue_type": issue_type,
        "diagnostic": diagnostic,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "n": len(rows),
        "auroc": roc_auc(y_true, scores),
        "auprc": precision_recall_auc(y_true, scores),
        "precision_at": precision_at,
        "recall_at": recall_at,
        "enrichment_at": enrichment_at,
        "effective_k": effective_k,
        "bootstrap_ci": _bootstrap_ci(
            y_true,
            scores,
            bootstrap_samples=bootstrap_samples,
            seed=seed,
        ),
        "underpowered": positive_count < min_positive_count,
        "warnings": warnings,
        "top_rows": _top_rows(
            rows,
            diagnostic=diagnostic,
            issue_type=issue_type,
            positive_items=positive_items,
            issue_meta_by_item_type=issue_meta_by_item_type,
        ),
    }


def _topk_metrics(
    y_true: list[bool],
    scores: list[float],
    rows: list[dict[str, Any]],
) -> tuple[
    dict[str, float | None], dict[str, float | None], dict[str, float | None], dict[str, int]
]:
    order = sorted(
        range(len(rows)),
        key=lambda index: (-scores[index], rows[index]["subject"], rows[index]["item_id"]),
    )
    positives = sum(y_true)
    random_rate = positives / len(rows) if rows else 0.0
    precision_at: dict[str, float | None] = {}
    recall_at: dict[str, float | None] = {}
    enrichment_at: dict[str, float | None] = {}
    effective_k: dict[str, int] = {}
    for requested_k in DEFAULT_TOP_K:
        k = min(requested_k, len(rows))
        top = order[:k]
        hits = sum(1 for index in top if y_true[index])
        precision = hits / k if k else None
        recall = hits / positives if positives else None
        precision_at[str(requested_k)] = precision
        recall_at[str(requested_k)] = recall
        enrichment_at[str(requested_k)] = (
            precision / random_rate if precision is not None and random_rate else None
        )
        effective_k[str(requested_k)] = k
    return precision_at, recall_at, enrichment_at, effective_k


def _bootstrap_ci(
    y_true: list[bool],
    scores: list[float],
    *,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, Any]:
    if bootstrap_samples <= 0 or not y_true:
        return {}
    rng = np.random.default_rng(seed)
    indices = np.arange(len(y_true))
    auc_values = []
    auprc_values = []
    for _ in range(bootstrap_samples):
        sample = rng.choice(indices, size=len(indices), replace=True)
        labels = [y_true[int(index)] for index in sample]
        sample_scores = [scores[int(index)] for index in sample]
        auc = roc_auc(labels, sample_scores)
        auprc = precision_recall_auc(labels, sample_scores)
        if auc is not None:
            auc_values.append(auc)
        if auprc is not None:
            auprc_values.append(auprc)
    return {"auroc": _ci(auc_values), "auprc": _ci(auprc_values)}


def _ci(values: list[float]) -> dict[str, Any] | None:
    if not values:
        return None
    lower, upper = np.quantile(values, [0.025, 0.975])
    return {"lower": float(lower), "upper": float(upper), "n": len(values)}


def _top_rows(
    rows: list[dict[str, Any]],
    *,
    diagnostic: str,
    issue_type: str,
    positive_items: set[str],
    issue_meta_by_item_type: dict[tuple[str, str], list[ExternalIssue]],
    limit: int = 50,
) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda row: (-float(row["diagnostics"][diagnostic]), row["subject"], row["item_id"]),
    )
    top = []
    for rank, row in enumerate(ordered[:limit], start=1):
        item_id = row["item_id"]
        item_issues = issue_meta_by_item_type.get((issue_type, item_id), [])
        details = row.get("diagnostic_details", {}).get(diagnostic, {})
        top.append(
            {
                "issue_type_target": issue_type,
                "diagnostic": diagnostic,
                "rank": rank,
                "item_id": item_id,
                "subject": row["subject"],
                "score": float(row["diagnostics"][diagnostic]),
                "raw_score": details.get("raw_score"),
                "subject_mean": details.get("subject_mean"),
                "subject_std": details.get("subject_std"),
                "direction": details.get("direction", SCORE_DIRECTION),
                "has_issue": bool(item_id in positive_items),
                "issue_severities": sorted({issue.severity for issue in item_issues}),
            }
        )
    return top


def _load_prediction_stats(predictions_path: str | Path) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(predictions_path):
        item_id = str(row.get("item_id") or "")
        if not item_id:
            continue
        bucket = stats.setdefault(
            item_id,
            {
                "subject": str(row.get("subset") or "default"),
                "gold": _choice_letter(row.get("gold")),
                "option_counts": Counter(),
                "n": 0,
            },
        )
        bucket["n"] += 1
        prediction = _choice_letter(row.get("prediction"))
        if prediction:
            bucket["option_counts"][prediction] += 1
        gold = _choice_letter(row.get("gold"))
        if gold and not bucket.get("gold"):
            bucket["gold"] = gold
    return stats


def _write_matrix_outputs(destination: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "issue_type",
        "diagnostic",
        "status",
        "positive_count",
        "negative_count",
        "auroc",
        "auprc",
        "precision_at_10",
        "precision_at_25",
        "precision_at_50",
        "recall_at_10",
        "recall_at_25",
        "recall_at_50",
        "enrichment_at_10",
        "enrichment_at_25",
        "enrichment_at_50",
        "auroc_ci_lower",
        "auroc_ci_upper",
        "auprc_ci_lower",
        "auprc_ci_upper",
        "underpowered",
    ]
    with (destination / "diagnostic_by_issue_matrix.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    (destination / "diagnostic_by_issue_matrix.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _write_top_items(destination: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "issue_type_target",
        "diagnostic",
        "rank",
        "item_id",
        "subject",
        "score",
        "raw_score",
        "subject_mean",
        "subject_std",
        "direction",
        "has_issue",
        "issue_severities",
    ]
    with (destination / "top_items_sanitized.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            serialized["issue_severities"] = ";".join(row.get("issue_severities", []))
            writer.writerow(serialized)


def _write_subject_normalized_item_scores(destination: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "item_id",
        "subject",
        "diagnostic",
        "raw_score",
        "subject_mean",
        "subject_std",
        "score",
        "direction",
        "zero_variance_subject",
    ]
    csv_path = destination / "subject_normalized_item_scores.csv"
    jsonl_path = destination / "subject_normalized_item_scores.jsonl"
    with (
        csv_path.open("w", encoding="utf-8", newline="") as csv_handle,
        jsonl_path.open("w", encoding="utf-8") as jsonl_handle,
    ):
        writer = csv.DictWriter(csv_handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            for diagnostic in sorted(SUBJECT_NORMALIZED_DIAGNOSTICS):
                details = row.get("diagnostic_details", {}).get(diagnostic)
                if not details:
                    continue
                payload = {
                    "item_id": row["item_id"],
                    "subject": row["subject"],
                    "diagnostic": diagnostic,
                    "raw_score": details.get("raw_score"),
                    "subject_mean": details.get("subject_mean"),
                    "subject_std": details.get("subject_std"),
                    "score": details.get("score"),
                    "direction": details.get("direction", SCORE_DIRECTION),
                    "zero_variance_subject": details.get("zero_variance_subject", False),
                }
                writer.writerow(payload)
                jsonl_handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _write_raw_vs_subject_normalized_comparison(
    destination: Path,
    payload: dict[str, Any],
) -> None:
    issue_type = "label_error"
    comparisons = []
    issue_metrics = payload.get("issue_type_metrics", {}).get(issue_type, {})
    for diagnostic in [
        "correct_answer_rarely_selected",
        "high_disagreement",
        "option_selection_anomaly",
    ]:
        normalized = _subject_normalized_name(diagnostic)
        raw_metrics = issue_metrics.get(diagnostic)
        normalized_metrics = issue_metrics.get(normalized)
        comparisons.append(
            {
                "issue_type": issue_type,
                "raw_diagnostic": diagnostic,
                "normalized_diagnostic": normalized,
                "raw": _metric_summary(raw_metrics),
                "subject_normalized": _metric_summary(normalized_metrics),
                "interpretation": _comparison_interpretation(raw_metrics, normalized_metrics),
            }
        )
    comparison_payload = {
        "schema_version": "0.1",
        "status": "ok",
        "note": "Preliminary raw-vs-subject-normalized comparison under structural alignment.",
        "comparisons": comparisons,
    }
    (destination / "raw_vs_subject_normalized_comparison.json").write_text(
        json.dumps(comparison_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "raw_vs_subject_normalized_comparison.md").write_text(
        _render_raw_vs_subject_normalized_comparison(comparison_payload),
        encoding="utf-8",
    )


def _metric_summary(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {"status": "missing"}
    precision_at = row.get("precision_at", {})
    recall_at = row.get("recall_at", {})
    enrichment_at = row.get("enrichment_at", {})
    return {
        "status": row.get("status"),
        "positive_count": row.get("positive_count"),
        "negative_count": row.get("negative_count"),
        "auroc": row.get("auroc"),
        "auprc": row.get("auprc"),
        "precision_at_10": precision_at.get("10"),
        "precision_at_25": precision_at.get("25"),
        "precision_at_50": precision_at.get("50"),
        "recall_at_10": recall_at.get("10"),
        "recall_at_25": recall_at.get("25"),
        "recall_at_50": recall_at.get("50"),
        "enrichment_at_10": enrichment_at.get("10"),
        "enrichment_at_25": enrichment_at.get("25"),
        "enrichment_at_50": enrichment_at.get("50"),
    }


def _comparison_interpretation(
    raw_metrics: dict[str, Any] | None,
    normalized_metrics: dict[str, Any] | None,
) -> str:
    if not raw_metrics or not normalized_metrics:
        return "missing_metrics"
    raw_auc = raw_metrics.get("auroc")
    norm_auc = normalized_metrics.get("auroc")
    raw_pr = raw_metrics.get("auprc")
    norm_pr = normalized_metrics.get("auprc")
    if raw_auc is None or norm_auc is None:
        return "not_comparable"
    if norm_auc > raw_auc + 0.01 and (raw_pr is None or norm_pr is None or norm_pr >= raw_pr):
        return "preliminary_improvement_after_subject_normalization"
    if norm_auc < raw_auc - 0.01 or (
        raw_pr is not None and norm_pr is not None and norm_pr < raw_pr * 0.8
    ):
        return "weakened_after_subject_normalization"
    return "similar_after_subject_normalization"


def _render_raw_vs_subject_normalized_comparison(payload: dict[str, Any]) -> str:
    lines = [
        "# Raw vs Subject-Normalized Comparison",
        "",
        "Preliminary, protocol-scoped comparison. No raw MMLU question text or answer choices are included.",
        "",
        "| Raw diagnostic | Subject-normalized diagnostic | Raw AUROC | Norm AUROC | Raw AUPRC | Norm AUPRC | Raw P@10 | Norm P@10 | Interpretation |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["comparisons"]:
        raw = row["raw"]
        normalized = row["subject_normalized"]
        lines.append(
            f"| `{row['raw_diagnostic']}` | `{row['normalized_diagnostic']}` | "
            f"{_fmt(raw.get('auroc'))} | {_fmt(normalized.get('auroc'))} | "
            f"{_fmt(raw.get('auprc'))} | {_fmt(normalized.get('auprc'))} | "
            f"{_fmt(raw.get('precision_at_10'))} | "
            f"{_fmt(normalized.get('precision_at_10'))} | "
            f"`{row['interpretation']}` |"
        )
    lines.extend(
        [
            "",
            "Interpretation is descriptive only. Improvements, weakenings, or stability remain preliminary under structural alignment confidence 0.85.",
        ]
    )
    return "\n".join(lines) + "\n"


def _subject_matched_null_payload(
    *,
    score_rows: list[dict[str, Any]],
    metrics: dict[str, dict[str, Any]],
    issue_items_by_type: dict[str, set[str]],
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    subject_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    item_subject = {}
    for row in score_rows:
        subject_rows[row["subject"]].append(row)
        item_subject[row["item_id"]] = row["subject"]

    output: dict[str, dict[str, Any]] = {}
    for issue_type, diagnostics in metrics.items():
        positive_items = issue_items_by_type.get(issue_type, set())
        positive_counts_by_subject = Counter(
            item_subject[item_id] for item_id in positive_items if item_id in item_subject
        )
        output[issue_type] = {}
        for diagnostic, metric in diagnostics.items():
            if metric.get("status") != "ok" or metric.get("positive_count", 0) <= 0:
                continue
            ranked_rows = [
                row
                for row in score_rows
                if row["diagnostics"].get(diagnostic) is not None
                and np.isfinite(float(row["diagnostics"][diagnostic]))
            ]
            ranked_rows = sorted(
                ranked_rows,
                key=lambda row: (
                    -float(row["diagnostics"][diagnostic]),
                    row["subject"],
                    row["item_id"],
                ),
            )
            simulated = {str(k): [] for k in DEFAULT_TOP_K}
            for _ in range(iterations):
                sampled = _sample_subject_matched_items(
                    subject_rows=subject_rows,
                    positive_items=positive_items,
                    positive_counts_by_subject=positive_counts_by_subject,
                    rng=rng,
                )
                for k in DEFAULT_TOP_K:
                    top = ranked_rows[: min(k, len(ranked_rows))]
                    precision = (
                        sum(1 for row in top if row["item_id"] in sampled) / len(top)
                        if top
                        else None
                    )
                    if precision is not None:
                        simulated[str(k)].append(precision)
            precision_at = metric.get("precision_at", {})
            output[issue_type][diagnostic] = {
                "iterations": iterations,
                "positive_count": metric.get("positive_count"),
                "precision_at": {
                    str(k): _null_summary(
                        values=simulated[str(k)],
                        observed=precision_at.get(str(k)),
                    )
                    for k in DEFAULT_TOP_K
                },
            }
    return {
        "schema_version": "0.1",
        "status": "ok",
        "iterations": iterations,
        "note": "Subject-matched random baseline; positives are resampled within each subject count profile.",
        "issue_type_diagnostics": output,
    }


def _sample_subject_matched_items(
    *,
    subject_rows: dict[str, list[dict[str, Any]]],
    positive_items: set[str],
    positive_counts_by_subject: Counter[str],
    rng: np.random.Generator,
) -> set[str]:
    sampled = set()
    for subject, count in positive_counts_by_subject.items():
        candidates = [
            row["item_id"]
            for row in subject_rows.get(subject, [])
            if row["item_id"] not in positive_items
        ]
        if not candidates or count <= 0:
            continue
        replace = len(candidates) < count
        draw = rng.choice(candidates, size=count, replace=replace)
        sampled.update(str(item_id) for item_id in np.atleast_1d(draw))
    return sampled


def _null_summary(values: list[float], observed: float | None) -> dict[str, Any]:
    if not values:
        return {
            "observed": observed,
            "null_mean": None,
            "null_ci_lower": None,
            "null_ci_upper": None,
            "observed_over_null_mean": None,
        }
    lower, upper = np.quantile(values, [0.025, 0.975])
    mean = float(np.mean(values))
    return {
        "observed": observed,
        "null_mean": mean,
        "null_ci_lower": float(lower),
        "null_ci_upper": float(upper),
        "observed_over_null_mean": (observed / mean if observed is not None and mean else None),
    }


def _write_subject_matched_null(destination: Path, payload: dict[str, Any]) -> None:
    (destination / "subject_matched_null.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "subject_matched_null.md").write_text(
        _render_subject_matched_null(payload),
        encoding="utf-8",
    )


def _render_subject_matched_null(payload: dict[str, Any]) -> str:
    lines = [
        "# Subject-Matched Null Baseline",
        "",
        "Preliminary, protocol-scoped null baseline. No raw MMLU question text or answer choices are included.",
        "",
        f"- Iterations: {payload['iterations']}",
        "",
        "| Issue type | Diagnostic | K | Observed P@K | Null mean P@K | Null 95% CI | Observed / null mean |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for issue_type, diagnostics in payload["issue_type_diagnostics"].items():
        for diagnostic, row in diagnostics.items():
            for k, summary in row["precision_at"].items():
                ci = (
                    "n/a"
                    if summary["null_ci_lower"] is None
                    else f"[{summary['null_ci_lower']:.3f}, {summary['null_ci_upper']:.3f}]"
                )
                lines.append(
                    f"| `{issue_type}` | `{diagnostic}` | {k} | "
                    f"{_fmt(summary['observed'])} | {_fmt(summary['null_mean'])} | "
                    f"{ci} | {_fmt(summary['observed_over_null_mean'])} |"
                )
    lines.extend(
        [
            "",
            "This null preserves the per-subject count of positives for each issue type and resamples non-issue items within the same subjects.",
        ]
    )
    return "\n".join(lines) + "\n"


def _matrix_row(issue_type: str, diagnostic: str, row: dict[str, Any]) -> dict[str, Any]:
    precision_at = row.get("precision_at", {})
    recall_at = row.get("recall_at", {})
    enrichment_at = row.get("enrichment_at", {})
    ci = row.get("bootstrap_ci", {})
    auroc_ci = ci.get("auroc") or {}
    auprc_ci = ci.get("auprc") or {}
    return {
        "issue_type": issue_type,
        "diagnostic": diagnostic,
        "status": row.get("status"),
        "positive_count": row.get("positive_count"),
        "negative_count": row.get("negative_count"),
        "auroc": row.get("auroc"),
        "auprc": row.get("auprc"),
        "precision_at_10": precision_at.get("10"),
        "precision_at_25": precision_at.get("25"),
        "precision_at_50": precision_at.get("50"),
        "recall_at_10": recall_at.get("10"),
        "recall_at_25": recall_at.get("25"),
        "recall_at_50": recall_at.get("50"),
        "enrichment_at_10": enrichment_at.get("10"),
        "enrichment_at_25": enrichment_at.get("25"),
        "enrichment_at_50": enrichment_at.get("50"),
        "auroc_ci_lower": auroc_ci.get("lower"),
        "auroc_ci_upper": auroc_ci.get("upper"),
        "auprc_ci_lower": auprc_ci.get("lower"),
        "auprc_ci_upper": auprc_ci.get("upper"),
        "underpowered": row.get("underpowered"),
    }


def _blocked_metric(
    *,
    issue_type: str,
    diagnostic: str,
    reason: str,
    positives: int,
    min_positive_count: int,
) -> dict[str, Any]:
    return {
        "status": "blocked",
        "issue_type": issue_type,
        "diagnostic": diagnostic,
        "positive_count": positives,
        "negative_count": None,
        "n": 0,
        "auroc": None,
        "auprc": None,
        "precision_at": {},
        "recall_at": {},
        "enrichment_at": {},
        "bootstrap_ci": {},
        "underpowered": positives < min_positive_count,
        "warnings": [reason],
    }


def _filter_issues(
    issues: list[ExternalIssue],
    *,
    severities: list[str] | None,
    issue_types: list[str] | None,
) -> list[ExternalIssue]:
    severity_set = set(severities or [])
    issue_type_set = set(issue_types or [])
    return [
        issue
        for issue in issues
        if (not severity_set or issue.severity in severity_set)
        and (not issue_type_set or issue.issue_type in issue_type_set)
    ]


def _sanitize_issue_record(row: dict[str, Any]) -> dict[str, str]:
    return {
        "issue_type": _value(row, "issue_type"),
        "severity": _value(row, "severity", default="unknown"),
        "subject": _value(row, "subset") or _value(row, "subject") or "default",
        "item_id": _value(row, "item_id"),
    }


def _value(row: dict[str, Any], key: str, *, default: str = "") -> str:
    value = row.get(key, default)
    return str(value if value is not None else default)


def _split_item_key(item_key: str) -> tuple[str, str]:
    if "::" in item_key:
        subject, item_id = item_key.split("::", 1)
        return subject, item_id
    return "default", item_key


def _choice_letter(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text if text in {"A", "B", "C", "D"} else None


def _normalized_entropy(fractions: list[float]) -> float:
    total = sum(fractions)
    if total <= 0:
        return 0.0
    entropy = -sum(frac * math.log(frac) for frac in fractions if frac > 0)
    return float(entropy / math.log(len(fractions))) if len(fractions) > 1 else 0.0


def _option_selection_anomaly(
    *,
    entropy: float | None,
    gold_fraction: float | None,
) -> float | None:
    if entropy is None or gold_fraction is None:
        return None
    return _clip01(0.5 * float(entropy) + 0.5 * (1.0 - float(gold_fraction)))


def _bimodal_choice_score(
    option_fractions: dict[str, float],
    *,
    gold: str,
    valid_option_n: int,
) -> float | None:
    if valid_option_n <= 0 or gold not in {"A", "B", "C", "D"}:
        return None
    distractors = sorted(
        [fraction for option, fraction in option_fractions.items() if option != gold],
        reverse=True,
    )
    if len(distractors) < 2:
        return 0.0
    return _clip01(2.0 * math.sqrt(distractors[0] * distractors[1]))


def _low_discrimination_score(discrimination: float | None) -> float | None:
    if discrimination is None:
        return None
    return _clip01(1.0 - min(abs(discrimination) / 0.05, 1.0))


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if np.isfinite(numeric) else None


def _none_if_none(value: float | None) -> float | None:
    return None if value is None else _clip01(float(value))


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int | float):
        return f"{float(value):.3f}"
    return str(value)
