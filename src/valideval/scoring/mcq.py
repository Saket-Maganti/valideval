from __future__ import annotations

import re

from valideval.schemas import BenchmarkItem, ScoreResult

LABEL_PATTERN = re.compile(r"\b([A-D])\b", re.IGNORECASE)


def normalize_mcq_label(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None
    if len(stripped) == 1 and stripped.upper() in {"A", "B", "C", "D"}:
        return stripped.upper()
    leading = re.match(r"^\s*([A-D])[\).:\s-]", stripped, flags=re.IGNORECASE)
    if leading:
        return leading.group(1).upper()
    match = LABEL_PATTERN.search(stripped)
    if match:
        return match.group(1).upper()
    return None


def score_mcq(item: BenchmarkItem, prediction: str) -> ScoreResult:
    expected_answers = item.answer if isinstance(item.answer, list) else [item.answer]
    normalized_answers = [
        normalize_mcq_label(str(expected)) or str(expected).strip().upper()
        for expected in expected_answers
    ]
    normalized_prediction = normalize_mcq_label(prediction)

    if normalized_prediction is None and item.choices:
        lower_prediction = prediction.strip().lower()
        for choice in item.choices:
            label = normalize_mcq_label(choice)
            text = re.sub(r"^\s*[A-D][\).]\s*", "", choice, flags=re.IGNORECASE).strip().lower()
            if text and lower_prediction == text:
                normalized_prediction = label
                break

    is_correct = normalized_prediction in normalized_answers
    matched_answer = normalized_prediction if is_correct else None
    return ScoreResult(
        score=1.0 if is_correct else 0.0,
        is_correct=is_correct,
        normalized_prediction=normalized_prediction,
        normalized_answer=normalized_answers[0],
        matched_answer=matched_answer,
        metadata={"accepted_answers": normalized_answers},
    )
