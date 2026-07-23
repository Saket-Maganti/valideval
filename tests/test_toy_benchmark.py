import pytest

from valideval.benchmarks.toy import ToyMCQBenchmark


def test_toy_benchmark_loads_items_and_variants():
    benchmark = ToyMCQBenchmark()
    items = benchmark.load_items()

    assert len(items) == 36
    assert "context_removed" in benchmark.available_prompt_variants()
    assert "label_prior_only" in benchmark.available_prompt_variants()
    assert "metadata_only" in benchmark.available_prompt_variants()
    assert "verbose_instructions" in benchmark.available_prompt_variants()


def test_toy_prompt_variants_remove_expected_information():
    benchmark = ToyMCQBenchmark()
    item = benchmark.load_items()[0]

    full = benchmark.render_prompt(item, "full")
    context_removed = benchmark.render_prompt(item, "context_removed")
    choices_only = benchmark.render_prompt(item, "choices_only")
    metadata_only = benchmark.render_prompt(item, "metadata_only")

    assert "glucose" in full
    assert "[removed]" in context_removed
    assert "Question:" not in choices_only
    assert "Label prior" in metadata_only


def test_toy_mcq_scoring():
    benchmark = ToyMCQBenchmark()
    item = benchmark.load_items()[0]

    assert benchmark.score_prediction(item, "B").is_correct is True
    assert benchmark.score_prediction(item, "A").score == 0.0


def test_toy_mcq_scoring_accepts_declared_answer_lists():
    benchmark = ToyMCQBenchmark()
    item = next(item for item in benchmark.load_items() if item.item_id == "toy_029")

    assert benchmark.score_prediction(item, "B").is_correct is True
    assert benchmark.score_prediction(item, "C").is_correct is True
    assert benchmark.score_prediction(item, "A").score == 0.0


def test_unknown_variant_fails_helpfully():
    benchmark = ToyMCQBenchmark()
    with pytest.raises(ValueError, match="Unknown prompt variant"):
        benchmark.render_prompt(benchmark.load_items()[0], "bad")
