from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from valideval.execution.config import V6ConfigurationError, load_run_config
from valideval.execution.models import load_panel_config
from valideval.execution.runner import _load_contract

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("benchmark", ["mmlu", "gsm8k", "bbh"])
def test_frozen_v6_run_configs_resolve_exact_hashes(benchmark: str):
    config = load_run_config(
        ROOT / f"configs/runs/{benchmark}_s1_v6.yaml",
        repository_root=ROOT,
    )
    assert config.mode == "smoke"
    assert config.evidence_class == "ENGINEERING_ONLY"
    subset = json.loads((ROOT / config.subset_manifest).read_text(encoding="utf-8"))
    assert subset["item_count"] == 50
    assert len(subset["items"]) == 50
    assert len({item["item_id"] for item in subset["items"]}) == 50
    contract = _load_contract(ROOT / config.benchmark_contract, benchmark)
    assert contract["few_shot_policy"] == "zero_shot_s1_v6"
    assert contract["few_shot_ids"] == []


def test_exact_panel_has_five_public_immutable_checkpoints():
    panel = load_panel_config(ROOT / "configs/panels/s1_smoke_exact_v6.yaml")
    assert len(panel["models"]) == 5
    assert len({model["family"] for model in panel["models"]}) == 3
    assert all(model["revision"] and len(model["revision"]) == 40 for model in panel["models"])
    assert all(model["quantization_fallback"] is None for model in panel["models"])
    assert panel["scientific_panel_adequacy"] is False


def test_hash_drift_fails_closed(tmp_path: Path):
    source = yaml.safe_load((ROOT / "configs/runs/mmlu_s1_v6.yaml").read_text(encoding="utf-8"))
    source["benchmark_contract_sha256"] = "0" * 64
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(source), encoding="utf-8")
    with pytest.raises(V6ConfigurationError, match="hash mismatch"):
        load_run_config(path, repository_root=ROOT)
