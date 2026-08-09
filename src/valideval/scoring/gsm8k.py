from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any

from valideval.scoring.contracts import ParsedPrediction

_REFUSAL = re.compile(
    r"\b(?:cannot|can't|unable\s+to|do\s+not\s+know|don't\s+know|refuse|insufficient)\b",
    re.I,
)
_BOXED = re.compile(r"\\boxed\s*\{([^{}]+)\}")
_MARKERS = (
    re.compile(r"####\s*(.+)", re.I | re.S),
    re.compile(r"(?:final\s+answer|the\s+answer)\s*(?:is|=|:)\s*(.+)", re.I | re.S),
    re.compile(r"(?:therefore|thus|hence)[,\s]+(?:the\s+answer\s+is\s*)?(.+)", re.I | re.S),
)
_NUMBER = re.compile(
    r"(?<![\w.])"
    r"(?:[$€£₹]\s*)?"
    r"[-+]?"
    r"(?:\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.\d+)?"
    r"(?:[eE][-+]?\d+)?"
    r"(?:\s*/\s*[-+]?(?:\d+(?:\.\d+)?))?"
    r"(?!\w)"
)


def parse_gsm8k_answer(raw_output: str) -> ParsedPrediction:
    """Extract one normalized numeric answer without seeing the reference answer."""

    text = str(raw_output).strip()
    if not text:
        return ParsedPrediction(None, "failed", "EMPTY_OUTPUT", "empty model output")
    if _REFUSAL.search(text):
        return ParsedPrediction(None, "failed", "EXTRACTION_FAILURE", "refusal-like output")
    boxed = _BOXED.findall(text)
    if boxed:
        text = f"Final answer: {boxed[-1]}"
    candidate_segment: str | None = None
    for marker in _MARKERS:
        matches = marker.findall(text)
        if matches:
            candidate_segment = str(matches[-1]).strip().splitlines()[0]
            break
    segment = candidate_segment if candidate_segment is not None else text
    tokens = [match.group(0).strip() for match in _NUMBER.finditer(segment)]
    normalized: list[str] = []
    for token in tokens:
        try:
            normalized.append(normalize_numeric_answer(token))
        except ValueError:
            continue
    unique = list(dict.fromkeys(normalized))
    if len(unique) == 1:
        return ParsedPrediction(unique[0], "success", "SUCCESS")
    if len(unique) > 1:
        return ParsedPrediction(
            None,
            "failed",
            "INVALID_FORMAT",
            "multiple distinct numeric answers in final-answer segment",
        )
    return ParsedPrediction(None, "failed", "EXTRACTION_FAILURE", "no numeric final answer")


def parse_gsm8k_answer_strict(raw_output: str) -> ParsedPrediction:
    """Require exactly one explicit ``Final answer:`` numeric segment."""

    text = str(raw_output).strip()
    if not text:
        return ParsedPrediction(None, "failed", "EMPTY_OUTPUT", "empty model output")
    matches = re.findall(r"final\s+answer\s*:\s*([^\n]+)", text, flags=re.I)
    if len(matches) != 1:
        return ParsedPrediction(
            None,
            "failed",
            "INVALID_FORMAT",
            "strict parser requires exactly one Final answer marker",
        )
    tokens = [match.group(0).strip() for match in _NUMBER.finditer(matches[0])]
    normalized: list[str] = []
    for token in tokens:
        try:
            normalized.append(normalize_numeric_answer(token))
        except ValueError:
            continue
    unique = list(dict.fromkeys(normalized))
    if len(unique) == 1:
        return ParsedPrediction(unique[0], "success", "SUCCESS")
    return ParsedPrediction(
        None,
        "failed",
        "INVALID_FORMAT" if unique else "EXTRACTION_FAILURE",
        "strict final-answer segment must contain one numeric value",
    )


def normalize_numeric_answer(value: Any) -> str:
    text = str(value).strip()
    text = re.sub(r"^[\$€£₹]\s*", "", text)
    text = text.replace(",", "").strip()
    text = re.sub(
        r"\s*(?:dollars?|usd|euros?|pounds?|rupees?|meters?|metres?|km|kilometers?|"
        r"kilometres?|hours?|minutes?|seconds?|items?|people|eggs?)\.?\s*$",
        "",
        text,
        flags=re.I,
    )
    if "/" in text:
        numerator, denominator, *rest = [part.strip() for part in text.split("/")]
        if rest:
            raise ValueError(f"invalid fraction: {value!r}")
        try:
            fraction = Fraction(Decimal(numerator)) / Fraction(Decimal(denominator))
        except (InvalidOperation, ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"invalid fraction: {value!r}") from exc
        return f"{fraction.numerator}/{fraction.denominator}"
    try:
        decimal = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric answer: {value!r}") from exc
    if not decimal.is_finite():
        raise ValueError("numeric answer must be finite")
    normalized = format(decimal.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return "0" if normalized in {"-0", "+0", ""} else normalized


def score_gsm8k_answer(parsed: ParsedPrediction, gold: Any) -> bool:
    if not parsed.succeeded:
        raise ValueError("cannot score an unsuccessful GSM8K parse")
    expected = normalize_numeric_answer(gold)
    observed = str(parsed.value)
    if "/" in expected or "/" in observed:
        try:
            return Fraction(expected) == Fraction(observed)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError("invalid normalized fraction") from exc
    return Decimal(observed) == Decimal(expected)
