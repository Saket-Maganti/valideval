from __future__ import annotations

import json
from pathlib import Path

from valideval.cli import build_parser, main
from valideval.execution.notebook import package_fixture_runs
from valideval.importers.kaggle_v5 import import_kaggle_archive_v5

V5_COMMANDS = (
    "validate-run",
    "import-kaggle",
    "post-import",
    "cross-benchmark",
    "build-evidence-ledger",
    "build-paper-assets",
    "build-release",
)


def test_v5_commands_are_discoverable_and_old_commands_remain() -> None:
    help_text = build_parser().format_help()
    for command in (*V5_COMMANDS, "doctor", "import-kaggle-outputs"):
        assert command in help_text


def test_validate_run_v5_fails_closed_only_in_strict_mode(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    assert main(["validate-run", str(missing)]) == 0
    assert main(["validate-run", str(missing), "--strict"]) == 2


def test_post_import_v5_routes_valid_receipt_without_running_retired_ablation(
    tmp_path: Path,
) -> None:
    package = package_fixture_runs(tmp_path / "notebook")
    imported = import_kaggle_archive_v5(
        package["packages"][0]["zip_path"],
        output_root=tmp_path / "imports",
    )
    receipt = Path(imported["import_dir"]) / "import_receipt_v5.json"
    output = tmp_path / "route"
    assert (
        main(
            [
                "post-import",
                "--receipt",
                str(receipt),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    payload = json.loads((output / "post_import_plan_v5.json").read_text(encoding="utf-8"))
    assert payload["status"] == "plan_ready"
    assert payload["dry_run"] is True
    assert "diagnostic_family_ablation" not in " ".join(payload["recommended_commands"])
    assert "post-import-analysis" not in " ".join(payload["recommended_commands"])


def test_cross_benchmark_v5_dry_run_records_missing_inputs(tmp_path: Path) -> None:
    output = tmp_path / "cross"
    assert main(["cross-benchmark", "--output", str(output)]) == 0
    payload = json.loads((output / "analysis_manifest_v5.json").read_text(encoding="utf-8"))
    assert payload["status"] == "blocked"
    assert payload["transfer_conclusion"] == "BLOCKED"
    assert set(payload["missing_benchmarks"]) == {"mmlu", "gsm8k", "bbh"}
