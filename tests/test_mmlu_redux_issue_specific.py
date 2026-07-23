from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from valideval.validation.mmlu_redux_issue_specific import (
    build_issue_taxonomy,
    compute_issue_specific_scores,
    load_issue_mapping,
    run_mmlu_redux_issue_validation,
    validate_issue_mapping,
)


def test_issue_taxonomy_extracts_counts_without_raw_text():
    records = [
        {
            "benchmark": "mmlu",
            "subset": "math",
            "item_id": "mmlu_math_id1",
            "issue_type": "label_error",
            "severity": "high",
            "source": "mmlu_redux",
            "metadata": {"question": "SECRET RAW"},
        },
        {
            "benchmark": "mmlu",
            "subset": "history",
            "item_id": "mmlu_history_id1",
            "issue_type": "ambiguous_question",
            "severity": "medium",
            "source": "mmlu_redux",
        },
    ]

    taxonomy = build_issue_taxonomy(records, min_positive_count=2)

    assert taxonomy["issue_type_counts"]["label_error"] == 1
    assert taxonomy["severity_counts"]["high"] == 1
    assert taxonomy["subject_counts"]["math"] == 1
    assert taxonomy["issue_type_status"]["label_error"]["underpowered"] is True
    assert "SECRET RAW" not in json.dumps(taxonomy)


def test_mapping_validation_accepts_observed_issue_types(tmp_path: Path):
    mapping = _write_mapping(tmp_path)
    payload = load_issue_mapping(mapping)

    warnings = validate_issue_mapping(payload, ["ambiguous_question", "label_error"])

    assert warnings == []


def test_matrix_derived_scores_include_disagreement_and_option_anomaly(tmp_path: Path):
    predictions, matrix, _issues, _mapping = _write_fixture(tmp_path)

    scores = compute_issue_specific_scores(predictions_path=predictions, matrix_path=matrix)
    by_item = {row["item_id"]: row for row in scores}

    item1 = by_item["mmlu_math_id1"]["diagnostics"]
    item2 = by_item["mmlu_math_id2"]["diagnostics"]
    assert item1["high_disagreement"] == 0.5
    assert item1["option_selection_anomaly"] > item2["option_selection_anomaly"]
    assert item1["correct_answer_rarely_selected"] > item2["correct_answer_rarely_selected"]


def test_subject_normalized_scores_and_zero_variance_handling(tmp_path: Path):
    predictions, matrix, _issues, _mapping = _write_fixture(tmp_path)

    scores = compute_issue_specific_scores(
        predictions_path=predictions,
        matrix_path=matrix,
        subject_normalize=True,
    )
    by_item = {row["item_id"]: row for row in scores}

    item1 = by_item["mmlu_math_id1"]
    item2 = by_item["mmlu_math_id2"]
    history = by_item["mmlu_history_id1"]
    assert item1["diagnostics"]["correct_answer_rarely_selected_subject_z"] == 1.0
    assert item2["diagnostics"]["correct_answer_rarely_selected_subject_z"] == -1.0
    assert item1["diagnostics"]["high_disagreement_subject_z"] == 1.0
    assert item2["diagnostics"]["high_disagreement_subject_z"] == -1.0
    assert history["diagnostics"]["high_disagreement_subject_z"] == 0.0

    details = history["diagnostic_details"]["high_disagreement_subject_z"]
    assert details["subject_std"] == 0.0
    assert details["zero_variance_subject"] is True
    assert details["direction"] == "higher_is_more_suspicious"


def test_issue_validation_filters_and_underpowered_outputs(tmp_path: Path):
    predictions, matrix, issues, mapping = _write_fixture(tmp_path)

    payload = run_mmlu_redux_issue_validation(
        predictions_path=predictions,
        matrix_path=matrix,
        ground_truth_path=issues,
        mapping_path=mapping,
        output_dir=tmp_path / "out",
        restrict_to_ground_truth_subjects=True,
        severities=["high"],
        min_positive_count=2,
        bootstrap_samples=0,
    )

    assert payload["status"] == "ok"
    assert payload["filters"]["restrict_to_ground_truth_subjects"] is True
    assert set(payload["issue_type_metrics"]) == {"label_error"}
    metric = payload["issue_type_metrics"]["label_error"]["high_disagreement"]
    assert metric["status"] == "underpowered"
    assert metric["positive_count"] == 1
    assert (tmp_path / "out" / "issue_type_metrics.json").exists()
    assert (tmp_path / "out" / "diagnostic_by_issue_matrix.csv").exists()
    assert (tmp_path / "out" / "top_items_sanitized.csv").exists()

    report = (tmp_path / "out" / "issue_type_metrics.md").read_text(encoding="utf-8")
    assert "SECRET RAW" not in report
    assert "answer choices" in report


def test_subject_normalized_validation_filters_and_null_outputs(tmp_path: Path):
    predictions, matrix, issues, mapping = _write_fixture(tmp_path)

    payload = run_mmlu_redux_issue_validation(
        predictions_path=predictions,
        matrix_path=matrix,
        ground_truth_path=issues,
        mapping_path=mapping,
        output_dir=tmp_path / "normalized",
        restrict_to_ground_truth_subjects=True,
        issue_types=["label_error"],
        diagnostics=["high_disagreement"],
        subject_normalize=True,
        subject_matched_null=5,
        min_positive_count=1,
        bootstrap_samples=0,
    )

    assert payload["status"] == "ok"
    assert payload["filters"]["subject_normalize"] is True
    assert set(payload["issue_type_metrics"]) == {"label_error"}
    assert set(payload["issue_type_metrics"]["label_error"]) == {
        "high_disagreement",
        "high_disagreement_subject_z",
    }
    metric = payload["issue_type_metrics"]["label_error"]["high_disagreement_subject_z"]
    assert metric["status"] == "ok"
    assert metric["positive_count"] == 1

    output = tmp_path / "normalized"
    assert (output / "subject_normalized_item_scores.csv").exists()
    assert (output / "subject_normalized_item_scores.jsonl").exists()
    assert (output / "raw_vs_subject_normalized_comparison.md").exists()
    assert (output / "subject_matched_null.json").exists()
    assert (output / "subject_matched_null.md").exists()
    combined = "\n".join(
        [
            (output / "issue_type_metrics.md").read_text(encoding="utf-8"),
            (output / "raw_vs_subject_normalized_comparison.md").read_text(encoding="utf-8"),
            (output / "subject_matched_null.md").read_text(encoding="utf-8"),
            (output / "subject_normalized_item_scores.jsonl").read_text(encoding="utf-8"),
        ]
    )
    assert "SECRET RAW" not in combined


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    matrix = tmp_path / "matrix.csv"
    pd.DataFrame(
        [
            [1.0, 1.0, 1.0],
            [0.0, 1.0, 0.0],
            [0.0, 1.0, 1.0],
            [0.0, 1.0, 0.0],
        ],
        index=["m1", "m2", "m3", "m4"],
        columns=[
            "math::mmlu_math_id1",
            "math::mmlu_math_id2",
            "history::mmlu_history_id1",
        ],
    ).to_csv(matrix)
    predictions = tmp_path / "predictions.jsonl"
    rows = [
        ("m1", "math", "mmlu_math_id1", "A", "A", True),
        ("m2", "math", "mmlu_math_id1", "B", "A", False),
        ("m3", "math", "mmlu_math_id1", "B", "A", False),
        ("m4", "math", "mmlu_math_id1", "C", "A", False),
        ("m1", "math", "mmlu_math_id2", "A", "A", True),
        ("m2", "math", "mmlu_math_id2", "A", "A", True),
        ("m3", "math", "mmlu_math_id2", "A", "A", True),
        ("m4", "math", "mmlu_math_id2", "A", "A", True),
        ("m1", "history", "mmlu_history_id1", "A", "A", True),
        ("m2", "history", "mmlu_history_id1", "B", "A", False),
        ("m3", "history", "mmlu_history_id1", "A", "A", True),
        ("m4", "history", "mmlu_history_id1", "C", "A", False),
    ]
    predictions.write_text(
        "\n".join(
            json.dumps(
                {
                    "benchmark": "mmlu",
                    "subset": subset,
                    "item_id": item_id,
                    "model_id": model_id,
                    "prediction": prediction,
                    "gold": gold,
                    "correct": correct,
                    "source": "fixture",
                    "source_file": "fixture",
                    "metadata": {"raw_text": "SECRET RAW"},
                }
            )
            for model_id, subset, item_id, prediction, gold, correct in rows
        )
        + "\n",
        encoding="utf-8",
    )
    issues = tmp_path / "issues.jsonl"
    issues.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "benchmark": "mmlu",
                        "subset": "math",
                        "item_id": "mmlu_math_id1",
                        "issue_type": "label_error",
                        "severity": "high",
                        "source": "mmlu_redux",
                    }
                ),
                json.dumps(
                    {
                        "benchmark": "mmlu",
                        "subset": "history",
                        "item_id": "mmlu_history_id1",
                        "issue_type": "ambiguous_question",
                        "severity": "medium",
                        "source": "mmlu_redux",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    mapping = _write_mapping(tmp_path)
    return predictions, matrix, issues, mapping


def _write_mapping(tmp_path: Path) -> Path:
    mapping = tmp_path / "mapping.yaml"
    mapping.write_text(
        """
issue_type_mapping:
  label_error:
    plausible_diagnostics:
      - high_disagreement
      - option_selection_anomaly
      - correct_answer_rarely_selected
    excluded_diagnostics: []
  ambiguous_question:
    plausible_diagnostics:
      - high_disagreement
      - prompt_sensitivity
    excluded_diagnostics: []
""".lstrip(),
        encoding="utf-8",
    )
    return mapping
