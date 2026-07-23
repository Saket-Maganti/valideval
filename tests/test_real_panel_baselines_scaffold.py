from __future__ import annotations

import json
from pathlib import Path

from valideval.cli import main


def test_real_panel_baselines_preflight_lists_required_baselines(tmp_path: Path) -> None:
    output = tmp_path / "baselines.json"

    assert (
        main(
            [
                "real-panel-baselines-preflight",
                "--config",
                "configs/real_panel/baselines_mmlu.yaml",
                "--output",
                str(output),
                "--dry-run",
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    names = {row["name"] for row in payload["baseline_specs"]}
    assert payload["mode"] == "dry_run_only"
    assert "accuracy_only_ranking" in names
    assert "mmlu_redux_external_label" in names
    assert payload["evidence_state"] == "RESULT_REQUIRED"
