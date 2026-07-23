from valideval.audit.runner import AuditRunner
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.diagnostics.shortcut import ShortcutDiagnostic
from valideval.models.panel import load_panel


def test_shortcut_diagnostic_detects_retention_under_label_prior(tmp_path):
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    matrices = runner.build_matrices(
        benchmark,
        panel,
        variants=["full", "context_removed", "label_prior_only"],
    )

    result = ShortcutDiagnostic().run(
        benchmark,
        matrices,
        config={"variants": ["context_removed", "label_prior_only"], "bootstrap_samples": 50},
    )

    assert result.summary_metrics["full_score"] > 0.3
    assert "label_prior_only" in result.summary_metrics["variants"]
    assert result.summary_metrics["variants"]["label_prior_only"]["shortcut_retention"] > 0.5
    assert any("High retained performance" in warning for warning in result.warnings)
