from __future__ import annotations

from pathlib import Path

from valideval.io.jsonl import write_jsonl
from valideval.validation.external_ground_truth import load_ground_truth


def test_load_ground_truth_accepts_aligned_mmlu_redux_rows(tmp_path: Path):
    path = tmp_path / "aligned.jsonl"
    write_jsonl(
        path,
        [
            {
                "schema_version": "0.1",
                "benchmark": "mmlu",
                "subject": "abstract_algebra",
                "item_id": "mmlu_abstract_algebra_id16",
                "source_issue_id": "mmlu_redux2_abstract_algebra_0000",
                "issue_type": "label_error",
                "severity": "high",
                "alignment_method": "subject_numeric_index",
                "alignment_confidence": 0.85,
                "source": "mmlu_redux",
                "metadata": {"source_row_index": 0},
            }
        ],
    )

    issues = load_ground_truth(path)

    assert len(issues) == 1
    assert issues[0].subset == "abstract_algebra"
    assert issues[0].item_id == "mmlu_abstract_algebra_id16"
    assert issues[0].metadata["alignment_method"] == "subject_numeric_index"
    assert issues[0].metadata["source_issue_id"] == "mmlu_redux2_abstract_algebra_0000"
