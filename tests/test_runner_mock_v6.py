from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from valideval.execution.datasets import frozen_items_from_records
from valideval.execution.packaging import (
    PackageValidationError,
    create_deterministic_run_zip,
    validate_zip_archive,
)
from valideval.execution.runner import run_from_config

ROOT = Path(__file__).resolve().parents[1]


def _mock_config(tmp_path: Path) -> Path:
    payload = yaml.safe_load((ROOT / "configs/runs/mmlu_s1_v6.yaml").read_text(encoding="utf-8"))
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    payload.update(
        {
            "run_id": "mock-production-path-v6",
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
    path = tmp_path / "mock_run.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def _items():
    contract = yaml.safe_load(
        (ROOT / "configs/benchmarks/mmlu_s1_v6.yaml").read_text(encoding="utf-8")
    )
    records = [
        {
            "subject": f"fixture_subject_{index:02d}",
            "question": f"NON_EVIDENCE_FIXTURE question {index}?",
            "choices": ["one", "two", "three", "four"],
            "answer": index % 4,
        }
        for index in range(50)
    ]
    return frozen_items_from_records(contract, records)


def test_mocked_production_runner_resume_validate_and_package(tmp_path: Path):
    config = _mock_config(tmp_path)
    output = tmp_path / "outputs"
    first = run_from_config(
        config,
        output_root=output,
        repository_root=ROOT,
        injected_items=_items(),
    )
    assert first["status"] == "RUN_COMPLETE"
    assert first["evidence_class"] == "NON_EVIDENCE_FIXTURE"
    assert first["row_count"] == 250
    validate_zip_archive(first["zip_path"])
    manifest = json.loads(
        (Path(first["run_dir"]) / "run_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["engineering_only"] is True
    assert manifest["execution_mode"] == "smoke"
    assert manifest["scheduler"]["worker_count"] == 2

    resumed = run_from_config(
        config,
        mode_override="resume",
        output_root=output,
        repository_root=ROOT,
        injected_items=_items(),
    )
    assert resumed["status"] == "RUN_COMPLETE"
    resumed_manifest = json.loads(
        (Path(resumed["run_dir"]) / "run_manifest.json").read_text(encoding="utf-8")
    )
    assert resumed_manifest["scheduler"]["resumed_count"] == 5

    validated = run_from_config(
        config,
        mode_override="validate_only",
        output_root=output,
        repository_root=ROOT,
    )
    assert validated["status"] == "RUN_COMPLETE"

    packaged = run_from_config(
        config,
        mode_override="package_only",
        output_root=output,
        repository_root=ROOT,
    )
    assert packaged["status"] == "RUN_COMPLETE"

    secret_path = Path(first["run_dir"]) / ".env"
    secret_path.write_text("HF_TOKEN=NON_EVIDENCE_FIXTURE\n", encoding="utf-8")
    with pytest.raises(PackageValidationError, match="forbidden|hidden"):
        create_deterministic_run_zip(first["run_dir"], tmp_path / "unsafe.zip")
