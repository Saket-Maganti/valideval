from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from valideval.kaggle_v4 import import_kaggle_outputs


def _write_zip(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps({"benchmark": rows[0].get("benchmark", "gsm8k")}),
        )
        archive.writestr(
            "predictions.jsonl",
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        )
        archive.writestr("run_log.txt", "synthetic test fixture\n")


def _rows(benchmark: str = "gsm8k") -> list[dict[str, object]]:
    rows = []
    for model_id in ["m1", "m2"]:
        for item_id, correct in [("i1", True), ("i2", False), ("i3", model_id == "m2")]:
            rows.append(
                {
                    "benchmark": benchmark,
                    "subset": "default",
                    "model_id": model_id,
                    "item_id": item_id,
                    "prediction": "42" if correct else "41",
                    "gold": "42",
                    "correct": correct,
                    "metadata": {"fixture_only": True},
                }
            )
    return rows


def test_importer_blocks_when_no_zips_exist(tmp_path: Path) -> None:
    payload = import_kaggle_outputs(
        input_dir=tmp_path / "kaggle_outputs",
        output_root=tmp_path / "data" / "external" / "kaggle_imported",
        cache_root=tmp_path / "cache",
        results_root=tmp_path / "results",
        strict=True,
    )

    assert payload["status"] == "blocked_no_zips"
    assert (tmp_path / "results" / "kaggle_import_v4" / "blocked_report.md").exists()


def test_importer_hashes_extracts_normalizes_and_builds_matrix(tmp_path: Path) -> None:
    zip_path = tmp_path / "kaggle_outputs" / "gsm8k" / "outputs.zip"
    _write_zip(zip_path, _rows("gsm8k"))

    payload = import_kaggle_outputs(
        input_dir=tmp_path / "kaggle_outputs",
        output_root=tmp_path / "data" / "external" / "kaggle_imported",
        cache_root=tmp_path / "cache",
        results_root=tmp_path / "results",
        strict=True,
    )

    assert payload["status"] == "ok"
    record = payload["imports"][0]
    assert record["zip_sha256"]
    assert Path(record["import_dir"]).exists()
    assert Path(record["normalized_predictions"]).exists()
    assert Path(record["matrix"]).exists()
    frame = pd.read_csv(tmp_path / "cache" / "gsm8k" / "wide" / "matrix.csv", index_col=0)
    assert frame.shape == (2, 3)
    assert record["schema_validation"]["correctness_field_checked"] is True


def test_importer_never_overwrites_old_import_dirs(tmp_path: Path) -> None:
    zip_path = tmp_path / "kaggle_outputs" / "bbh" / "outputs.zip"
    _write_zip(zip_path, _rows("bbh"))

    first = import_kaggle_outputs(
        input_dir=tmp_path / "kaggle_outputs",
        output_root=tmp_path / "imports",
        cache_root=tmp_path / "cache",
        results_root=tmp_path / "results",
        strict=True,
    )
    second = import_kaggle_outputs(
        input_dir=tmp_path / "kaggle_outputs",
        output_root=tmp_path / "imports",
        cache_root=tmp_path / "cache",
        results_root=tmp_path / "results",
        strict=True,
    )

    assert first["imports"][0]["import_dir"] != second["imports"][0]["import_dir"]
    assert Path(first["imports"][0]["import_dir"]).exists()
    assert Path(second["imports"][0]["import_dir"]).exists()


def test_importer_fails_loudly_on_schema_mismatch(tmp_path: Path) -> None:
    bad_rows = _rows("gsm8k")
    bad_rows[0].pop("correct")
    _write_zip(tmp_path / "kaggle_outputs" / "gsm8k" / "bad.zip", bad_rows)

    with pytest.raises(ValueError, match="missing required field correct"):
        import_kaggle_outputs(
            input_dir=tmp_path / "kaggle_outputs",
            output_root=tmp_path / "imports",
            cache_root=tmp_path / "cache",
            results_root=tmp_path / "results",
            strict=True,
        )
