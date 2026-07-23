from valideval.audit.runner import AuditRunner
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.diagnostics.calibration import CalibrationDiagnostic
from valideval.diagnostics.dif import DIFDiagnostic
from valideval.diagnostics.power import PowerDiagnostic
from valideval.diagnostics.ranking_uncertainty import RankingUncertaintyDiagnostic
from valideval.diagnostics.redundancy import RedundancyDiagnostic
from valideval.diagnostics.saturation import SaturationDiagnostic
from valideval.models.panel import load_panel
from valideval.psychometrics.calibration import abstention_report
from valideval.psychometrics.power import required_item_count
from valideval.psychometrics.ranking_uncertainty import bootstrap_rank_uncertainty
from valideval.psychometrics.redundancy import redundancy_report
from valideval.schemas import ModelPrediction, ResponseMatrix


def test_saturation_detects_ceiling():
    matrix = ResponseMatrix(
        model_ids=["m1", "m2", "m3"],
        item_ids=[f"i{i}" for i in range(12)],
        values=[[1] * 12, [1] * 12, [1] * 11 + [0]],
        metadata={"prompt_variant": "full"},
    )

    result = SaturationDiagnostic().run(ToyMCQBenchmark(), matrix, config={"top_n": 3})

    assert result.summary_metrics["saturation_category"] in {"moderate", "severe"}
    assert result.summary_metrics["fraction_solved_by_all_top_models"] > 0.9


def test_power_formula_and_diagnostic():
    matrix = ResponseMatrix(
        model_ids=["a", "b"],
        item_ids=[f"toy_{i:03d}" for i in range(1, 13)],
        values=[[1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0], [1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0]],
        metadata={"prompt_variant": "full"},
    )

    assert required_item_count(score=0.5, difference_points=5) > required_item_count(
        score=0.5, difference_points=10
    )
    result = PowerDiagnostic().run(
        ToyMCQBenchmark(), matrix, config={"bootstrap_samples": 25, "seed": 0}
    )

    assert result.summary_metrics["required_item_count"]["5_point"] > 0
    assert result.summary_metrics["do_not_overinterpret_within_points"] > 0


def test_dif_group_bias_flags_suspicious_item():
    matrix = ResponseMatrix(
        model_ids=["small_1", "small_2", "large_1", "large_2"],
        item_ids=["biased", "neutral"],
        values=[[0, 1], [0, 1], [1, 1], [1, 1]],
        metadata={"prompt_variant": "full"},
    )
    result = DIFDiagnostic().run(
        ToyMCQBenchmark(),
        matrix,
        config={
            "groups": {
                "small_1": "small",
                "small_2": "small",
                "large_1": "large",
                "large_2": "large",
            },
            "effect_size_threshold": 0.2,
        },
    )

    assert "biased" in result.summary_metrics["suspicious_items"]
    assert any("model-family" in warning for warning in result.warnings)


def test_redundancy_clusters_and_cluster_weighted_accuracy():
    benchmark = ToyMCQBenchmark()
    result = redundancy_report(benchmark)

    assert result["redundancy_fraction"] > 0
    diagnostic = RedundancyDiagnostic().run(
        benchmark,
        ResponseMatrix(
            model_ids=["m"],
            item_ids=[item.item_id for item in benchmark.load_items()],
            values=[[1] * len(benchmark.load_items())],
            metadata={"prompt_variant": "full"},
        ),
    )
    assert "cluster_weighted_accuracy" in diagnostic.summary_metrics


def test_calibration_and_abstention_with_cached_predictions(tmp_path):
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    matrices = runner.build_matrices(
        benchmark,
        panel,
        variants=["full", "context_removed", "context_shuffled"],
    )
    result = CalibrationDiagnostic().run(
        benchmark,
        matrices,
        config={"cache_root": str(tmp_path / "cache"), "panel_id": "mock", "n_bins": 5},
    )

    assert "ece" in result.summary_metrics
    assert result.summary_metrics["ece"] is None
    assert result.summary_metrics["calibration_status"] == "requires_confidence_outputs"
    assert result.summary_metrics["prompt_consistency_proxy"]["status"] == "not_calibration"
    assert "abstention" in result.summary_metrics
    assert result.warnings

    abstention = abstention_report(
        [
            ModelPrediction(
                model_id="m",
                item_id="i",
                prompt_variant="full",
                prediction="unparseable",
                score=0.0,
                raw_output="I cannot answer.",
            )
        ]
    )
    assert abstention["coverage"] == 0.0
    assert abstention["appropriate_refusal_rate"] == 1.0


def test_rank_uncertainty_outputs_probabilities():
    matrix = ResponseMatrix(
        model_ids=["a", "b", "c"],
        item_ids=[f"i{i}" for i in range(6)],
        values=[[1, 1, 1, 0, 1, 0], [1, 1, 0, 0, 1, 0], [0, 1, 0, 0, 0, 0]],
        metadata={"prompt_variant": "full"},
    )

    report = bootstrap_rank_uncertainty(matrix, n_boot=25, seed=0, top_k=2)
    assert 0.0 <= report["top_k_stability"] <= 1.0

    diagnostic = RankingUncertaintyDiagnostic().run(
        ToyMCQBenchmark(),
        matrix,
        config={"bootstrap_samples": 25, "seed": 0, "top_k": 2},
    )
    assert "probability_model_a_beats_model_b" in diagnostic.summary_metrics
