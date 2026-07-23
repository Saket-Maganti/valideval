from __future__ import annotations

import json
from pathlib import Path

from valideval.io.jsonl import read_jsonl, write_jsonl
from valideval.validation.mmlu_redux_alignment import align_mmlu_redux


def test_direct_item_id_alignment(tmp_path: Path):
    predictions = tmp_path / "predictions.jsonl"
    redux = tmp_path / "redux.jsonl"
    output = tmp_path / "aligned.jsonl"
    report = tmp_path / "report.md"
    write_jsonl(
        predictions,
        [
            {
                "benchmark": "mmlu",
                "subset": "abstract_algebra",
                "item_id": "mmlu_abstract_algebra_id16",
                "model_id": "model/a",
                "correct": True,
            }
        ],
    )
    write_jsonl(
        redux,
        [
            {
                "benchmark": "mmlu_redux",
                "subset": "abstract_algebra",
                "item_id": "mmlu_abstract_algebra_id16",
                "issue_type": "mmlu_redux_flaw",
                "severity": "unknown",
                "source": "synthetic",
            }
        ],
    )

    summary = align_mmlu_redux(
        predictions_path=predictions,
        redux_path=redux,
        output_path=output,
        report_path=report,
    )

    rows = read_jsonl(output)
    assert summary["aligned_count"] == 1
    assert rows[0]["alignment_method"] == "direct_item_id"
    assert rows[0]["alignment_confidence"] == 1.0
    assert rows[0]["item_id"] == "mmlu_abstract_algebra_id16"


def test_subject_index_alignment_and_deterministic_order(tmp_path: Path):
    predictions = tmp_path / "predictions.jsonl"
    redux = tmp_path / "redux.jsonl"
    output = tmp_path / "aligned.jsonl"
    write_jsonl(
        predictions,
        [
            {"benchmark": "mmlu", "subset": "math", "item_id": "mmlu_math_id11"},
            {"benchmark": "mmlu", "subset": "math", "item_id": "mmlu_math_id10"},
            {"benchmark": "mmlu", "subset": "math", "item_id": "mmlu_math_id12"},
        ],
    )
    write_jsonl(
        redux,
        [
            {
                "benchmark": "mmlu_redux",
                "subset": "math",
                "item_id": "mmlu_redux2_math_0002",
                "issue_type": "mmlu_redux_flaw",
                "source": "synthetic",
                "metadata": {"source_row_index": 2, "mmlu_redux_error_type": "wrong_groundtruth"},
            },
            {
                "benchmark": "mmlu_redux",
                "subset": "math",
                "item_id": "mmlu_redux2_math_0000",
                "issue_type": "mmlu_redux_flaw",
                "source": "synthetic",
                "metadata": {"source_row_index": 0, "mmlu_redux_error_type": "no_correct_answer"},
            },
        ],
    )

    summary = align_mmlu_redux(
        predictions_path=predictions,
        redux_path=redux,
        output_path=output,
    )

    rows = read_jsonl(output)
    assert summary["alignment_method_counts"] == {"subject_numeric_index": 2}
    assert [row["source_issue_id"] for row in rows] == [
        "mmlu_redux2_math_0000",
        "mmlu_redux2_math_0002",
    ]
    assert [row["item_id"] for row in rows] == ["mmlu_math_id10", "mmlu_math_id12"]
    assert rows[0]["issue_type"] == "answer_error"
    assert rows[1]["issue_type"] == "label_error"


def test_unaligned_labels_are_marked(tmp_path: Path):
    predictions = tmp_path / "predictions.jsonl"
    redux = tmp_path / "redux.jsonl"
    output = tmp_path / "aligned.jsonl"
    write_jsonl(predictions, [{"benchmark": "mmlu", "subset": "math", "item_id": "mmlu_math_id1"}])
    write_jsonl(
        redux,
        [
            {
                "benchmark": "mmlu_redux",
                "subset": "history",
                "item_id": "mmlu_redux2_history_0000",
                "issue_type": "mmlu_redux_flaw",
                "source": "synthetic",
            }
        ],
    )

    summary = align_mmlu_redux(
        predictions_path=predictions,
        redux_path=redux,
        output_path=output,
    )

    rows = read_jsonl(output)
    assert summary["status"] == "blocked"
    assert summary["unaligned_count"] == 1
    assert rows[0]["alignment_method"] == "unaligned"
    assert rows[0]["alignment_confidence"] == 0.0


def test_duplicate_source_issue_ids_are_skipped(tmp_path: Path):
    predictions = tmp_path / "predictions.jsonl"
    redux = tmp_path / "redux.jsonl"
    output = tmp_path / "aligned.jsonl"
    write_jsonl(predictions, [{"benchmark": "mmlu", "subset": "math", "item_id": "mmlu_math_id1"}])
    duplicate = {
        "benchmark": "mmlu_redux",
        "subset": "math",
        "item_id": "mmlu_math_id1",
        "issue_type": "mmlu_redux_flaw",
        "source": "synthetic",
    }
    write_jsonl(redux, [duplicate, duplicate])

    summary = align_mmlu_redux(
        predictions_path=predictions,
        redux_path=redux,
        output_path=output,
    )

    assert summary["total_redux_labels"] == 2
    assert summary["output_rows"] == 1
    assert summary["skipped_duplicate_source_issue_count"] == 1
    assert len(read_jsonl(output)) == 1


def test_report_and_output_do_not_expose_raw_text(tmp_path: Path):
    predictions = tmp_path / "predictions.jsonl"
    redux = tmp_path / "redux.jsonl"
    output = tmp_path / "aligned.jsonl"
    report = tmp_path / "report.md"
    raw_text = "SECRET SYNTHETIC RAW QUESTION"
    write_jsonl(predictions, [{"benchmark": "mmlu", "subset": "math", "item_id": "mmlu_math_id1"}])
    write_jsonl(
        redux,
        [
            {
                "benchmark": "mmlu_redux",
                "subset": "math",
                "item_id": "mmlu_math_id1",
                "issue_type": "mmlu_redux_flaw",
                "source": "synthetic",
                "metadata": {"question": raw_text, "mmlu_redux_error_type": "bad_question_clarity"},
            }
        ],
    )

    align_mmlu_redux(
        predictions_path=predictions,
        redux_path=redux,
        output_path=output,
        report_path=report,
    )

    assert raw_text not in report.read_text(encoding="utf-8")
    assert raw_text not in json.dumps(read_jsonl(output))
