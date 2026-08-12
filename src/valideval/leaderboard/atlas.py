from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.human.reporting import atlas_human_status, read_human_artifacts
from valideval.leaderboard.badges import health_badges
from valideval.schemas import DiagnosticResult, utc_now


def build_benchmark_atlas(
    *,
    benchmark_id: str,
    panel_id: str,
    results: list[DiagnosticResult],
    results_root: str | Path = "results",
    output_dir: str | Path = "leaderboard",
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    certificate = _read_json(
        Path(results_root) / benchmark_id / panel_id / "validity_certificate.json"
    )
    human_summary = read_human_artifacts(Path(results_root) / benchmark_id / panel_id)
    badges = health_badges(results)["badges"]
    row = {
        "benchmark_id": benchmark_id,
        "panel_id": panel_id,
        "certificate_level": certificate.get("profile_level", "not issued"),
        "shortcut_resistance": badges["shortcut_resistance"]["status"],
        "item_quality": badges["item_quality"]["status"],
        "reliability": badges["reliability"]["status"],
        "contamination_provenance": badges["contamination_risk"]["status"],
        "saturation": badges["saturation"]["status"],
        "power": _power_status(results),
        "human_validation": atlas_human_status(human_summary),
        "coverage": badges["coverage"]["status"],
    }
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "benchmarks": [row],
        "warnings": [
            "Atlas dimensions are profiles. They are not averaged into one benchmark-health score."
        ],
    }
    json_path = output / "benchmark_atlas.json"
    md_path = output / "benchmark_atlas.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    return {"benchmark_atlas_json": str(json_path), "benchmark_atlas_md": str(md_path)}


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Atlas",
        "",
        "This atlas compares benchmark-health dimensions. It does not report a total score.",
        "",
        (
            "| Benchmark | Panel | Certificate | Shortcut | Item Quality | Reliability | "
            "Contamination/Provenance | Saturation | Power | Human Validation | Coverage |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["benchmarks"]:
        lines.append(
            f"| {row['benchmark_id']} | {row['panel_id']} | {row['certificate_level']} | "
            f"{row['shortcut_resistance']} | {row['item_quality']} | {row['reliability']} | "
            f"{row['contamination_provenance']} | {row['saturation']} | {row['power']} | "
            f"{row['human_validation']} | {row['coverage']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _power_status(results: list[DiagnosticResult]) -> str:
    result = next((item for item in results if item.diagnostic_name == "power"), None)
    if not result:
        return "unknown"
    value = result.summary_metrics.get("do_not_overinterpret_within_points")
    if value is None:
        return "unknown"
    value = float(value)
    if value <= 5:
        return "strong"
    if value <= 15:
        return "moderate"
    if value <= 30:
        return "weak"
    return "threatened"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
