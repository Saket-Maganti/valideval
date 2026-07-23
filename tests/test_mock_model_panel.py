from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.models.mock import (
    AlwaysA,
    ContextAwareMock,
    FormatFragile,
    KeywordMatcher,
    ShortcutExploiter,
)
from valideval.models.panel import load_panel


def test_mock_panel_contains_expected_models():
    panel = load_panel("mock")

    assert panel.model_ids == [
        "always_a",
        "majority_label",
        "keyword_matcher",
        "shortcut_exploiter",
        "context_aware",
        "noisy_strong",
        "noisy_weak",
        "format_fragile",
    ]


def test_context_aware_mock_uses_context():
    benchmark = ToyMCQBenchmark()
    item = benchmark.load_items()[0]
    prompt = benchmark.render_prompt(item, "full")

    assert ContextAwareMock().generate(prompt).prediction == "B"


def test_keyword_matcher_uses_label_prior_variant():
    benchmark = ToyMCQBenchmark()
    item = benchmark.load_items()[11]
    prompt = benchmark.render_prompt(item, "label_prior_only")

    assert KeywordMatcher().generate(prompt).prediction == item.answer
    assert AlwaysA().generate(prompt).prediction == "A"


def test_shortcut_exploiter_uses_full_prompt_artifact_prior():
    benchmark = ToyMCQBenchmark()
    item = next(item for item in benchmark.load_items() if item.item_id == "toy_034")
    prompt = benchmark.render_prompt(item, "full")

    assert ShortcutExploiter().generate(prompt).prediction == item.answer


def test_format_fragile_fails_on_question_only_variant():
    benchmark = ToyMCQBenchmark()
    item = benchmark.load_items()[0]

    full = benchmark.render_prompt(item, "full")
    question_only = benchmark.render_prompt(item, "question_only")

    assert FormatFragile().generate(full).prediction == item.answer
    assert FormatFragile().generate(question_only).prediction == "unparseable"
