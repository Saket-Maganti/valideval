from __future__ import annotations

import json
from pathlib import Path

from valideval.cli import main


def _write_real_panel_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    matrix = tmp_path / "matrix.csv"
    matrix.write_text("item_id,model_a,model_b\nmmlu_001,1,0\n", encoding="utf-8")
    predictions = tmp_path / "predictions.jsonl"
    predictions.write_text(
        '{"item_id": "mmlu_001", "model_id": "model_a", "correct": true}\n',
        encoding="utf-8",
    )
    redux = tmp_path / "mmlu_redux.jsonl"
    redux.write_text(
        '{"item_id": "mmlu_001", "stable_hash": "abc123", "issue_type": "label_error"}\n',
        encoding="utf-8",
    )
    return matrix, predictions, redux


def test_real_panel_ranking_audit_dry_run_writes_manifest(tmp_path: Path) -> None:
    matrix, predictions, redux = _write_real_panel_inputs(tmp_path)
    output = tmp_path / "real_panel.json"

    assert (
        main(
            [
                "real-panel-ranking-audit",
                "--matrix",
                str(matrix),
                "--predictions",
                str(predictions),
                "--mmlu-redux",
                str(redux),
                "--output",
                str(output),
                "--dry-run",
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == "dry_run_only"
    assert payload["status"] == "dry_run_ready"
    assert payload["evidence_state"] == "RESULT_REQUIRED"
    assert (
        "accuracy_only_vs_validity_adjusted_ranking_disagreement"
        in payload["planned_finding_types"]
    )


def test_real_panel_audit_refuses_without_dry_run(tmp_path: Path) -> None:
    matrix, predictions, redux = _write_real_panel_inputs(tmp_path)

    assert (
        main(
            [
                "diagnostic-disagreement-audit",
                "--matrix",
                str(matrix),
                "--predictions",
                str(predictions),
                "--mmlu-redux",
                str(redux),
            ]
        )
        == 1
    )
