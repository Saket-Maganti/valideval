from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from valideval.human.importer_v5 import HumanLabelImportError, import_human_labels_v5
from valideval.human.protocol_v5 import (
    FORBIDDEN_PUBLIC_FIELDS,
    build_blinded_human_packet,
)


def _candidate(index: int) -> dict[str, object]:
    return {
        "item_id": f"item_{index}",
        "question": f"Question {index}?",
        "choices": ["A", "B", "C"],
        "answer": "A",
        "subject": "logic",
        "diagnostic_score": 0.9 - index / 100,
        "risk_rank": index,
        "selection_reason": "high diagnostic score",
        "external_issue_label": "hidden",
        "intended_hypothesis": "hidden",
    }


def _control(index: int, control_type: str, expectation: str) -> dict[str, object]:
    return {
        "item_id": f"control_{index}",
        "question": f"Control question {index}?",
        "choices": ["A", "B"],
        "answer": "A",
        "subject": "control",
        "control_type": control_type,
        "control_expectation": expectation,
    }


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _annotations(
    path: Path,
    task_ids: list[str],
    *,
    expectations: dict[str, str] | None = None,
    bad_label: bool = False,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "blinded_task_id",
                "anonymized_annotator",
                "label",
                "confidence",
                "rationale",
                "expertise_attestation",
                "exclusion_reason",
                "duration_seconds",
            ],
        )
        writer.writeheader()
        for task_id in task_ids:
            for annotator in ("ann_001", "ann_002"):
                writer.writerow(
                    {
                        "blinded_task_id": task_id,
                        "anonymized_annotator": annotator,
                        "label": (
                            "NOT_A_LABEL"
                            if bad_label
                            else (expectations or {}).get(task_id, "NO_DETECTED_ISSUE")
                        ),
                        "confidence": "0.8",
                        "rationale": "Reviewed under the frozen rubric.",
                        "expertise_attestation": "general",
                        "exclusion_reason": "",
                        "duration_seconds": "45",
                    }
                )


def test_packet_is_deterministically_randomized_blinded_and_controlled(tmp_path: Path) -> None:
    result = build_blinded_human_packet(
        [_candidate(index) for index in range(5)],
        control_rows=[
            _control(1, "positive", "AMBIGUOUS_QUESTION"),
            _control(2, "negative", "NO_DETECTED_ISSUE"),
        ],
        packet_dir=tmp_path / "public",
        audit_dir=tmp_path / "private",
        sample_size=3,
        seed=17,
    )
    public_rows = _jsonl(Path(result["blinded_tasks_jsonl"]))
    private = json.loads(Path(result["private_randomization_key_json"]).read_text(encoding="utf-8"))

    assert len(public_rows) == 5
    assert all(FORBIDDEN_PUBLIC_FIELDS.isdisjoint(row) for row in public_rows)
    assert all(
        "control_type" not in row and "control_expectation" not in row for row in public_rows
    )
    assert all(row["subject"] != "control" for row in public_rows)
    assert {row["control_type"] for row in private["mapping"] if row["control_type"]} == {
        "positive",
        "negative",
    }
    repeat = build_blinded_human_packet(
        [_candidate(index) for index in range(5)],
        control_rows=[
            _control(1, "positive", "AMBIGUOUS_QUESTION"),
            _control(2, "negative", "NO_DETECTED_ISSUE"),
        ],
        packet_dir=tmp_path / "repeat_public",
        audit_dir=tmp_path / "repeat_private",
        sample_size=3,
        seed=17,
    )
    assert _jsonl(Path(repeat["blinded_tasks_jsonl"])) == public_rows


def test_valid_import_links_privately_and_remains_result_required(tmp_path: Path) -> None:
    packet = build_blinded_human_packet(
        [_candidate(1), _candidate(2)],
        control_rows=[
            _control(1, "positive", "AMBIGUOUS_QUESTION"),
            _control(2, "negative", "NO_DETECTED_ISSUE"),
        ],
        packet_dir=tmp_path / "public",
        audit_dir=tmp_path / "private",
        seed=5,
    )
    task_ids = [row["blinded_task_id"] for row in _jsonl(Path(packet["blinded_tasks_jsonl"]))]
    private = json.loads(Path(packet["private_randomization_key_json"]).read_text(encoding="utf-8"))
    expectations = {
        row["blinded_task_id"]: row["control_expectation"]
        for row in private["mapping"]
        if row["control_expectation"]
    }
    annotations = tmp_path / "annotations.csv"
    _annotations(annotations, task_ids, expectations=expectations)

    result = import_human_labels_v5(
        annotations,
        blinded_tasks_path=packet["blinded_tasks_jsonl"],
        private_manifest_path=packet["private_randomization_key_json"],
        output_dir=tmp_path / "imported_private",
    )

    assert result["valid"] is True
    assert result["protocol_complete"] is True
    assert result["accepted_rows"] == 8
    assert result["claim_state"] == "RESULT_REQUIRED"
    assert Path(result["validated_labels_jsonl"]).exists()


def test_invalid_label_blocks_entire_batch(tmp_path: Path) -> None:
    packet = build_blinded_human_packet(
        [_candidate(1)],
        control_rows=[
            _control(1, "positive", "AMBIGUOUS_QUESTION"),
            _control(2, "negative", "NO_DETECTED_ISSUE"),
        ],
        packet_dir=tmp_path / "public",
        audit_dir=tmp_path / "private",
    )
    task_ids = [row["blinded_task_id"] for row in _jsonl(Path(packet["blinded_tasks_jsonl"]))]
    annotations = tmp_path / "bad.csv"
    _annotations(annotations, task_ids, bad_label=True)

    result = import_human_labels_v5(
        annotations,
        blinded_tasks_path=packet["blinded_tasks_jsonl"],
        private_manifest_path=packet["private_randomization_key_json"],
        output_dir=tmp_path / "blocked",
    )

    assert result["valid"] is False
    assert result["accepted_rows"] == 0
    assert result["validated_labels_jsonl"] is None


def test_packet_hash_tampering_is_rejected(tmp_path: Path) -> None:
    packet = build_blinded_human_packet(
        [_candidate(1)],
        control_rows=[
            _control(1, "positive", "AMBIGUOUS_QUESTION"),
            _control(2, "negative", "NO_DETECTED_ISSUE"),
        ],
        packet_dir=tmp_path / "public",
        audit_dir=tmp_path / "private",
    )
    tasks = Path(packet["blinded_tasks_jsonl"])
    tasks.write_text(tasks.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    annotations = tmp_path / "unused.csv"
    annotations.write_text(
        "blinded_task_id,anonymized_annotator,label,confidence\n", encoding="utf-8"
    )

    with pytest.raises(HumanLabelImportError, match="SHA-256"):
        import_human_labels_v5(
            annotations,
            blinded_tasks_path=tasks,
            private_manifest_path=packet["private_randomization_key_json"],
            output_dir=tmp_path / "blocked",
        )


def test_private_audit_directory_cannot_be_inside_public_packet(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not be inside"):
        build_blinded_human_packet(
            [_candidate(1)],
            packet_dir=tmp_path / "packet",
            audit_dir=tmp_path / "packet" / "private",
        )


def test_positive_and_negative_controls_are_required_by_default(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="positive and one negative"):
        build_blinded_human_packet(
            [_candidate(1)],
            packet_dir=tmp_path / "public",
            audit_dir=tmp_path / "private",
        )
