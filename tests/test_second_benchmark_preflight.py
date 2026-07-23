from __future__ import annotations

import json
from pathlib import Path

from valideval.cli import main


def test_second_benchmark_preflight_is_build_only(tmp_path: Path) -> None:
    output = tmp_path / "benchmark.json"

    assert (
        main(
            [
                "benchmark-preflight",
                "--config",
                "configs/benchmarks/gsm8k_audit.yaml",
                "--output",
                str(output),
                "--dry-run",
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == "dry_run_only"
    assert payload["benchmark_id"] == "gsm8k"
    assert payload["download_run"] is False
    assert payload["evaluation_run"] is False
    assert payload["claim_state"] == "RESULT_REQUIRED"


def test_second_benchmark_preflight_blocks_malformed_fixture_schema(tmp_path: Path) -> None:
    fixture = tmp_path / "bad_gsm8k.jsonl"
    fixture.write_text('{"item_id": "gsm8k_001", "question": ', encoding="utf-8")
    config = tmp_path / "benchmark.yaml"
    config.write_text(
        "\n".join(
            [
                "benchmark_id: gsm8k",
                "claim_state: RESULT_REQUIRED",
                f"fixture_path: {fixture}",
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "benchmark.json"

    assert (
        main(
            [
                "benchmark-preflight",
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
    assert payload["fixture_schema"]["schema_status"] == "blocked"
    assert payload["fixture_schema"]["parse_status"] == "parse_error"
