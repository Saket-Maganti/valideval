from __future__ import annotations

import json
from pathlib import Path

from valideval.validation.external_flag_validation import (
    export_flags_from_results,
    validate_flags_against_ground_truth,
)
from valideval.validation.mmlu_redux import import_mmlu_redux_ground_truth


def test_flag_export_and_external_validation(tmp_path: Path):
    results = tmp_path / "results"
    results.mkdir()
    (results / "irt.json").write_text(
        json.dumps(
            {
                "diagnostic_name": "irt",
                "per_item_metrics": {
                    "item_001": {"discrimination": 0.01},
                    "item_002": {"discrimination": 0.90},
                },
            }
        ),
        encoding="utf-8",
    )
    flags = tmp_path / "flags.jsonl"
    flag_summary = export_flags_from_results(results, flags, benchmark="mmlu")
    assert flag_summary["flag_count"] == 2

    issues = tmp_path / "issues.jsonl"
    import_mmlu_redux_ground_truth("examples/mmlu_redux_mock.jsonl", issues)
    metrics = validate_flags_against_ground_truth(
        flags,
        issues,
        tmp_path / "external",
        benchmark="mmlu",
        bootstrap_samples=10,
        seed=0,
    )
    assert metrics["status"] == "ok"
    assert (tmp_path / "external" / "summary.md").exists()


def test_proxy_irt_flag_export_and_subject_filtered_validation(tmp_path: Path):
    irt = tmp_path / "irt"
    irt.mkdir()
    (irt / "item_parameters.csv").write_text(
        "\n".join(
            [
                "item_id,proportion_correct,difficulty_proxy,discrimination_proxy,label",
                "math::mmlu_math_id1,0.50,0.0,-0.60,negative_discrimination",
                "math::mmlu_math_id2,0.50,0.0,0.00,low_discrimination",
                "history::mmlu_history_id1,0.99,-4.0,0.40,unstable_estimate",
                "other::mmlu_other_id1,0.99,-4.0,0.40,unstable_estimate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    flags = tmp_path / "flags.jsonl"
    flag_summary = export_flags_from_results(
        None,
        flags,
        benchmark="mmlu",
        matrix_path=tmp_path / "matrix.csv",
        irt_dir=irt,
    )

    assert flag_summary["group_counts"]["negative_discrimination"] == 1
    assert flag_summary["group_counts"]["low_discrimination"] == 1
    assert flag_summary["group_counts"]["extreme_difficulty"] == 2
    assert (tmp_path / "flags_negative_discrimination.jsonl").exists()
    assert (tmp_path / "flags_combined.jsonl").exists()

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
    metrics = validate_flags_against_ground_truth(
        flags,
        issues,
        tmp_path / "external",
        benchmark="mmlu",
        bootstrap_samples=0,
        restrict_to_ground_truth_subjects=True,
    )

    assert metrics["status"] == "ok"
    assert metrics["filters"]["restrict_to_ground_truth_subjects"] is True
    assert metrics["ground_truth_subject_count"] == 2
    assert "combined_flags" in metrics["diagnostics"]
    assert (tmp_path / "external" / "top_flagged_items_sanitized.csv").exists()
