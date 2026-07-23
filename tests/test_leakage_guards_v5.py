from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from valideval.leakage.guards import (
    DiagnosticLabelLeakageError,
    ModelExecutionIdentity,
    assert_diagnostic_inputs_isolated,
    assert_neutral_artifact_name,
    build_overlap_candidates,
    compare_model_execution_identity,
    normalize_text,
    normalized_text_hash,
    option_aware_hash,
    option_set_hash,
    write_overlap_candidates_csv,
)


def test_normalization_and_hashes_are_explicit_and_deterministic() -> None:
    left = "<p>What\u00a0is \u201cvalidity\u201d?</p>"
    right = 'what is "validity"?'

    assert normalize_text(left) == normalize_text(right)
    assert normalized_text_hash(left) == normalized_text_hash(right)


def test_option_hash_distinguishes_order_and_detects_permutations() -> None:
    ordered = ["(A) alpha", "(B) beta", "(C) gamma"]
    permuted = ["C) gamma", "A) alpha", "B) beta"]

    assert option_aware_hash("Question", ordered) != option_aware_hash("Question", permuted)
    assert option_set_hash("Question", ordered) == option_set_hash("Question", permuted)


def test_overlap_candidates_cover_exact_permutation_and_fuzzy_paths(tmp_path: Path) -> None:
    candidates = build_overlap_candidates(
        {
            "mmlu": [
                {
                    "item_id": "m1",
                    "question": "Which planet is closest to the Sun?",
                    "choices": ["Mercury", "Venus"],
                },
                {
                    "item_id": "m2",
                    "question": "A long repeated token sequence about causal inference validity",
                    "choices": ["A", "B"],
                },
            ],
            "bbh": [
                {
                    "item_id": "b1",
                    "question": "Which planet is closest to the Sun?",
                    "choices": ["Venus", "Mercury"],
                },
                {
                    "item_id": "b2",
                    "question": "A long repeated token sequence about causal inference validity audit",
                    "choices": ["yes", "no"],
                },
            ],
        },
        fuzzy_threshold=0.7,
    )

    assert {row.match_type for row in candidates} == {
        "OPTION_PERMUTATION",
        "TOKEN_NGRAM_CANDIDATE",
    }
    assert all(row.manual_review_required for row in candidates)
    output = write_overlap_candidates_csv(tmp_path / "overlap.csv", candidates)
    assert output.read_text(encoding="utf-8").startswith("left_dataset,left_item_id")


def test_diagnostic_label_and_path_leakage_fail_closed() -> None:
    assert_diagnostic_inputs_isolated({"item_id": "neutral", "responses": ["A", "B"]})

    with pytest.raises(DiagnosticLabelLeakageError, match="human_label"):
        assert_diagnostic_inputs_isolated({"metadata": {"human_label": "bad_item"}})
    with pytest.raises(DiagnosticLabelLeakageError, match="high_risk"):
        assert_neutral_artifact_name("inputs/high_risk/items.jsonl")


def test_exact_execution_identity_rejects_unknowns_and_revision_drift() -> None:
    identity = ModelExecutionIdentity(
        canonical_model_id="Qwen/Qwen2.5-0.5B-Instruct",
        checkpoint="Qwen/Qwen2.5-0.5B-Instruct",
        revision="abc123",
        quantization_class="unquantized",
        base_or_instruction="instruction",
        chat_template="tokenizer-v1",
        prompt_regime="zero-shot-v5",
        decoding_hash="decode123",
        extraction_version="choice-v5",
    )
    assert compare_model_execution_identity(identity, identity).exact_match is True

    planned = ModelExecutionIdentity(**{**identity.__dict__, "revision": "PLANNED_UNVERIFIED"})
    comparison = compare_model_execution_identity(identity, planned)
    assert comparison.exact_match is False
    assert comparison.mismatched_fields == ("revision",)


def test_model_registry_separates_studies_and_freezes_s0_through_s5() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = yaml.safe_load(
        (root / "configs" / "models" / "model_registry_v5.yaml").read_text(encoding="utf-8")
    )
    required_fields = {
        "canonical_model_id",
        "checkpoint",
        "revision",
        "architecture_family",
        "base_or_instruction",
        "chat_template",
        "mmlu_historical_id",
        "gsm8k_planned_id",
        "bbh_planned_id",
        "exact_identity_status",
        "runnable_on_t4",
        "known_limitations",
    }

    assert set(registry["studies"]) == {"study_h", "study_c"}
    assert set(registry["tiers"]) == {f"S{index}" for index in range(6)}
    assert len(registry["studies"]["study_h"]["historical_model_aliases"]) == 39
    assert all(required_fields.issubset(model) for model in registry["models"])
    candidates = [
        model
        for model in registry["models"]
        if model["exact_identity_status"] != "NON_EVIDENCE_FIXTURE"
    ]
    frozen = [
        model
        for model in candidates
        if model["exact_identity_status"] == "FROZEN_IMMUTABLE_REVISION"
    ]
    blocked = [
        model
        for model in candidates
        if model["exact_identity_status"] == "PLANNED_REVISION_REQUIRED"
    ]
    assert len(frozen) == 5
    assert len(blocked) == 1
    assert all(len(model["revision"]) == 40 for model in frozen)
    assert all(model["chat_template"].startswith("sha256:") for model in frozen)
    assert all(model["studies"] == ["study_c"] for model in candidates)
