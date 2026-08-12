from __future__ import annotations

from pathlib import Path

from valideval.execution.doctor_v7_2_1 import run_cpu_maxout_doctor

ROOT = Path(__file__).resolve().parents[1]


def test_cpu_doctor_is_explicit_about_tag_and_gpu_boundary() -> None:
    result = run_cpu_maxout_doctor(ROOT)
    checks = {row["name"]: row for row in result["checks"]}
    assert checks["source_coherence"]["status"] == "PASS"
    assert checks["s1_configs"]["status"] == "PASS"
    assert result["gpu_requested"] is False
    assert "scientific evidence" in result["claim_boundary"]
