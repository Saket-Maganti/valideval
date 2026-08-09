# Ruff classifies these same-package imports differently across the macOS and Linux resolvers.
# ruff: noqa: I001
from __future__ import annotations

import json
from pathlib import Path

from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.leaderboard.atlas import build_benchmark_atlas
from valideval.leaderboard.badges import health_badges
from valideval.leaderboard.dashboard import export_dashboard_data
from valideval.leaderboard.diff import diff_audits
from valideval.leaderboard.flips import detect_ranking_flips
from valideval.leaderboard.platform import build_platform_exports
from valideval.leaderboard.ranking_views import RANKING_VIEW_NAMES, build_ranking_views
from valideval.leaderboard.registry import (
    add_audit_to_registry,
    list_audits,
    validate_registry,
)
from valideval.leaderboard.significance import ranking_significance
from valideval.leaderboard.site import build_static_site
from valideval.schemas import DiagnosticResult, ResponseMatrix


def _matrix() -> ResponseMatrix:
    return ResponseMatrix(
        model_ids=["m1", "m2", "m3"],
        item_ids=["i1", "i2", "i3", "i4"],
        values=[
            [1, 1, 0, 0],
            [1, 0, 1, 1],
            [0, 1, 0, 1],
        ],
        metadata={"benchmark_id": "toy_mcq", "panel_id": "mock"},
    )


def _results() -> list[DiagnosticResult]:
    return [
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="irt",
            version="test",
            summary_metrics={
                "negative_discrimination_items": 0,
                "near_zero_discrimination_fraction": 0.1,
                "n_items": 4,
            },
            per_model_metrics={
                "m1": {"latent_ability_proxy": 0.9},
                "m2": {"latent_ability_proxy": 0.3},
                "m3": {"latent_ability_proxy": 0.2},
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="reliability",
            version="test",
            summary_metrics={"benchmark_level_reliability_estimate": 0.75},
            per_model_metrics={
                "m1": {"score_variance_across_variants": 0.01},
                "m2": {"score_variance_across_variants": 0.10},
                "m3": {"score_variance_across_variants": 0.00},
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="shortcut",
            version="test",
            summary_metrics={
                "high_retention_variants": ["label_prior_only"],
                "variants": {"label_prior_only": {"shortcut_retention": 0.9}},
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="prompt_sensitivity",
            version="test",
            summary_metrics={"prompt_specific_ranking_flips": [{"model_id": "m1"}]},
            per_model_metrics={
                "m1": {"score_variance_across_prompt_templates": 0.2},
                "m2": {"score_variance_across_prompt_templates": 0.0},
                "m3": {"score_variance_across_prompt_templates": 0.1},
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="extraction_robustness",
            version="test",
            summary_metrics={"extraction_disagreement_rate": 0.01},
            per_model_metrics={
                "m1": {"strict_score": 0.5},
                "m2": {"strict_score": 0.6},
                "m3": {"strict_score": 0.5},
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="data_forensics",
            version="test",
            summary_metrics={
                "signals": {
                    "corpus_overlap": {
                        "status": "measured",
                        "risk_level": "low local evidence",
                        "metrics": {},
                    }
                }
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="saturation",
            version="test",
            summary_metrics={"saturation_category": "mild"},
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="power",
            version="test",
            summary_metrics={"do_not_overinterpret_within_points": 8.0},
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="coverage",
            version="test",
            summary_metrics={"missing_expected_tags": [], "n_unique_tags": 3},
        ),
    ]


def test_ranking_views_and_significance_include_expected_views(tmp_path: Path):
    payload = build_ranking_views(
        _matrix(),
        _results(),
        output_dir=tmp_path,
        n_boot=25,
        seed=0,
    )
    significance = ranking_significance(_matrix(), n_boot=25, seed=0)

    assert set(RANKING_VIEW_NAMES) <= set(payload["views"])
    assert payload["views"]["irt_latent_ability"]["ranking"][0]["model_id"] == "m1"
    assert significance["paired_bootstrap_differences"]
    assert "do_not_overinterpret_within_points" in significance
    assert (tmp_path / "ranking_views.json").exists()


def test_ranking_flip_detector_finds_raw_vs_irt_flip(tmp_path: Path):
    views = build_ranking_views(_matrix(), _results(), output_dir=tmp_path, n_boot=25)
    flips = detect_ranking_flips(views, matrix=_matrix(), output_dir=tmp_path)

    raw_vs_irt = flips["comparisons"]["raw_vs_irt_latent_ability"]
    assert raw_vs_irt["available"] is True
    assert raw_vs_irt["flip_count"] > 0
    assert (tmp_path / "ranking_flips.json").exists()


def test_health_badges_registry_atlas_dashboard_and_site(tmp_path: Path):
    results_root = tmp_path / "results"
    registry_root = tmp_path / "registry"
    leaderboard_root = tmp_path / "leaderboard"
    dashboard_root = tmp_path / "dashboard_data"
    site_root = tmp_path / "site"
    audit_dir = results_root / "toy_mcq" / "mock"
    audit_dir.mkdir(parents=True)
    (results_root / "toy_mcq" / "manifest.json").write_text(
        json.dumps({"item_text_hash": "abc", "benchmark_config_hash": "cfg", "item_count": 4}),
        encoding="utf-8",
    )
    (audit_dir / "validity_certificate.json").write_text(
        json.dumps({"profile_level": "Silver"}),
        encoding="utf-8",
    )
    (audit_dir / "item_forensics.csv").write_text("item_id\n", encoding="utf-8")

    badges = health_badges(_results(), output_dir=audit_dir)
    record = add_audit_to_registry(
        benchmark_id="toy_mcq",
        panel_id="mock",
        results=_results(),
        results_root=results_root,
        registry_root=registry_root,
    )
    atlas = build_benchmark_atlas(
        benchmark_id="toy_mcq",
        panel_id="mock",
        results=_results(),
        results_root=results_root,
        output_dir=leaderboard_root,
    )
    dashboard = export_dashboard_data(
        benchmark_id="toy_mcq",
        panel_id="mock",
        results=_results(),
        results_root=results_root,
        registry_root=registry_root,
        output_dir=dashboard_root,
    )
    site = build_static_site(
        site_dir=site_root,
        registry_root=registry_root,
        leaderboard_root=leaderboard_root,
        results_root=results_root,
        reportcards_root=tmp_path / "reportcards",
    )

    assert badges["badges"]["shortcut_resistance"]["status"] == "threatened"
    assert record["audit_id"].startswith("toy_mcq:mock:")
    assert validate_registry(registry_root)["valid"] is True
    assert len(list_audits(registry_root)) == 1
    assert Path(atlas["benchmark_atlas_json"]).exists()
    assert Path(dashboard["benchmark_profiles_json"]).exists()
    assert Path(site["index.html"]).exists()


def test_audit_diff_compares_diagnostic_and_ranking_changes(tmp_path: Path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    old.mkdir()
    new.mkdir()
    old_irt = DiagnosticResult(
        benchmark_id="toy_mcq",
        diagnostic_name="irt",
        version="old",
        summary_metrics={"n_items": 4, "near_zero_discrimination_fraction": 0.3},
    )
    new_irt = DiagnosticResult(
        benchmark_id="toy_mcq",
        diagnostic_name="irt",
        version="new",
        summary_metrics={"n_items": 5, "near_zero_discrimination_fraction": 0.1},
    )
    (old / "irt.json").write_text(
        json.dumps(old_irt.model_dump(mode="json")),
        encoding="utf-8",
    )
    (new / "irt.json").write_text(
        json.dumps(new_irt.model_dump(mode="json")),
        encoding="utf-8",
    )
    (old / "validity_certificate.json").write_text(
        json.dumps({"profile_level": "Bronze"}),
        encoding="utf-8",
    )
    (new / "validity_certificate.json").write_text(
        json.dumps({"profile_level": "Silver"}),
        encoding="utf-8",
    )

    diff = diff_audits(old, new, output_path=tmp_path / "audit_diff.json")

    assert diff["item_count_change"] == 1
    assert diff["certificate_change"]["new"] == "Silver"
    assert diff["irt_change"]["delta"] < 0
    assert (tmp_path / "audit_diff.json").exists()


def test_platform_exports_orchestrate_all_outputs(tmp_path: Path):
    results_root = tmp_path / "results"
    reportcards_root = tmp_path / "reportcards"
    registry_root = tmp_path / "registry"
    leaderboard_root = tmp_path / "leaderboard"
    dashboard_root = tmp_path / "dashboard"
    audit_dir = results_root / "toy_mcq" / "mock"
    audit_dir.mkdir(parents=True)
    (results_root / "toy_mcq" / "manifest.json").write_text(
        json.dumps({"item_text_hash": "abc", "benchmark_config_hash": "cfg", "item_count": 36}),
        encoding="utf-8",
    )
    (audit_dir / "validity_certificate.json").write_text(
        json.dumps({"profile_level": "Silver"}),
        encoding="utf-8",
    )

    output = build_platform_exports(
        benchmark=ToyMCQBenchmark(),
        panel_id="mock",
        results=_results(),
        matrix=_matrix(),
        results_root=results_root,
        reportcards_root=reportcards_root,
        registry_root=registry_root,
        leaderboard_root=leaderboard_root,
        dashboard_root=dashboard_root,
        n_boot=25,
        seed=0,
    )

    assert Path(output["ranking_views_json"]).exists()
    assert Path(output["ranking_flips_json"]).exists()
    assert Path(output["health_badges_json"]).exists()
    assert Path(output["platform_exports_json"]).exists()
