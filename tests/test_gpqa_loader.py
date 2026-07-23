from __future__ import annotations

import pytest

from valideval.benchmarks.base import get_benchmark
from valideval.benchmarks.gpqa import GPQADiamondJSONLBenchmark
from valideval.models.panel import load_panel


def test_gpqa_fixture_loader_validates_and_renders_prompts():
    benchmark = get_benchmark("gpqa_diamond_tiny_fixture")
    items = benchmark.load_items()

    assert benchmark.benchmark_id == "gpqa_diamond_tiny_fixture"
    assert len(items) == 6
    assert items[0].metadata["artifact_scope"] == "gpqa_fixture_dry_run"
    assert items[0].metadata["is_synthetic_fixture"] is True
    assert "full" in benchmark.available_prompt_variants()
    assert "randomized_choices" in benchmark.available_prompt_variants()

    prompt = benchmark.render_prompt(items[0], "full")
    assert "Return exactly one answer letter" in prompt
    assert "B. E4 to E1" in prompt

    randomized = benchmark.render_prompt(items[0], "randomized_choices")
    assert "B. E4 to E1" in randomized
    assert benchmark.score_prediction(items[0], "B").is_correct is True


def test_gpqa_exploratory_prompt_file_does_not_change_primary_variant_list():
    benchmark = get_benchmark("gpqa_diamond_tiny_fixture")
    item = benchmark.load_items()[0]

    assert "full_answer_only_v2" not in benchmark.available_prompt_variants()
    prompt = benchmark.render_prompt(item, "full_answer_only_v2")
    assert "Return exactly one letter" in prompt


def test_gpqa_loader_requires_local_path_for_real_benchmark():
    with pytest.raises(ValueError, match="requires --local-path"):
        get_benchmark("gpqa_diamond")


def test_gpqa_loader_rejects_duplicate_item_ids(tmp_path):
    path = tmp_path / "gpqa.jsonl"
    row = (
        '{"item_id":"x","question":"Which option?","choices":{"A":"one","B":"two",'
        '"C":"three","D":"four"},"answer":"A","metadata":{}}\n'
    )
    path.write_text(row + row, encoding="utf-8")

    benchmark = GPQADiamondJSONLBenchmark(path)
    with pytest.raises(ValueError, match="Duplicate GPQA item_id"):
        benchmark.load_items()


def test_gpqa_loader_rejects_metadata_answer_leakage(tmp_path):
    path = tmp_path / "gpqa.jsonl"
    path.write_text(
        (
            '{"item_id":"x","question":"Which option?","choices":{"A":"one","B":"two",'
            '"C":"three","D":"four"},"answer":"C","metadata":{"answer_hint":"C"}}\n'
        ),
        encoding="utf-8",
    )

    benchmark = GPQADiamondJSONLBenchmark(path)
    with pytest.raises(ValueError, match="may leak the answer"):
        benchmark.load_items()


def test_gpqa_loader_rejects_bad_choice_schema(tmp_path):
    path = tmp_path / "gpqa.jsonl"
    path.write_text(
        (
            '{"item_id":"x","question":"Which option?","choices":{"A":"one","B":"two",'
            '"C":"three"},"answer":"C","metadata":{}}\n'
        ),
        encoding="utf-8",
    )

    benchmark = GPQADiamondJSONLBenchmark(path)
    with pytest.raises(ValueError, match="exactly choices A/B/C/D"):
        benchmark.load_items()


def test_gpqa_open_local_panel_loads_as_cached_output_plan():
    panel = load_panel("gpqa_open_local")

    assert panel.panel_id == "gpqa_open_local"
    assert len(panel.models) >= 8
    with pytest.raises(ValueError, match="configured for cached outputs"):
        panel.models[0].generate("prompt")
