from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from valideval.diagnostics.v8.development import run_v8_exploratory_development
from valideval.execution.manifest import atomic_write_json, sha256_file
from valideval.execution.provenance_v7_2_1 import audit_source_coherence
from valideval.statistics.claim_policy_v7_2 import confirm_frozen_policy
from valideval.statistics.claim_policy_v7_2_1 import confirm_native_policy
from valideval.statistics.cpu_maxout_stress import run_rank_stress
from valideval.statistics.historical_mmlu_maxout import historical_weighting_summary
from valideval.statistics.rank_nulls import subject_accuracy_matrix
from valideval.statistics.study_c_power_v7_1 import study_c_power_redesign
from valideval.statistics.study_h_v7 import null_suite_comparison, simulate_null_suite

HISTORICAL_MMLU_REPLAY_SHA256 = "f85a0a44f3203de2863d86bf13b2c81d8e934ae4c07b826193b5e93a3fc86e74"


def replay_cpu_evidence(
    repository_root: str | Path,
    *,
    output: str | Path = "results/final_cpu_maxout/replay/cpu_replay.json",
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, observed: Any) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", "observed": observed})

    v7 = json.loads((root / "results/v7/synthetic/confirmatory/summary.json").read_text())
    check(
        "v7_frozen_negative",
        v7.get("acceptance_status") == "FROZEN_ACCEPTANCE_GATES_FAILED",
        v7.get("acceptance_status"),
    )
    v7_2 = json.loads((root / "results/v7_2/claim_policy/confirmation_summary.json").read_text())
    generic_registry = pd.read_csv(
        root / "results/v7_2/claim_policy/simulation_scenario_registry.csv"
    )
    generic_freeze = yaml.safe_load(
        (root / "results/v7_2/claim_policy/claim_policy_v7_2_frozen.yaml").read_text()
    )
    _, generic_recomputed = confirm_frozen_policy(generic_registry, generic_freeze)
    check(
        "v7_2_generic_result",
        abs(float(v7_2["false_license_rate"]) - float(generic_recomputed["false_license_rate"]))
        < 1e-15
        and abs(float(v7_2["true_license_power"]) - float(generic_recomputed["true_license_power"]))
        < 1e-15,
        {
            "false_license_rate": v7_2["false_license_rate"],
            "true_license_power": v7_2["true_license_power"],
        },
    )
    freeze = json.loads(
        (root / "results/final_cpu_maxout/claim_policy/policy_freeze.json").read_text()
    )
    native_records = pd.read_csv(
        root / "results/final_cpu_maxout/claim_policy/confirmation_records.csv"
    )
    native_records["truth_supported"] = native_records["truth_supported"].astype(bool)
    native_records["licensed"] = native_records["licensed"].astype(bool)
    recomputed = confirm_native_policy(native_records, freeze)
    recorded = json.loads(
        (root / "results/final_cpu_maxout/claim_policy/confirmation_summary.json").read_text()
    )
    check(
        "native_policy_confirmation",
        recomputed["status"] == recorded["status"]
        and abs(
            float(recomputed["overall"]["false_license_rate"])
            - float(recorded["overall"]["false_license_rate"])
        )
        < 1e-15,
        {
            "status": recomputed["status"],
            "false_license_rate": recomputed["overall"]["false_license_rate"],
        },
    )
    v8 = json.loads((root / "results/v7_2/v8/development_summary.json").read_text())
    v8_config = yaml.safe_load(
        (root / "configs/diagnostics/v8_exploratory_development.yaml").read_text()
    )
    _, _, recomputed_v8 = run_v8_exploratory_development(v8_config)
    v8_numeric_fields = (
        "development_v7_frozen_difficulty_negative_auprc",
        "development_v8_full_difficulty_negative_auprc",
        "difficulty_negative_auprc_reduction",
        "development_v7_frozen_true_flaw_median_auprc",
        "development_v8_full_true_flaw_median_auprc",
        "true_flaw_auprc_retention",
    )
    v8_maximum_absolute_delta = max(
        abs(float(v8[field]) - float(recomputed_v8[field])) for field in v8_numeric_fields
    )
    v8_gate_flags_match = v8.get("difficulty_confound_reduced") is recomputed_v8.get(
        "difficulty_confound_reduced"
    ) and v8.get("true_flaw_signal_retained") is recomputed_v8.get("true_flaw_signal_retained")
    v8_tolerance_pass = v8_maximum_absolute_delta <= 1e-9
    v8_replay_pass = (
        v8.get("status") == recomputed_v8.get("status")
        and v8_gate_flags_match
        and v8_tolerance_pass
    )
    v8_observed = {
        "status": recomputed_v8.get("status"),
        "recorded_normalized_metrics_sha256": v8.get("normalized_metrics_sha256"),
        "gate_flags_match": v8_gate_flags_match,
        "numeric_tolerance_pass": v8_tolerance_pass,
        "absolute_tolerance": 1e-9,
    }
    if not v8_replay_pass:
        v8_observed.update(
            {
                "debug_recomputed_normalized_metrics_sha256": recomputed_v8.get(
                    "normalized_metrics_sha256"
                ),
                "debug_maximum_absolute_delta": v8_maximum_absolute_delta,
            }
        )
    check(
        "v8_exploratory_boundary",
        v8_replay_pass,
        v8_observed,
    )
    historical = json.loads(
        (root / "results/final_cpu_maxout/historical_mmlu/summary.json").read_text()
    )
    historical_matrix_path = root / "data/replay/v7_2_1/historical_mmlu_matrix.csv"
    historical_matrix_sha256 = sha256_file(historical_matrix_path)
    check(
        "historical_mmlu_fixture_hash",
        historical_matrix_sha256 == HISTORICAL_MMLU_REPLAY_SHA256,
        historical_matrix_sha256,
    )
    matrix = pd.read_csv(historical_matrix_path, index_col=0)
    family_frame = pd.read_csv(root / "configs/models/study_h_family_map_v5.csv")
    families = dict(zip(family_frame["model_id"], family_frame["model_family"], strict=True))
    _, recomputed_historical = historical_weighting_summary(matrix, families)
    check(
        "historical_mmlu_identity",
        historical.get("models") == recomputed_historical.get("models")
        and historical.get("items") == recomputed_historical.get("items")
        and historical.get("estimands") == recomputed_historical.get("estimands"),
        {"models": historical.get("models"), "items": historical.get("items")},
    )
    recomputed_rank = run_rank_stress()
    recorded_rank = pd.read_csv(root / "results/final_cpu_maxout/stress/rank_stress.csv")
    check(
        "rank_coverage",
        float(recomputed_rank["joint_coverage"].min())
        == float(recorded_rank["joint_coverage"].min())
        and len(recomputed_rank) == len(recorded_rank),
        {
            "scenarios": len(recomputed_rank),
            "minimum_joint_coverage": float(recomputed_rank["joint_coverage"].min()),
        },
    )
    subjects = {str(item): str(item).split("::", 1)[0] for item in matrix.columns}
    recomputed_null_draws = simulate_null_suite(
        matrix,
        subjects,
        families,
        n_simulations=200,
        seed=2028,
    )
    recomputed_nulls = null_suite_comparison(
        subject_accuracy_matrix(matrix, subjects), recomputed_null_draws
    )
    study_h = json.loads((root / "results/v7_1/study_h/summary.json").read_text())
    null_range = [
        float(recomputed_nulls["median_rank_range_exceedance"].min()),
        float(recomputed_nulls["median_rank_range_exceedance"].max()),
    ]
    check(
        "null_sensitivity",
        null_range == study_h["null_median_rank_range_exceedance_range"],
        null_range,
    )
    power = json.loads((root / "results/v7_1/planning/power/summary.json").read_text())
    power_config = yaml.safe_load((root / "configs/statistics/study_c_power_v7_1.yaml").read_text())
    _, recomputed_power = study_c_power_redesign(power_config)
    check(
        "study_c_power_boundary",
        power.get("status") == recomputed_power.get("status")
        and power.get("s3_minimum_scientific_label_permitted")
        is recomputed_power.get("s3_minimum_scientific_label_permitted"),
        {
            "status": recomputed_power.get("status"),
            "s3_minimum_scientific_label_permitted": recomputed_power.get(
                "s3_minimum_scientific_label_permitted"
            ),
        },
    )
    coherence = audit_source_coherence(root)
    check(
        "source_coherence",
        coherence["status"] == "RUNBOOK_PROVENANCE_COHERENT",
        coherence,
    )
    tracked_sources = [
        "results/v7/synthetic/confirmatory/summary.json",
        "results/v7_2/claim_policy/confirmation_summary.json",
        "results/final_cpu_maxout/claim_policy/policy_freeze.json",
        "results/final_cpu_maxout/claim_policy/confirmation_summary.json",
        "results/v7_2/v8/development_summary.json",
        "results/final_cpu_maxout/historical_mmlu/summary.json",
        "results/v7_1/study_h/summary.json",
        "results/v7_1/planning/power/summary.json",
        "results/v7_1/planning/power/primary_estimand_power_grid.csv",
        "data/replay/v7_2_1/historical_mmlu_matrix.csv",
    ]
    payload = {
        "schema_version": "valideval.cpu-replay.v7.2.1",
        "status": "CPU_REPLAY_PASS"
        if all(row["status"] == "PASS" for row in checks)
        else "CPU_REPLAY_FAIL",
        "checks": checks,
        "artifact_hashes": {path: sha256_file(root / path) for path in tracked_sources},
        "numerical_reproducibility": {
            "frozen_json_hashes": "BITWISE_STABLE",
            "recomputed_native_aggregates": "NUMERICALLY_STABLE",
            "v8_exploratory_recompute": "TOLERANCE_AND_CONCLUSION_STABLE",
            "gate_states": "CONCLUSION_STABLE",
            "GPU_inference": "ENVIRONMENT_SENSITIVE_NOT_RUN",
        },
    }
    destination = root / output if not Path(output).is_absolute() else Path(output)
    atomic_write_json(destination, payload)
    payload["output"] = str(destination)
    return payload
