from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TRUSTED_STATUSES = {"credible_under_synthetic_harness"}
PROTOTYPE_STATUSES = {"prototype_only", "uncalibrated"}
QUARANTINE_STATUSES = {"quarantine"}


def write_experiment_report(result: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    stem = f"{result['diagnostic']}_{result['flaw_type']}"
    json_path = root / f"{stem}.json"
    md_path = root / f"{stem}.md"
    json_path.write_text(json.dumps(_json_safe(result), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_experiment_markdown(result), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def write_summary_report(results: list[dict[str, Any]], output_dir: str | Path) -> dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary = summarize_results(results)
    json_path = root / "diagnostic_validation_summary.json"
    md_path = root / "diagnostic_validation_summary.md"
    json_path.write_text(
        json.dumps(_json_safe(summary), indent=2, sort_keys=True), encoding="utf-8"
    )
    md_path.write_text(_render_summary_markdown(summary), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def summarize_report_directory(report_dir: str | Path = "validation_reports") -> dict[str, Any]:
    root = Path(report_dir)
    results = []
    for path in sorted(root.glob("*.json")):
        if path.name == "diagnostic_validation_summary.json":
            continue
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and "diagnostic" in payload and "flaw_type" in payload:
            results.append(payload)
    return summarize_results(results)


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    validated = [
        _result_key(result)
        for result in results
        if result.get("credibility_status") in TRUSTED_STATUSES
    ]
    prototype = [
        _result_key(result)
        for result in results
        if result.get("credibility_status") in PROTOTYPE_STATUSES
    ]
    quarantined = [
        _result_key(result)
        for result in results
        if result.get("credibility_status") in QUARANTINE_STATUSES
    ]
    return {
        "schema_version": "0.1",
        "report_type": "synthetic_diagnostic_validation_summary",
        "real_benchmark_claims": False,
        "executive_summary": (
            "This report validates ValidEval diagnostics only on controlled synthetic "
            "benchmarks with known injected flaws. It does not make claims about any "
            "real benchmark."
        ),
        "diagnostics_validated": validated,
        "diagnostics_prototype_only": prototype,
        "diagnostics_to_quarantine": quarantined,
        "n_experiments": len(results),
        "experiments": results,
        "limitations": [
            "Synthetic detector validation estimates sensitivity and false-positive behavior under the implemented generators only.",
            "Passing this harness is not evidence that a real benchmark has or lacks the corresponding validity threat.",
            "Diagnostics with unavailable p-values use empirical null thresholds rather than parametric significance tests.",
        ],
        "recommended_next_validation_experiments": [
            "Add generator variants that differ from the diagnostic implementation assumptions.",
            "Add held-out synthetic templates to test detector generalization.",
            "Compare synthetic detector thresholds against a small human-reviewed real-benchmark sample before making strong claims.",
        ],
    }


def _render_experiment_markdown(result: dict[str, Any]) -> str:
    metrics = result.get("metrics", {})
    paths = result.get("artifacts", {})
    lines = [
        f"# Diagnostic Validation: {result.get('diagnostic')} on {result.get('flaw_type')}",
        "",
        "This is a controlled synthetic detector-validation experiment. It is not a real benchmark audit.",
        "",
        "## Executive Summary",
        "",
        f"- Credibility status: {result.get('credibility_status')}",
        f"- Diagnostic: {result.get('diagnostic')}",
        f"- Synthetic flaw: {result.get('flaw_type')}",
        f"- Items per run: {result.get('n_items')}",
        f"- Seeds: {result.get('n_seeds')}",
        f"- Strength grid: {result.get('strength_grid')}",
        "",
        "## Detector ROC/AUC Results",
        "",
        f"- ROC AUC: {_fmt(metrics.get('auc'))}",
        f"- PR AUC: {_fmt(metrics.get('pr_auc'))}",
        f"- Sensitivity at threshold: {_fmt(metrics.get('sensitivity'))}",
        f"- Specificity at threshold: {_fmt(metrics.get('specificity'))}",
        f"- False-positive rate at threshold: {_fmt(metrics.get('false_positive_rate'))}",
        f"- Threshold at target FPR: {_fmt(result.get('threshold_at_5pct_fpr'))}",
        "",
        "## Strength Response",
        "",
        f"- Monotonicity vs flaw strength: {_fmt(result.get('monotonicity'))}",
        f"- Spearman score-strength correlation: {_fmt(result.get('score_strength_correlation'))}",
        "",
        "## Null Distribution",
        "",
        "```json",
        json.dumps(_json_safe(result.get("null_distribution", {})), indent=2, sort_keys=True),
        "```",
        "",
        "## Materiality",
        "",
        "```json",
        json.dumps(_json_safe(result.get("materiality", {})), indent=2, sort_keys=True),
        "```",
        "",
        "## Multiplicity / Error Control",
        "",
        "Per-item flags include empirical p-values and corrected q-values when null scores are available.",
        "",
        "```json",
        json.dumps(_json_safe(result.get("multiplicity", {})), indent=2, sort_keys=True),
        "```",
        "",
        "## Warnings",
        "",
    ]
    lines.extend(f"- {warning}" for warning in result.get("warnings", []) or ["None."])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in result.get("limitations", []) or ["None."])
    if paths:
        lines.extend(["", "## Artifacts", ""])
        lines.extend(f"- {key}: `{value}`" for key, value in sorted(paths.items()))
    lines.append("")
    return "\n".join(lines)


def _render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Diagnostic Validation Summary",
        "",
        "This report summarizes synthetic detector-validation experiments only. It contains no real benchmark validity findings.",
        "",
        "## Executive Summary",
        "",
        summary["executive_summary"],
        "",
        "## Diagnostics Validated",
        "",
    ]
    lines.extend(f"- {item}" for item in summary["diagnostics_validated"] or ["None."])
    lines.extend(["", "## Diagnostics Prototype-Only", ""])
    lines.extend(f"- {item}" for item in summary["diagnostics_prototype_only"] or ["None."])
    lines.extend(["", "## Diagnostics To Quarantine", ""])
    lines.extend(f"- {item}" for item in summary["diagnostics_to_quarantine"] or ["None."])
    lines.extend(["", "## Synthetic Flaw Generator Description", ""])
    lines.append(
        "The harness generates MCQ-style benchmarks with ground-truth `metadata.is_flawed`, "
        "`metadata.flaw_type`, `metadata.flaw_strength`, and `metadata.ground_truth_signal` fields."
    )
    lines.extend(["", "## Flaw Sweep Grid", ""])
    for result in summary["experiments"]:
        lines.append(
            f"- {result.get('diagnostic')} / {result.get('flaw_type')}: {result.get('strength_grid')}"
        )
    lines.extend(["", "## Detector ROC/AUC Results", ""])
    lines.append("| Diagnostic | Flaw | Status | ROC AUC | PR AUC | Clean FPR | Monotonicity |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    for result in summary["experiments"]:
        metrics = result.get("metrics", {})
        lines.append(
            f"| {result.get('diagnostic')} | {result.get('flaw_type')} | "
            f"{result.get('credibility_status')} | {_fmt(metrics.get('auc'))} | "
            f"{_fmt(metrics.get('pr_auc'))} | {_fmt(metrics.get('false_positive_rate'))} | "
            f"{_fmt(result.get('monotonicity'))} |"
        )
    lines.extend(
        [
            "",
            "## False-Positive Rates On Clean Benchmarks",
            "",
            "Clean/null behavior is estimated from strength 0.0 synthetic runs. Thresholds are empirical and generator-specific.",
            "",
            "## Null Distributions",
            "",
            "Each per-diagnostic JSON file contains the null distribution used for thresholding and corrected per-item flags.",
            "",
            "## Threshold Recommendations",
            "",
            "Use the reported threshold-at-target-FPR as a starting point only for the corresponding synthetic generator. Do not transfer it directly to a real benchmark without validation.",
            "",
            "## Materiality Thresholds",
            "",
            "Materiality rules distinguish statistically detectable signals from practically material, ranking-changing, or decision-changing signals.",
            "",
            "## Multiplicity/Error-Control Behavior",
            "",
            "The harness applies Benjamini-Hochberg correction to empirical null p-values for per-item flags when possible.",
            "",
            "## Diagnostics To Trust Now",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["diagnostics_validated"] or ["None."])
    lines.extend(["", "## Diagnostics To Quarantine", ""])
    lines.extend(f"- {item}" for item in summary["diagnostics_to_quarantine"] or ["None."])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in summary["limitations"])
    lines.extend(["", "## Next Validation Experiments", ""])
    lines.extend(f"- {item}" for item in summary["recommended_next_validation_experiments"])
    lines.append("")
    return "\n".join(lines)


def _result_key(result: dict[str, Any]) -> str:
    return f"{result.get('diagnostic')} / {result.get('flaw_type')}"


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and (value != value or value in {float("inf"), float("-inf")}):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value
