from valideval.audit.runner import AuditRunner
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.models.panel import load_panel


def test_response_matrix_building(tmp_path):
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")

    matrices = runner.build_matrices(benchmark, panel, variants=["full"])
    matrix = matrices["full"]

    assert matrix.metadata["benchmark_id"] == "toy_mcq"
    assert matrix.metadata["schema_version"] == "0.1"
    assert matrix.metadata["n_models"] == 8
    assert matrix.metadata["n_items"] == 36
    assert matrix.metadata["prediction_hash"]
    assert matrix.to_dataframe().shape == (8, 36)
    assert (tmp_path / "cache" / "toy_mcq" / "mock" / "matrix_full.csv").exists()
