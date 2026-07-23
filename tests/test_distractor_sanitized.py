from pathlib import Path

from valideval.audit.runner import AuditRunner
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.diagnostics.distractors import DistractorQualityDiagnostic
from valideval.models.panel import load_panel


def test_distractor_quality_sanitized_omits_choice_text(tmp_path):
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    matrices = runner.build_matrices(benchmark, panel, variants=["full"])
    output_dir = tmp_path / "results" / "toy_mcq" / "mock"

    result = DistractorQualityDiagnostic().run(
        benchmark,
        matrices,
        config={
            "cache_root": str(tmp_path / "cache"),
            "panel_id": "mock",
            "output_dir": str(output_dir),
            "sanitized": True,
        },
    )

    assert result.summary_metrics["sanitized"] is True
    assert result.summary_metrics["raw_choice_text_included"] is False
    assert result.artifacts["distractor_quality_csv"] is None
    json_path = Path(result.artifacts["distractor_quality_sanitized_json"])
    assert json_path.exists()
    payload = json_path.read_text(encoding="utf-8")
    assert "distractor_text" not in payload
    assert "choice_label" in payload
