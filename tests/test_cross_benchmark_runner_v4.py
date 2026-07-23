from __future__ import annotations

from pathlib import Path

import pandas as pd

from valideval.kaggle_v4 import cross_benchmark_analysis


def _write_matrix(path: Path, offset: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(
        {
            "model_id": ["Model A", "Model B", "Model C"],
            "default::i1": [1, 1 - offset, 0],
            "default::i2": [1, 0, offset],
            "alt::i3": [0, 1, 1],
        }
    )
    frame.to_csv(path, index=False)


def test_cross_benchmark_blocks_with_fewer_than_two_matrices(tmp_path: Path) -> None:
    _write_matrix(tmp_path / "cache" / "mmlu" / "wide" / "matrix.csv")

    payload = cross_benchmark_analysis(
        benchmarks=["mmlu", "gsm8k", "bbh"],
        cache_root=tmp_path / "cache",
        results_root=tmp_path / "results",
        output=tmp_path / "results" / "cross",
        execute=True,
    )

    assert payload["status"] == "blocked_need_second_matrix"
    assert payload["final_verdict"] == "CROSS_BENCHMARK_RUNNER_BLOCKED_NEED_SECOND_MATRIX"
    assert (tmp_path / "results" / "cross" / "blocked_report.md").exists()


def test_cross_benchmark_computes_overlap_and_correlations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_matrix(tmp_path / "cache" / "mmlu" / "wide" / "matrix.csv")
    _write_matrix(tmp_path / "cache" / "gsm8k" / "wide" / "matrix.csv", offset=1)

    payload = cross_benchmark_analysis(
        benchmarks=["mmlu", "gsm8k"],
        cache_root=tmp_path / "cache",
        results_root=tmp_path / "results",
        output=tmp_path / "results" / "cross",
        execute=True,
    )

    assert payload["status"] == "ok"
    assert payload["final_verdict"] == "CROSS_BENCHMARK_RUNNER_READY"
    assert payload["model_overlap"][0]["overlap_models"] == 3
    assert (tmp_path / "results" / "cross" / "ranking_correlations.csv").exists()
    assert (tmp_path / "results" / "cross" / "cross_benchmark_ranking_correlations.svg").exists()
