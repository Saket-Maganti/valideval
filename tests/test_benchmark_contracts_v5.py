from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FIELDS = {
    "benchmark_id",
    "benchmark_version",
    "dataset_source",
    "dataset_revision",
    "split",
    "subtasks",
    "item_id_method",
    "prompt_template_version",
    "few_shot_policy",
    "few_shot_examples_hash",
    "chat_template_policy",
    "generation_mode",
    "generation_parameters",
    "scoring_version",
    "extraction_version",
    "failure_taxonomy",
    "license",
    "redistribution_policy",
    "expected_item_count",
}
REQUIRED_FAILURES = {
    "SUCCESS",
    "MODEL_LOAD_FAILURE",
    "OOM",
    "TIMEOUT",
    "GENERATION_FAILURE",
    "EMPTY_OUTPUT",
    "TRUNCATED_OUTPUT",
    "EXTRACTION_FAILURE",
    "INVALID_FORMAT",
    "SCORING_FAILURE",
    "DATASET_FAILURE",
    "UNKNOWN_FAILURE",
}


def _contract(name: str) -> dict:
    path = ROOT / "configs" / "benchmarks" / f"{name}_v5.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_v5_benchmark_contracts_are_complete_and_frozen() -> None:
    for benchmark in ("mmlu", "gsm8k", "bbh"):
        contract = _contract(benchmark)
        assert REQUIRED_FIELDS <= set(contract)
        assert len(contract["dataset_revision"]) == 40
        assert contract["expected_item_count"] > 0
        assert contract["subtasks"]
        assert len(contract["subtasks"]) == len(set(contract["subtasks"]))
        assert REQUIRED_FAILURES == set(contract["failure_taxonomy"])
        assert contract["generation_parameters"]["do_sample"] is False
        assert contract["claim_state"] == "RESULT_REQUIRED"


def test_v5_contract_specific_counts_and_gold_isolation() -> None:
    mmlu = _contract("mmlu")
    gsm8k = _contract("gsm8k")
    bbh = _contract("bbh")

    assert len(mmlu["subtasks"]) == 57
    assert mmlu["expected_item_count"] == 14_042
    assert gsm8k["expected_item_count"] == 1_319
    assert len(bbh["subtasks"]) == 27
    assert bbh["expected_item_count"] == 6_511
    assert mmlu["scoring_contract"]["gold_answer_feedback_forbidden"] is True
    assert gsm8k["numeric_extraction_contract"]["gold_answer_feedback_forbidden"] is True
    assert bbh["task_contract"]["gold_answer_feedback_forbidden"] is True
