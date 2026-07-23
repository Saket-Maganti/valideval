from __future__ import annotations

import json
from pathlib import Path

from valideval.cli import main


def test_calibration_preflight_lists_future_metrics_without_computing(tmp_path: Path) -> None:
    output = tmp_path / "calibration.json"

    assert (
        main(
            [
                "calibration-preflight",
                "--config",
                "configs/calibration/mmlu_logprob_calibration.yaml",
                "--output",
                str(output),
                "--dry-run",
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == "dry_run_only"
    assert payload["metrics_computed"] is False
    assert payload["claim_state"] == "BLOCKED_UNTIL_LOGPROB_OUTPUTS_EXIST"
    assert "ECE" in payload["future_metrics"]


def test_calibration_preflight_blocks_malformed_logprob_schema(tmp_path: Path) -> None:
    logprobs = tmp_path / "bad_logprobs.json"
    logprobs.write_text('{"item_id": "mmlu_001", "logprob_selected": ', encoding="utf-8")
    config = tmp_path / "calibration.yaml"
    config.write_text(
        "\n".join(
            [
                "benchmark: mmlu",
                "claim_state: BLOCKED_UNTIL_LOGPROB_OUTPUTS_EXIST",
                f"logprob_input: {logprobs}",
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "calibration.json"

    assert (
        main(
            [
                "calibration-preflight",
                "--config",
                str(config),
                "--output",
                str(output),
                "--dry-run",
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked"
    assert payload["input_schema"]["schema_status"] == "blocked"
    assert payload["input_schema"]["parse_status"] == "parse_error"
    assert payload["metrics_computed"] is False
