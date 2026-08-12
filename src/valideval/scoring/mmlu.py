from __future__ import annotations

import re
from typing import Any

from valideval.scoring.contracts import ParsedPrediction

_CHOICES = frozenset({"A", "B", "C", "D"})
_FINAL_PATTERNS = (
    re.compile(
        r"(?:final\s+answer|answer)\s*(?:is|:)\s*[\(\[]?([A-D])[\)\]]?(?![A-Za-z])",
        re.I,
    ),
    re.compile(r"####\s*[\(\[]?([A-D])[\)\]]?(?![A-Za-z])", re.I),
)


def parse_mmlu_answer(raw_output: str) -> ParsedPrediction:
    """Parse a controlled choice without access to the correct option."""

    text = str(raw_output).strip()
    if not text:
        return ParsedPrediction(None, "failed", "EMPTY_OUTPUT", "empty model output")
    compact = re.sub(r"[\s.!,:;()\[\]{}]+", "", text).upper()
    if compact in _CHOICES:
        return ParsedPrediction(compact, "success", "SUCCESS")
    matches: list[str] = []
    for pattern in _FINAL_PATTERNS:
        matches.extend(match.upper() for match in pattern.findall(text))
    unique = sorted(set(matches))
    if len(unique) == 1:
        return ParsedPrediction(unique[0], "success", "SUCCESS")
    if len(unique) > 1:
        return ParsedPrediction(None, "failed", "INVALID_FORMAT", "conflicting final choices")
    return ParsedPrediction(None, "failed", "EXTRACTION_FAILURE", "no final A-D choice")


def score_mmlu_answer(parsed: ParsedPrediction, gold: Any) -> bool:
    if not parsed.succeeded:
        raise ValueError("cannot score an unsuccessful MMLU parse")
    if isinstance(gold, bool):
        raise ValueError("boolean is not a valid MMLU answer index")
    if isinstance(gold, int) or (isinstance(gold, str) and gold.strip().isdigit()):
        index = int(gold)
        if index not in range(4):
            raise ValueError(f"MMLU answer index out of range: {gold!r}")
        expected = "ABCD"[index]
    else:
        expected = str(gold).strip().upper()
        if expected not in _CHOICES:
            raise ValueError(f"invalid MMLU gold answer: {gold!r}")
    return parsed.value == expected
