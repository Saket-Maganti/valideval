from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from valideval.execution.datasets import PublicInferenceItem, reject_gold_fields


class PromptRenderingError(ValueError):
    """Raised when a prompt cannot be rendered without crossing the gold boundary."""


def render_prompt(item: PublicInferenceItem, contract: Mapping[str, Any]) -> str:
    if not isinstance(item, PublicInferenceItem):
        if isinstance(item, Mapping):
            reject_gold_fields(item)
        raise PromptRenderingError("renderer requires PublicInferenceItem, not a raw dataset row")
    public = item.to_dict()
    reject_gold_fields(public)
    benchmark_id = item.benchmark_id
    if benchmark_id != contract.get("benchmark_id"):
        raise PromptRenderingError("item and benchmark contract disagree")
    if benchmark_id == "mmlu":
        return _render_mmlu(item, contract)
    if benchmark_id == "gsm8k":
        return _render_gsm8k(item, contract)
    if benchmark_id == "bbh":
        return _render_bbh(item, contract)
    raise PromptRenderingError(f"unsupported benchmark: {benchmark_id}")


def _render_mmlu(item: PublicInferenceItem, contract: Mapping[str, Any]) -> str:
    if len(item.choices) != 4:
        raise PromptRenderingError(f"MMLU item {item.item_id} does not have four choices")
    labels = ("A", "B", "C", "D")
    options = "\n".join(
        f"{label}. {choice}" for label, choice in zip(labels, item.choices, strict=True)
    )
    instruction = str(
        contract.get(
            "prompt_instruction",
            "Answer the multiple-choice question. Return only one uppercase letter: A, B, C, or D.",
        )
    )
    return f"{instruction}\n\nQuestion: {item.prompt_input}\n{options}\n\nAnswer:"


def _render_gsm8k(item: PublicInferenceItem, contract: Mapping[str, Any]) -> str:
    instruction = str(
        contract.get(
            "prompt_instruction",
            "Solve the problem. Show your reasoning, then write the final numeric answer as "
            "'Final answer: <number>'.",
        )
    )
    return f"{instruction}\n\nProblem: {item.prompt_input}\n\nSolution:"


def _render_bbh(item: PublicInferenceItem, contract: Mapping[str, Any]) -> str:
    policies = contract.get("task_prompt_policies")
    if not isinstance(policies, Mapping):
        raise PromptRenderingError("BBH contract has no task_prompt_policies mapping")
    policy = policies.get(item.subtask_id)
    if not isinstance(policy, Mapping):
        raise PromptRenderingError(f"BBH task has no frozen prompt policy: {item.subtask_id}")
    instruction = str(policy.get("instruction", "")).strip()
    answer_format = str(policy.get("answer_format", "")).strip()
    if not instruction or not answer_format:
        raise PromptRenderingError(f"incomplete prompt policy for BBH task {item.subtask_id}")
    return (
        f"{instruction}\n\n{item.prompt_input}\n\n"
        f"Return the final answer using this format: {answer_format}\nFinal answer:"
    )
