from __future__ import annotations

import ast
import inspect
import json
import textwrap
from pathlib import Path

import pytest

from valideval.validation.decoupled_synthetic import (
    FORBIDDEN_HIDDEN_METADATA_KEYS,
    FixedDiagnosticReadout,
    FlawAgnosticSyntheticModel,
    FlawAgnosticSyntheticModelConfig,
    ObservableItemFeatures,
    PanelOutput,
    build_decoupled_synthetic_preflight,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "decoupled_synthetic"
FORBIDDEN_PREDICT_PARAMETERS = {
    "is_flawed",
    "flaw_type",
    "label",
    "injected",
    "ground_truth_flaw",
}
FORBIDDEN_HIDDEN_FIELDS = {
    "is_flawed",
    "flaw_type",
    "injected_flaw",
    "ground_truth_flaw",
    "synthetic_label",
    "oracle_flaw",
}


def _fixture_payload(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _observable_from_payload(payload: dict[str, object]) -> ObservableItemFeatures:
    return ObservableItemFeatures(
        item_id=str(payload["item_id"]),
        prompt=str(payload["prompt"]),
        choices=[str(choice) for choice in payload["choices"]],
        answer=str(payload["answer"]) if payload.get("answer") is not None else None,
        subject=str(payload["subject"]) if payload.get("subject") is not None else None,
        metadata=dict(payload.get("metadata", {})),
    )


def test_predict_signature_excludes_hidden_and_label_inputs() -> None:
    signature = inspect.signature(FlawAgnosticSyntheticModel.predict)

    assert FORBIDDEN_PREDICT_PARAMETERS.isdisjoint(signature.parameters)
    assert list(signature.parameters) == ["self", "item", "variant"]


def test_observable_item_features_do_not_expose_hidden_flaw_fields() -> None:
    field_names = set(ObservableItemFeatures.__dataclass_fields__)

    assert FORBIDDEN_HIDDEN_FIELDS.isdisjoint(field_names)
    assert {"item_id", "prompt", "choices", "answer", "subject", "metadata"}.issubset(field_names)


def test_fixed_readout_branches_do_not_use_flaw_family_names() -> None:
    source = textwrap.dedent(inspect.getsource(FixedDiagnosticReadout.score_items))
    tree = ast.parse(source)
    branch_tests = [
        ast.unparse(node.test) for node in ast.walk(tree) if isinstance(node, (ast.If, ast.IfExp))
    ]
    forbidden_terms = FORBIDDEN_HIDDEN_FIELDS | {
        "shortcut_signal",
        "label_imbalance",
        "answer_length_artifact",
        "prompt_format_fragility",
        "low_discrimination",
        "negative_discrimination",
    }

    assert all(term not in branch_test for branch_test in branch_tests for term in forbidden_terms)


def test_preflight_manifest_records_no_run_and_guard_statuses(tmp_path: Path) -> None:
    output = tmp_path / "preflight.json"

    payload = build_decoupled_synthetic_preflight(output=output, dry_run=True)
    written = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "dry_run_only"
    assert written["preflight_status"] == "dry_run_ready"
    assert written["generation_run"] is False
    assert written["model_inference_run"] is False
    assert written["auc_computed"] is False
    assert written["metrics_written"] is False
    assert written["hidden_label_guard"] == "pass"
    assert written["flaw_type_guard"] == "pass"
    assert written["fixed_readout_guard"] == "pass"
    assert written["evidence_state_impact"] == "none"


def test_clean_observable_fixture_loads() -> None:
    item = _observable_from_payload(_fixture_payload("observable_item_clean.json"))

    assert item.item_id == "fixture_clean_001"
    assert item.public_metadata() == {
        "difficulty_band": "medium",
        "public_source": "fixture",
    }


def test_hidden_top_level_fixture_fields_are_rejected_by_dataclass() -> None:
    payload = _fixture_payload("observable_item_with_hidden_labels.json")

    with pytest.raises(TypeError):
        ObservableItemFeatures(**payload)


def test_hidden_metadata_fields_are_stripped_before_prediction() -> None:
    clean_item = _observable_from_payload(_fixture_payload("observable_item_clean.json"))
    hidden_item = _observable_from_payload(
        _fixture_payload("observable_item_with_hidden_labels.json")
    )
    model = FlawAgnosticSyntheticModel(
        FlawAgnosticSyntheticModelConfig(ability=0.2, format_sensitivity=0.1, seed=7)
    )

    assert FORBIDDEN_HIDDEN_FIELDS.issubset(FORBIDDEN_HIDDEN_METADATA_KEYS)
    assert FORBIDDEN_HIDDEN_FIELDS.isdisjoint(hidden_item.public_metadata())
    assert clean_item.public_metadata() == hidden_item.public_metadata()
    assert model.predict(clean_item) == model.predict(hidden_item)


def test_hidden_fields_cannot_reach_fixed_readout() -> None:
    signature = inspect.signature(FixedDiagnosticReadout.score_items)
    panel_fields = set(PanelOutput.__dataclass_fields__)
    readout = FixedDiagnosticReadout()

    assert FORBIDDEN_HIDDEN_FIELDS.isdisjoint(signature.parameters)
    assert FORBIDDEN_HIDDEN_FIELDS.isdisjoint(panel_fields)
    assert readout.score_items(
        [
            PanelOutput(
                item_id="fixture_clean_001",
                model_id="model_a",
                prediction="A",
                answer="A",
            )
        ]
    ) == {"fixture_clean_001": 0.0}


def test_legacy_and_paper_docs_keep_synthetic_demoted() -> None:
    docs = [
        "SYNTHETIC_EVIDENCE_STATUS_TABLE.md",
        "SYNTHETIC_HARNESS_CIRCULARITY_AUDIT.md",
        "SYNTHETIC_DEMOTION_AND_DECOUPLING_BUILD_AUDIT.md",
        "NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md",
        "CLAIMS_LEDGER_NEURIPS.md",
        "paper/CLAIMS_LEDGER.md",
        "paper/claims.md",
        "paper/diagnostic_validation.md",
        "paper/limitations.md",
    ]
    combined = "\n".join((REPO_ROOT / path).read_text(encoding="utf-8") for path in docs)

    assert "DEMOTED_TO_WIRING_CHECK" in combined
    assert "wiring/sanity-check" in combined
    assert "primary positive evidence" not in combined


def test_paper_claim_files_do_not_promote_legacy_synthetic_results() -> None:
    claim_files = [
        "CLAIMS_LEDGER_NEURIPS.md",
        "paper/CLAIMS_LEDGER.md",
        "paper/claims.md",
        "paper/diagnostic_validation.md",
        "paper/limitations.md",
        "paper/reframed_abstract_negative_result.md",
        "paper/reframed_intro_negative_result.md",
    ]
    forbidden_phrases = [
        "10/12 credible",
        "synthetic validation proves diagnostic validity",
        "synthetic validation is primary positive evidence",
    ]
    offenders: list[str] = []
    for relative_path in claim_files:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8").lower()
        for phrase in forbidden_phrases:
            if phrase in text:
                offenders.append(f"{relative_path}: {phrase}")

    assert offenders == []
