from __future__ import annotations

from valideval.benchmarks.base import get_benchmark
from valideval.benchmarks.gpqa_inputs import extract_gpqa_prediction
from valideval.scoring.extraction import (
    invalid_output_detector,
    lenient_letter,
    normalized_text_match,
    regex_final_answer,
    strict_letter,
)
from valideval.scoring.mcq_utils import correct_choice_text


def test_gpqa_extraction_modes():
    assert strict_letter("C").value == "C"
    assert strict_letter("Answer: C").invalid is True
    assert lenient_letter("Answer: C").value == "C"
    assert regex_final_answer("Final Answer: (C)").value == "C"
    assert regex_final_answer('{"answer": "C"}').value == "C"

    match = normalized_text_match(" second order ", aliases=["second order"])
    assert match.value == "second order"
    assert match.metadata["matched_alias"] is True

    assert invalid_output_detector("I cannot determine this").invalid is True


def test_gpqa_final_answer_extraction_patterns():
    benchmark = get_benchmark("gpqa_diamond_tiny_fixture")
    item = next(item for item in benchmark.load_items() if item.item_id == "gpqa_fixture_0002")

    examples = [
        "Answer: C",
        "Final answer: C",
        "Final Answer: (C)",
        "The correct option is C.",
        "I choose option C.",
        '{"answer": "C"}',
        "C",
        "Therefore, the answer is C.",
        "A and B are wrong. Final answer: C.",
    ]

    for raw_output in examples:
        extraction = extract_gpqa_prediction(item, raw_output)
        assert extraction["prediction"] == "C"
        assert extraction["invalid"] is False


def test_gpqa_ambiguous_or_missing_answer_extraction_patterns():
    benchmark = get_benchmark("gpqa_diamond_tiny_fixture")
    item = next(item for item in benchmark.load_items() if item.item_id == "gpqa_fixture_0002")

    examples = [
        "It could be A or C.",
        "A. ... B. ... C. ... D. ...",
        "I am not sure.",
        "No answer provided.",
        "The answer might be B, but C is also plausible.",
    ]

    for raw_output in examples:
        extraction = extract_gpqa_prediction(item, raw_output)
        assert extraction["prediction"] is None
        assert extraction["invalid"] is True


def test_gpqa_scoring_accepts_letter_and_normalized_choice_text():
    benchmark = get_benchmark("gpqa_diamond_tiny_fixture")
    item = next(item for item in benchmark.load_items() if item.item_id == "gpqa_fixture_0002")

    assert benchmark.score_prediction(item, "C").is_correct is True
    assert benchmark.score_prediction(item, "second order").is_correct is True
    assert benchmark.score_prediction(item, "B").score == 0.0
    assert correct_choice_text(item) == "second order"


def test_gpqa_randomized_choices_preserve_answer_mapping():
    benchmark = get_benchmark("gpqa_diamond_tiny_fixture")
    item = next(item for item in benchmark.load_items() if item.item_id == "gpqa_fixture_0005")

    prompt = benchmark.render_prompt(item, "randomized_choices")

    assert "C. 2" in prompt
    assert benchmark.score_prediction(item, "C").is_correct is True
    assert benchmark.score_prediction(item, "2").is_correct is True
