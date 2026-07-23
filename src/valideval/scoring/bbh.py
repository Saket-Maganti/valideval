from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from valideval.scoring.contracts import ParsedPrediction
from valideval.scoring.gsm8k import normalize_numeric_answer

MULTIPLE_CHOICE_TASKS = frozenset(
    {
        "causal_judgement",
        "date_understanding",
        "disambiguation_qa",
        "formal_fallacies",
        "geometric_shapes",
        "hyperbaton",
        "logical_deduction_five_objects",
        "logical_deduction_seven_objects",
        "logical_deduction_three_objects",
        "movie_recommendation",
        "penguins_in_a_table",
        "reasoning_about_colored_objects",
        "ruin_names",
        "salient_translation_error_detection",
        "snarks",
        "sports_understanding",
        "temporal_sequences",
        "tracking_shuffled_objects_five_objects",
        "tracking_shuffled_objects_seven_objects",
        "tracking_shuffled_objects_three_objects",
    }
)
BOOLEAN_TASKS = frozenset({"boolean_expressions", "navigate", "web_of_lies"})
NUMERIC_TASKS = frozenset({"multistep_arithmetic_two", "object_counting"})
SEQUENCE_TASKS = frozenset({"dyck_languages", "word_sorting"})
_FINAL = re.compile(r"(?:####|final\s+answer\s*(?:is|=|:)?)\s*(.+)", re.I | re.S)
_OPTION = re.compile(r"(?:^|[\s:])[\(\[]?([A-Z])[\)\]]?(?:\s|[.!?,;]|$)")


def parse_bbh_answer(
    raw_output: str,
    subtask_id: str,
    task_policy: Mapping[str, Any] | None = None,
) -> ParsedPrediction:
    """Apply a frozen task-aware parser without receiving the target."""

    text = str(raw_output).strip()
    if not text:
        return ParsedPrediction(None, "failed", "EMPTY_OUTPUT", "empty model output")
    final_matches = _FINAL.findall(text)
    candidate = str(final_matches[-1]).strip().splitlines()[0] if final_matches else text
    if subtask_id in MULTIPLE_CHOICE_TASKS:
        compact = re.sub(r"[\s()[\].,:;]+", "", candidate).upper()
        if len(compact) == 1 and compact.isalpha():
            return ParsedPrediction(f"({compact})", "success", "SUCCESS")
        options = _OPTION.findall(candidate.upper())
        unique = list(dict.fromkeys(options))
        if len(unique) == 1:
            return ParsedPrediction(f"({unique[0]})", "success", "SUCCESS")
        failure = "INVALID_FORMAT" if len(unique) > 1 else "EXTRACTION_FAILURE"
        return ParsedPrediction(None, "failed", failure, "ambiguous or missing BBH option")
    if subtask_id in BOOLEAN_TASKS:
        matches = re.findall(r"\b(true|false|yes|no)\b", candidate, flags=re.I)
        normalized_boole = [
            "True" if value.lower() in {"true", "yes"} else "False" for value in matches
        ]
        unique = list(dict.fromkeys(normalized_boole))
        if len(unique) == 1:
            return ParsedPrediction(unique[0], "success", "SUCCESS")
        failure = "INVALID_FORMAT" if len(unique) > 1 else "EXTRACTION_FAILURE"
        return ParsedPrediction(None, "failed", failure, "ambiguous or missing Boolean answer")
    if subtask_id in NUMERIC_TASKS:
        try:
            return ParsedPrediction(normalize_numeric_answer(candidate), "success", "SUCCESS")
        except ValueError:
            numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", candidate)
            if len(numbers) == 1:
                return ParsedPrediction(normalize_numeric_answer(numbers[0]), "success", "SUCCESS")
            failure = "INVALID_FORMAT" if len(numbers) > 1 else "EXTRACTION_FAILURE"
            return ParsedPrediction(None, "failed", failure, "ambiguous or missing number")
    if subtask_id in SEQUENCE_TASKS:
        normalized_text = _normalize_text_answer(candidate, preserve_symbols=True)
    else:
        normalized_text = _normalize_text_answer(candidate, preserve_symbols=False)
    if not normalized_text:
        return ParsedPrediction(None, "failed", "EXTRACTION_FAILURE", "empty normalized answer")
    return ParsedPrediction(normalized_text, "success", "SUCCESS")


def score_bbh_answer(parsed: ParsedPrediction, gold: Any, subtask_id: str) -> bool:
    if not parsed.succeeded:
        raise ValueError("cannot score an unsuccessful BBH parse")
    if subtask_id in MULTIPLE_CHOICE_TASKS:
        expected_match = re.fullmatch(r"\s*\(?([A-Za-z])\)?\s*", str(gold))
        if expected_match is None:
            raise ValueError(f"invalid BBH multiple-choice target: {gold!r}")
        expected = f"({expected_match.group(1).upper()})"
    elif subtask_id in BOOLEAN_TASKS:
        value = str(gold).strip().lower()
        if value not in {"true", "false", "yes", "no"}:
            raise ValueError(f"invalid BBH Boolean target: {gold!r}")
        expected = "True" if value in {"true", "yes"} else "False"
    elif subtask_id in NUMERIC_TASKS:
        expected = normalize_numeric_answer(gold)
    elif subtask_id in SEQUENCE_TASKS:
        expected = _normalize_text_answer(str(gold), preserve_symbols=True)
    else:
        expected = _normalize_text_answer(str(gold), preserve_symbols=False)
    return parsed.value == expected


def _normalize_text_answer(value: str, *, preserve_symbols: bool) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if not preserve_symbols:
        text = text.rstrip(".")
        text = text.casefold()
    return text
