from valideval.audit.runner import AuditRunner
from valideval.baselines import BASELINE_REGISTRY, evaluate_baselines
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.diagnostics.baselines import BaselineDiagnostic
from valideval.models.panel import load_panel


def test_baseline_zoo_runs_offline():
    benchmark = ToyMCQBenchmark()
    results = evaluate_baselines(benchmark, seed=0)

    assert set(BASELINE_REGISTRY) == {result.baseline_id for result in results}
    assert len(results) == 13
    assert all(0.0 <= result.score <= 1.0 for result in results)
    assert any(result.baseline_id == "metadata_artifact_baseline" for result in results)


def test_baseline_diagnostic_reports_dumb_baseline_gap(tmp_path):
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    matrices = runner.build_matrices(benchmark, panel, variants=["full"])

    result = BaselineDiagnostic().run(benchmark, matrices, config={"seed": 0})

    assert result.summary_metrics["best_shallow_baseline"]["score"] >= 0.0
    assert "dumb_baseline_gap" in result.summary_metrics
    assert "metadata_artifact_baseline" in result.summary_metrics["baseline_scores"]
