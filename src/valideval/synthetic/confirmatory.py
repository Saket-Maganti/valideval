"""Dry-run and non-evidence fixture orchestration for V5 synthetic validation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from valideval.synthetic.contracts import (
    FixedSyntheticReadout,
    assert_public_synthetic_isolation,
    build_non_evidence_fixture,
)

REQUIRED_EXPERIMENTS = frozenset(
    {
        "no_flaw",
        "one_flaw",
        "multiple_flaws",
        "unseen_flaw",
        "severity_sweep",
        "prevalence_sweep",
        "panel_size_sweep",
        "item_count_sweep",
        "model_family_dependence",
        "missingness",
        "correlated_flaws",
        "label_permutation",
        "diagnostic_ablation",
        "negative_controls",
    }
)
REQUIRED_FREEZE_FIELDS = frozenset(
    {
        "generator_families",
        "primary_diagnostics",
        "primary_metric",
        "threshold_policy",
        "sample_sizes",
        "seeds",
        "success_criteria",
        "exclusions",
        "held_out_generator_families",
    }
)


def load_confirmatory_config(path: str | Path) -> dict[str, Any]:
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("confirmatory synthetic config must be a mapping")
    return value


def validate_confirmatory_config(config: Mapping[str, Any]) -> dict[str, Any]:
    experiments = config.get("experiments")
    freeze = config.get("preregistration_freeze")
    experiment_names = set(experiments) if isinstance(experiments, Mapping) else set()
    freeze_names = set(freeze) if isinstance(freeze, Mapping) else set()
    missing_experiments = sorted(REQUIRED_EXPERIMENTS - experiment_names)
    missing_freeze_fields = sorted(REQUIRED_FREEZE_FIELDS - freeze_names)
    problems: list[str] = []
    if config.get("schema_version") != "5.0":
        problems.append("schema_version must equal '5.0'")
    if config.get("evidence_status") != "PLANNED":
        problems.append("evidence_status must remain PLANNED before confirmatory execution")
    if config.get("claim_state") != "RESULT_REQUIRED":
        problems.append("claim_state must remain RESULT_REQUIRED")
    if missing_experiments:
        problems.append("missing experiments: " + ", ".join(missing_experiments))
    if missing_freeze_fields:
        problems.append("missing preregistration fields: " + ", ".join(missing_freeze_fields))
    heldout = (
        (freeze or {}).get("held_out_generator_families", []) if isinstance(freeze, Mapping) else []
    )
    generators = (freeze or {}).get("generator_families", []) if isinstance(freeze, Mapping) else []
    if not heldout:
        problems.append("at least one held-out generator family is required")
    if set(heldout) & set(generators):
        problems.append("held-out generator families must be disjoint from development families")
    return {
        "valid": not problems,
        "problems": problems,
        "missing_experiments": missing_experiments,
        "missing_preregistration_fields": missing_freeze_fields,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def run_confirmatory_synthetic_v5(
    config_path: str | Path,
    *,
    public_output_dir: str | Path,
    private_output_dir: str | Path,
    mode: str = "dry-run",
) -> dict[str, Any]:
    """Validate the freeze or exercise a fixture; never run confirmatory evidence here."""

    if mode not in {"dry-run", "fixture"}:
        raise ValueError("mode must be 'dry-run' or 'fixture'; confirmatory execution is gated")
    public_dir = Path(public_output_dir)
    private_dir = Path(private_output_dir)
    if public_dir.resolve() == private_dir.resolve() or _is_relative_to(private_dir, public_dir):
        raise ValueError(
            "private synthetic truth must not be inside the diagnostic-visible directory"
        )
    config_file = Path(config_path)
    config = load_confirmatory_config(config_file)
    validation = validate_confirmatory_config(config)
    if not validation["valid"]:
        raise ValueError(
            "invalid confirmatory synthetic config: " + "; ".join(validation["problems"])
        )
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = public_dir / "synthetic_run_manifest_v5.json"
    base_manifest: dict[str, Any] = {
        "schema_version": "5.0",
        "mode": mode,
        "config_path": str(config_file),
        "config_sha256": _sha256(config_file),
        "config_validation": validation,
        "confirmatory_execution_run": False,
        "primary_metric_computed": False,
        "threshold_tuned": False,
        "claim_state": "RESULT_REQUIRED",
    }

    if mode == "dry-run":
        manifest = {
            **base_manifest,
            "status": "SYNTHETIC_PROTOCOL_READY",
            "evidence_status": "PLANNED",
            "generation_run": False,
            "diagnostic_run": False,
            "fixture_artifacts": {},
        }
        _write_json(manifest_path, manifest)
        return {**manifest, "manifest_json": str(manifest_path)}

    fixture = config.get("fixture") or {}
    seed = int(fixture.get("seed", 20260715))
    item_count = int(fixture.get("item_count", 12))
    panel_size = int(fixture.get("panel_size", 4))
    public_items, hidden_truth, responses = build_non_evidence_fixture(
        seed=seed,
        item_count=item_count,
        panel_size=panel_size,
    )
    public_payload = [asdict(item) for item in public_items]
    response_payload = [asdict(row) for row in responses]
    assert_public_synthetic_isolation(public_payload)
    assert_public_synthetic_isolation(response_payload)
    public_items_path = public_dir / "observable_fixture_items_v5.jsonl"
    responses_path = public_dir / "observable_fixture_responses_v5.jsonl"
    scores_path = public_dir / "fixture_readout_scores_v5.json"
    truth_path = private_dir / "private_fixture_truth_v5.jsonl"
    _write_jsonl(public_items_path, public_payload)
    _write_jsonl(responses_path, response_payload)
    _write_jsonl(truth_path, [asdict(row) for row in hidden_truth])
    fixture_scores = FixedSyntheticReadout().score(responses)
    _write_json(
        scores_path,
        {
            "artifact_class": "NON_EVIDENCE_FIXTURE",
            "scores": fixture_scores,
            "claim_state": "RESULT_REQUIRED",
        },
    )
    manifest = {
        **base_manifest,
        "status": "SYNTHETIC_FIXTURE_PASS",
        "evidence_status": "NON_EVIDENCE_FIXTURE",
        "generation_run": True,
        "diagnostic_run": True,
        "fixture_artifacts": {
            "public_items_jsonl": str(public_items_path),
            "public_responses_jsonl": str(responses_path),
            "fixture_scores_json": str(scores_path),
            "public_items_sha256": _sha256(public_items_path),
            "public_responses_sha256": _sha256(responses_path),
            "private_truth_sha256": _sha256(truth_path),
        },
        "limitations": [
            "Fixture scores validate deterministic plumbing only.",
            "No confirmatory metric, threshold, recovery estimate, or paper evidence was produced.",
        ],
    }
    _write_json(manifest_path, manifest)
    private_manifest_path = private_dir / "private_fixture_manifest_v5.json"
    _write_json(
        private_manifest_path,
        {
            "schema_version": "5.0",
            "packet": "PRIVATE_NOT_FOR_DIAGNOSTIC_PIPELINE",
            "truth_jsonl": str(truth_path),
            "truth_sha256": _sha256(truth_path),
            "claim_state": "RESULT_REQUIRED",
        },
    )
    return {
        **manifest,
        "manifest_json": str(manifest_path),
        "private_manifest_json": str(private_manifest_path),
    }
