from __future__ import annotations

import json
from pathlib import Path

from valideval.cli import main


def test_mmlu_redux_alignment_preflight_reports_fields_not_text(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.jsonl"
    predictions.write_text(
        '{"item_id": "mmlu_001", "model_id": "model_a", "prediction": "A"}\n',
        encoding="utf-8",
    )
    redux = tmp_path / "redux.jsonl"
    redux.write_text(
        '{"item_id": "mmlu_001", "stable_hash": "abc123", "issue_type": "label_error"}\n',
        encoding="utf-8",
    )
    output = tmp_path / "alignment.json"

    assert (
        main(
            [
                "mmlu-redux-alignment-preflight",
                "--predictions",
                str(predictions),
                "--redux",
                str(redux),
                "--output",
                str(output),
                "--dry-run",
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "direct_or_hash_fields_present"
    assert payload["raw_text_exposed"] is False
    assert "observed_fields" in payload["predictions_schema"]
