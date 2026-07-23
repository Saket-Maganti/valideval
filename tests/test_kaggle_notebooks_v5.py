from __future__ import annotations

import ast
import json
from pathlib import Path

from valideval.execution.notebook import EXECUTION_MODES

NOTEBOOK_ROOT = Path(__file__).parents[1] / "kaggle_max_ceiling"
EXPECTED = [
    "00_valideval_t4x2_environment_and_preflight.ipynb",
    "01_valideval_common_panel_mmlu_t4x2.ipynb",
    "02_valideval_common_panel_gsm8k_t4x2.ipynb",
    "03_valideval_common_panel_bbh_t4x2.ipynb",
    "04_valideval_t4x2_merge_validate_package.ipynb",
    "05_valideval_optional_robustness_runs_t4x2.ipynb",
]


def test_canonical_notebook_suite_is_valid_and_compilable() -> None:
    assert sorted(path.name for path in NOTEBOOK_ROOT.glob("*.ipynb")) == EXPECTED
    for name in EXPECTED:
        payload = json.loads((NOTEBOOK_ROOT / name).read_text(encoding="utf-8"))
        assert payload["nbformat"] == 4
        assert payload["metadata"]["valideval"]["execution_modes"] == list(EXECUTION_MODES)
        assert payload["metadata"]["valideval"]["fixture_evidence_state"] == "NON_EVIDENCE_FIXTURE"
        code = "\n".join(
            "".join(cell["source"]) for cell in payload["cells"] if cell["cell_type"] == "code"
        )
        ast.parse(code, filename=name)
        assert "trust_remote_code=True" not in code
        assert 'device_map="auto"' not in code
        assert "CUDA_VISIBLE_DEVICES" not in code
        assert "TOKEN=" not in code
