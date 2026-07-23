from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from valideval.importers.leaderboard_details import import_published_details
from valideval.importers.lm_eval_details import import_lm_eval_samples
from valideval.importers.wide_matrix import build_matrix_from_wide_predictions
from valideval.io.jsonl import read_jsonl


def test_lm_eval_directory_import_discards_text_by_default(tmp_path: Path):
    output = tmp_path / "predictions.jsonl"
    summary = import_published_details(
        "tests/fixtures/lm_eval_samples",
        benchmark="mmlu",
        detail_format="lm_eval_dir",
        output_path=output,
        mapping_report=tmp_path / "mapping.md",
    )

    assert summary["status"] == "ok"
    assert summary["rows_written"] == 4
    assert summary["model_count"] == 2
    assert "mmlu_high_school_biology" in summary["subsets"]
    text = output.read_text(encoding="utf-8")
    assert "PARSER TEST ONLY" not in text
    rows = list(read_jsonl(output))
    assert {row["prediction"] for row in rows} == {"A", "B", "C"}
    assert {row["gold"] for row in rows} == {"A", "C"}

    matrix_path = tmp_path / "matrix.csv"
    matrix = build_matrix_from_wide_predictions(output, matrix_path)
    frame = pd.read_csv(matrix_path, index_col=0)
    assert matrix["n_models"] == 2
    assert matrix["n_items"] == 2
    assert list(frame.index) == ["parser_only_model_a", "parser_only_model_b"]


def test_lm_eval_import_reports_missing_gold(tmp_path: Path):
    bad = tmp_path / "samples_mmlu_bad.jsonl"
    bad.write_text('{"doc_id": 0, "filtered_resps": ["A"], "acc": 1.0}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="missing required field: gold"):
        import_lm_eval_samples(
            bad,
            benchmark="mmlu",
            output_path=tmp_path / "predictions.jsonl",
            model_id="parser_only_model",
        )


def test_lm_eval_mmlu_loglikelihood_samples_map_to_choice_letters(tmp_path: Path):
    root = tmp_path / "lm_eval_output"
    model_dir = root / "Qwen__Qwen2.5-0.5B-Instruct"
    model_dir.mkdir(parents=True)
    (model_dir / "results_2026-06-12T00-00-00.json").write_text(
        '{"model_name":"Qwen/Qwen2.5-0.5B-Instruct","config":{"model_args":{"pretrained":"Qwen/Qwen2.5-0.5B-Instruct"}}}',
        encoding="utf-8",
    )
    samples = model_dir / "samples_mmlu_high_school_biology_2026-06-12T00-00-00.jsonl"
    samples.write_text(
        "\n".join(
            [
                '{"doc_id":0,"doc":{"question":"PARSER TEST ONLY"},"target":"0","filtered_resps":[["-3.0","False"],["-0.5","True"],["-5.0","False"],["-8.0","False"]],"acc":0.0}',
                '{"doc_id":1,"doc":{"question":"PARSER TEST ONLY"},"target":"2","filtered_resps":[["-6.0","False"],["-7.0","False"],["-0.1","True"],["-3.0","False"]],"acc":1.0}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    output = tmp_path / "predictions.jsonl"
    summary = import_published_details(
        root,
        benchmark="mmlu",
        detail_format="lm_eval",
        output_path=output,
        mapping_report=tmp_path / "mapping.md",
    )
    rows = list(read_jsonl(output))

    assert summary["rows_written"] == 2
    assert summary["model_count"] == 1
    assert rows[0]["model_id"] == "Qwen/Qwen2.5-0.5B-Instruct"
    assert rows[0]["subset"] == "mmlu_high_school_biology"
    assert rows[0]["prediction"] == "B"
    assert rows[0]["gold"] == "A"
    assert rows[0]["correct"] is False
    assert rows[0]["metadata"]["prediction_index"] == 1
    assert rows[0]["metadata"]["gold_index"] == 0
    assert rows[1]["prediction"] == "C"
    assert rows[1]["gold"] == "C"
    assert "PARSER TEST ONLY" not in output.read_text(encoding="utf-8")
