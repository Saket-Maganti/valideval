from __future__ import annotations

from pathlib import Path

from valideval.importers.wide_matrix import (
    build_matrix_from_wide_predictions,
    import_wide_predictions,
)
from valideval.validation.mmlu_redux import import_mmlu_redux_ground_truth
from valideval.validation.mmlu_redux_pipeline import run_mmlu_redux_validation


def test_mmlu_redux_pipeline_blocks_missing_inputs(tmp_path: Path):
    payload = run_mmlu_redux_validation(
        predictions_path=tmp_path / "missing_predictions.jsonl",
        matrix_path=tmp_path / "missing_matrix.csv",
        ground_truth_path=tmp_path / "missing_gt.jsonl",
        output_dir=tmp_path / "out",
    )
    assert payload["status"] == "blocked"
    assert "predictions" in payload["missing_inputs"]
    assert (tmp_path / "out" / "README.md").exists()


def test_mmlu_redux_pipeline_runs_on_tiny_local_fixture(tmp_path: Path):
    predictions = tmp_path / "predictions.jsonl"
    import_wide_predictions("examples/wide_predictions_mock.jsonl", predictions, benchmark="mmlu")
    matrix = tmp_path / "matrix.csv"
    build_matrix_from_wide_predictions(predictions, matrix)
    gt = tmp_path / "ground_truth.jsonl"
    import_mmlu_redux_ground_truth("examples/mmlu_redux_mock.jsonl", gt)

    payload = run_mmlu_redux_validation(
        predictions_path=predictions,
        matrix_path=matrix,
        ground_truth_path=gt,
        output_dir=tmp_path / "out",
    )
    assert payload["status"] in {"ok", "blocked_panel"}
    assert (tmp_path / "out" / "paper_table_mmlu_redux.md").exists()
