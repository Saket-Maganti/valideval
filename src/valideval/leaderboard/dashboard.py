from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from valideval.leaderboard.badges import health_badges
from valideval.leaderboard.registry import ensure_registry, list_audits
from valideval.schemas import DiagnosticResult, utc_now


def export_dashboard_data(
    *,
    benchmark_id: str,
    panel_id: str,
    results: list[DiagnosticResult],
    results_root: str | Path = "results",
    registry_root: str | Path = "registry",
    output_dir: str | Path = "dashboard_data",
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    root = Path(results_root)
    certificate = _read_json(root / benchmark_id / panel_id / "validity_certificate.json")
    ranking_flips = _read_json(root / benchmark_id / panel_id / "ranking_flips.json")
    badges = health_badges(results)["badges"]
    ensure_registry(registry_root)
    audit_history = list_audits(registry_root)

    profiles = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "benchmark_profiles": [
            {
                "benchmark_id": benchmark_id,
                "panel_id": panel_id,
                "certificate_level": certificate.get("profile_level", "not issued"),
                "badges": badges,
            }
        ],
    }
    diagnostics_summary = {
        "schema_version": "0.1",
        "diagnostics": [
            {
                "diagnostic_name": result.diagnostic_name,
                "warnings": len(result.warnings),
                "limitations": len(result.limitations),
                "summary_keys": sorted(result.summary_metrics.keys()),
            }
            for result in results
        ],
    }
    paths = {
        "benchmark_profiles_json": output / "benchmark_profiles.json",
        "diagnostics_summary_json": output / "diagnostics_summary.json",
        "ranking_flips_json": output / "ranking_flips.json",
        "certificates_json": output / "certificates.json",
        "audit_history_json": output / "audit_history.json",
        "benchmark_profiles_csv": output / "benchmark_profiles.csv",
        "diagnostics_summary_csv": output / "diagnostics_summary.csv",
        "item_forensics_csv": output / f"{benchmark_id}_{panel_id}_item_forensics.csv",
    }
    _write_json(paths["benchmark_profiles_json"], profiles)
    _write_json(paths["diagnostics_summary_json"], diagnostics_summary)
    _write_json(
        paths["ranking_flips_json"], ranking_flips or {"schema_version": "0.1", "comparisons": {}}
    )
    _write_json(
        paths["certificates_json"], {"schema_version": "0.1", "certificates": [certificate]}
    )
    _write_json(paths["audit_history_json"], {"schema_version": "0.1", "audits": audit_history})
    _write_profiles_csv(paths["benchmark_profiles_csv"], profiles["benchmark_profiles"])
    _write_diagnostics_csv(paths["diagnostics_summary_csv"], diagnostics_summary["diagnostics"])
    item_source = root / benchmark_id / panel_id / "item_forensics.csv"
    if item_source.exists():
        paths["item_forensics_csv"].write_text(
            item_source.read_text(encoding="utf-8"), encoding="utf-8"
        )
    else:
        paths["item_forensics_csv"].write_text("item_id\n", encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_profiles_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["benchmark_id", "panel_id", "certificate_level"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "benchmark_id": row["benchmark_id"],
                    "panel_id": row["panel_id"],
                    "certificate_level": row["certificate_level"],
                }
            )


def _write_diagnostics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["diagnostic_name", "warnings", "limitations", "summary_keys"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "summary_keys": ";".join(row["summary_keys"]),
                }
            )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
