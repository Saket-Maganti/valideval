from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
import yaml

from valideval.claims import (
    ClaimEvidence,
    ClaimStatus,
    ClaimType,
    DecisionDirection,
    InferentialUnit,
    RankIntervalType,
    license_claim,
)
from valideval.execution.authorization_v7_1 import (
    StudyCAuthorizationEvidence,
    assess_study_c_authorization,
)
from valideval.execution.datasets import frozen_items_from_records
from valideval.execution.errors import GenerationOOM, ModelLoadOOM
from valideval.execution.runner import run_from_config
from valideval.execution.shards import T4x2Scheduler
from valideval.execution.workers import production_worker
from valideval.human.planning_v7 import annotation_power_plan
from valideval.importers.ingest_v7 import IngestV7Error, ingest_and_analyze_v7
from valideval.influence.analysis import crossfit_removal_evaluation
from valideval.statistics.rank_inference_v7_1 import (
    marginal_rank_intervals,
    pairwise_multiplicity_analysis,
    simultaneous_rank_confidence_sets,
)
from valideval.statistics.study_c_power_v7_1 import study_c_power_redesign
from valideval.transport import analyze_transportability, build_fold_manifest
from valideval.validation.detector_metrics import expected_precision_at_k, precision_recall_auc
from valideval.validation.synthetic_controls_v7_1 import run_synthetic_control_completion

ROOT = Path(__file__).resolve().parents[1]


def _item_evidence(**updates: Any) -> ClaimEvidence:
    payload: dict[str, Any] = {
        "estimand_unit": InferentialUnit.ITEM,
        "raw_n": 1_000,
        "effective_n": 1_000,
        "independence_unit": InferentialUnit.ITEM,
        "dependence_structure": "paired item responses",
        "decision_regret_upper": 0.005,
    }
    payload.update(updates)
    return ClaimEvidence(**payload)


@pytest.mark.parametrize(
    ("lower", "upper", "threshold", "direction", "expected"),
    [
        (0.21, 0.30, 0.20, DecisionDirection.ABOVE, ClaimStatus.LICENSED),
        (0.19, 0.30, 0.20, DecisionDirection.ABOVE, ClaimStatus.BLOCKED_BY_UNCERTAINTY),
        (0.20, 0.30, 0.20, DecisionDirection.ABOVE, ClaimStatus.BLOCKED_BY_UNCERTAINTY),
        (0.10, 0.19, 0.20, DecisionDirection.BELOW, ClaimStatus.LICENSED),
    ],
)
def test_threshold_claim_uses_explicit_directional_threshold(
    lower: float,
    upper: float,
    threshold: float,
    direction: DecisionDirection,
    expected: ClaimStatus,
) -> None:
    result = license_claim(
        ClaimType.MODEL_CROSSES_THRESHOLD,
        _item_evidence(
            confidence_lower=lower,
            confidence_upper=upper,
            decision_threshold=threshold,
            decision_direction=direction,
        ),
    )
    assert result.status is expected


def test_threshold_claim_missing_threshold_fails_closed() -> None:
    result = license_claim(
        ClaimType.MODEL_CROSSES_THRESHOLD,
        _item_evidence(confidence_lower=0.8, effect_size=0.1),
    )
    assert result.status is ClaimStatus.BLOCKED_BY_UNCERTAINTY


def test_huge_raw_n_with_small_effective_n_blocks() -> None:
    result = license_claim(
        ClaimType.MODEL_A_OUTPERFORMS_MODEL_B,
        ClaimEvidence(
            confidence_lower=0.2,
            raw_n=14_000,
            effective_n=11,
            estimand_unit=InferentialUnit.ITEM,
            independence_unit=InferentialUnit.MODEL_FAMILY,
            dependence_structure="14k items supported by 11 related checkpoints",
            decision_regret_upper=0.0,
        ),
    )
    assert result.status is ClaimStatus.UNDERPOWERED


def test_missing_effective_n_blocks() -> None:
    result = license_claim(
        ClaimType.MODEL_A_OUTPERFORMS_MODEL_B,
        ClaimEvidence(confidence_lower=0.2, sample_size=100_000, decision_regret_upper=0.0),
    )
    assert result.status is ClaimStatus.UNDERPOWERED


def test_only_joint_rank_interval_can_license_top_k() -> None:
    marginal = license_claim(
        ClaimType.MODEL_IN_TOP_K,
        _item_evidence(
            simultaneous_rank_upper=3,
            requested_top_k=3,
            rank_interval_type=RankIntervalType.MARGINAL_BOOTSTRAP,
        ),
    )
    simultaneous = license_claim(
        ClaimType.MODEL_IN_TOP_K,
        _item_evidence(
            simultaneous_rank_upper=3,
            requested_top_k=3,
            rank_interval_type=RankIntervalType.BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS,
        ),
    )
    assert marginal.status is ClaimStatus.BLOCKED_BY_UNCERTAINTY
    assert simultaneous.licensed


def test_simultaneous_rank_and_pairwise_multiplicity_contracts() -> None:
    draws = pd.DataFrame(
        {
            "a": [0.9, 0.88, 0.91, 0.90, 0.89],
            "b": [0.7, 0.72, 0.69, 0.71, 0.70],
            "c": [0.5, 0.48, 0.51, 0.49, 0.50],
        }
    )
    joint = simultaneous_rank_confidence_sets(draws)
    marginal = marginal_rank_intervals(draws)
    pairs = pairwise_multiplicity_analysis(draws)
    assert set(joint["interval_type"]) == {"BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS"}
    assert set(marginal["interval_type"]) == {"MARGINAL_BOOTSTRAP"}
    assert {"adjusted_p_bh", "adjusted_p_holm", "hypothesis_family_id"}.issubset(pairs)


def test_tie_invariant_detector_metrics() -> None:
    labels = [True, False, True, False]
    scores = [0.8, 0.8, 0.2, 0.2]
    first = precision_recall_auc(labels, scores)
    second = precision_recall_auc([False, True, False, True], scores)
    assert first == second
    assert expected_precision_at_k(labels, scores, 1) == 0.5


def test_family_grouped_crossfit_has_no_family_leakage() -> None:
    random = np.random.default_rng(8)
    rng = pd.DataFrame(
        random.binomial(1, np.linspace(0.25, 0.75, 8)[:, None], size=(8, 40)),
        index=[f"m{index}" for index in range(8)],
        columns=[f"i{index}" for index in range(40)],
    )
    families = {f"m{index}": f"f{index // 2}" for index in range(8)}
    result = crossfit_removal_evaluation(rng, model_families=families, seed=8)
    assert result["family_overlap_count"].eq(0).all()


def test_study_c_authorization_is_sequential_and_fail_closed() -> None:
    blocked = assess_study_c_authorization(StudyCAuthorizationEvidence())
    assert blocked["stages"]["s1"]["status"] == "S1_BLOCKED"
    assert blocked["stages"]["s3"]["status"] == "S3_BLOCKED_PENDING_S2"
    assert blocked["stages"]["s4"]["status"] == "S4_BLOCKED_PENDING_S3"
    ready = StudyCAuthorizationEvidence(
        **{key: True for key in StudyCAuthorizationEvidence.__dataclass_fields__}
    )
    authorized = assess_study_c_authorization(ready)
    assert all(row["status"].endswith("_AUTHORIZED") for row in authorized["stages"].values())


def test_human_planner_multiplies_all_four_strata() -> None:
    row = annotation_power_plan((300,)).iloc[0]
    assert row["total_unique_items"] == 1_200
    assert row["total_raw_labels_2_annotators"] == 2_400
    assert row["expected_adjudication_labels"] == 240


def test_power_redesign_uses_model_and_family_counts() -> None:
    config = {
        "simulations": 100,
        "alpha": 0.05,
        "target_power": 0.8,
        "effect_sizes": [0.03],
        "material_effect": 0.03,
        "primary_estimands": ["MODEL_BENCHMARK_INTERACTION"],
        "designs": {
            "SMALL": {
                "model_count": 4,
                "family_count": 2,
                "benchmark_count": 3,
                "item_count": 200,
                "family_correlation": 0.5,
                "paired_response_correlation": 0.25,
                "measurement_error": 0.1,
                "transport_heterogeneity": 0.2,
                "held_out_benchmark": "LOBO",
                "held_out_family": "LOFO",
            },
            "LARGE": {
                "model_count": 16,
                "family_count": 12,
                "benchmark_count": 3,
                "item_count": 200,
                "family_correlation": 0.5,
                "paired_response_correlation": 0.25,
                "measurement_error": 0.1,
                "transport_heterogeneity": 0.2,
                "held_out_benchmark": "LOBO",
                "held_out_family": "LOFO",
            },
        },
    }
    grid, _ = study_c_power_redesign(config)
    interaction = grid[grid["estimand"] == "MODEL_BENCHMARK_INTERACTION"].set_index("stage")
    assert (
        interaction.loc["LARGE", "simulated_standard_error"]
        < interaction.loc["SMALL", "simulated_standard_error"]
    )


def test_synthetic_controls_are_separate_complete_and_deterministic() -> None:
    config = {
        "seeds": [1],
        "model_count": 12,
        "family_count": 4,
        "item_count": 60,
        "subject_count": 5,
        "prevalence": 0.2,
        "severity": 0.6,
    }
    first, first_summary = run_synthetic_control_completion(config)
    second, second_summary = run_synthetic_control_completion(config)
    assert first_summary["status"] == "V7_1_SYNTHETIC_CONTROL_SUITE_COMPLETE"
    assert first_summary["v7_primary_result"].endswith("FAILED_AND_PRESERVED")
    assert (
        first_summary["deterministic_normalized_result_sha256"]
        == second_summary["deterministic_normalized_result_sha256"]
    )
    pd.testing.assert_frame_equal(first, second)


def _fold(benchmark: str) -> dict[str, Any]:
    return build_fold_manifest(
        fold_id=f"lobo-{benchmark}",
        training_benchmarks=[name for name in ("mmlu", "gsm8k", "bbh") if name != benchmark],
        held_out_benchmark=benchmark,
        training_families=["f1", "f2", "f3", "f4", "f5"],
        held_out_families=[],
        training_model_ids=["train-1", "train-2"],
        evaluation_model_ids=["eval-1", "eval-2"],
        discovery_item_ids=["discover-1"],
        evaluation_item_ids=["evaluate-1"],
        source_commit="a" * 40,
        config_hash="b" * 64,
        execution_status="EXECUTED",
        data_artifact_hashes={"effects.csv": "c" * 64},
    )


def test_transport_requires_valid_fold_provenance() -> None:
    frame = pd.DataFrame(
        {
            "estimand": ["score_transport"] * 3,
            "benchmark": ["mmlu", "gsm8k", "bbh"],
            "estimate": [0.4, 0.35, 0.45],
            "standard_error": [0.05] * 3,
            "exact_identity": [True] * 3,
            "fold_manifest": [_fold(name) for name in ("mmlu", "gsm8k", "bbh")],
            "independent_families": [6] * 3,
        }
    )
    assert analyze_transportability(frame)["overall_status"] == "TRANSFER_SUPPORTED"
    frame.at[0, "fold_manifest"] = build_fold_manifest(
        fold_id="planned-mmlu",
        training_benchmarks=["gsm8k", "bbh"],
        held_out_benchmark="mmlu",
        training_families=["f1", "f2", "f3", "f4", "f5"],
        held_out_families=[],
        training_model_ids=["train-1"],
        evaluation_model_ids=["eval-1"],
        discovery_item_ids=["discover-1"],
        evaluation_item_ids=["evaluate-1"],
        source_commit="a" * 40,
        config_hash="b" * 64,
    )
    assert analyze_transportability(frame)["overall_status"] == "BLOCKED"
    frame.at[0, "fold_manifest"] = {"held_out": True}
    assert analyze_transportability(frame)["overall_status"] == "BLOCKED"


def test_scheduler_propagates_oom_and_records_bounded_fallback(tmp_path: Path) -> None:
    attempts: list[dict[str, Any]] = []

    def worker(task: dict[str, Any], _gpu_id: str) -> dict[str, Any]:
        attempts.append(task)
        if len(attempts) == 1:
            raise GenerationOOM("CUDA out of memory")
        return {"rows": [], "ok": True}

    scheduler = T4x2Scheduler(
        tmp_path / "scheduler", gpu_ids=["0"], max_retries=2, use_processes=False
    )
    result = scheduler.run(
        [
            {
                "task_id": "generation-oom",
                "batch_size": 4,
                "max_sequence_length": 2048,
                "minimum_sequence_length": 512,
                "allow_sequence_length_fallback": True,
            }
        ],
        worker,
        config={"fixture": True},
        resume=False,
    )
    assert result["results"][0]["status"] == "success"
    assert result["results"][0]["fallbacks"][0]["action"] == "reduce_batch_size"
    assert attempts[1]["batch_size"] == 2


@pytest.mark.parametrize("error_type", [ModelLoadOOM, GenerationOOM])
def test_repeated_oom_exhaustion_is_recorded(tmp_path: Path, error_type: type[Exception]) -> None:
    def worker(_task: dict[str, Any], _gpu_id: str) -> dict[str, Any]:
        raise error_type("CUDA out of memory")

    scheduler = T4x2Scheduler(
        tmp_path / error_type.__name__, gpu_ids=["0"], max_retries=2, use_processes=False
    )
    result = scheduler.run(
        [
            {
                "task_id": error_type.__name__,
                "batch_size": 1,
                "max_sequence_length": 2048,
                "minimum_sequence_length": 512,
                "allow_sequence_length_fallback": True,
            }
        ],
        worker,
        config={"fixture": True},
        resume=False,
    )
    row = result["results"][0]
    assert row["status"] == "failed"
    assert row["failure_type"] == "OOM"
    assert [fallback["action"] for fallback in row["fallbacks"]].count(
        "reduce_sequence_length"
    ) == 1


def _mock_v7_config(tmp_path: Path) -> Path:
    payload = yaml.safe_load((ROOT / "configs/runs_v7/mmlu_s2_v7.yaml").read_text())
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    payload.update(
        {
            "run_id": "mock-production-path-v7-1",
            "evidence_class": "NON_EVIDENCE_FIXTURE",
            "mode": "fixture",
            "expected_source_commit": source_commit,
        }
    )
    payload["execution"].update(
        {
            "backend": "mock",
            "use_processes": False,
            "minimum_free_disk_gb": 0,
            "model_download_margin_gb": 0,
        }
    )
    path = tmp_path / "mock_v7_1.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def _mmlu_items() -> list[Any]:
    contract = yaml.safe_load(
        (ROOT / "configs/benchmarks/mmlu_s2_v7.yaml").read_text(encoding="utf-8")
    )
    records = [
        {
            "subject": f"fixture_subject_{index % 57:02d}",
            "question": f"NON_EVIDENCE_FIXTURE V7.1 question {index}?",
            "choices": ["one", "two", "three", "four"],
            "answer": index % 4,
        }
        for index in range(200)
    ]
    return frozen_items_from_records(contract, records)


@pytest.fixture()
def runner_package(tmp_path: Path) -> dict[str, Any]:
    config = _mock_v7_config(tmp_path)
    result = run_from_config(
        config,
        output_root=tmp_path / "outputs",
        repository_root=ROOT,
        injected_items=_mmlu_items(),
    )
    assert result["status"] == "RUN_COMPLETE"
    return {"result": result, "config": config, "tmp": tmp_path}


def test_actual_runner_zip_and_directory_reach_router_and_ledger(
    runner_package: dict[str, Any],
) -> None:
    result = runner_package["result"]
    root = runner_package["tmp"]
    zipped = ingest_and_analyze_v7(result["zip_path"], output_root=root / "zip-import")
    directory = ingest_and_analyze_v7(result["run_dir"], output_root=root / "dir-import")
    assert zipped["status"] == "INGESTED_ROUTED_AND_LEDGER_UPDATED"
    assert Path(zipped["evidence_ledger_path"]).is_file()
    assert not zipped["claim_eligible"]
    assert directory["validation"]["row_count"] == 1600


def test_resume_produced_package_is_ingestible(runner_package: dict[str, Any]) -> None:
    resumed = run_from_config(
        runner_package["config"],
        mode_override="resume",
        output_root=runner_package["tmp"] / "outputs",
        repository_root=ROOT,
        injected_items=_mmlu_items(),
    )
    assert resumed["status"] == "RUN_COMPLETE"
    receipt = ingest_and_analyze_v7(
        resumed["zip_path"], output_root=runner_package["tmp"] / "resume-import"
    )
    assert receipt["validation"]["row_count"] == 1600


def test_runner_package_with_declared_model_failure_is_ingestible(tmp_path: Path) -> None:
    config = _mock_v7_config(tmp_path)
    payload = yaml.safe_load(config.read_text(encoding="utf-8"))
    payload["run_id"] = "mock-v7-1-declared-failure"
    config.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    failed_task: str | None = None

    def worker(task: dict[str, Any], gpu_id: str) -> dict[str, Any]:
        nonlocal failed_task
        if failed_task is None:
            failed_task = str(task["task_id"])
        if str(task["task_id"]) == failed_task:
            raise RuntimeError("declared fixture generation failure")
        return production_worker(task, gpu_id)

    result = run_from_config(
        config,
        output_root=tmp_path / "failure-output",
        repository_root=ROOT,
        injected_items=_mmlu_items(),
        worker=worker,
    )
    assert result["status"] == "RUN_COMPLETE_WITH_RECORDED_FAILURES"
    receipt = ingest_and_analyze_v7(result["zip_path"], output_root=tmp_path / "failure-import")
    assert receipt["declared_failure_state"] == "recorded_model_or_item_failures"


def _copy_run(runner_package: dict[str, Any], name: str) -> Path:
    destination = runner_package["tmp"] / name
    shutil.copytree(runner_package["result"]["run_dir"], destination)
    return destination


def _resign_predictions(run_dir: Path) -> None:
    digest = hashlib.sha256((run_dir / "predictions.jsonl").read_bytes()).hexdigest()
    checksums = json.loads((run_dir / "file_checksums.json").read_text())
    checksums["files"]["predictions.jsonl"] = digest
    (run_dir / "file_checksums.json").write_text(json.dumps(checksums), encoding="utf-8")
    manifest = json.loads((run_dir / "run_manifest.json").read_text())
    manifest["file_checksums"]["predictions.jsonl"] = digest
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


@pytest.mark.parametrize("mutation", ["checksum", "schema", "revision", "duplicate", "source"])
def test_runner_package_adversarial_failures(runner_package: dict[str, Any], mutation: str) -> None:
    run_dir = _copy_run(runner_package, f"bad-{mutation}")
    prediction_path = run_dir / "predictions.jsonl"
    lines = prediction_path.read_text(encoding="utf-8").splitlines()
    if mutation == "checksum":
        prediction_path.write_text("tampered\n", encoding="utf-8")
    elif mutation in {"schema", "revision"}:
        row = json.loads(lines[0])
        if mutation == "schema":
            row["schema_version"] = "wrong-schema"
        else:
            row["model_revision"] = "deadbeef"
        lines[0] = json.dumps(row)
        prediction_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _resign_predictions(run_dir)
    elif mutation == "duplicate":
        prediction_path.write_text("\n".join(lines + [lines[0]]) + "\n", encoding="utf-8")
        _resign_predictions(run_dir)
    else:
        manifest = json.loads((run_dir / "run_manifest.json").read_text())
        manifest["actual_source_commit"] = "f" * 40
        manifest["source_match"] = False
        (run_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(IngestV7Error):
        ingest_and_analyze_v7(run_dir, output_root=runner_package["tmp"] / f"import-{mutation}")


def test_ingest_config_and_source_expectations_fail_closed(runner_package: dict[str, Any]) -> None:
    with pytest.raises(IngestV7Error, match="Configuration hash mismatch"):
        ingest_and_analyze_v7(
            runner_package["result"]["run_dir"],
            output_root=runner_package["tmp"] / "config-mismatch",
            expected_config_hash="0" * 64,
        )
    with pytest.raises(IngestV7Error, match="source mismatch"):
        ingest_and_analyze_v7(
            runner_package["result"]["run_dir"],
            output_root=runner_package["tmp"] / "source-mismatch",
            expected_source_commit="0" * 40,
        )
