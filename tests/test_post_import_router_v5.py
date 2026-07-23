from __future__ import annotations

import json
from pathlib import Path

from valideval.execution.notebook import package_fixture_runs
from valideval.importers.kaggle_v5 import import_kaggle_archive_v5
from valideval.importers.post_import_v5 import (
    POST_IMPORT_BLOCKED_INVALID_RECEIPT,
    POST_IMPORT_FIXTURE_READY,
    ROUTE_BLOCKED,
    ROUTE_READY_FIXTURE,
    build_post_import_plan_v5,
)


def _import_fixture(tmp_path: Path, benchmark_index: int = 0) -> Path:
    package = package_fixture_runs(tmp_path / "notebook")
    zip_path = Path(package["packages"][benchmark_index]["zip_path"])
    receipt = import_kaggle_archive_v5(zip_path, output_root=tmp_path / "imports")
    return Path(receipt["import_dir"]) / "import_receipt_v5.json"


def _route(payload: dict[str, object], stage: str, benchmark: str = "mmlu") -> dict[str, object]:
    matches = [
        row
        for row in payload["routes"]
        if row["stage_id"] == stage and row["benchmark_id"] == benchmark
    ]
    assert len(matches) == 1
    return matches[0]


def test_fixture_receipt_routes_only_non_evidence_safe_stages(tmp_path: Path) -> None:
    receipt = _import_fixture(tmp_path)
    payload = build_post_import_plan_v5([receipt], output_dir=tmp_path / "plan")

    assert payload["final_verdict"] == POST_IMPORT_FIXTURE_READY
    assert _route(payload, "feasibility")["status"] == ROUTE_READY_FIXTURE
    assert _route(payload, "extraction_reliability")["status"] == ROUTE_READY_FIXTURE
    assert _route(payload, "coverage")["status"] == ROUTE_READY_FIXTURE
    assert _route(payload, "model_accuracy")["status"] == ROUTE_READY_FIXTURE
    assert _route(payload, "ranking_materiality")["status"] == ROUTE_BLOCKED
    assert _route(payload, "measurement_models")["status"] == ROUTE_BLOCKED
    assert (
        _route(payload, "paper_artifact_generation", benchmark="multi")["status"] == ROUTE_BLOCKED
    )
    assert (tmp_path / "plan" / "post_import_plan_v5.json").is_file()
    assert (tmp_path / "plan" / "post_import_plan_v5.md").is_file()


def test_tampered_receipt_blocks_every_route(tmp_path: Path) -> None:
    receipt = _import_fixture(tmp_path)
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["run_id"] = "tampered-run-id"
    receipt.write_text(json.dumps(payload), encoding="utf-8")

    result = build_post_import_plan_v5([receipt], output_dir=tmp_path / "blocked")

    assert result["final_verdict"] == POST_IMPORT_BLOCKED_INVALID_RECEIPT
    assert result["routes"] == []
    assert result["recommended_commands"] == []
    assert "run_id" in result["invalid_receipts"][0]["error"]


def test_low_extraction_and_item_coverage_block_dependents(tmp_path: Path) -> None:
    receipt = _import_fixture(tmp_path)
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["prediction_summary"]["extraction_reliability"] = 0.50
    payload["prediction_summary"]["usable_item_count"] = 2
    payload["cross_benchmark_eligibility"]["extraction_reliability"] = 0.50
    payload["cross_benchmark_eligibility"]["usable_items"] = 2
    receipt.write_text(json.dumps(payload), encoding="utf-8")

    result = build_post_import_plan_v5([receipt], output_dir=tmp_path / "plan")

    assert _route(result, "extraction_reliability")["status"] == ROUTE_BLOCKED
    assert _route(result, "coverage")["status"] == ROUTE_BLOCKED
    assert _route(result, "model_accuracy")["status"] == ROUTE_BLOCKED
    assert _route(result, "subject_subtask_analysis")["status"] == ROUTE_BLOCKED
    assert _route(result, "model_accuracy")["recommended_command"] is None
    assert _route(result, "model_accuracy")["blocked_command"]


def test_multiple_fixture_receipts_fail_cross_science_gate_and_never_route_v4_ablation(
    tmp_path: Path,
) -> None:
    package = package_fixture_runs(tmp_path / "notebook")
    receipts: list[Path] = []
    for row in package["packages"]:
        imported = import_kaggle_archive_v5(
            row["zip_path"],
            output_root=tmp_path / "imports",
        )
        receipts.append(Path(imported["import_dir"]) / "import_receipt_v5.json")

    result = build_post_import_plan_v5(receipts, output_dir=tmp_path / "plan")
    cross = _route(result, "cross_benchmark_eligibility", benchmark="multi")
    serialized = json.dumps(result).casefold()

    assert cross["status"] == ROUTE_BLOCKED
    assert cross["gate_status"] == "CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY"
    assert "v4_diagnostic_family_ablation" in serialized
    assert "post-import-analysis" not in serialized
    assert "diagnostic_family_ablation" not in " ".join(result["recommended_commands"])
