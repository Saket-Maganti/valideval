from __future__ import annotations

from pathlib import Path

import pytest

from valideval.statistics.claim_policy_v7_2_1 import (
    CLAIM_FAMILIES,
    GENERIC_V7_2_RESULT,
    POLICY_CONFIRMATION,
    POLICY_DEVELOPMENT,
    POLICY_VALIDATION,
    build_native_scenarios,
    load_native_policy_spec,
    native_policy_confirmation,
    native_policy_development,
    validate_policy_freeze,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/statistics/claim_policy_v7_2_1.yaml"


@pytest.fixture(scope="module")
def specification() -> dict:
    return load_native_policy_spec(CONFIG)


def test_native_registry_has_disjoint_splits_and_generators(specification: dict) -> None:
    split_scenarios = {
        split: build_native_scenarios(specification, split, quick=True)
        for split in (POLICY_DEVELOPMENT, POLICY_VALIDATION, POLICY_CONFIRMATION)
    }
    ids = {split: {row.scenario_id for row in rows} for split, rows in split_scenarios.items()}
    seeds = {split: {row.seed for row in rows} for split, rows in split_scenarios.items()}
    generators = {split: {row.generator for row in rows} for split, rows in split_scenarios.items()}
    for left_index, left in enumerate(ids):
        for right in list(ids)[left_index + 1 :]:
            assert not ids[left].intersection(ids[right])
            assert not seeds[left].intersection(seeds[right])
            assert not generators[left].intersection(generators[right])
    assert {row.claim_family for row in split_scenarios[POLICY_CONFIRMATION]} == set(CLAIM_FAMILIES)


def test_gaussian_mixture_is_declared_as_an_actual_mixture(specification: dict) -> None:
    assert specification["gaussian_mixture_implementation"] == "ACTUAL_TWO_COMPONENT_MIXTURE"


def test_quick_native_development_and_confirmation_are_non_evidence(
    specification: dict,
) -> None:
    records, selection, freeze = native_policy_development(specification, quick=True)
    selected = validate_policy_freeze(freeze)
    assert selection["mode"] == "NON_EVIDENCE_FIXTURE"
    assert selected.policy_id == selection["selected_policy_id"]
    assert records["claim_family"].nunique() == len(CLAIM_FAMILIES)
    confirmation_records, confirmation = native_policy_confirmation(
        specification, freeze, quick=True
    )
    assert confirmation["status"] == "NON_EVIDENCE_FIXTURE"
    assert confirmation["generic_v7_2_result_preserved"] == GENERIC_V7_2_RESULT
    assert len(confirmation_records) == len(CLAIM_FAMILIES) * 120


def test_policy_freeze_rejects_mutation(specification: dict) -> None:
    _, _, freeze = native_policy_development(specification, quick=True)
    freeze["policy"]["confidence_level"] = 0.5
    with pytest.raises(ValueError, match="freeze hash mismatch"):
        validate_policy_freeze(freeze)
