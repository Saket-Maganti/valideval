from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from valideval.io.jsonl import read_jsonl_as, write_jsonl
from valideval.schemas import ModelPrediction, ResponseMatrix, ResponseMatrixMetadata


def cache_dir(root: str | Path, benchmark_id: str, panel_id: str) -> Path:
    return Path(root) / benchmark_id / panel_id


def prediction_path(root: str | Path, benchmark_id: str, panel_id: str, variant: str) -> Path:
    return cache_dir(root, benchmark_id, panel_id) / f"predictions_{variant}.jsonl"


def matrix_path(root: str | Path, benchmark_id: str, panel_id: str, variant: str) -> Path:
    return cache_dir(root, benchmark_id, panel_id) / f"matrix_{variant}.csv"


def matrix_metadata_path(root: str | Path, benchmark_id: str, panel_id: str, variant: str) -> Path:
    return cache_dir(root, benchmark_id, panel_id) / f"matrix_{variant}.metadata.json"


def _stable_json_hash(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def save_predictions(
    root: str | Path,
    benchmark_id: str,
    panel_id: str,
    variant: str,
    predictions: list[ModelPrediction],
) -> Path:
    path = prediction_path(root, benchmark_id, panel_id, variant)
    write_jsonl(path, predictions)
    return path


def load_predictions(
    root: str | Path,
    benchmark_id: str,
    panel_id: str,
    variant: str,
) -> list[ModelPrediction]:
    return read_jsonl_as(prediction_path(root, benchmark_id, panel_id, variant), ModelPrediction)


def build_response_matrix(
    predictions: list[ModelPrediction],
    *,
    benchmark_id: str,
    panel_id: str,
    variant: str,
    scoring_method: str = "mcq",
    seed: int | None = None,
) -> ResponseMatrix:
    rows = [
        {
            "model_id": prediction.model_id,
            "item_id": prediction.item_id,
            "score": prediction.score,
        }
        for prediction in predictions
    ]
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("Cannot build a response matrix from zero predictions.")
    matrix_frame = frame.pivot_table(
        index="model_id",
        columns="item_id",
        values="score",
        aggfunc="mean",
    )
    matrix_frame = matrix_frame.sort_index().sort_index(axis=1)
    metadata = ResponseMatrixMetadata(
        benchmark_id=benchmark_id,
        panel_id=panel_id,
        prompt_variant=variant,
        scoring_method=scoring_method,
        n_models=matrix_frame.shape[0],
        n_items=matrix_frame.shape[1],
        seed=seed,
        prediction_hash=_stable_json_hash(
            [prediction.model_dump(mode="json") for prediction in predictions]
        ),
        limitations=[
            "Response matrices summarize scored outputs only; inspect prediction JSONL for raw outputs."
        ],
    )
    return ResponseMatrix.from_dataframe(matrix_frame, metadata=metadata.to_json_dict())


def save_matrix(
    root: str | Path,
    benchmark_id: str,
    panel_id: str,
    variant: str,
    matrix: ResponseMatrix,
) -> Path:
    path = matrix_path(root, benchmark_id, panel_id, variant)
    path.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_dataframe().to_csv(path)
    with matrix_metadata_path(root, benchmark_id, panel_id, variant).open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(matrix.metadata, handle, indent=2, sort_keys=True)
    return path


def load_matrix(root: str | Path, benchmark_id: str, panel_id: str, variant: str) -> ResponseMatrix:
    path = matrix_path(root, benchmark_id, panel_id, variant)
    frame = pd.read_csv(path, index_col=0)
    metadata_file = matrix_metadata_path(root, benchmark_id, panel_id, variant)
    metadata = {}
    if metadata_file.exists():
        with metadata_file.open("r", encoding="utf-8") as handle:
            metadata = json.load(handle)
    return ResponseMatrix.from_dataframe(frame, metadata=metadata)
