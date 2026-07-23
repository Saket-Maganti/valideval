from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from valideval.cli import main
from valideval.importers.wide_matrix import (
    build_matrix_from_wide_predictions,
    import_wide_predictions,
)


def test_wide_jsonl_import_and_matrix_shape(tmp_path: Path):
    source = tmp_path / "predictions.jsonl"
    source.write_text(
        "\n".join(
            [
                json.dumps({"item_id": "i1", "model_id": "m2", "prediction": "A", "gold": "A"}),
                json.dumps({"item_id": "i2", "model_id": "m2", "prediction": "B", "gold": "A"}),
                json.dumps({"item_id": "i1", "model_id": "m1", "prediction": "B", "gold": "A"}),
                json.dumps({"item_id": "i2", "model_id": "m1", "prediction": "A", "gold": "A"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    normalized = tmp_path / "normalized.jsonl"
    summary = import_wide_predictions(source, normalized, benchmark="mockbench")
    assert summary["rows_written"] == 4
    assert summary["model_count"] == 2

    matrix = tmp_path / "matrix.csv"
    matrix_summary = build_matrix_from_wide_predictions(normalized, matrix)
    frame = pd.read_csv(matrix, index_col=0)
    assert matrix_summary["n_models"] == 2
    assert list(frame.index) == ["m1", "m2"]
    assert list(frame.columns) == ["default::i1", "default::i2"]


def test_wide_import_reports_missing_fields(tmp_path: Path):
    source = tmp_path / "bad.jsonl"
    source.write_text(
        json.dumps({"item_id": "i1", "prediction": "A", "gold": "A"}) + "\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Missing required field"):
        import_wide_predictions(source, tmp_path / "out.jsonl", benchmark="mockbench")


def test_wide_cli_smoke(tmp_path: Path):
    out = tmp_path / "out.jsonl"
    assert (
        main(
            [
                "import-wide-predictions",
                "--input",
                "examples/wide_predictions_mock.csv",
                "--output",
                str(out),
                "--benchmark",
                "mmlu",
            ]
        )
        == 0
    )
    assert out.exists()
