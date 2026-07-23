from __future__ import annotations

from pathlib import Path

from valideval.schemas import ResponseMatrix


def save_matrix_parquet(path: str | Path, matrix: ResponseMatrix) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        matrix.to_dataframe().to_parquet(destination)
    except Exception as exc:  # pragma: no cover - depends on optional pyarrow/fastparquet.
        raise RuntimeError("Parquet support requires the optional 'parquet' extra.") from exc
    return destination
