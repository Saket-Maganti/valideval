from __future__ import annotations

import inspect

import pytest
import yaml

from valideval.execution.datasets import PublicInferenceItem, reject_gold_fields
from valideval.execution.prompts import render_prompt
from valideval.scoring.gsm8k import parse_gsm8k_answer
from valideval.scoring.mmlu import parse_mmlu_answer


def _public_item() -> PublicInferenceItem:
    return PublicInferenceItem(
        item_id="mmlu-subject-123",
        item_hash="a" * 64,
        benchmark_id="mmlu",
        subtask_id="subject",
        split="test",
        prompt_input="Question?",
        choices=("one", "two", "three", "four"),
        public_metadata={},
    )


def test_renderer_requires_gold_free_public_type():
    contract = yaml.safe_load(open("configs/benchmarks/mmlu_s1_v6.yaml", encoding="utf-8"))
    prompt = render_prompt(_public_item(), contract)
    assert "Question?" in prompt
    with pytest.raises(ValueError, match="gold-bearing"):
        render_prompt(
            {
                **_public_item().to_dict(),
                "gold_answer": "A",
            },
            contract,
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"gold": "A"},
        {"public_metadata": {"diagnostic": {"is_correct": True}}},
        {"items": [{"target": "private"}]},
    ],
)
def test_recursive_gold_guard_rejects_leaks(payload: object):
    with pytest.raises(ValueError, match="forbidden gold-bearing"):
        reject_gold_fields(payload)


def test_parsers_have_no_gold_parameter():
    for parser in (parse_mmlu_answer, parse_gsm8k_answer):
        parameters = set(inspect.signature(parser).parameters)
        assert not parameters.intersection(
            {"gold", "answer", "gold_answer", "correct_answer", "target"}
        )
