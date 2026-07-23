from __future__ import annotations

import zipfile
from pathlib import Path

from valideval.importers.s1_v6 import (
    S1_SMOKE_REJECTED_DATA_INTEGRITY,
    S1_SMOKE_REQUIRES_RERUN,
    accept_s1_smoke_v6,
)

ROOT = Path(__file__).resolve().parents[1]


def test_s1_acceptance_requires_all_three_archives(tmp_path: Path) -> None:
    result = accept_s1_smoke_v6(tmp_path, repository_root=ROOT)
    assert result["status"] == S1_SMOKE_REQUIRES_RERUN
    assert len(result["problems"]) == 3


def test_s1_acceptance_rejects_duplicate_benchmark_archives(tmp_path: Path) -> None:
    for name in (
        "valideval_v6_s1_mmlu_first.zip",
        "valideval_v6_s1_mmlu_second.zip",
        "valideval_v6_s1_gsm8k_one.zip",
        "valideval_v6_s1_bbh_one.zip",
    ):
        with zipfile.ZipFile(tmp_path / name, "w"):
            pass
    result = accept_s1_smoke_v6(tmp_path, repository_root=ROOT)
    assert result["status"] == S1_SMOKE_REJECTED_DATA_INTEGRITY
    assert "multiple candidate archives for mmlu" in result["problems"]
