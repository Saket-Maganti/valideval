from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.leaderboard.atlas import build_benchmark_atlas
from valideval.leaderboard.badges import health_badges
from valideval.leaderboard.dashboard import export_dashboard_data
from valideval.leaderboard.flips import detect_ranking_flips
from valideval.leaderboard.ranking_views import build_ranking_views
from valideval.leaderboard.registry import add_audit_to_registry
from valideval.schemas import DiagnosticResult, ResponseMatrix


def build_platform_exports(
    *,
    benchmark: Benchmark,
    panel_id: str,
    results: list[DiagnosticResult],
    matrix: ResponseMatrix,
    results_root: str | Path = "results",
    reportcards_root: str | Path = "reportcards",
    registry_root: str | Path = "registry",
    leaderboard_root: str | Path = "leaderboard",
    dashboard_root: str | Path = "dashboard_data",
    n_boot: int = 500,
    seed: int = 0,
) -> dict[str, Any]:
    output_dir = Path(results_root) / benchmark.benchmark_id / panel_id
    repair_diff = output_dir / "repair_diff.json"
    views = build_ranking_views(
        matrix,
        results,
        output_dir=output_dir,
        repair_diff_path=repair_diff,
        n_boot=n_boot,
        seed=seed,
    )
    flips = detect_ranking_flips(
        views,
        matrix=matrix,
        output_dir=output_dir,
        repair_diff_path=repair_diff,
    )
    badges = health_badges(results, output_dir=output_dir)
    registry_record = add_audit_to_registry(
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel_id,
        results=results,
        results_root=results_root,
        reportcards_root=reportcards_root,
        registry_root=registry_root,
    )
    atlas = build_benchmark_atlas(
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel_id,
        results=results,
        results_root=results_root,
        output_dir=leaderboard_root,
    )
    dashboard = export_dashboard_data(
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel_id,
        results=results,
        results_root=results_root,
        registry_root=registry_root,
        output_dir=dashboard_root,
    )
    payload = {
        "ranking_views_json": str(output_dir / "ranking_views.json"),
        "ranking_views_csv": str(output_dir / "ranking_views.csv"),
        "ranking_significance_json": str(output_dir / "ranking_significance.json"),
        "ranking_flips_json": str(output_dir / "ranking_flips.json"),
        "health_badges_json": str(output_dir / "health_badges.json"),
        "registry_audit_id": registry_record["audit_id"],
        **atlas,
        **dashboard,
        "summary": {
            "ranking_view_count": len(views.get("views", {})),
            "flip_comparison_count": len(flips.get("comparisons", {})),
            "badge_count": len(badges.get("badges", {})),
        },
    }
    (output_dir / "platform_exports.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    payload["platform_exports_json"] = str(output_dir / "platform_exports.json")
    return payload
