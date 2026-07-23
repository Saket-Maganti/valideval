from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from valideval.execution.notebook import run_notebook_stage

ROOT = Path(__file__).resolve().parents[1]


def _mock_config(tmp_path: Path) -> Path:
    payload = yaml.safe_load((ROOT / "configs/runs/mmlu_s1_v6.yaml").read_text())
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    payload.update(
        {
            "run_id": "notebook-mocked-production-v6",
            "evidence_class": "NON_EVIDENCE_FIXTURE",
            "required_source_ref": "HEAD",
            "expected_source_commit": source_commit,
        }
    )
    payload["execution"].update(
        {
            "backend": "mock",
            "use_processes": False,
            "minimum_free_disk_gb": 0,
            "model_download_margin_gb": 0,
        }
    )
    path = tmp_path / "mock_notebook_run.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def test_notebook_mocked_production_resume_validate_and_package(
    tmp_path: Path, monkeypatch
) -> None:
    config = _mock_config(tmp_path)
    output = tmp_path / "outputs"
    monkeypatch.setenv("VALIDEVAL_EXECUTION_CONFIG", str(config))
    monkeypatch.setenv("VALIDEVAL_MOCKED_PRODUCTION_ITEMS", "1")

    first = run_notebook_stage("mmlu", mode="smoke", output_root=output)
    assert first["status"] == "RUN_COMPLETE"
    assert first["evidence_class"] == "NON_EVIDENCE_FIXTURE"

    resumed = run_notebook_stage("mmlu", mode="resume", output_root=output)
    assert resumed["status"] == "RUN_COMPLETE"

    validated = run_notebook_stage("mmlu", mode="validate_only", output_root=output)
    assert validated["status"] == "RUN_COMPLETE"

    packaged = run_notebook_stage("mmlu", mode="package_only", output_root=output)
    assert packaged["status"] == "RUN_COMPLETE"


def test_mocked_item_injection_is_rejected_for_real_backend(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(
        "VALIDEVAL_EXECUTION_CONFIG",
        str(ROOT / "configs/runs/mmlu_s1_v6.yaml"),
    )
    monkeypatch.setenv("VALIDEVAL_MOCKED_PRODUCTION_ITEMS", "1")
    try:
        run_notebook_stage("mmlu", mode="smoke", output_root=tmp_path)
    except ValueError as exc:
        assert "mock backend" in str(exc)
    else:  # pragma: no cover - fail-closed assertion
        raise AssertionError("real backend accepted mocked production items")
