from pathlib import Path

from valideval.audit.runner import AuditRunner
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.diagnostics.answer_distribution import AnswerDistributionDiagnostic
from valideval.diagnostics.distractors import DistractorQualityDiagnostic
from valideval.diagnostics.prompt_sensitivity import PromptSensitivityDiagnostic
from valideval.models.panel import load_panel
from valideval.schemas import ResponseMatrix


def test_answer_distribution_metrics_cover_artifact_categories():
    benchmark = ToyMCQBenchmark()
    result = AnswerDistributionDiagnostic().run(
        benchmark, ResponseMatrix(model_ids=[], item_ids=[], values=[])
    )

    assert result.summary_metrics["n_items"] == 36
    assert sum(result.summary_metrics["label_counts"].values()) == 36
    assert "longest_option_correct_fraction" in result.summary_metrics["answer_length_bias"]
    assert "distractor_choice_distribution" in result.summary_metrics


def test_distractor_quality_exports_csv(tmp_path):
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
        },
    )

    csv_path = Path(result.artifacts["distractor_quality_csv"])
    assert csv_path.exists()
    assert result.summary_metrics["total_distractors"] > 0
    assert "dead_distractor_fraction" in result.summary_metrics


def test_prompt_sensitivity_detects_ranking_flip():
    full = ResponseMatrix(
        model_ids=["m1", "m2", "m3"],
        item_ids=["i1", "i2"],
        values=[[1, 1], [1, 0], [0, 0]],
        metadata={"prompt_variant": "full"},
    )
    flipped = ResponseMatrix(
        model_ids=["m1", "m2", "m3"],
        item_ids=["i1", "i2"],
        values=[[0, 0], [1, 0], [1, 1]],
        metadata={"prompt_variant": "variant"},
    )

    result = PromptSensitivityDiagnostic().run(
        ToyMCQBenchmark(),
        {"full": full, "variant": flipped},
        config={"variants": ["variant"], "rank_flip_threshold": 1},
    )

    assert result.summary_metrics["prompt_specific_ranking_flips"]
    assert result.summary_metrics["prompt_robustness_coefficient"] < 0
