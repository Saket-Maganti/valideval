from __future__ import annotations

import inspect
import json
from pathlib import Path

from valideval.cli import main
from valideval.validation.decoupled_synthetic import (
    FixedDiagnosticReadout,
    FlawAgnosticSyntheticModel,
    build_decoupled_synthetic_preflight,
)
from valideval.validation.synthetic_benchmark import (
    LEGACY_SYNTHETIC_HARNESS_STATUS,
    LEGACY_SYNTHETIC_HARNESS_WARNING,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARAMETERS = {
    "is_flawed",
    "flaw_type",
    "flaw_family",
    "diagnostic",
    "target_flaw",
}


def test_decoupled_model_predict_api_excludes_hidden_flaw_inputs() -> None:
    signature = inspect.signature(FlawAgnosticSyntheticModel.predict)

    assert FORBIDDEN_PARAMETERS.isdisjoint(signature.parameters)
    assert list(signature.parameters) == ["self", "item", "variant"]


def test_fixed_readout_api_does_not_switch_by_flaw_family() -> None:
    signature = inspect.signature(FixedDiagnosticReadout.score_items)

    assert FORBIDDEN_PARAMETERS.isdisjoint(signature.parameters)
    assert list(signature.parameters) == ["self", "panel_outputs"]


def test_legacy_controlled_output_path_is_labeled_wiring_only() -> None:
    assert LEGACY_SYNTHETIC_HARNESS_STATUS == "legacy_wiring_only"
    assert "wiring/sanity-check" in LEGACY_SYNTHETIC_HARNESS_WARNING
    assert "independent diagnostic-validation evidence" in LEGACY_SYNTHETIC_HARNESS_WARNING


def test_decoupled_synthetic_preflight_writes_manifest_only(tmp_path: Path) -> None:
    output = tmp_path / "decoupled_preflight.json"

    payload = build_decoupled_synthetic_preflight(output=output, dry_run=True)

    assert output.exists()
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["mode"] == "dry_run_only"
    assert written["status"] == "dry_run_only"
    assert written["preflight_status"] == "dry_run_ready"
    assert written["legacy_harness_status"] == "legacy_wiring_only"
    assert written["hidden_label_guard"] == "pass"
    assert written["flaw_type_guard"] == "pass"
    assert written["fixed_readout_guard"] == "pass"
    assert written["claim_state"] == "RESULT_REQUIRED"
    assert written["evidence_state_impact"] == "none"
    assert written["generation_run"] is False
    assert written["model_inference_run"] is False
    assert written["auc_computed"] is False
    assert written["metrics_written"] is False
    assert written["model_api"]["forbidden_parameters_present"] == []
    assert written["readout_api"]["forbidden_parameters_present"] == []
    assert payload["manifest_path"] == str(output)


def test_decoupled_synthetic_cli_is_dry_run_only(tmp_path: Path) -> None:
    output = tmp_path / "cli_preflight.json"

    assert main(["decoupled-synthetic-preflight", "--output", str(output), "--dry-run"]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == "dry_run_only"
    assert payload["status"] == "dry_run_only"
    assert payload["preflight_status"] == "dry_run_ready"
    assert payload["generation_run"] is False
    assert payload["model_inference_run"] is False
    assert payload["auc_computed"] is False


def test_claim_docs_record_synthetic_demotion() -> None:
    required_docs = [
        "SYNTHETIC_HARNESS_CIRCULARITY_AUDIT.md",
        "SYNTHETIC_EVIDENCE_STATUS_TABLE.md",
        "NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md",
        "paper/claims.md",
        "paper/diagnostic_validation.md",
        "paper/limitations.md",
    ]

    for relative_path in required_docs:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "wiring/sanity-check" in text or "DEMOTED_TO_WIRING_CHECK" in text
        assert "RESULT_REQUIRED" in text


def test_paper_claims_do_not_promote_synthetic_results_as_main_evidence() -> None:
    paper_files = list((REPO_ROOT / "paper").rglob("*.md")) + list(
        (REPO_ROOT / "paper").rglob("*.tex")
    )
    offenders = []
    for path in paper_files:
        text = path.read_text(encoding="utf-8")
        if "primary positive evidence" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []
