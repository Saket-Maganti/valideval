from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.schemas import DiagnosticResult


def render_audit_summary(
    results: list[DiagnosticResult],
    *,
    manifest: dict[str, Any] | None = None,
) -> str:
    lines = ["# Audit summary", ""]
    if manifest:
        lines.extend(
            [
                f"- Benchmark: `{manifest.get('benchmark_id', 'unknown')}`",
                f"- Panel: `{manifest.get('panel_id', 'unknown')}`",
                f"- Diagnostics run: {len(manifest.get('diagnostics_run', []))}",
                "",
            ]
        )
    lines.append("## Diagnostic health")
    lines.append("")
    lines.append("| Diagnostic | Status | Key signal |")
    lines.append("| --- | --- | --- |")
    for result in sorted(results, key=lambda item: item.diagnostic_name):
        status, signal = _summary_row(result)
        lines.append(f"| {result.diagnostic_name} | {status} | {signal} |")
    warnings = [warning for result in results for warning in result.warnings]
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings[:12]:
            lines.append(f"- {warning}")
        if len(warnings) > 12:
            lines.append(f"- ... and {len(warnings) - 12} more")
    lines.extend(
        [
            "",
            "This summary is a diagnostic profile, not a scalar validity score.",
            "",
        ]
    )
    return "\n".join(lines)


def print_audit_summary(
    results: list[DiagnosticResult],
    *,
    manifest: dict[str, Any] | None = None,
    console: Any | None = None,
) -> None:
    text = render_audit_summary(results, manifest=manifest)
    if console is not None:
        try:
            from rich.markdown import Markdown

            console.print(Markdown(text))
            return
        except Exception:
            pass
    print(text)


def load_results_for_summary(
    results_root: Path, benchmark_id: str, panel_id: str
) -> list[DiagnosticResult]:
    directory = results_root / benchmark_id / panel_id
    if not directory.exists():
        return []
    results = []
    for path in sorted(directory.glob("*.json")):
        if path.name in {"manifest.json"}:
            continue
        payload = path.read_text(encoding="utf-8")
        import json

        results.append(DiagnosticResult.model_validate(json.loads(payload)))
    return results


def _summary_row(result: DiagnosticResult) -> tuple[str, str]:
    metrics = result.summary_metrics
    if metrics.get("status") in {
        "requires_external_criterion",
        "requires_longitudinal_or_intervention_data",
        "unavailable",
    }:
        return str(metrics.get("status")), "not computed"
    if result.diagnostic_name == "shortcut":
        retention = metrics.get("mean_retention") or metrics.get("retention")
        return "measured", f"retention={_fmt(retention)}"
    if result.diagnostic_name == "irt":
        return "measured", f"models={_fmt(metrics.get('n_models'))}"
    if result.diagnostic_name == "coverage":
        return "measured", f"balance={_fmt(metrics.get('balance_score'))}"
    if result.diagnostic_name == "predictive":
        return str(
            metrics.get("status", "measured")
        ), f"r={_fmt(metrics.get('pearson_correlation'))}"
    if result.diagnostic_name == "goodhart":
        return str(
            metrics.get("status", "measured")
        ), f"drift={_fmt(metrics.get('mean_score_drift'))}"
    if "signals" in metrics:
        measured = sum(
            1
            for signal in metrics["signals"].values()
            if isinstance(signal, dict) and signal.get("status") == "measured"
        )
        return "measured", f"{measured} signals"
    if "risk_level" in metrics:
        return "measured", str(metrics["risk_level"])
    return "measured", "see artifact"


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
