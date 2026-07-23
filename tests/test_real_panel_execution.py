from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from valideval.cli import main


def _write_matrix(tmp_path: Path) -> Path:
    matrix = tmp_path / "matrix.csv"
    matrix.write_text(
        "\n".join(
            [
                "model_id,math::item_1,math::item_2,history::item_3,history::item_4",
                "model_a,1,1,1,0",
                "model_b,1,0,0,0",
                "model_c,0,1,1,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return matrix


def _write_predictions(tmp_path: Path) -> Path:
    predictions = tmp_path / "predictions.jsonl"
    predictions.write_text(
        '{"item_id": "item_1", "model_id": "model_a", "correct": true}\n',
        encoding="utf-8",
    )
    return predictions


def _write_irt(tmp_path: Path) -> Path:
    irt = tmp_path / "irt"
    irt.mkdir()
    pd.DataFrame(
        [
            {
                "item_id": "math::item_1",
                "discrimination_proxy": 0.4,
                "information_proxy": 0.2,
                "negative_discrimination": False,
                "near_zero_discrimination": False,
                "too_easy": False,
                "too_hard": False,
            },
            {
                "item_id": "math::item_2",
                "discrimination_proxy": -0.1,
                "information_proxy": 0.1,
                "negative_discrimination": True,
                "near_zero_discrimination": False,
                "too_easy": False,
                "too_hard": False,
            },
            {
                "item_id": "history::item_3",
                "discrimination_proxy": 0.0,
                "information_proxy": 0.0,
                "negative_discrimination": False,
                "near_zero_discrimination": True,
                "too_easy": False,
                "too_hard": False,
            },
            {
                "item_id": "history::item_4",
                "discrimination_proxy": 0.3,
                "information_proxy": 0.2,
                "negative_discrimination": False,
                "near_zero_discrimination": False,
                "too_easy": False,
                "too_hard": True,
            },
        ]
    ).to_csv(irt / "item_parameters.csv", index=False)
    return irt


def test_real_panel_execute_commands_write_sanitized_artifacts(tmp_path: Path) -> None:
    matrix = _write_matrix(tmp_path)
    predictions = _write_predictions(tmp_path)
    irt = _write_irt(tmp_path)

    assert (
        main(
            [
                "real-panel-ranking-audit",
                "--matrix",
                str(matrix),
                "--predictions",
                str(predictions),
                "--output",
                str(tmp_path / "ranking"),
                "--execute",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "ranking-disagreement",
                "--matrix",
                str(matrix),
                "--irt",
                str(irt),
                "--output",
                str(tmp_path / "disagreement"),
                "--bootstrap",
                "4",
                "--execute",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "real-panel-baselines",
                "--matrix",
                str(matrix),
                "--output",
                str(tmp_path / "baselines"),
                "--bootstrap",
                "4",
                "--execute",
            ]
        )
        == 0
    )

    ranking = json.loads((tmp_path / "ranking" / "real_panel_ranking_audit.json").read_text())
    disagreement = json.loads(
        (tmp_path / "disagreement" / "ranking_disagreement_summary.json").read_text()
    )
    baselines = json.loads((tmp_path / "baselines" / "baseline_summary.json").read_text())

    assert ranking["evidence_state"] == "ARTIFACT_BACKED_REAL_PANEL_ANALYSIS"
    assert disagreement["diagnostic_source_is_irt_proxy"] is True
    assert baselines["bootstrap"]["bootstrap_iterations_per_resampling_baseline"] == 4
    assert (tmp_path / "disagreement" / "materiality_thresholds.csv").exists()
