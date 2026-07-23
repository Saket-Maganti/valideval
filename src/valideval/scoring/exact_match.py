from __future__ import annotations

import re

from valideval.schemas import ScoreResult


def normalize_text(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"^[\"'`]+|[\"'`]+$", "", normalized)
    return normalized


def exact_match_score(answer: str | list[str], prediction: str) -> ScoreResult:
    answers = answer if isinstance(answer, list) else [answer]
    normalized_prediction = normalize_text(prediction)
    normalized_answers = [normalize_text(value) for value in answers]
    is_correct = normalized_prediction in normalized_answers
    return ScoreResult(
        score=1.0 if is_correct else 0.0,
        is_correct=is_correct,
        normalized_prediction=normalized_prediction,
        normalized_answer="|".join(normalized_answers),
    )
