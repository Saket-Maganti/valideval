from __future__ import annotations

import hashlib
import json
from pathlib import Path

from valideval.execution.manifest import compute_configuration_hash
from valideval.planning.s3_proposal_v7_2_1 import propose_s3_from_s2
from valideval.release.final_cpu_maxout import build_structured_state
from valideval.release.machine_state_v7_2_1 import validate_machine_state
from valideval.release.pre_gpu_bundle_v7_2_1 import build_pre_gpu_bundle
from valideval.release.validation_v7_2_1 import REQUIRED_REPORTS

ROOT = Path(__file__).resolve().parents[1]


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_reported_claim_policy_numbers_come_from_structured_artifacts() -> None:
    state = build_structured_state(ROOT)
    source = _json("results/final_cpu_maxout/claim_policy/confirmation_summary.json")
    assert state["claim_policy"]["records_sha256"] == source["records_sha256"]
    report = (ROOT / "reports/final_cpu_maxout/CPU_MAXOUT_CLAIM_POLICY.md").read_text()
    overall = source["overall"]
    assert f"{100 * overall['false_license_rate']:.3f}%" in report
    assert f"{100 * overall['true_license_power']:.3f}%" in report
    assert "21 of 60" in report


def test_report_manifest_hashes_every_generated_report() -> None:
    manifest = _json("results/final_cpu_maxout/release/report_manifest.json")
    for relative, expected in manifest["reports"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    assert set(REQUIRED_REPORTS).issubset({Path(relative).name for relative in manifest["reports"]})


def test_machine_state_is_typed_and_schema_complete() -> None:
    machine = _json("VALID_EVAL_FINAL_CPU_MAXOUT_MACHINE_STATE.json")
    validated = validate_machine_state(machine)
    assert validated.canonical_s1_source_ref == "valideval-v7.2.1-icml2027-kaggle-s1-ready"
    assert validated.critical_strata["passed"] == 39
    assert validated.critical_strata["failed"] == 21
    assert validated.remaining_cpu_work == []


def test_seed_and_experiment_registries_have_unique_ids() -> None:
    seeds = _json("configs/release/seed_registry_v7_2_1.json")["seeds"]
    assert len({row["seed"] for row in seeds}) == len(seeds)
    assert len({row["study_id"] for row in seeds}) == len(seeds)
    experiments = _json("results/experiments/experiment_registry.json")["experiments"]
    assert len({row["study_id"] for row in experiments}) == len(experiments)


def test_legacy_compatibility_is_explicit_and_single_canonical() -> None:
    matrix = _json("configs/release/legacy_compatibility_v7_2_1.json")
    assert matrix["implicit_compatibility"] is False
    canonical = [row for row in matrix["versions"] if row["canonical"]]
    assert [row["version"] for row in canonical] == ["V7.2.1"]


def test_dependency_locks_cover_active_cpu_and_gpu_packages() -> None:
    cpu = (ROOT / "requirements-cpu-v7-2-1.lock").read_text(encoding="utf-8")
    gpu = (ROOT / "requirements-kaggle-t4x2-v7-2-1.lock").read_text(encoding="utf-8")
    for name in ("numpy", "pandas", "pydantic", "PyYAML", "scipy"):
        assert f"{name}==" in cpu
    for name in ("torch", "transformers", "datasets", "tokenizers"):
        assert f"{name}==" in gpu


def test_future_stage_documents_do_not_authorize_s2_or_s3() -> None:
    s2 = (ROOT / "VALID_EVAL_V7_2_1_S2_DRAFT_RUNBOOK.md").read_text(encoding="utf-8")
    s3 = (ROOT / "VALID_EVAL_V7_2_1_S3_PROPOSAL_CONTRACT.md").read_text(encoding="utf-8")
    assert "DRAFT_PENDING_ACCEPTED_S1" in s2
    assert "BLOCKED_PENDING_S2" in s3


def test_s3_proposal_generator_is_fail_closed_and_non_authorizing() -> None:
    measured = {
        "status": "S2_ACCEPTED",
        "runtime_seconds_per_model": 100.0,
        "variance_estimate": 0.02,
        "model_failure_rate": 0.0,
        "family_coverage": 6,
        "extraction_reliability": 0.99,
        "primary_claim_power_floor": 0.85,
    }
    proposed = propose_s3_from_s2(measured)
    assert proposed["status"] == "S3_PROPOSED"
    assert proposed["execution_authorized"] is False
    measured["extraction_reliability"] = 0.94
    blocked = propose_s3_from_s2(measured)
    assert blocked["status"] == "S3_REDESIGN_REQUIRED"


def test_pre_gpu_bundle_is_deterministic(tmp_path) -> None:
    first = build_pre_gpu_bundle(ROOT, output=tmp_path / "first.zip")
    second = build_pre_gpu_bundle(ROOT, output=tmp_path / "second.zip")
    assert first["sha256"] == second["sha256"]
    assert first["member_count"] == second["member_count"]


def test_evidence_identity_is_timezone_and_locale_environment_independent(monkeypatch) -> None:
    contract = {"decimal": 0.125, "unicode": "δ", "members": ["a", "b"]}
    baseline = compute_configuration_hash(contract)
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")
    monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    assert compute_configuration_hash(contract) == baseline
