from valideval.audit.runner import AuditRunner
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.diagnostics.extraction_robustness import ExtractionRobustnessDiagnostic
from valideval.models.panel import load_panel
from valideval.scoring.extraction import (
    alias_aware_match,
    invalid_output_detector,
    lenient_letter,
    normalized_exact_match,
    numeric_tolerance,
    refusal_detector,
    regex_final_answer,
    strict_letter,
)


def test_extraction_modes():
    assert strict_letter("A").value == "A"
    assert strict_letter("Answer: A").invalid is True
    assert lenient_letter("Answer: A").value == "A"
    assert regex_final_answer("Final answer: C").value == "C"
    assert numeric_tolerance("about 7", answer=7).metadata["within_tolerance"] is True
    assert normalized_exact_match("  Yes ", aliases=["yes"]).metadata["matched_alias"] is True
    assert alias_aware_match("rapid", aliases=["rapid"]).metadata["canonical_alias"] == "rapid"
    assert refusal_detector("I cannot answer").refusal is True
    assert invalid_output_detector("not enough information").invalid is True


def test_extraction_robustness_reports_strict_lenient_shift(tmp_path):
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    matrices = runner.build_matrices(benchmark, panel, variants=["full"])

    result = ExtractionRobustnessDiagnostic().run(
        benchmark,
        matrices,
        config={"cache_root": str(tmp_path / "cache"), "panel_id": "mock"},
    )

    assert "strict_vs_lenient_score_shift" in result.summary_metrics
    assert result.summary_metrics["ambiguous_item_count"] >= 1
    assert result.per_model_metrics["format_fragile"]["lenient_score"] >= 0.0
