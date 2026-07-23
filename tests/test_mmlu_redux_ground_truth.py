from __future__ import annotations

from pathlib import Path

import pytest

from valideval.validation.mmlu_redux import import_mmlu_redux_ground_truth


def test_mmlu_redux_ground_truth_import(tmp_path: Path):
    output = tmp_path / "issues.jsonl"
    summary = import_mmlu_redux_ground_truth("examples/mmlu_redux_mock.jsonl", output)

    assert summary["status"] == "ok"
    assert summary["issue_count"] == 2
    assert output.exists()


def test_ground_truth_requires_source(tmp_path: Path):
    source = tmp_path / "bad.jsonl"
    source.write_text(
        '{"benchmark":"mmlu","item_id":"i1","issue_type":"wrong_answer"}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="validation errors"):
        import_mmlu_redux_ground_truth(source, tmp_path / "issues.jsonl")
