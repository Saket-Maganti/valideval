from __future__ import annotations

import json
from pathlib import Path

import pytest

from valideval.synthetic.confirmatory import (
    REQUIRED_EXPERIMENTS,
    load_confirmatory_config,
    run_confirmatory_synthetic_v5,
    validate_confirmatory_config,
)
from valideval.synthetic.contracts import assert_public_synthetic_isolation

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / "configs" / "synthetic" / "confirmatory_synthetic_v5.yaml"


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_confirmatory_config_freezes_all_required_experiments() -> None:
    config = load_confirmatory_config(CONFIG)
    validation = validate_confirmatory_config(config)

    assert validation["valid"] is True
    assert REQUIRED_EXPERIMENTS.issubset(config["experiments"])
    assert config["claim_state"] == "RESULT_REQUIRED"
    assert config["evidence_status"] == "PLANNED"


def test_dry_run_writes_no_generation_or_metric_claim(tmp_path: Path) -> None:
    result = run_confirmatory_synthetic_v5(
        CONFIG,
        public_output_dir=tmp_path / "public",
        private_output_dir=tmp_path / "private",
        mode="dry-run",
    )

    assert result["status"] == "SYNTHETIC_PROTOCOL_READY"
    assert result["generation_run"] is False
    assert result["primary_metric_computed"] is False
    assert result["claim_state"] == "RESULT_REQUIRED"
    assert list((tmp_path / "public").iterdir()) == [Path(result["manifest_json"])]


def test_fixture_outputs_are_decoupled_and_non_evidence(tmp_path: Path) -> None:
    result = run_confirmatory_synthetic_v5(
        CONFIG,
        public_output_dir=tmp_path / "public",
        private_output_dir=tmp_path / "private",
        mode="fixture",
    )
    artifacts = result["fixture_artifacts"]
    public_items = _jsonl(Path(artifacts["public_items_jsonl"]))
    public_responses = _jsonl(Path(artifacts["public_responses_jsonl"]))

    assert result["status"] == "SYNTHETIC_FIXTURE_PASS"
    assert result["evidence_status"] == "NON_EVIDENCE_FIXTURE"
    assert result["claim_state"] == "RESULT_REQUIRED"
    assert result["primary_metric_computed"] is False
    assert_public_synthetic_isolation(public_items)
    assert_public_synthetic_isolation(public_responses)
    assert not any("truth" in path.name for path in (tmp_path / "public").iterdir())
    assert any("truth" in path.name for path in (tmp_path / "private").iterdir())


def test_private_truth_cannot_be_nested_under_public_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not be inside"):
        run_confirmatory_synthetic_v5(
            CONFIG,
            public_output_dir=tmp_path / "public",
            private_output_dir=tmp_path / "public" / "private",
            mode="fixture",
        )


def test_real_confirmatory_mode_is_not_available_in_pre_execution_build(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="gated"):
        run_confirmatory_synthetic_v5(
            CONFIG,
            public_output_dir=tmp_path / "public",
            private_output_dir=tmp_path / "private",
            mode="confirmatory",
        )
