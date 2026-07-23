from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from valideval.diagnostics.panel_validity import (
    evaluate_panel_validity,
    write_panel_validity_report,
)


def test_minimum_matrix_adequacy_blocks_all_chance_panel():
    frame = pd.DataFrame(
        np.full((10, 12), 0.25),
        index=[f"m{idx}" for idx in range(10)],
        columns=[f"i{idx}" for idx in range(12)],
    )
    payload = evaluate_panel_validity(frame, chance=0.25, min_models=8, min_items=10)
    assert payload["status"] == "blocked"
    assert "ability_spread_too_narrow" in payload["blockers"]


def test_minimum_matrix_adequacy_pass_is_not_psychometric_validation(tmp_path: Path):
    rows = []
    for model_index in range(32):
        ability = model_index / 31
        rows.append([1.0 if ability > item_index / 24 else 0.0 for item_index in range(24)])
    frame = pd.DataFrame(
        rows,
        index=[f"m{idx}" for idx in range(32)],
        columns=[f"i{idx}" for idx in range(24)],
    )
    matrix = tmp_path / "matrix.csv"
    frame.to_csv(matrix)
    payload = write_panel_validity_report(matrix, tmp_path / "panel", min_models=30, min_items=20)
    assert payload["status"] == "pass"
    assert payload["diagnostic_name"] == "minimum_matrix_adequacy"
    assert payload["psychometric_validity_established"] is False
    assert "does not validate psychometric assumptions" in payload["interpretation"]
    assert (tmp_path / "panel" / "panel_validity.md").exists()
