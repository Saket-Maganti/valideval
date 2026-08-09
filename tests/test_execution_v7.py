from __future__ import annotations

import json
from pathlib import Path

import pytest

from valideval.execution.config import load_run_config, load_yaml_mapping
from valideval.execution.models import load_panel_config
from valideval.execution.notebook_v7 import run_notebook_config_v7
from valideval.execution.runner import (
    _apply_robustness_contract,
    _load_contract,
    _validate_robustness_panel,
)
from valideval.scoring.gsm8k import parse_gsm8k_answer_strict

ROOT = Path(__file__).resolve().parents[1]


def test_all_frozen_v7_run_configs_resolve_hashes_and_contracts() -> None:
    paths = sorted((ROOT / "configs/runs_v7").glob("*.yaml"))
    assert len(paths) == 19
    for path in paths:
        config = load_run_config(path, repository_root=ROOT)
        panel = load_panel_config(ROOT / config.panel_config)
        contract = _load_contract(ROOT / config.benchmark_contract, config.benchmark_id)
        subset = json.loads((ROOT / config.subset_manifest).read_text(encoding="utf-8"))
        assert config.schema_version == "7.0"
        assert len(panel["models"]) == panel["model_count"]
        assert subset["item_count"] == contract["expected_item_count"]
        assert len({item["item_id"] for item in subset["items"]}) == subset["item_count"]
        if config.robustness_config:
            robustness = load_yaml_mapping(ROOT / config.robustness_config)
            _apply_robustness_contract(contract, robustness, config.benchmark_id)
            _validate_robustness_panel(panel, robustness)


@pytest.mark.parametrize(
    ("benchmark", "raw_count", "retired"),
    [("mmlu", 14042, 27), ("gsm8k", 1319, 0), ("bbh", 6511, 4)],
)
def test_scientific_manifests_record_exact_duplicate_retirement(
    benchmark: str, raw_count: int, retired: int
) -> None:
    contract = load_yaml_mapping(ROOT / f"configs/benchmarks/{benchmark}_scientific_v7.yaml")
    assert contract["raw_full_item_count"] == raw_count
    assert contract["exact_duplicate_items_retired"] == retired
    assert contract["expected_item_count"] == raw_count - retired


def test_v7_notebook_fixture_validates_production_config(tmp_path: Path) -> None:
    result = run_notebook_config_v7(
        ROOT / "configs/runs_v7/mmlu_s2_v7.yaml",
        mode="fixture",
        output_root=tmp_path,
    )
    assert result["evidence_class"] == "NON_EVIDENCE_FIXTURE"
    assert result["production_config_validated"] is True
    assert result["production_model_count"] == 8
    assert result["production_item_count"] == 200


def test_strict_gsm8k_parser_requires_one_explicit_marker() -> None:
    assert parse_gsm8k_answer_strict("work\nFinal answer: 12").value == "12"
    assert not parse_gsm8k_answer_strict("12").succeeded
    assert not parse_gsm8k_answer_strict("Final answer: 12\nFinal answer: 13").succeeded
