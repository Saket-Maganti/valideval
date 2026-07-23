from __future__ import annotations

import json
from pathlib import Path

from valideval.cli import main


def test_power_materiality_preflight_runs_no_simulations(tmp_path: Path) -> None:
    output = tmp_path / "power.json"

    assert (
        main(
            [
                "power-materiality-preflight",
                "--config",
                "configs/statistics/power_materiality_mmlu.yaml",
                "--output",
                str(output),
                "--dry-run",
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == "dry_run_only"
    assert payload["simulations_run"] is False
    assert payload["metrics_computed"] is False
    assert "minimum_detectable_effect" in payload["future_metrics"]
