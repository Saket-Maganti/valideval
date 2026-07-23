from __future__ import annotations

import json
import os
import platform
import sys
import zipfile
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from valideval.execution.manifest import (
    EXECUTION_SCHEMA_VERSION,
    NON_EVIDENCE_FIXTURE,
    atomic_write_json,
    atomic_write_text,
    build_file_checksums,
    build_run_manifest,
    compute_configuration_hash,
    sha256_bytes,
)
from valideval.execution.shards import (
    T4x2Scheduler,
    build_deterministic_shards,
    merge_jsonl_shards,
)

EXECUTION_MODES = (
    "fixture",
    "smoke",
    "pilot",
    "minimum_scientific",
    "full_common_panel",
    "robustness",
    "resume",
    "validate_only",
    "package_only",
)

NOTEBOOK_STAGES = (
    "environment",
    "mmlu",
    "gsm8k",
    "bbh",
    "package",
    "robustness",
)

FIXTURE_MODEL_RECORDS = (
    {
        "model_id": "fixture-model-a@v1",
        "model_revision": "fixture-revision-a",
        "model_family": "fixture-family-a",
        "dtype": "float32",
        "quantization": "none",
        "minimum_gpu_memory_gb": 0,
        "evidence_state": NON_EVIDENCE_FIXTURE,
    },
    {
        "model_id": "fixture-model-b@v1",
        "model_revision": "fixture-revision-b",
        "model_family": "fixture-family-b",
        "dtype": "float32",
        "quantization": "none",
        "minimum_gpu_memory_gb": 0,
        "evidence_state": NON_EVIDENCE_FIXTURE,
    },
)


def validate_execution_mode(mode: str) -> str:
    normalized = str(mode).strip().lower()
    if normalized not in EXECUTION_MODES:
        raise ValueError(f"Unsupported execution mode {mode!r}; expected one of {EXECUTION_MODES}")
    return normalized


def run_notebook_stage(
    stage: str,
    *,
    mode: str | None = None,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    normalized_stage = str(stage).strip().lower()
    if normalized_stage not in NOTEBOOK_STAGES:
        raise ValueError(f"Unsupported notebook stage: {stage!r}")
    execution_mode = validate_execution_mode(
        mode or os.environ.get("VALIDEVAL_EXECUTION_MODE", "fixture")
    )
    root = Path(
        output_root
        or os.environ.get("VALIDEVAL_NOTEBOOK_OUTPUT_ROOT", "kaggle_max_ceiling_outputs")
    )
    root.mkdir(parents=True, exist_ok=True)

    if execution_mode == "fixture":
        if normalized_stage == "environment":
            return _fixture_environment(root)
        if normalized_stage in {"mmlu", "gsm8k", "bbh"}:
            return build_fixture_run(normalized_stage, root)
        if normalized_stage == "package":
            return package_fixture_runs(root)
        return build_fixture_run("mmlu", root, run_suffix="robustness")

    if execution_mode == "package_only":
        return package_completed_runs(root)
    if execution_mode == "validate_only":
        return validate_completed_runs(root)

    payload = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "stage": normalized_stage,
        "mode": execution_mode,
        "status": "CONTROLLED_GPU_EXECUTION_CONFIG_REQUIRED",
        "evidence_state": "RESULT_REQUIRED",
        "required_configuration": os.environ.get(
            "VALIDEVAL_EXECUTION_CONFIG",
            "Set VALIDEVAL_EXECUTION_CONFIG to a frozen V5 YAML configuration on Kaggle.",
        ),
        "instructions": [
            "Select the Kaggle T4 x2 accelerator before running benchmark stages.",
            "Freeze model and dataset revisions in the V5 configuration snapshot.",
            "Use one worker per visible GPU and preserve isolated worker outputs.",
            "Do not interpret a run until merge, checksum, coverage, and importer gates pass.",
        ],
    }
    atomic_write_json(root / f"{normalized_stage}_{execution_mode}_preflight.json", payload)
    return payload


def build_fixture_run(
    benchmark_id: str,
    output_root: str | Path,
    *,
    run_suffix: str | None = None,
) -> dict[str, Any]:
    if benchmark_id not in {"mmlu", "gsm8k", "bbh"}:
        raise ValueError(f"Unsupported fixture benchmark: {benchmark_id}")
    root = Path(output_root)
    run_label = f"fixture-{benchmark_id}-v5"
    if run_suffix:
        run_label = f"{run_label}-{run_suffix}"
    run_dir = root / "runs" / run_label
    run_dir.mkdir(parents=True, exist_ok=True)
    item_ids = [f"{benchmark_id}-fixture-{index:03d}" for index in range(4)]
    shards = build_deterministic_shards(item_ids, shard_count=2, prefix=f"{benchmark_id}-fixture")
    config = _fixture_config(benchmark_id, run_label, shards, run_suffix=run_suffix)
    config_hash = compute_configuration_hash(config)
    environment = _fixture_environment_payload()
    environment_hash = sha256_bytes(
        json.dumps(environment, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )

    tasks = []
    model_by_id = {model["model_id"]: model for model in FIXTURE_MODEL_RECORDS}
    for model in FIXTURE_MODEL_RECORDS:
        for shard in shards:
            tasks.append(
                {
                    "task_id": f"{model['model_id']}--{shard.shard_id}",
                    "study_id": "study-c-fixture",
                    "run_id": run_label,
                    "benchmark_id": benchmark_id,
                    "benchmark_version": "fixture-v1",
                    "model": dict(model),
                    "shard": shard.to_dict(),
                    "config_hash": config_hash,
                    "environment_hash": environment_hash,
                }
            )
    scheduler = T4x2Scheduler(
        root / "scheduler" / run_label,
        gpu_ids=("0", "1"),
        max_retries=1,
        use_processes=False,
    )
    scheduler_result = scheduler.run(
        tasks,
        fixture_worker,
        config=config,
        resume=True,
    )
    shard_files: list[Path] = []
    for result in scheduler_result["results"]:
        if result["status"] != "success":
            continue
        worker_dir = root / "scheduler" / run_label / result["worker_id"] / "outputs"
        output_path = worker_dir / f"{_safe_task_name(result['task_id'])}.jsonl"
        rows = result["output"]["rows"]
        atomic_write_text(
            output_path,
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        )
        shard_files.append(output_path)
    merge_summary = merge_jsonl_shards(
        shard_files,
        run_dir / "predictions.jsonl",
        expected_shards=[shard.shard_id for shard in shards],
    )
    rows = [
        json.loads(line)
        for line in (run_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    _write_fixture_matrix(rows, run_dir / "matrix.csv")

    atomic_write_json(run_dir / "environment.json", environment)
    atomic_write_json(
        run_dir / "models.json",
        {
            "schema_version": EXECUTION_SCHEMA_VERSION,
            "models": [dict(model) for model in FIXTURE_MODEL_RECORDS],
            "evidence_state": NON_EVIDENCE_FIXTURE,
        },
    )
    atomic_write_json(
        run_dir / "benchmark_contract.json",
        {
            "schema_version": EXECUTION_SCHEMA_VERSION,
            "benchmark_id": benchmark_id,
            "benchmark_version": "fixture-v1",
            "tasks": [{"task_id": f"{benchmark_id}-fixture-task"}],
            "subtasks": [{"subtask_id": "fixture-default"}],
            "split": "fixture",
            "item_count": len(item_ids),
            "evidence_state": NON_EVIDENCE_FIXTURE,
        },
    )
    atomic_write_text(
        run_dir / "config_snapshot.yaml",
        yaml.safe_dump(config, sort_keys=True),
    )
    shard_task_results: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in scheduler_result["results"]:
        shard_id = str(result["task_id"]).rsplit("--", 1)[-1]
        shard_task_results[shard_id].append(result)
    shard_status = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "config_hash": config_hash,
        "shards": [
            {
                "shard_id": shard.shard_id,
                "status": (
                    "success"
                    if all(
                        result["status"] == "success"
                        for result in shard_task_results[shard.shard_id]
                    )
                    else "failed"
                ),
                "item_count": shard.item_count,
                "model_count": len(FIXTURE_MODEL_RECORDS),
                "expected_rows": shard.item_count * len(FIXTURE_MODEL_RECORDS),
            }
            for shard in shards
        ],
        "evidence_state": NON_EVIDENCE_FIXTURE,
    }
    atomic_write_json(run_dir / "shard_status.json", shard_status)
    atomic_write_text(
        run_dir / "failure_summary.csv",
        "failure_type,count\nSUCCESS," + str(len(rows)) + "\n",
    )
    checksummed_files = (
        "environment.json",
        "models.json",
        "benchmark_contract.json",
        "config_snapshot.yaml",
        "shard_status.json",
        "failure_summary.csv",
        "predictions.jsonl",
        "matrix.csv",
    )
    checksums = build_file_checksums(run_dir, checksummed_files)
    manifest = build_run_manifest(
        study_id="study-c-fixture",
        run_id=run_label,
        benchmark_id=benchmark_id,
        benchmark_version="fixture-v1",
        config=config,
        models=FIXTURE_MODEL_RECORDS,
        shards=[shard.to_dict() for shard in shards],
        item_count=len(item_ids),
        expected_prediction_rows=len(rows),
        completion_state="complete",
        failure_state="none",
        evidence_state=NON_EVIDENCE_FIXTURE,
        config_class=("fixture_robustness_v5" if run_suffix else "fixture_common_panel_v5"),
        file_checksums=checksums,
        code_revision="fixture-code-v5",
        created_at="2000-01-01T00:00:00+00:00",
        extra={
            "execution_mode": "fixture",
            "scheduler": {
                "strategy": "one_worker_per_gpu",
                "gpu_ids": ["0", "1"],
                "worker_count": 2,
                "single_gpu_fallback": True,
            },
            "merge_summary": {
                "output_sha256": merge_summary["output_sha256"],
                "row_count": merge_summary["row_count"],
                "identical_duplicates_removed": merge_summary["identical_duplicates_removed"],
                "observed_shards": merge_summary["observed_shards"],
            },
            "fixture_model_lookup": model_by_id,
        },
    )
    atomic_write_json(run_dir / "run_manifest.json", manifest)
    atomic_write_json(
        run_dir / "file_checksums.json",
        {
            "schema_version": EXECUTION_SCHEMA_VERSION,
            "files": checksums,
            "evidence_state": NON_EVIDENCE_FIXTURE,
        },
    )
    return {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "status": "KAGGLE_T4X2_FIXTURE_VALIDATED",
        "stage": run_suffix or benchmark_id,
        "benchmark_id": benchmark_id,
        "mode": "fixture",
        "run_dir": str(run_dir),
        "run_id": run_label,
        "config_hash": config_hash,
        "row_count": len(rows),
        "worker_count": scheduler_result["worker_count"],
        "resumed_count": scheduler_result["resumed_count"],
        "evidence_state": NON_EVIDENCE_FIXTURE,
    }


def fixture_worker(task: Mapping[str, Any], gpu_id: str) -> dict[str, Any]:
    model = dict(task["model"])
    shard = dict(task["shard"])
    rows = [
        _fixture_prediction_row(
            task,
            model,
            item_id,
            shard_id=str(shard["shard_id"]),
            gpu_id=gpu_id,
        )
        for item_id in shard["item_ids"]
    ]
    return {
        "rows": rows,
        "shard_id": shard["shard_id"],
        "model_id": model["model_id"],
        "evidence_state": NON_EVIDENCE_FIXTURE,
    }


def package_fixture_runs(output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root)
    runs = [build_fixture_run(benchmark, root) for benchmark in ("mmlu", "gsm8k", "bbh")]
    package_dir = root / "packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    packages = []
    for run in runs:
        run_dir = Path(run["run_dir"])
        zip_path = package_dir / f"{run['run_id']}.zip"
        digest = create_deterministic_zip(run_dir, zip_path)
        packages.append(
            {
                "run_id": run["run_id"],
                "zip_path": str(zip_path),
                "zip_sha256": digest,
                "evidence_state": NON_EVIDENCE_FIXTURE,
            }
        )
    payload = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "status": "KAGGLE_T4X2_FIXTURE_VALIDATED",
        "stage": "package",
        "mode": "fixture",
        "packages": packages,
        "evidence_state": NON_EVIDENCE_FIXTURE,
    }
    atomic_write_json(root / "fixture_package_manifest.json", payload)
    return payload


def package_completed_runs(output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root)
    validation = validate_completed_runs(root)
    if validation["status"] != "pass":
        raise ValueError(f"Cannot package incomplete runs: {validation['problems']}")
    package_dir = root / "packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    packages = []
    for run_dir in sorted((root / "runs").iterdir()):
        if not run_dir.is_dir():
            continue
        zip_path = package_dir / f"{run_dir.name}.zip"
        packages.append(
            {
                "run_id": run_dir.name,
                "zip_path": str(zip_path),
                "zip_sha256": create_deterministic_zip(run_dir, zip_path),
            }
        )
    return {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "status": "packaged",
        "packages": packages,
        "evidence_state": "RESULT_REQUIRED_UNTIL_IMPORTED_AND_VALIDATED",
    }


def validate_completed_runs(output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root)
    run_root = root / "runs"
    problems: list[str] = []
    runs: list[str] = []
    if not run_root.exists():
        problems.append(f"Run directory does not exist: {run_root}")
    else:
        for run_dir in sorted(run_root.iterdir()):
            if not run_dir.is_dir():
                continue
            runs.append(run_dir.name)
            missing = [name for name in _fixture_package_files() if not (run_dir / name).is_file()]
            if missing:
                problems.append(f"{run_dir.name}: missing {missing}")
    return {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "status": "pass" if runs and not problems else "fail",
        "runs": runs,
        "problems": problems,
        "evidence_state": "VALIDATION_ONLY",
    }


def create_deterministic_zip(source_dir: str | Path, zip_path: str | Path) -> str:
    source = Path(source_dir)
    destination = Path(zip_path)
    if not source.is_dir():
        raise FileNotFoundError(f"Package source directory does not exist: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(path for path in source.rglob("*") if path.is_file())
    if not files:
        raise ValueError(f"Package source directory has no files: {source}")
    temp = destination.with_name(f".{destination.name}.tmp")
    with zipfile.ZipFile(
        temp,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        for path in files:
            if path.resolve() == destination.resolve() or path.resolve() == temp.resolve():
                continue
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2000, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100600 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(
                info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
            )
    os.replace(temp, destination)
    from valideval.execution.manifest import sha256_file

    return sha256_file(destination)


def _fixture_environment(root: Path) -> dict[str, Any]:
    payload = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "status": "KAGGLE_T4X2_FIXTURE_VALIDATED",
        "stage": "environment",
        "mode": "fixture",
        "environment": _fixture_environment_payload(),
        "supported_modes": list(EXECUTION_MODES),
        "worker_strategy": "one_worker_per_gpu_with_single_gpu_fallback",
        "external_tracking": "disabled",
        "embedded_tokens": False,
        "evidence_state": NON_EVIDENCE_FIXTURE,
    }
    atomic_write_json(root / "fixture_environment_preflight.json", payload)
    return payload


def _fixture_environment_payload() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "executable_name": Path(sys.executable).name,
        "pytorch": _package_version("torch"),
        "transformers": _package_version("transformers"),
        "accelerate": _package_version("accelerate"),
        "datasets": _package_version("datasets"),
        "tokenizers": _package_version("tokenizers"),
        "bitsandbytes": _package_version("bitsandbytes"),
        "deterministic_fixture": True,
        "external_tracking": "disabled",
        "evidence_state": NON_EVIDENCE_FIXTURE,
    }


def _package_version(name: str) -> str | None:
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return None


def _fixture_config(
    benchmark_id: str,
    run_id: str,
    shards: Sequence[Any],
    *,
    run_suffix: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "execution_mode": "fixture",
        "evidence_state": NON_EVIDENCE_FIXTURE,
        "study_id": "study-c-fixture",
        "run_id": run_id,
        "benchmark": {
            "benchmark_id": benchmark_id,
            "revision": "fixture-v1",
            "split": "fixture",
        },
        "models": [
            {
                "model_id": model["model_id"],
                "revision": model["model_revision"],
                "dtype": model["dtype"],
                "quantization": model["quantization"],
            }
            for model in FIXTURE_MODEL_RECORDS
        ],
        "prompt": {
            "prompt_template_id": "fixture-prompt-v1",
            "few_shot_id": "fixture-zero-shot",
            "chat_template_id": "fixture-chat-v1",
        },
        "generation": {
            "generation_config_id": "fixture-greedy-v1",
            "seed": 0,
            "max_new_tokens": 8,
        },
        "scoring": {"version": "fixture-scoring-v1"},
        "extraction": {"version": "fixture-extraction-v1"},
        "shards": [shard.to_dict() for shard in shards],
        "code_revision": "fixture-code-v5",
        "robustness_condition": run_suffix,
    }


def _fixture_prediction_row(
    task: Mapping[str, Any],
    model: Mapping[str, Any],
    item_id: str,
    *,
    shard_id: str,
    gpu_id: str,
) -> dict[str, Any]:
    benchmark_id = str(task["benchmark_id"])
    item_hash = sha256_bytes(f"{benchmark_id}|fixture|{item_id}".encode())
    correct = (
        int(item_hash[-2:], 16) % 2
        == int(sha256_bytes(str(model["model_id"]).encode())[-2:], 16) % 2
    )
    return {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "study_id": task["study_id"],
        "run_id": task["run_id"],
        "benchmark_id": benchmark_id,
        "benchmark_version": task["benchmark_version"],
        "task_id": f"{benchmark_id}-fixture-task",
        "subtask_id": "fixture-default",
        "split": "fixture",
        "item_id": item_id,
        "item_hash": item_hash,
        "model_id": model["model_id"],
        "model_revision": model["model_revision"],
        "model_family": model["model_family"],
        "prompt_template_id": "fixture-prompt-v1",
        "few_shot_id": "fixture-zero-shot",
        "chat_template_id": "fixture-chat-v1",
        "generation_config_id": "fixture-greedy-v1",
        "scoring_version": "fixture-scoring-v1",
        "extraction_version": "fixture-extraction-v1",
        "seed": 0,
        "shard_id": shard_id,
        "attempt_id": "fixture-attempt-1",
        "raw_output": "A" if correct else "B",
        "parsed_output": "A" if correct else "B",
        "gold_output": "A",
        "is_correct": correct,
        "extraction_status": "success",
        "generation_status": "success",
        "failure_type": "SUCCESS",
        "latency_seconds": 0.0,
        "input_tokens": 1,
        "output_tokens": 1,
        "device": f"cuda:{gpu_id}" if gpu_id != "cpu" else "cpu",
        "dtype": model["dtype"],
        "quantization": model["quantization"],
        "code_revision": "fixture-code-v5",
        "environment_hash": task["environment_hash"],
        "config_hash": task["config_hash"],
        "created_at": "2000-01-01T00:00:00+00:00",
        "evidence_state": NON_EVIDENCE_FIXTURE,
    }


def _write_fixture_matrix(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    frame = pd.DataFrame(rows).pivot(
        index="model_id",
        columns="item_id",
        values="is_correct",
    )
    frame = frame.sort_index().reindex(sorted(frame.columns), axis=1).astype(int)
    frame.index.name = "model_id"
    atomic_write_text(path, frame.to_csv(lineterminator="\n"))


def _safe_task_name(task_id: str) -> str:
    return "".join(
        character if character.isalnum() or character in "._-" else "_" for character in task_id
    )


def _fixture_package_files() -> tuple[str, ...]:
    return (
        "run_manifest.json",
        "environment.json",
        "models.json",
        "benchmark_contract.json",
        "config_snapshot.yaml",
        "file_checksums.json",
        "shard_status.json",
        "failure_summary.csv",
        "predictions.jsonl",
        "matrix.csv",
    )
