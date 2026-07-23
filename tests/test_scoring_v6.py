from __future__ import annotations

import pytest

from valideval.scoring.bbh import parse_bbh_answer, score_bbh_answer
from valideval.scoring.gsm8k import (
    normalize_numeric_answer,
    parse_gsm8k_answer,
    score_gsm8k_answer,
)
from valideval.scoring.mmlu import parse_mmlu_answer, score_mmlu_answer


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("18", "18"),
        ("Final answer: -12", "-12"),
        ("The answer is $1,250.", "1250"),
        ("#### 3.50 dollars", "3.5"),
        ("Final answer: 3/4", "3/4"),
        (r"\boxed{42}", "42"),
        ("Thus, the answer is 6 meters.", "6"),
        ("Final answer: 1e3", "1000"),
    ],
)
def test_gsm8k_gold_blind_numeric_parser(raw: str, expected: str):
    parsed = parse_gsm8k_answer(raw)
    assert parsed.succeeded
    assert parsed.value == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "I cannot answer this problem.",
        "Final answer: 3 or 4",
        "There are many possible values.",
    ],
)
def test_gsm8k_parser_records_failures(raw: str):
    parsed = parse_gsm8k_answer(raw)
    assert not parsed.succeeded
    assert parsed.failure_type in {"EMPTY_OUTPUT", "EXTRACTION_FAILURE", "INVALID_FORMAT"}


def test_gsm8k_fraction_and_decimal_scores_are_exact():
    parsed = parse_gsm8k_answer("Final answer: 0.5")
    assert score_gsm8k_answer(parsed, "1/2")
    assert normalize_numeric_answer("£2,000.00") == "2000"


@pytest.mark.parametrize(
    ("raw", "gold", "correct"),
    [
        ("A", 0, True),
        ("Final answer: (C)", 2, True),
        ("Answer: D", "A", False),
    ],
)
def test_mmlu_parser_and_scorer(raw: str, gold: object, correct: bool):
    parsed = parse_mmlu_answer(raw)
    assert parsed.succeeded
    assert score_mmlu_answer(parsed, gold) is correct


def test_mmlu_conflicting_choices_fail():
    parsed = parse_mmlu_answer("Answer: A. Final answer: B")
    assert parsed.failure_type == "INVALID_FORMAT"


@pytest.mark.parametrize(
    ("task", "raw", "gold"),
    [
        ("causal_judgement", "Final answer: (B)", "(B)"),
        ("boolean_expressions", "Final answer: True", "True"),
        ("multistep_arithmetic_two", "Final answer: -15", "-15"),
        ("dyck_languages", "Final answer: ] ]", "] ]"),
        ("word_sorting", "Final answer: alpha beta", "alpha beta"),
    ],
)
def test_bbh_task_specific_parsers(task: str, raw: str, gold: str):
    parsed = parse_bbh_answer(raw, task)
    assert parsed.succeeded
    assert score_bbh_answer(parsed, gold, task)
