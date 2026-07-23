from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from valideval.psychometrics.irt_2pl import fit_irt_from_matrix


def test_fit_irt_writes_proxy_artifacts(tmp_path: Path):
    rows = []
    for model_index in range(12):
        ability = model_index / 11
        rows.append([1.0 if ability > item_index / 10 else 0.0 for item_index in range(10)])
    matrix = tmp_path / "matrix.csv"
    pd.DataFrame(
        np.array(rows),
        index=[f"m{idx}" for idx in range(12)],
        columns=[f"i{idx}" for idx in range(10)],
    ).to_csv(matrix)

    payload = fit_irt_from_matrix(matrix, tmp_path / "irt", min_models=8, min_items=8)
    assert payload["estimation_layers"]["proxy"]
    assert (tmp_path / "irt" / "item_parameters.csv").exists()
    assert (tmp_path / "irt" / "flags.jsonl").exists()
