from __future__ import annotations

from pathlib import Path

import pytest

from valideval.audit.runner import LEGENDARY_DIAGNOSTICS, AuditRunner
from valideval.audit.summary import render_audit_summary
from valideval.benchmarks.base import get_benchmark
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.diagnostics.coverage import CoverageDiagnostic
from valideval.diagnostics.goodhart import GoodhartDiagnostic
from valideval.diagnostics.predictive import PredictiveDiagnostic
from valideval.domains.diagnostics import (
    AgentValidityDiagnostic,
    CodeValidityDiagnostic,
    MedicalValidityDiagnostic,
    SafetyValidityDiagnostic,
)
from valideval.forensics.semantic_duplicates import semantic_duplicate_report
from valideval.models.panel import load_panel
from valideval.report.figures import diagnostic_bar_chart_svg, write_diagnostic_figures
from valideval.schemas import BenchmarkItem


def _item_with_metadata(item_id: str, metadata: dict) -> BenchmarkItem:
    return BenchmarkItem(
        item_id=item_id,
        prompt="Sample prompt",
        answer="A",
        choices=["A. one", "B. two", "C. three", "D. four"],
        construct_tags=["test"],
        metadata=metadata,
    )


class MetadataBenchmark:
    benchmark_id = "metadata_fixture"
    claimed_construct = "metadata fixture"
    construct_spec = ToyMCQBenchmark().construct_spec

    def load_items(self):
        return [
            _item_with_metadata(
                "safe_001",
                {
                    "policy_version": "policy-a",
                    "risk_category": "benign",
                    "expected_refusal": False,
                    "rubric_version": "rubric-a",
                },
            ),
            _item_with_metadata(
                "safe_002",
                {
                    "policy_version": "policy-a",
                    "risk_category": "unsafe",
                    "expected_refusal": True,
                    "adversarial_style": "roleplay",
                    "rubric_version": "rubric-a",
                },
            ),
            _item_with_metadata(
                "code_001",
                {
                    "hidden_test_count": 10,
                    "public_test_count": 2,
                    "flaky_rerun_count": 0,
                    "package_lock_hash": "lock-1",
                    "language": "python",
                },
            ),
            _item_with_metadata(
                "med_001",
                {
                    "site_id": "site_a",
                    "annotator_count": 3,
                    "severity": "moderate",
                    "clinical_utility_weight": 0.8,
                    "uncertainty_score": 0.2,
                },
            ),
            _item_with_metadata(
                "agent_001",
                {
                    "agent_trace": {
                        "environment_seed": 7,
                        "success": True,
                        "steps": [
                            {
                                "state_hash": "s1",
                                "reward": 0.2,
                                "tool_call": {"name": "lookup"},
                            },
                            {"state_hash": "s2", "reward": 1.0, "tool_call": {"name": "submit"}},
                        ],
                    }
                },
            ),
        ]

    def render_prompt(self, item, variant: str = "full") -> str:
        return item.prompt

    def score_prediction(self, item, prediction: str):
        raise NotImplementedError

    def available_prompt_variants(self):
        return ["full"]


def test_semantic_duplicate_report_finds_paraphrase_cluster():
    items = [
        BenchmarkItem(
            item_id="a",
            prompt="Which planet is known as the red planet in our solar system?",
            answer="A",
            choices=["A. Mars", "B. Venus", "C. Jupiter", "D. Saturn"],
            construct_tags=["astronomy"],
        ),
        BenchmarkItem(
            item_id="b",
            prompt="The red planet in our solar system is which planet?",
            answer="A",
            choices=["A. Mars", "B. Venus", "C. Jupiter", "D. Saturn"],
            construct_tags=["astronomy"],
        ),
        BenchmarkItem(
            item_id="c",
            prompt="What is the capital of France?",
            answer="A",
            choices=["A. Paris", "B. Lyon", "C. Nice", "D. Bordeaux"],
            construct_tags=["geography"],
        ),
    ]
    report = semantic_duplicate_report(items, threshold=0.5)
    assert report["status"] == "measured"
    assert report["metrics"]["cluster_count"] >= 1


def test_domain_diagnostics_measure_metadata_signals():
    benchmark = MetadataBenchmark()
    safety = SafetyValidityDiagnostic().run(benchmark, {})
    code = CodeValidityDiagnostic().run(benchmark, {})
    medical = MedicalValidityDiagnostic().run(benchmark, {})
    agent = AgentValidityDiagnostic().run(benchmark, {})

    assert safety.summary_metrics["signals"]["policy_version_consistency"]["status"] == "measured"
    assert code.summary_metrics["signals"]["hidden_test_strength"]["status"] == "measured"
    assert medical.summary_metrics["signals"]["site_diversity"]["status"] == "measured"
    assert agent.summary_metrics["signals"]["trace_replay_completeness"]["status"] == "measured"


def test_predictive_and_goodhart_diagnostics_with_fixtures(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    matrices = runner.build_matrices(benchmark, panel, variants=["full"])

    criterion = tmp_path / "criterion.jsonl"
    criterion.write_text(
        Path("examples/external_criterion_mock.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    intervention = tmp_path / "intervention.jsonl"
    intervention.write_text(
        Path("examples/intervention_mock.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    predictive = PredictiveDiagnostic().run(
        benchmark,
        matrices,
        config={"external_criterion_path": str(criterion)},
    )
    goodhart = GoodhartDiagnostic().run(
        benchmark,
        matrices,
        config={"intervention_path": str(intervention)},
    )

    assert predictive.summary_metrics["status"] == "measured"
    assert "pearson_correlation" in predictive.summary_metrics
    assert goodhart.summary_metrics["status"] == "measured"
    assert "mean_score_drift" in goodhart.summary_metrics


def test_coverage_diagnostic_reports_balance_score():
    benchmark = ToyMCQBenchmark()
    result = CoverageDiagnostic().run(benchmark, {})
    assert "balance_score" in result.summary_metrics
    assert "singleton_tags" in result.summary_metrics


def test_mmlu_local_loader(tmp_path: Path):
    source = Path("examples/mmlu_subset.jsonl")
    benchmark = get_benchmark("mmlu", local_path=source)
    items = benchmark.load_items()
    assert len(items) == 4
    assert benchmark.benchmark_id == "mmlu"
    assert "stem" in benchmark.construct_spec.construct_tags


def test_legendary_preset_contains_core_and_extended_diagnostics():
    assert "shortcut" in LEGENDARY_DIAGNOSTICS
    assert "coverage" in LEGENDARY_DIAGNOSTICS
    assert "ranking_uncertainty" in LEGENDARY_DIAGNOSTICS
    assert len(LEGENDARY_DIAGNOSTICS) >= 18


def test_audit_summary_and_figures_render(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    runner.run_diagnostics(benchmark, panel, diagnostics=["shortcut", "coverage"])
    results = runner.load_diagnostic_results(benchmark.benchmark_id, panel.panel_id)
    summary = render_audit_summary(results)
    assert "Audit summary" in summary
    assert "shortcut" in summary

    figures = write_diagnostic_figures(
        results,
        tmp_path / "figures",
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel.panel_id,
    )
    svg = Path(figures["diagnostic_overview_svg"]).read_text(encoding="utf-8")
    assert "<svg" in svg
    assert diagnostic_bar_chart_svg(results)


def test_mmlu_requires_local_path():
    with pytest.raises(ValueError, match="requires --local-path"):
        get_benchmark("mmlu")
