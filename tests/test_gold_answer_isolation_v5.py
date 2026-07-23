from __future__ import annotations

import pytest

from valideval.leakage.guards import (
    ExtractionOutcome,
    GoldAnswerLeakageError,
    assert_gold_isolated,
    build_generation_payload,
)


def test_generation_payload_drops_source_gold_answer() -> None:
    source = {
        "item_id": "mmlu_1",
        "prompt": "Select one option.",
        "choices": ["A", "B"],
        "answer": "B",
        "is_correct": True,
        "public_metadata": {"subject": "logic"},
    }

    payload = build_generation_payload(source)

    assert payload["item_id"] == "mmlu_1"
    assert "answer" not in payload
    assert "is_correct" not in payload
    assert_gold_isolated(payload)


def test_nested_metadata_and_few_shot_gold_are_rejected() -> None:
    with pytest.raises(GoldAnswerLeakageError, match="gold_answer"):
        build_generation_payload(
            {
                "item_id": "x",
                "prompt": "p",
                "public_metadata": {"nested": {"gold_answer": "A"}},
            }
        )


def test_rendered_few_shot_responses_are_allowed_but_target_overlap_is_rejected() -> None:
    payload = build_generation_payload(
        {"item_id": "target", "prompt": "What is the capital of France?"},
        few_shot_examples=[
            {"item_id": "demo", "prompt": "What is two plus two?", "response": "Four."}
        ],
    )
    assert payload["few_shot_examples"][0]["response"] == "Four."

    with pytest.raises(GoldAnswerLeakageError, match="overlaps the target"):
        build_generation_payload(
            {"item_id": "target", "prompt": "What is the capital of France?"},
            few_shot_examples=[
                {
                    "item_id": "target",
                    "prompt": "What is the capital of France?",
                    "response": "Paris.",
                }
            ],
        )
    with pytest.raises(GoldAnswerLeakageError, match="correct_answer"):
        build_generation_payload(
            {"item_id": "x", "prompt": "p"},
            few_shot_examples=[{"prompt": "demo", "correct_answer": "A"}],
        )


def test_retry_correctness_feedback_is_rejected() -> None:
    with pytest.raises(GoldAnswerLeakageError, match="is_correct"):
        assert_gold_isolated(
            {"attempt": 2, "feedback": {"is_correct": False}},
            boundary="retry",
        )


def test_extraction_failures_are_explicit_not_silent_wrong_answers() -> None:
    assert ExtractionOutcome(status="success", prediction="A").prediction == "A"
    failed = ExtractionOutcome(status="failed", prediction=None, failure_type="no_parse")
    assert failed.prediction is None

    with pytest.raises(ValueError, match="prediction=None"):
        ExtractionOutcome(status="failed", prediction="A", failure_type="no_parse")
    with pytest.raises(ValueError, match="requires a prediction"):
        ExtractionOutcome(status="success", prediction=None)
