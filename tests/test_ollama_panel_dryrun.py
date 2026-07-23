from __future__ import annotations

import json
from pathlib import Path

from valideval.cli import main


def test_ollama_panel_preflight_does_not_contact_server(tmp_path: Path) -> None:
    output = tmp_path / "panel.json"

    assert (
        main(
            [
                "panel-preflight",
                "--config",
                "configs/panels/ollama_local_small.yaml",
                "--output",
                str(output),
                "--dry-run",
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == "dry_run_only"
    assert payload["server_contacted"] is False
    assert payload["inference_run"] is False
    assert payload["planned_models"]
