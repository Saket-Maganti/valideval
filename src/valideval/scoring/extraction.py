from __future__ import annotations

import math
import re
from dataclasses import dataclass

from valideval.scoring.exact_match import normalize_text
from valideval.scoring.mcq import normalize_mcq_label


@dataclass(frozen=True)
class ExtractionResult:
    mode: str
    value: str | None
    invalid: bool = False
    refusal: bool = False
    metadata: dict[str, object] | None = None


REFUSAL_RE = re.compile(r"\b(cannot|can't|unable|refuse|insufficient|not enough)\b", re.I)
FINAL_ANSWER_PATTERNS = [
    re.compile(r'"answer"\s*:\s*"?\(?\s*([A-D])\s*\)?"?', re.I),
    re.compile(r"\bfinal\s+answer\s*(?:is|[:=\-])?\s*\(?\s*([A-D])\s*\)?\b", re.I),
    re.compile(r"\banswer\s*(?:is|[:=\-])\s*\(?\s*([A-D])\s*\)?\b", re.I),
    re.compile(
        r"\bthe\s+correct\s+(?:answer|option|choice)\s*(?:is|[:=\-])?\s*\(?\s*([A-D])\s*\)?\b",
        re.I,
    ),
    re.compile(r"\bi\s+choose\s+(?:option\s+|choice\s*)?\(?\s*([A-D])\s*\)?\b", re.I),
    re.compile(r"\b(?:option|choice)\s+([A-D])\b", re.I),
]


def detect_refusal(text: str) -> bool:
    return bool(REFUSAL_RE.search(text))


def strict_letter(text: str) -> ExtractionResult:
    stripped = text.strip()
    value = stripped.upper() if stripped.upper() in {"A", "B", "C", "D"} else None
    return ExtractionResult("strict_letter", value, invalid=value is None)


def lenient_letter(text: str) -> ExtractionResult:
    value = normalize_mcq_label(text)
    return ExtractionResult("lenient_letter", value, invalid=value is None)


def regex_final_answer(text: str) -> ExtractionResult:
    value = None
    for pattern in FINAL_ANSWER_PATTERNS:
        matches = [match.group(1).upper() for match in pattern.finditer(text)]
        if matches:
            value = matches[-1]
            break
    if value is None:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            match = re.match(r"^\(?\s*([A-D])\s*\)?[.)]?$", lines[-1], flags=re.I)
            if match:
                value = match.group(1).upper()
    return ExtractionResult("regex_final_answer", value, invalid=value is None)


def numeric_tolerance(
    text: str, *, answer: str | float | int | None = None, tolerance: float = 1e-6
) -> ExtractionResult:
    numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
    if not numbers:
        return ExtractionResult("numeric_tolerance", None, invalid=True)
    value = float(numbers[-1])
    metadata: dict[str, object] = {"numeric_value": value, "tolerance": tolerance}
    if answer is not None:
        try:
            metadata["within_tolerance"] = math.isclose(
                value, float(answer), rel_tol=tolerance, abs_tol=tolerance
            )
        except (TypeError, ValueError):
            metadata["within_tolerance"] = False
    return ExtractionResult("numeric_tolerance", str(value), metadata=metadata)


def normalized_exact_match(text: str, *, aliases: list[str] | None = None) -> ExtractionResult:
    value = normalize_text(text)
    accepted = [normalize_text(alias) for alias in aliases or []]
    return ExtractionResult(
        "normalized_exact_match",
        value,
        invalid=not value,
        metadata={"matched_alias": value in accepted if accepted else None},
    )


def normalized_text_match(text: str, *, aliases: list[str] | None = None) -> ExtractionResult:
    result = normalized_exact_match(text, aliases=aliases)
    return ExtractionResult(
        "normalized_text_match",
        result.value,
        invalid=result.invalid,
        refusal=result.refusal,
        metadata=result.metadata,
    )


def alias_aware_match(text: str, *, aliases: list[str] | None = None) -> ExtractionResult:
    value = normalize_text(text)
    alias_map = {normalize_text(alias): alias for alias in aliases or []}
    return ExtractionResult(
        "alias_aware_match",
        value if value in alias_map or not alias_map else None,
        invalid=bool(alias_map) and value not in alias_map,
        metadata={"canonical_alias": alias_map.get(value)},
    )


def refusal_detector(text: str) -> ExtractionResult:
    refusal = detect_refusal(text)
    return ExtractionResult("refusal_detector", None, invalid=refusal, refusal=refusal)


def invalid_output_detector(text: str) -> ExtractionResult:
    value = normalize_mcq_label(text)
    refusal = detect_refusal(text)
    invalid = value is None or refusal
    return ExtractionResult(
        "invalid_output_detector",
        value,
        invalid=invalid,
        refusal=refusal,
    )


EXTRACTORS = {
    "strict_letter": strict_letter,
    "lenient_letter": lenient_letter,
    "regex_final_answer": regex_final_answer,
    "numeric_tolerance": numeric_tolerance,
    "normalized_exact_match": normalized_exact_match,
    "normalized_text_match": normalized_text_match,
    "alias_aware_match": alias_aware_match,
    "refusal_detector": refusal_detector,
    "invalid_output_detector": invalid_output_detector,
}
