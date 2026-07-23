from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from valideval.kaggle_v4 import post_import_analysis


def _matrix(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(
        {
            "model_id": ["m1", "m2", "m3", "m4"],
            "math::i1": [1, 1, 0, 0],
            "math::i2": [1, 0, 0, 1],
            "logic::i3": [0, 1, 1, 0],
            "logic::i4": [1, 1, 1, 0],
        }
    )
    frame.to_csv(path, index=False)
    return path


def _predictions(path: Path) -> Path:
    rows = []
    for model_id in ["m1", "m2", "m3", "m4"]:
        for item_id in ["i1", "i2", "i3", "i4"]:
            rows.append(
                {
                    "benchmark": "gsm8k",
                    "subset": "math" if item_id in {"i1", "i2"} else "logic",
                    "model_id": model_id,
                    "item_id": item_id,
                    "prediction": "A",
                    "gold": "A",
                    "correct": True,
                }
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def test_post_import_analysis_dry_run_writes_manifest(tmp_path: Path) -> None:
    payload = post_import_analysis(
        benchmark="gsm8k",
        matrix=tmp_path / "missing.csv",
        predictions=None,
        output=tmp_path / "analysis",
        execute=False,
    )

    assert payload["status"] == "dry_run_only"
    assert "cross_benchmark_preparation_if_mmlu_exists" in payload["analyses_planned"]
    assert (tmp_path / "analysis" / "post_import_analysis_manifest.json").exists()


def test_post_import_analysis_executes_router_on_tiny_matrix(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    _matrix(cache_root / "mmlu" / "wide" / "matrix.csv")
    matrix = _matrix(tmp_path / "cache" / "gsm8k" / "wide" / "matrix.csv")
    predictions = _predictions(tmp_path / "cache" / "gsm8k" / "wide" / "predictions.jsonl")

    payload = post_import_analysis(
        benchmark="gsm8k",
        matrix=matrix,
        predictions=predictions,
        output=tmp_path / "results" / "gsm8k",
        cache_root=cache_root,
        results_root=tmp_path / "results",
        execute=True,
        bootstrap=5,
    )

    assert payload["status"] == "ok"
    assert payload["cross_benchmark_prepared"]["status"] == "prepared"
    assert (tmp_path / "results" / "gsm8k" / "irt_proxy" / "fit_summary.json").exists()
    assert (tmp_path / "results" / "gsm8k" / "diagnostic_family_ablation.csv").exists()
