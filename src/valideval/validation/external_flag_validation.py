from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import Field

from valideval.io.jsonl import read_jsonl, write_jsonl
from valideval.schemas import JsonModel
from valideval.validation.detector_metrics import precision_recall_auc, roc_auc
from valideval.validation.external_ground_truth import ExternalIssue, load_ground_truth


class DiagnosticFlag(JsonModel):
    schema_version: str = "0.1"
    benchmark: str
    subset: str = "default"
    item_id: str
    diagnostic: str
    score: float
    severity: str = "unknown"
    direction: str = "higher_is_more_suspicious"
    source: str = "diagnostic_result"
    evidence: dict[str, Any] = Field(default_factory=dict)
    evidence_summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


def export_flags_from_results(
    results_dir: str | Path | None,
    output_path: str | Path,
    *,
    benchmark: str,
    matrix_path: str | Path | None = None,
    irt_dir: str | Path | None = None,
) -> dict[str, Any]:
    if irt_dir is not None:
        return export_flags_from_irt(
            irt_dir,
            output_path,
            benchmark=benchmark,
            matrix_path=matrix_path,
        )
    if results_dir is None:
        raise ValueError("export_flags_from_results requires either results_dir or irt_dir.")
    source = Path(results_dir)
    destination = Path(output_path)
    flags: list[DiagnosticFlag] = []
    warnings: list[str] = []
    if not source.exists():
        warnings.append(f"Results directory does not exist: {source}")
    else:
        for path in sorted(source.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            diagnostic = payload.get("diagnostic_name") or path.stem
            per_item = payload.get("per_item_metrics") or {}
            for item_id, metrics in per_item.items():
                score, evidence = _extract_score(metrics)
                flags.append(
                    DiagnosticFlag(
                        benchmark=benchmark,
                        subset=str(metrics.get("subset", "default"))
                        if isinstance(metrics, dict)
                        else "default",
                        item_id=str(item_id),
                        diagnostic=str(diagnostic),
                        score=float(score),
                        severity=_severity(score),
                        evidence_summary=evidence,
                        evidence={"summary": evidence, "sanitized": True},
                        metadata={"source_result": str(path)},
                    )
                )
    write_jsonl(destination, flags)
    summary = {
        "schema_version": "0.1",
        "status": "ok" if flags else "empty",
        "results_dir": str(source),
        "output_path": str(destination),
        "flag_count": len(flags),
        "diagnostics": sorted({flag.diagnostic for flag in flags}),
        "item_count": len({flag.item_id for flag in flags}),
        "warnings": warnings,
    }
    destination.with_suffix(destination.suffix + ".summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def export_flags_from_irt(
    irt_dir: str | Path,
    output_path: str | Path,
    *,
    benchmark: str,
    matrix_path: str | Path | None = None,
) -> dict[str, Any]:
    source = Path(irt_dir)
    destination = Path(output_path)
    parameters_path = source / "item_parameters.csv"
    warnings: list[str] = []
    if not parameters_path.exists():
        raise FileNotFoundError(f"IRT item parameters not found: {parameters_path}")

    rows = _read_csv_dicts(parameters_path)
    flags: list[DiagnosticFlag] = []
    group_flags: dict[str, list[DiagnosticFlag]] = {
        "negative_discrimination": [],
        "low_discrimination": [],
        "extreme_difficulty": [],
        "combined_flags": [],
    }
    thresholds = {
        "negative_discrimination": "discrimination_proxy < -0.05",
        "low_discrimination": "abs(discrimination_proxy) < 0.05",
        "extreme_difficulty": "proportion_correct <= 0.05 or >= 0.95",
    }

    for row in rows:
        original_item_key = str(row.get("item_id") or "")
        subset, item_id = _split_item_key(original_item_key)
        discrimination = _float_or_none(row.get("discrimination_proxy"))
        difficulty = _float_or_none(row.get("difficulty_proxy"))
        proportion_correct = _float_or_none(row.get("proportion_correct"))
        if proportion_correct is None and difficulty is not None:
            proportion_correct = 1.0 / (1.0 + float(np.exp(difficulty)))

        item_components: list[DiagnosticFlag] = []
        common_metadata = {
            "original_item_key": original_item_key,
            "source_irt_dir": str(source),
            "matrix_path": str(matrix_path) if matrix_path is not None else None,
            "difficulty_proxy": difficulty,
            "discrimination_proxy": discrimination,
            "proportion_correct": proportion_correct,
            "thresholds": thresholds,
        }
        if discrimination is not None and discrimination < -0.05:
            item_components.append(
                _irt_flag(
                    benchmark=benchmark,
                    subset=subset,
                    item_id=item_id,
                    diagnostic="negative_discrimination",
                    score=max(0.0, min(1.0, -discrimination)),
                    metadata=common_metadata,
                )
            )
        if discrimination is not None and abs(discrimination) < 0.05:
            item_components.append(
                _irt_flag(
                    benchmark=benchmark,
                    subset=subset,
                    item_id=item_id,
                    diagnostic="low_discrimination",
                    score=max(0.0, 1.0 - min(abs(discrimination) / 0.05, 1.0)),
                    metadata=common_metadata,
                )
            )
        if proportion_correct is not None and (
            proportion_correct <= 0.05 or proportion_correct >= 0.95
        ):
            item_components.append(
                _irt_flag(
                    benchmark=benchmark,
                    subset=subset,
                    item_id=item_id,
                    diagnostic="extreme_difficulty",
                    score=max(proportion_correct, 1.0 - proportion_correct),
                    metadata=common_metadata,
                )
            )
        if item_components:
            combined_score = max(flag.score for flag in item_components)
            item_components.append(
                _irt_flag(
                    benchmark=benchmark,
                    subset=subset,
                    item_id=item_id,
                    diagnostic="combined_flags",
                    score=combined_score,
                    metadata={
                        **common_metadata,
                        "component_diagnostics": [flag.diagnostic for flag in item_components],
                    },
                )
            )
        for flag in item_components:
            flags.append(flag)
            group_flags[flag.diagnostic].append(flag)

    write_jsonl(destination, flags)
    separate_files = {}
    for diagnostic, diagnostic_flags in group_flags.items():
        suffix = "combined" if diagnostic == "combined_flags" else diagnostic
        path = destination.parent / f"{destination.stem}_{suffix}{destination.suffix}"
        write_jsonl(path, diagnostic_flags)
        separate_files[diagnostic] = str(path)

    summary = {
        "schema_version": "0.1",
        "status": "ok" if flags else "empty",
        "source_irt_dir": str(source),
        "matrix_path": str(matrix_path) if matrix_path is not None else None,
        "output_path": str(destination),
        "flag_count": len(flags),
        "diagnostics": sorted({flag.diagnostic for flag in flags}),
        "group_counts": {
            diagnostic: len(diagnostic_flags)
            for diagnostic, diagnostic_flags in sorted(group_flags.items())
        },
        "item_count": len({flag.item_id for flag in flags}),
        "separate_files": separate_files,
        "warnings": [
            *warnings,
            "Proxy IRT flags are preliminary diagnostic review aids, not full psychometric IRT findings.",
            "No raw item text is exported.",
        ],
    }
    destination.with_suffix(destination.suffix + ".summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def validate_flags_against_ground_truth(
    flags_path: str | Path,
    ground_truth_path: str | Path,
    output_dir: str | Path,
    *,
    benchmark: str,
    top_k: int | None = None,
    bootstrap_samples: int = 200,
    seed: int = 0,
    group_by: str = "diagnostic",
    restrict_to_ground_truth_subjects: bool = False,
    issue_types: list[str] | None = None,
    severities: list[str] | None = None,
) -> dict[str, Any]:
    flags = [DiagnosticFlag(**record) for record in read_jsonl(flags_path)]
    issues = _filter_issues(
        load_ground_truth(ground_truth_path),
        issue_types=issue_types,
        severities=severities,
    )
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    ground_truth_subjects = sorted({issue.subset for issue in issues if issue.subset})
    if restrict_to_ground_truth_subjects:
        allowed_subjects = set(ground_truth_subjects)
        flags = [
            flag
            for flag in flags
            if (
                flag.subset in allowed_subjects
                or _split_item_key(flag.item_id)[0] in allowed_subjects
            )
        ]

    issue_by_item: dict[str, list[ExternalIssue]] = defaultdict(list)
    for issue in issues:
        issue_by_item[issue.item_id].append(issue)

    joined: list[dict[str, Any]] = []
    for flag in flags:
        item_issues = issue_by_item.get(flag.item_id, [])
        joined.append(
            {
                **flag.model_dump(mode="json"),
                "has_external_issue": bool(item_issues),
                "external_issue_types": sorted({issue.issue_type for issue in item_issues}),
                "external_issue_severities": sorted({issue.severity for issue in item_issues}),
                "external_source_issue_ids": sorted(
                    {
                        str(issue.metadata.get("source_issue_id") or "")
                        for issue in item_issues
                        if issue.metadata.get("source_issue_id")
                    }
                ),
            }
        )
    write_jsonl(destination / "joined.jsonl", joined)
    _write_top_flagged_artifacts(destination, joined)

    metrics_by_diagnostic = {}
    group_key = "diagnostic" if group_by == "diagnostic" else group_by
    for diagnostic in sorted({str(row.get(group_key, "all")) for row in joined}):
        rows = [row for row in joined if str(row.get(group_key, "all")) == diagnostic]
        metrics_by_diagnostic[diagnostic] = _metrics_for_rows(
            rows,
            top_k=top_k,
            bootstrap_samples=bootstrap_samples,
            seed=seed,
        )

    issue_type_counts = _count_values(issue.issue_type for issue in issues)
    severity_counts = _count_values(issue.severity for issue in issues)
    metrics = {
        "schema_version": "0.1",
        "benchmark": benchmark,
        "status": "ok" if flags and issues else "insufficient_data",
        "flag_count": len(flags),
        "ground_truth_issue_count": len(issues),
        "ground_truth_item_count": len(issue_by_item),
        "ground_truth_subject_count": len(ground_truth_subjects),
        "ground_truth_subjects": ground_truth_subjects,
        "ground_truth_issue_types": issue_type_counts,
        "ground_truth_severities": severity_counts,
        "filters": {
            "restrict_to_ground_truth_subjects": restrict_to_ground_truth_subjects,
            "issue_types": issue_types or [],
            "severities": severities or [],
            "group_by": group_by,
        },
        "diagnostics": metrics_by_diagnostic,
        "warnings": [
            "External validation estimates association with available issue labels; it is not a global benchmark-validity conclusion."
        ],
    }
    (destination / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "summary.md").write_text(
        render_external_validation_summary(metrics), encoding="utf-8"
    )
    return metrics


def render_external_validation_summary(metrics: dict[str, Any]) -> str:
    lines = [
        "# External Diagnostic Validation Summary",
        "",
        f"- Benchmark: `{metrics['benchmark']}`",
        f"- Status: `{metrics['status']}`",
        f"- Flags: {metrics['flag_count']}",
        f"- Ground-truth issue items: {metrics['ground_truth_item_count']}",
        f"- Ground-truth subjects: {metrics.get('ground_truth_subject_count', 0)}",
        "",
        "| Diagnostic | AUROC | AUPRC | P@10 | P@25 | P@50 | R@10 | R@25 | R@50 | Enrich@10 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for diagnostic, row in metrics["diagnostics"].items():
        precision_at = row.get("precision_at", {})
        recall_at = row.get("recall_at", {})
        enrichment_at = row.get("enrichment_at", {})
        lines.append(
            f"| {diagnostic} | {_fmt(row.get('auroc'))} | {_fmt(row.get('auprc'))} | "
            f"{_fmt(precision_at.get('10'))} | {_fmt(precision_at.get('25'))} | "
            f"{_fmt(precision_at.get('50'))} | {_fmt(recall_at.get('10'))} | "
            f"{_fmt(recall_at.get('25'))} | {_fmt(recall_at.get('50'))} | "
            f"{_fmt(enrichment_at.get('10'))} |"
        )
    lines.extend(
        [
            "",
            "Use cautious paper language: evidence consistent with external issue labels under this protocol.",
        ]
    )
    return "\n".join(lines) + "\n"


def _extract_score(metrics: Any) -> tuple[float, str]:
    if not isinstance(metrics, dict):
        return 0.0, "No per-item metric dictionary available."
    priority_keys = [
        "score",
        "risk_score",
        "shortcut_score",
        "dead_distractor_fraction",
        "discrimination",
        "extractor_disagreement_rate",
        "invalid_output_rate",
        "mean_item_stability",
    ]
    for key in priority_keys:
        value = metrics.get(key)
        if isinstance(value, int | float):
            score = float(value)
            if key == "discrimination":
                score = max(0.0, 1.0 - abs(score))
            if key == "mean_item_stability":
                score = max(0.0, 1.0 - score)
            return score, f"Derived from `{key}`."
    numeric = [float(value) for value in metrics.values() if isinstance(value, int | float)]
    if numeric:
        return float(max(numeric)), "Derived from maximum numeric per-item metric."
    return 0.0, "No numeric per-item metric available."


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(numeric):
        return None
    return numeric


def _split_item_key(item_key: str) -> tuple[str, str]:
    if "::" in item_key:
        subset, item_id = item_key.split("::", 1)
        return subset, item_id
    return "default", item_key


def _irt_flag(
    *,
    benchmark: str,
    subset: str,
    item_id: str,
    diagnostic: str,
    score: float,
    metadata: dict[str, Any],
) -> DiagnosticFlag:
    summary = "Sanitized proxy-IRT item statistic; no item text exported."
    return DiagnosticFlag(
        benchmark=benchmark,
        subset=subset,
        item_id=item_id,
        diagnostic=diagnostic,
        score=float(score),
        severity="review",
        direction="higher_is_more_suspicious",
        source="proxy_irt",
        evidence={"summary": summary, "sanitized": True},
        evidence_summary=summary,
        metadata=metadata,
    )


def _filter_issues(
    issues: list[ExternalIssue],
    *,
    issue_types: list[str] | None,
    severities: list[str] | None,
) -> list[ExternalIssue]:
    issue_type_set = set(issue_types or [])
    severity_set = set(severities or [])
    return [
        issue
        for issue in issues
        if (not issue_type_set or issue.issue_type in issue_type_set)
        and (not severity_set or issue.severity in severity_set)
    ]


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        counts[str(value)] += 1
    return {key: counts[key] for key in sorted(counts)}


def _write_top_flagged_artifacts(
    destination: Path,
    joined: list[dict[str, Any]],
    *,
    limit: int = 100,
) -> None:
    rows = sorted(
        joined,
        key=lambda row: (
            -float(row.get("score", 0.0)),
            str(row.get("diagnostic", "")),
            str(row.get("item_id", "")),
        ),
    )[:limit]
    csv_path = destination / "top_flagged_items_sanitized.csv"
    md_path = destination / "top_flagged_items_sanitized.md"
    columns = [
        "rank",
        "item_id",
        "subject",
        "diagnostic",
        "score",
        "redux_issue_exists",
        "issue_type",
        "severity",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow(_top_row(rank, row))
    lines = [
        "# Top Flagged Items (Sanitized)",
        "",
        "| Rank | Item ID | Subject | Diagnostic | Score | Redux issue | Issue type | Severity |",
        "|---:|---|---|---|---:|---|---|---|",
    ]
    for rank, row in enumerate(rows[:50], start=1):
        rendered = _top_row(rank, row)
        lines.append(
            f"| {rendered['rank']} | `{rendered['item_id']}` | `{rendered['subject']}` | "
            f"`{rendered['diagnostic']}` | {float(rendered['score']):.3f} | "
            f"{rendered['redux_issue_exists']} | {rendered['issue_type']} | "
            f"{rendered['severity']} |"
        )
    lines.extend(["", "No raw MMLU question text or answer text is included."])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _top_row(rank: int, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": rank,
        "item_id": str(row.get("item_id", "")),
        "subject": str(row.get("subset", "")),
        "diagnostic": str(row.get("diagnostic", "")),
        "score": float(row.get("score", 0.0)),
        "redux_issue_exists": "yes" if row.get("has_external_issue") else "no",
        "issue_type": ";".join(row.get("external_issue_types") or []),
        "severity": ";".join(row.get("external_issue_severities") or []),
    }


def _severity(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def _metrics_for_rows(
    rows: list[dict[str, Any]],
    *,
    top_k: int | None,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, Any]:
    if not rows:
        return {"status": "empty"}
    y_true = [bool(row["has_external_issue"]) for row in rows]
    scores = [float(row["score"]) for row in rows]
    requested_k_values = sorted({10, 25, 50, top_k or 10})
    order = sorted(
        range(len(rows)),
        key=lambda index: (
            -scores[index],
            str(rows[index].get("diagnostic", "")),
            str(rows[index].get("item_id", "")),
        ),
    )
    positives = sum(y_true)
    random_rate = positives / len(rows) if rows else 0.0
    precision_at: dict[str, float | None] = {}
    recall_at: dict[str, float | None] = {}
    enrichment_at: dict[str, float | None] = {}
    effective_k: dict[str, int] = {}
    for requested_k in requested_k_values:
        k = min(int(requested_k), len(rows))
        top = order[:k]
        top_hits = sum(1 for index in top if y_true[index])
        precision = top_hits / k if k else None
        recall_value = top_hits / positives if positives else None
        precision_at[str(requested_k)] = precision
        recall_at[str(requested_k)] = recall_value
        enrichment_at[str(requested_k)] = (
            precision / random_rate if precision is not None and random_rate else None
        )
        effective_k[str(requested_k)] = k
    legacy_k = top_k or min(10, len(rows))
    precision_at_k = precision_at.get(str(legacy_k))
    recall_at_k = recall_at.get(str(legacy_k))
    enrichment = (
        (precision_at_k / random_rate) if precision_at_k is not None and random_rate else None
    )
    return {
        "status": "ok" if positives and positives < len(rows) else "degenerate_labels",
        "n": len(rows),
        "positives": positives,
        "top_k": legacy_k,
        "effective_top_k": effective_k.get(str(legacy_k), legacy_k),
        "auroc": roc_auc(y_true, scores),
        "auprc": precision_recall_auc(y_true, scores),
        "precision_at": precision_at,
        "recall_at": recall_at,
        "enrichment_at": enrichment_at,
        "effective_k": effective_k,
        "precision_at_k": precision_at_k,
        "recall_at_k": recall_at_k,
        "enrichment_over_random": enrichment,
        "bootstrap_ci": _bootstrap_metric_ci(
            y_true, scores, bootstrap_samples=bootstrap_samples, seed=seed
        ),
    }


def _bootstrap_metric_ci(
    y_true: list[bool],
    scores: list[float],
    *,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, Any]:
    if bootstrap_samples <= 0 or not y_true:
        return {}
    rng = np.random.default_rng(seed)
    auroc_values = []
    auprc_values = []
    indices = np.arange(len(y_true))
    for _ in range(bootstrap_samples):
        sample = rng.choice(indices, size=len(indices), replace=True)
        labels = [y_true[int(index)] for index in sample]
        sample_scores = [scores[int(index)] for index in sample]
        auc_value = roc_auc(labels, sample_scores)
        if auc_value is not None:
            auroc_values.append(auc_value)
        value = precision_recall_auc(labels, sample_scores)
        if value is not None:
            auprc_values.append(value)
    return {
        "auroc": _ci(auroc_values),
        "auprc": _ci(auprc_values),
    }


def _ci(values: list[float]) -> dict[str, Any] | None:
    if not values:
        return None
    lower, upper = np.quantile(values, [0.025, 0.975])
    return {"lower": float(lower), "upper": float(upper), "n": len(values)}


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int | float):
        return f"{float(value):.3f}"
    return str(value)
