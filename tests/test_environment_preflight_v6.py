from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from valideval.execution.config import (
    RunConfigV6,
    V6ConfigurationError,
    load_run_config,
    resolve_source_commit,
)
from valideval.execution.models import load_panel_config
from valideval.execution.runner import (
    InsufficientDiskError,
    InsufficientGpuError,
    environment_preflight,
)

ROOT = Path(__file__).resolve().parents[1]


def _config(*, gpu_ids: list[str], required: int, allow_one: bool = False) -> RunConfigV6:
    original = load_run_config(ROOT / "configs/runs/mmlu_s1_v6.yaml", repository_root=ROOT)
    payload = original.model_dump(mode="json")
    payload.update(
        {
            "evidence_class": "NON_EVIDENCE_FIXTURE",
            "required_source_ref": "HEAD",
            "expected_source_commit": None,
        }
    )
    payload["execution"].update(
        {
            "backend": "mock",
            "gpu_ids": gpu_ids,
            "required_gpu_count": required,
            "allow_single_gpu_fallback": allow_one,
            "minimum_free_disk_gb": 0,
            "model_download_margin_gb": 0,
        }
    )
    return RunConfigV6.model_validate(payload)


def test_zero_one_and_two_gpu_preflight_contract(tmp_path: Path) -> None:
    panel = load_panel_config(ROOT / "configs/panels/s1_smoke_exact_v6.yaml")
    with pytest.raises(InsufficientGpuError):
        environment_preflight(_config(gpu_ids=[], required=2), panel, ROOT, tmp_path)
    with pytest.raises(InsufficientGpuError):
        environment_preflight(_config(gpu_ids=["0"], required=2), panel, ROOT, tmp_path)
    one = environment_preflight(
        _config(gpu_ids=["0"], required=2, allow_one=True), panel, ROOT, tmp_path
    )
    assert one["visible_gpu_count"] == 1
    two = environment_preflight(_config(gpu_ids=["0", "1"], required=2), panel, ROOT, tmp_path)
    assert two["visible_gpu_count"] == 2


def test_insufficient_disk_fails_before_execution(tmp_path: Path, monkeypatch) -> None:
    panel = load_panel_config(ROOT / "configs/panels/s1_smoke_exact_v6.yaml")
    config = _config(gpu_ids=[], required=0)
    payload = config.model_dump(mode="json")
    payload["execution"]["minimum_free_disk_gb"] = 1
    config = RunConfigV6.model_validate(payload)
    monkeypatch.setattr(
        "valideval.execution.runner.shutil.disk_usage",
        lambda _: shutil._ntuple_diskusage(total=1024, used=1024, free=0),
    )
    with pytest.raises(InsufficientDiskError):
        environment_preflight(config, panel, ROOT, tmp_path)


def test_missing_production_dependencies_fail_closed(tmp_path: Path, monkeypatch) -> None:
    panel = load_panel_config(ROOT / "configs/panels/s1_smoke_exact_v6.yaml")
    config = load_run_config(ROOT / "configs/runs/mmlu_s1_v6.yaml", repository_root=ROOT)
    config = config.model_copy(
        update={"required_source_ref": "HEAD", "expected_source_commit": None}
    )
    monkeypatch.setattr("valideval.execution.runner._dependency_versions", lambda: {})
    with pytest.raises(V6ConfigurationError, match="missing production dependencies"):
        environment_preflight(config, panel, ROOT, tmp_path)


def test_wrong_expected_commit_is_rejected() -> None:
    with pytest.raises(V6ConfigurationError, match="source commit mismatch"):
        resolve_source_commit(
            ROOT,
            required_source_ref="HEAD",
            expected_source_commit="0" * 40,
            allow_environment=False,
        )
