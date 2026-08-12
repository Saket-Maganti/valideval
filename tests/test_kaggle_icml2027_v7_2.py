from __future__ import annotations

import json
from pathlib import Path

import pytest

from valideval.execution.notebook_v7_2 import run_notebook_stage_v7_2
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
            == "valideval-v7.2-icml2027-kaggle-s1-ready"
        )
        code = "\n".join(
            "".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"
        )
        compile(code, str(path), "exec")
        assert "run_notebook_stage_v7_2" in code
        assert "AutoModelForCausalLM" not in code
        assert "model.generate(" not in code
        assert "accept-s1-v7-2" in code


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
