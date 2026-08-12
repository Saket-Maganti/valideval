from __future__ import annotations

from pathlib import Path

import pytest

from valideval.statistics.claim_policy_v7_2 import (
    POLICY_CONFIRMATION,
    POLICY_DEVELOPMENT,
    POLICY_VALIDATION,
    assert_split_isolation,
    build_scenario_registry,
    confirm_frozen_policy,
    evaluate_candidates,
    freeze_policy_payload,
    load_candidate_policies,
    select_primary_policy,
    split_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "configs/statistics/claim_policy_v7_2_scenarios.yaml"
CANDIDATES = ROOT / "configs/statistics/claim_policy_v7_2_candidates.yaml"


def test_policy_splits_have_disjoint_seeds_generators_and_rows() -> None:
    registry = build_scenario_registry(SCENARIOS, replicates_per_claim_family=45)
    assert_split_isolation(registry)
    manifests = {
        split: split_manifest(registry, split)
        for split in (POLICY_DEVELOPMENT, POLICY_VALIDATION, POLICY_CONFIRMATION)
    }
    assert len({manifest["rows_sha256"] for manifest in manifests.values()}) == 3
    assert len({manifest["scenario_ids_sha256"] for manifest in manifests.values()}) == 3
    generators = [set(manifest["generator_versions"]) for manifest in manifests.values()]
    assert not generators[0].intersection(generators[1])
    assert not generators[1].intersection(generators[2])


def test_seed_leakage_fails_closed() -> None:
    registry = build_scenario_registry(SCENARIOS, replicates_per_claim_family=30)
    development_seed = registry.loc[
        registry["split"] == POLICY_DEVELOPMENT, "seed"
    ].iloc[0]
    validation_index = registry.index[registry["split"] == POLICY_VALIDATION][0]
    registry.loc[validation_index, "seed"] = development_seed
    with pytest.raises(ValueError, match="seed leakage"):
        assert_split_isolation(registry)


def test_selected_policy_is_nonvacuous_and_confirmation_is_untouched() -> None:
    registry = build_scenario_registry(SCENARIOS, replicates_per_claim_family=60)
    candidates = load_candidate_policies(CANDIDATES)
    metrics, _ = evaluate_candidates(registry, candidates)
    selected, selection = select_primary_policy(metrics, candidates)
    manifests = {
        split: split_manifest(registry, split)
        for split in (POLICY_DEVELOPMENT, POLICY_VALIDATION, POLICY_CONFIRMATION)
    }
    frozen = freeze_policy_payload(
        selected, scenario_manifests=manifests, selection=selection
    )
    _, confirmation = confirm_frozen_policy(registry, frozen)
    assert selection["true_license_power"] > 0.0
    assert selection["abstention_rate"] < 1.0
    assert selection["false_license_upper_95"] <= 0.05
    assert confirmation["status"] == "CLAIM_POLICY_CONFIRMATION_PASS"
    assert confirmation["split"] == POLICY_CONFIRMATION
    assert confirmation["split_leakage"] is False


def test_confirmation_rejects_policy_changed_after_freeze() -> None:
    registry = build_scenario_registry(SCENARIOS, replicates_per_claim_family=30)
    candidates = load_candidate_policies(CANDIDATES)
    metrics, _ = evaluate_candidates(registry, candidates)
    selected, selection = select_primary_policy(metrics, candidates)
    manifests = {
        split: split_manifest(registry, split)
        for split in (POLICY_DEVELOPMENT, POLICY_VALIDATION, POLICY_CONFIRMATION)
    }
    frozen = freeze_policy_payload(
        selected, scenario_manifests=manifests, selection=selection
    )
    frozen["policy"]["fdr"] = 0.5
    with pytest.raises(ValueError, match="hash mismatch"):
        confirm_frozen_policy(registry, frozen)
