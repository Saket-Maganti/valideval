from __future__ import annotations

import csv
import json
from pathlib import Path

from valideval.external_labels.mmlu_redux_linkage_v5 import (
    LinkageTier,
    link_mmlu_redux_rows,
    resolve_mmlu_redux_linkage,
)


def test_stable_and_canonical_content_matches_can_be_confirmed() -> None:
    benchmark = [
        {
            "item_id": "mmlu_logic_1",
            "question": "What is 2 + 2?",
            "choices": ["3", "4", "5"],
            "answer": "4",
            "metadata": {"upstream_item_id": "upstream-1"},
        },
        {
            "item_id": "mmlu_logic_2",
            "question": "Which inference is valid?",
            "choices": ["modus ponens", "affirming the consequent"],
            "answer": "modus ponens",
        },
    ]
    redux = [
        {"item_id": "redux_a", "metadata": {"upstream_item_id": "upstream-1"}},
        {
            "item_id": "redux_b",
            "question": "  WHICH inference is valid? ",
            "choices": ["A) modus ponens", "B) affirming the consequent"],
        },
    ]

    rows, summary = link_mmlu_redux_rows(redux, benchmark)

    assert rows[0].tier == LinkageTier.CONFIRMED_EXACT
    assert rows[1].tier == LinkageTier.CONFIRMED_CANONICAL
    assert all(row.confirmed for row in rows)
    assert summary.status == "REDUX_ITEM_IDENTITY_CONFIRMED"


def test_structural_position_is_never_confirmed_identity() -> None:
    benchmark = [{"item_id": "mmlu_logic_0003", "subject": "logic", "source_row_index": 3}]
    redux = [{"item_id": "redux_logic_0003", "subject": "logic", "source_row_index": 3}]

    rows, summary = link_mmlu_redux_rows(redux, benchmark)

    assert rows[0].method == "canonical_subject_source_index"
    assert rows[0].tier == LinkageTier.HIGH_CONFIDENCE_MANUAL_REVIEW
    assert rows[0].confirmed is False
    assert rows[0].structural_only is True
    assert summary.status == "REDUX_EXPLORATORY_ONLY"


def test_options_only_candidate_requires_manual_review() -> None:
    benchmark = [{"item_id": "mmlu_1", "choices": ["red", "green", "blue"]}]
    redux = [{"item_id": "redux_1", "options": ["blue", "red", "green"]}]

    rows, summary = link_mmlu_redux_rows(redux, benchmark)

    assert rows[0].method == "exact_normalized_options"
    assert rows[0].tier == LinkageTier.HIGH_CONFIDENCE_MANUAL_REVIEW
    assert rows[0].confirmed is False
    assert summary.status == "REDUX_EXPLORATORY_ONLY"


def test_hash_collision_is_ambiguous_not_silently_confirmed() -> None:
    benchmark = [
        {"item_id": "one", "question": "Duplicate question", "choices": ["A", "B"]},
        {"item_id": "two", "question": "Duplicate question", "choices": ["A", "B"]},
    ]
    redux = [{"item_id": "redux", "question": "duplicate question", "choices": ["A", "B"]}]

    rows, summary = link_mmlu_redux_rows(redux, benchmark)

    assert rows[0].tier == LinkageTier.AMBIGUOUS
    assert rows[0].candidate_count == 2
    assert rows[0].collision_detected is True
    assert summary.confirmed_count == 0


def test_file_output_is_sanitized_and_contains_no_raw_question_text(tmp_path: Path) -> None:
    redux = tmp_path / "redux.jsonl"
    benchmark = tmp_path / "benchmark.jsonl"
    output = tmp_path / "linkage.csv"
    summary = tmp_path / "summary.json"
    secret = "Raw licensed question must not be emitted"
    redux.write_text(json.dumps({"item_id": "r", "question": secret}) + "\n", encoding="utf-8")
    benchmark.write_text(json.dumps({"item_id": "b", "question": secret}) + "\n", encoding="utf-8")

    result = resolve_mmlu_redux_linkage(
        redux_path=redux,
        benchmark_path=benchmark,
        output_csv=output,
        summary_json=summary,
    )

    assert result.confirmed_count == 1
    assert secret not in output.read_text(encoding="utf-8")
    with output.open("r", encoding="utf-8", newline="") as handle:
        assert "question_hash" in next(csv.DictReader(handle))
