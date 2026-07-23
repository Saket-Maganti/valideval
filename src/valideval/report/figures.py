from __future__ import annotations

from pathlib import Path

from valideval.schemas import DiagnosticResult


def ensure_figure_dir(path: str | Path = "paper/figures") -> Path:
    destination = Path(path)
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def diagnostic_bar_chart_svg(
    results: list[DiagnosticResult],
    *,
    width: int = 640,
    height: int = 320,
    title: str = "Diagnostic signal overview",
) -> str:
    rows = _chart_rows(results)
    if not rows:
        return _empty_svg(title, width=width, height=height)

    bar_height = 24
    margin_left = 180
    margin_top = 48
    chart_height = margin_top + len(rows) * (bar_height + 8) + 16
    chart_height = max(chart_height, height)
    max_value = max(value for _, value in rows) or 1.0
    bars = []
    for index, (label, value) in enumerate(rows):
        y = margin_top + index * (bar_height + 8)
        bar_width = int((width - margin_left - 40) * (value / max_value))
        bars.append(
            f'<text x="8" y="{y + 16}" font-size="12" fill="#334155">{_escape(label)}</text>'
        )
        bars.append(
            f'<rect x="{margin_left}" y="{y}" width="{bar_width}" height="{bar_height}" '
            f'fill="#3b82f6" rx="4" />'
        )
        bars.append(
            f'<text x="{margin_left + bar_width + 8}" y="{y + 16}" font-size="12" '
            f'fill="#334155">{value:.3f}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{chart_height}">'
        f'<rect width="100%" height="100%" fill="#f8fafc"/>'
        f'<text x="{margin_left}" y="28" font-size="16" font-weight="600" fill="#0f172a">'
        f"{_escape(title)}</text>"
        f"{''.join(bars)}"
        f"</svg>"
    )


def write_diagnostic_figures(
    results: list[DiagnosticResult],
    output_dir: str | Path,
    *,
    benchmark_id: str,
    panel_id: str,
) -> dict[str, str]:
    destination = ensure_figure_dir(output_dir)
    svg = diagnostic_bar_chart_svg(results, title=f"{benchmark_id}/{panel_id} diagnostics")
    path = destination / f"{benchmark_id}_{panel_id}_diagnostic_overview.svg"
    path.write_text(svg, encoding="utf-8")
    return {"diagnostic_overview_svg": str(path)}


def _chart_rows(results: list[DiagnosticResult]) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for result in sorted(results, key=lambda item: item.diagnostic_name):
        value = _extract_chart_value(result)
        if value is not None:
            rows.append((result.diagnostic_name, value))
    return rows[:12]


def _extract_chart_value(result: DiagnosticResult) -> float | None:
    metrics = result.summary_metrics
    for key in (
        "mean_retention",
        "retention",
        "balance_score",
        "pearson_correlation",
        "mean_score_drift",
    ):
        if key in metrics and metrics[key] is not None:
            return abs(float(metrics[key]))
    signals = metrics.get("signals")
    if isinstance(signals, dict):
        measured = sum(
            1
            for signal in signals.values()
            if isinstance(signal, dict) and signal.get("status") == "measured"
        )
        total = len(signals)
        if total:
            return measured / total
    return None


def _empty_svg(title: str, *, width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        f'<rect width="100%" height="100%" fill="#f8fafc"/>'
        f'<text x="24" y="48" font-size="16" fill="#64748b">'
        f"No chartable diagnostics for {_escape(title)}</text></svg>"
    )


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )
