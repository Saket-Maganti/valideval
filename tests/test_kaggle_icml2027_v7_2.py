from __future__ import annotations

import json
from pathlib import Path

import pytest

from valideval.execution.notebook_v7_2 import (
    _validate_v7_2_hardware,
    _verify_huggingface_access,
    run_notebook_stage_v7_2,
)
from valideval.planning.runtime_recalibration_v7_2 import recalibrate_study_c_after_s1

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [
    "00_v7_2_t4x2_preflight.ipynb",
    "01_v7_2_s1_mmlu.ipynb",
    "02_v7_2_s1_gsm8k.ipynb",
    "03_v7_2_s1_bbh.ipynb",
    "04_v7_2_s1_validate_package.ipynb",
]


def test_canonical_v7_2_notebooks_compile_and_delegate_to_package_code() -> None:
    paths = sorted((ROOT / "kaggle_icml2027").glob("*.ipynb"))
    assert [path.name for path in paths] == EXPECTED
    for path in paths:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        assert notebook["metadata"]["valideval"]["schema_version"] == "7.2"
        assert (
            notebook["metadata"]["valideval"]["required_source_ref"]
            == "valideval-v7.2.1-icml2027-kaggle-s1-ready"
        )
        code = "\n".join(
            "".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"
        )
        compile(code, str(path), "exec")
        assert "run_notebook_stage_v7_2" in code
        assert "AutoModelForCausalLM" not in code
        assert "model.generate(" not in code
        assert "accept-s1-v7-2-1" in code
        assert "imported/v7_2_1/s1" in code
        assert "requirements-kaggle-t4x2-v7-2-1.lock" in code


def test_notebook_fixture_preflight_validates_all_production_identities(tmp_path: Path) -> None:
    result = run_notebook_stage_v7_2(
        "preflight",
        mode="fixture",
        output_root=tmp_path,
        repository_root=ROOT,
    )
    assert result["status"] == "V7_2_PRODUCTION_CONFIGS_VALIDATED_FIXTURE_BOUNDARY"
    assert result["evidence_class"] == "NON_EVIDENCE_FIXTURE"
    assert {row["benchmark_id"] for row in result["configs"]} == {
        "mmlu",
        "gsm8k",
        "bbh",
    }
    assert all(len(row["model_revisions"]) == 5 for row in result["configs"])


def test_v7_2_hardware_requires_exactly_two_t4s() -> None:
    result = _validate_v7_2_hardware(["Tesla T4", "NVIDIA T4"], 16 * 1024**3)
    assert result["gpu_count"] == 2
    with pytest.raises(RuntimeError, match="exactly two T4"):
        _validate_v7_2_hardware(["NVIDIA A100", "NVIDIA A100"], 80 * 1024**3)
    with pytest.raises(RuntimeError, match="12 GiB RAM"):
        _validate_v7_2_hardware(["Tesla T4", "Tesla T4"], 8 * 1024**3)


def test_v7_2_access_preflight_resolves_every_exact_revision() -> None:
    class FakeApi:
        def __init__(self) -> None:
            self.models: list[tuple[str, str]] = []
            self.datasets: list[tuple[str, str]] = []

        def model_info(self, *, repo_id: str, revision: str) -> None:
            self.models.append((repo_id, revision))

        def dataset_info(self, *, repo_id: str, revision: str) -> None:
            self.datasets.append((repo_id, revision))

    api = FakeApi()
    result = _verify_huggingface_access(ROOT, api)
    assert len(api.models) == 5
    assert len(api.datasets) == 3
    assert result["internet"] == "PASS"


def test_post_s1_recalibration_rejects_fixture_receipt(tmp_path: Path) -> None:
    (tmp_path / "s1_acceptance_receipt_v7_2.json").write_text(
        json.dumps(
            {
                "status": "S1_V7_2_ACCEPTED",
                "fixture_only": True,
                "benchmarks": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="NON_EVIDENCE_FIXTURE"):
        recalibrate_study_c_after_s1(tmp_path, tmp_path / "recalibrated.json")
