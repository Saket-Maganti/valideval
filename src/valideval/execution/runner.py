from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import shutil
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from valideval import __version__
from valideval.execution.config import (
    V6ConfigurationError,
    discover_repository_root,
    load_run_config,
    load_yaml_mapping,
    resolve_source_commit,
    semantic_config_hash,
)
from valideval.execution.datasets import (
    DatasetResolutionError,
    FrozenBenchmarkItem,
    load_frozen_benchmark_items,
)
from valideval.execution.manifest import (
    EXECUTION_SCHEMA_VERSION,
    atomic_write_json,
    atomic_write_text,
    build_file_checksums,
    build_run_manifest,
    canonical_json_bytes,
    sha256_bytes,
)
from valideval.execution.models import ModelResolutionError, load_panel_config
from valideval.execution.packaging import (
    PackageValidationError,
    create_deterministic_run_zip,
    validate_run_directory,
)
from valideval.execution.shards import (
    IncompleteShardError,
    ShardError,
    T4x2Scheduler,
    build_deterministic_shards,
    merge_jsonl_shards,
)
from valideval.execution.workers import production_worker

RUN_COMPLETE = "RUN_COMPLETE"
RUN_COMPLETE_WITH_RECORDED_FAILURES = "RUN_COMPLETE_WITH_RECORDED_FAILURES"
RUN_INCOMPLETE_RETRYABLE = "RUN_INCOMPLETE_RETRYABLE"
RUN_INCOMPLETE_FATAL = "RUN_INCOMPLETE_FATAL"
CONFIG_MISMATCH = "CONFIG_MISMATCH"
DATASET_RESOLUTION_FAILURE = "DATASET_RESOLUTION_FAILURE"
MODEL_RESOLUTION_FAILURE = "MODEL_RESOLUTION_FAILURE"
INSUFFICIENT_DISK = "INSUFFICIENT_DISK"
INSUFFICIENT_GPU = "INSUFFICIENT_GPU"
PACKAGE_VALIDATION_FAILURE = "PACKAGE_VALIDATION_FAILURE"

_DEPENDENCIES = (
    "numpy",
    "pandas",
    "pydantic",
    "PyYAML",
    "torch",
    "transformers",
    "accelerate",
    "datasets",
    "tokenizers",
    "safetensors",
    "pyarrow",
    "tqdm",
)


def run_from_config(
    config_path: str | Path,
    *,
    mode_override: str | None = None,
    output_root: str | Path | None = None,
    repository_root: str | Path | None = None,
    injected_items: Sequence[FrozenBenchmarkItem] | None = None,
    worker: Callable[[Mapping[str, Any], str], Mapping[str, Any]] = production_worker,
) -> dict[str, Any]:
    config_source = Path(config_path).resolve()
    try:
        root = (
            Path(repository_root).resolve()
            if repository_root is not None
            else discover_repository_root(config_source)
        )
        config = load_run_config(config_source, repository_root=root)
        if mode_override is not None:
            config = config.model_copy(update={"mode": mode_override})
            config = type(config).model_validate(config.model_dump(mode="json"))
    except V6ConfigurationError as exc:
        return _terminal(CONFIG_MISMATCH, error=str(exc), config_path=str(config_source))

    destination_root = Path(output_root or config.output_root)
    if not destination_root.is_absolute():
        destination_root = root / destination_root
    run_dir = destination_root / "runs" / config.run_id

    if config.mode == "validate_only":
        try:
            validation = validate_run_directory(
                run_dir,
                expected_benchmark=config.benchmark_id,
                expected_config_hash=semantic_config_hash(config),
            )
        except (PackageValidationError, ValueError) as exc:
            return _terminal(PACKAGE_VALIDATION_FAILURE, error=str(exc), run_dir=str(run_dir))
        return _terminal(RUN_COMPLETE, run_dir=str(run_dir), validation=validation)
    if config.mode == "package_only":
        return _package_existing_run(config, run_dir, destination_root)

    try:
        panel_path = root / config.panel_config
        contract_path = root / config.benchmark_contract
        subset_path = root / config.subset_manifest
        panel = load_panel_config(panel_path)
        contract = _load_contract(contract_path, config.benchmark_id)
        robustness_path = getattr(config, "robustness_config", None)
        if robustness_path:
            robustness = load_yaml_mapping(root / robustness_path)
            contract = _apply_robustness_contract(
                contract,
                robustness,
                config.benchmark_id,
            )
            _validate_robustness_panel(panel, robustness)
    except (V6ConfigurationError, ModelResolutionError, ValueError) as exc:
        return _terminal(MODEL_RESOLUTION_FAILURE, error=str(exc))

    try:
        preflight = environment_preflight(config, panel, root, destination_root)
    except InsufficientDiskError as exc:
        return _terminal(INSUFFICIENT_DISK, error=str(exc))
    except InsufficientGpuError as exc:
        return _terminal(INSUFFICIENT_GPU, error=str(exc))
    except V6ConfigurationError as exc:
        return _terminal(CONFIG_MISMATCH, error=str(exc))

    try:
        if injected_items is None:
            items, loaded_contract, subset = load_frozen_benchmark_items(contract_path, subset_path)
            if loaded_contract != contract:
                raise DatasetResolutionError("benchmark contract changed during resolution")
        else:
            if config.execution.backend != "mock":
                raise DatasetResolutionError(
                    "injected items are allowed only with the mock backend"
                )
            items = list(injected_items)
            subset = json.loads(subset_path.read_text(encoding="utf-8"))
        _validate_item_contract(items, contract)
    except (DatasetResolutionError, OSError, ValueError, json.JSONDecodeError) as exc:
        return _terminal(DATASET_RESOLUTION_FAILURE, error=str(exc))

    config_hash = semantic_config_hash(config)
    prompt_hash = _prompt_hash(contract)
    environment_payload = _environment_payload(config, preflight)
    environment_hash = sha256_bytes(canonical_json_bytes(environment_payload))
    try:
        _initialize_run_directory(
            run_dir,
            config=config,
            config_hash=config_hash,
            resume=config.mode == "resume",
        )
        scheduler_result, logical_shards = _execute_jobs(
            config=config,
            panel=panel,
            contract=contract,
            subset=subset,
            items=items,
            destination_root=destination_root,
            config_hash=config_hash,
            prompt_hash=prompt_hash,
            environment_hash=environment_hash,
            source_commit=preflight["source_commit"],
            worker=worker,
        )
        outcome = _materialize_run(
            config=config,
            panel=panel,
            contract=contract,
            subset=subset,
            items=items,
            run_dir=run_dir,
            destination_root=destination_root,
            scheduler_result=scheduler_result,
            logical_shards=logical_shards,
            environment_payload=environment_payload,
            config_hash=config_hash,
            prompt_hash=prompt_hash,
            source_commit=preflight["source_commit"],
        )
        return outcome
    except (ShardError, IncompleteShardError, PackageValidationError) as exc:
        return _terminal(RUN_INCOMPLETE_RETRYABLE, error=str(exc), run_dir=str(run_dir))
    except Exception as exc:
        return _terminal(RUN_INCOMPLETE_FATAL, error=str(exc), run_dir=str(run_dir))


def preflight_from_config(
    config_path: str | Path,
    *,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    source = Path(config_path).resolve()
    try:
        root = discover_repository_root(source)
        config = load_run_config(source, repository_root=root)
        panel = load_panel_config(root / config.panel_config)
        destination = Path(output_root or config.output_root)
        if not destination.is_absolute():
            destination = root / destination
        payload = environment_preflight(config, panel, root, destination)
    except InsufficientDiskError as exc:
        return _terminal(INSUFFICIENT_DISK, error=str(exc), config_path=str(source))
    except InsufficientGpuError as exc:
        return _terminal(INSUFFICIENT_GPU, error=str(exc), config_path=str(source))
    except (V6ConfigurationError, ModelResolutionError, ValueError) as exc:
        return _terminal(CONFIG_MISMATCH, error=str(exc), config_path=str(source))
    return {
        "schema_version": config.schema_version,
        "status": "PREFLIGHT_COMPLETE",
        "config_path": str(source),
        "mode": config.mode,
        "benchmark_id": config.benchmark_id,
        "evidence_class": config.evidence_class,
        "preflight": payload,
    }


class InsufficientDiskError(RuntimeError):
    pass


class InsufficientGpuError(RuntimeError):
    pass


def environment_preflight(
    config: Any,
    panel: Mapping[str, Any],
    repository_root: str | Path,
    output_root: str | Path,
) -> dict[str, Any]:
    root = Path(repository_root)
    source_commit = resolve_source_commit(
        root,
        required_source_ref=config.required_source_ref,
        expected_source_commit=config.expected_source_commit,
        allow_environment=config.allow_source_commit_from_environment,
    )
    dependencies = _dependency_versions()
    if config.execution.backend == "transformers":
        missing = [name for name in _DEPENDENCIES if dependencies.get(name) is None]
        if missing:
            raise V6ConfigurationError(f"missing production dependencies: {missing}")
        try:
            import torch
        except ImportError as exc:
            raise V6ConfigurationError("torch is unavailable") from exc
        visible_gpu_count = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
    else:
        visible_gpu_count = len(config.execution.gpu_ids)
    required = config.execution.required_gpu_count
    if visible_gpu_count < required:
        single_allowed = visible_gpu_count == 1 and config.execution.allow_single_gpu_fallback
        if not single_allowed:
            raise InsufficientGpuError(
                f"visible GPU count {visible_gpu_count} is below required count {required}"
            )
    gated = [
        model["repository"]
        for model in panel["models"]
        if str(model.get("access", "public")) != "public"
    ]
    if config.execution.backend == "transformers" and gated and not os.environ.get("HF_TOKEN"):
        raise V6ConfigurationError(
            f"gated checkpoints require HF_TOKEN before execution; unavailable={gated}"
        )
    destination = Path(output_root)
    destination.mkdir(parents=True, exist_ok=True)
    free_bytes = shutil.disk_usage(destination).free
    model_bytes = sum(int(model["expected_download_size"]) for model in panel["models"])
    if config.execution.backend == "mock":
        model_bytes = 0
    required_bytes = (
        int(
            (config.execution.minimum_free_disk_gb + config.execution.model_download_margin_gb)
            * 1024**3
        )
        + model_bytes
    )
    if free_bytes < required_bytes:
        raise InsufficientDiskError(
            f"free disk {free_bytes / 1024**3:.2f} GiB is below the fail-closed requirement "
            f"{required_bytes / 1024**3:.2f} GiB"
        )
    return {
        "status": "pass",
        "package_version": __version__,
        "execution_schema_version": EXECUTION_SCHEMA_VERSION,
        "source_commit": source_commit,
        "required_source_ref": config.required_source_ref,
        "expected_source_commit": source_commit,
        "actual_source_commit": source_commit,
        "source_match": True,
        "config_hash": semantic_config_hash(config),
        "visible_gpu_count": visible_gpu_count,
        "configured_gpu_ids": list(config.execution.gpu_ids),
        "free_disk_bytes": free_bytes,
        "required_disk_bytes": required_bytes,
        "dependencies": dependencies,
    }


def _execute_jobs(
    *,
    config: Any,
    panel: Mapping[str, Any],
    contract: Mapping[str, Any],
    subset: Mapping[str, Any],
    items: Sequence[FrozenBenchmarkItem],
    destination_root: Path,
    config_hash: str,
    prompt_hash: str,
    environment_hash: str,
    source_commit: str,
    worker: Callable[[Mapping[str, Any], str], Mapping[str, Any]],
) -> tuple[dict[str, Any], list[Any]]:
    item_ids = [item.public.item_id for item in items]
    shards = build_deterministic_shards(
        item_ids,
        shard_count=config.execution.shard_count,
        prefix=f"{config.benchmark_id}-{str(getattr(config, 'stage', 'S1')).lower()}-v{config.schema_version[0]}",
    )
    item_to_shard = {item_id: shard.shard_id for shard in shards for item_id in shard.item_ids}
    private_gold = {item.public.item_id: item.private_gold for item in items}
    tasks = []
    for model in panel["models"]:
        task_id = _safe_task_id(str(model["canonical_model_id"]))
        tasks.append(
            {
                "task_id": task_id,
                "study_id": config.study_id,
                "run_id": config.run_id,
                "benchmark_id": config.benchmark_id,
                "benchmark_contract": dict(contract),
                "subset_hash": subset["public_subset_sha256"],
                "model": dict(model),
                "items": [item.public.to_dict() for item in items],
                "private_gold": private_gold,
                "item_to_shard": item_to_shard,
                "backend": config.execution.backend,
                "model_cache_dir": os.environ.get("HF_HOME"),
                "config_hash": config_hash,
                "prompt_hash": prompt_hash,
                "environment_hash": environment_hash,
                "code_revision": source_commit,
                "evidence_class": config.evidence_class,
                "batch_size": config.execution.batch_size,
                "max_sequence_length": config.execution.max_sequence_length,
                "allow_batch_size_fallback": config.execution.allow_batch_size_fallback,
                "allow_sequence_length_fallback": config.execution.allow_sequence_length_fallback,
                "minimum_sequence_length": config.execution.minimum_sequence_length,
                "dtype": model["dtype"],
                "quantization": model["quantization"],
                "estimated_duration": float(model["expected_download_size"]),
            }
        )
    gpu_ids = list(config.execution.gpu_ids)
    if config.execution.backend == "mock" and not gpu_ids:
        gpu_ids = ["0", "1"]
    scheduler = T4x2Scheduler(
        destination_root / "scheduler" / config.run_id,
        gpu_ids=gpu_ids,
        max_retries=config.execution.max_retries,
        use_processes=config.execution.use_processes,
        process_start_method=config.execution.process_start_method,
    )
    scheduler_run_config = _frozen_config_payload(config)
    scheduler_config = {
        "run_config": scheduler_run_config,
        "config_hash": config_hash,
        "prompt_hash": prompt_hash,
        "subset_hash": subset["public_subset_sha256"],
        "source_commit": source_commit,
        "model_revisions": {
            model["canonical_model_id"]: model["revision"] for model in panel["models"]
        },
        "logical_shards": [shard.to_dict() for shard in shards],
    }
    return (
        scheduler.run(tasks, worker, config=scheduler_config, resume=config.mode == "resume"),
        shards,
    )


def _materialize_run(
    *,
    config: Any,
    panel: Mapping[str, Any],
    contract: Mapping[str, Any],
    subset: Mapping[str, Any],
    items: Sequence[FrozenBenchmarkItem],
    run_dir: Path,
    destination_root: Path,
    scheduler_result: Mapping[str, Any],
    logical_shards: Sequence[Any],
    environment_payload: Mapping[str, Any],
    config_hash: str,
    prompt_hash: str,
    source_commit: str,
) -> dict[str, Any]:
    scheduler_root = destination_root / "scheduler" / config.run_id
    shard_files: list[Path] = []
    failed_jobs: list[dict[str, Any]] = []
    successful_resource_fallbacks: dict[str, list[dict[str, Any]]] = {}
    model_job_status: dict[str, str] = {}
    for result in scheduler_result["results"]:
        task_id = str(result["task_id"])
        if result["status"] != "success":
            failed_jobs.append(
                {
                    "task_id": task_id,
                    "failure_type": result.get("failure_type", "UNKNOWN_FAILURE"),
                    "error_type": result.get("error_type"),
                    "attempts": result.get("attempts"),
                    "fallbacks": result.get("fallbacks", []),
                }
            )
            model_job_status[task_id] = "failed"
            continue
        worker_dir = scheduler_root / str(result["worker_id"]) / "outputs"
        output_path = worker_dir / f"{task_id}.jsonl"
        rows = result["output"]["rows"]
        if result.get("fallbacks"):
            successful_resource_fallbacks[task_id] = list(result["fallbacks"])
        atomic_write_text(
            output_path,
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
                for row in rows
            ),
        )
        shard_files.append(output_path)
        model_job_status[task_id] = "complete"
    if not shard_files:
        raise IncompleteShardError("no model job produced predictions")
    merge = merge_jsonl_shards(
        shard_files,
        run_dir / "predictions.jsonl",
        expected_shards=[shard.shard_id for shard in logical_shards],
        allow_identical_duplicates=False,
    )
    prediction_rows = [
        json.loads(line)
        for line in (run_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    _validate_prediction_coverage(prediction_rows, items, panel, failed_jobs)
    _write_matrix(prediction_rows, run_dir / "matrix.csv")
    atomic_write_json(run_dir / "environment.json", dict(environment_payload))
    manifest_models = [
        {
            "model_id": model["canonical_model_id"],
            "revision": model["revision"],
            "tokenizer_revision": model["tokenizer_revision"],
            "family": model["family"],
            "dtype": model["dtype"],
            "quantization": model["quantization"],
            "trust_remote_code": model["trust_remote_code"],
            "chat_template_policy": model["chat_template_policy"],
        }
        for model in panel["models"]
    ]
    atomic_write_json(
        run_dir / "models.json",
        {
            "schema_version": config.schema_version,
            "panel_id": panel["panel_id"],
            "evidence_class": panel["evidence_class"],
            "scientific_panel_adequacy": panel.get("scientific_panel_adequacy", False),
            "models": manifest_models,
        },
    )
    atomic_write_json(
        run_dir / "benchmark_contract.json",
        {
            **dict(contract),
            "frozen_subset_manifest": config.subset_manifest,
            "frozen_subset_sha256": config.subset_manifest_sha256,
            "public_subset_sha256": subset["public_subset_sha256"],
            "prompt_hash": prompt_hash,
        },
    )
    atomic_write_text(
        run_dir / "config_snapshot.yaml",
        yaml.safe_dump(_frozen_config_payload(config), sort_keys=True),
    )
    _write_failure_summary(prediction_rows, failed_jobs, run_dir / "failure_summary.csv")
    shard_status = _build_shard_status(
        prediction_rows, logical_shards, len(panel["models"]), failed_jobs, config_hash
    )
    atomic_write_json(run_dir / "shard_status.json", shard_status)
    checksum_names = (
        "environment.json",
        "models.json",
        "benchmark_contract.json",
        "config_snapshot.yaml",
        "shard_status.json",
        "failure_summary.csv",
        "predictions.jsonl",
        "matrix.csv",
    )
    checksums = build_file_checksums(run_dir, checksum_names)
    completion_state = "complete_with_declared_failures" if failed_jobs else "complete"
    failure_state = (
        "recorded_model_or_item_failures"
        if (failed_jobs or any(row["failure_type"] != "SUCCESS" for row in prediction_rows))
        else "none"
    )
    manifest = build_run_manifest(
        study_id=config.study_id,
        run_id=config.run_id,
        benchmark_id=config.benchmark_id,
        benchmark_version=str(contract["benchmark_version"]),
        config=_frozen_config_payload(config),
        models=manifest_models,
        shards=[shard.to_dict() for shard in logical_shards],
        item_count=len(items),
        expected_prediction_rows=len(items) * len(panel["models"]),
        completion_state=completion_state,
        failure_state=failure_state,
        evidence_state=config.evidence_class,
        config_class=(
            "s1_engineering_smoke_v6"
            if config.schema_version == "6.0"
            else f"study_c_{config.stage.lower()}_v7"
        ),
        file_checksums=checksums,
        code_revision=source_commit,
        extra={
            "execution_mode": config.mode,
            "execution_backend": config.execution.backend,
            "mocked_production_path": config.execution.backend == "mock",
            "source_commit": source_commit,
            "required_source_ref": config.required_source_ref,
            "expected_source_commit": source_commit,
            "actual_source_commit": source_commit,
            "source_match": True,
            "dataset_revision": contract["dataset_revision"],
            "prompt_hash": prompt_hash,
            "subset_manifest_sha256": config.subset_manifest_sha256,
            "allowed_failed_models": [row["task_id"] for row in failed_jobs],
            "scheduler": {
                "strategy": "one_isolated_worker_per_gpu_lpt",
                "gpu_ids": list(scheduler_result["gpu_ids"]),
                "worker_count": scheduler_result["worker_count"],
                "resumed_count": scheduler_result["resumed_count"],
                "model_job_status": model_job_status,
                "successful_resource_fallbacks": successful_resource_fallbacks,
            },
            "merge_summary": merge,
            # Every V6 S1 artifact belongs to the engineering-smoke protocol, including
            # NON_EVIDENCE_FIXTURE exercises of that path. V7 uses stage-scoped claim gates.
            "engineering_only": config.schema_version == "6.0",
        },
    )
    if manifest["config_hash"] != config_hash:
        raise V6ConfigurationError("manifest and runner configuration hashes disagree")
    atomic_write_json(run_dir / "run_manifest.json", manifest)
    atomic_write_json(
        run_dir / "file_checksums.json",
        {"schema_version": config.schema_version, "files": checksums},
    )
    validation = validate_run_directory(
        run_dir,
        expected_benchmark=config.benchmark_id,
        expected_config_hash=config_hash,
    )
    package_dir = destination_root / "packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    version_label = "v6_s1" if config.schema_version == "6.0" else f"v7_{config.stage.lower()}"
    zip_path = package_dir / f"valideval_{version_label}_{config.benchmark_id}_{config.run_id}.zip"
    zip_sha256 = create_deterministic_run_zip(run_dir, zip_path)
    terminal = RUN_COMPLETE_WITH_RECORDED_FAILURES if failure_state != "none" else RUN_COMPLETE
    return _terminal(
        terminal,
        run_id=config.run_id,
        benchmark_id=config.benchmark_id,
        mode=config.mode,
        evidence_class=config.evidence_class,
        run_dir=str(run_dir),
        config_hash=config_hash,
        row_count=len(prediction_rows),
        failed_model_jobs=failed_jobs,
        validation=validation,
        zip_path=str(zip_path),
        zip_sha256=zip_sha256,
    )


def _package_existing_run(
    config: Any,
    run_dir: Path,
    destination_root: Path,
) -> dict[str, Any]:
    try:
        validation = validate_run_directory(
            run_dir,
            expected_benchmark=config.benchmark_id,
            expected_config_hash=semantic_config_hash(config),
        )
        zip_path = (
            destination_root
            / "packages"
            / (
                f"valideval_v6_s1_{config.benchmark_id}_{config.run_id}.zip"
                if config.schema_version == "6.0"
                else f"valideval_v7_{config.stage.lower()}_{config.benchmark_id}_{config.run_id}.zip"
            )
        )
        digest = create_deterministic_run_zip(run_dir, zip_path)
    except (PackageValidationError, ValueError) as exc:
        return _terminal(PACKAGE_VALIDATION_FAILURE, error=str(exc), run_dir=str(run_dir))
    return _terminal(
        RUN_COMPLETE,
        run_dir=str(run_dir),
        validation=validation,
        zip_path=str(zip_path),
        zip_sha256=digest,
    )


def _load_contract(path: Path, expected_benchmark: str) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise V6ConfigurationError("benchmark contract must be a mapping")
    required = {
        "schema_version",
        "benchmark_contract_id",
        "benchmark_id",
        "benchmark_version",
        "dataset_repository",
        "dataset_revision",
        "split",
        "prompt_template_version",
        "few_shot_policy",
        "few_shot_examples_hash",
        "generation_config_id",
        "generation_parameters",
        "scoring_version",
        "extraction_version",
        "generation_view",
    }
    missing = sorted(required.difference(payload))
    if "expected_item_count" not in payload and "expected_s1_item_count" not in payload:
        missing.append("expected_item_count")
    if missing:
        raise V6ConfigurationError(f"benchmark contract missing fields: {missing}")
    if payload["benchmark_id"] != expected_benchmark:
        raise V6ConfigurationError("run and benchmark contract disagree")
    forbidden = set(payload["generation_view"].get("forbidden_fields", []))
    required_forbidden = {"answer", "gold", "gold_answer", "is_correct"}
    if not required_forbidden.issubset(forbidden):
        raise V6ConfigurationError("benchmark generation view does not seal the gold boundary")
    if payload["few_shot_policy"] not in {"zero_shot_s1_v6", "zero_shot_v7"}:
        raise V6ConfigurationError("execution requires a frozen zero-shot policy")
    return payload


def _apply_robustness_contract(
    contract: Mapping[str, Any],
    robustness: Mapping[str, Any],
    benchmark_id: str,
) -> dict[str, Any]:
    declared = robustness.get("benchmark", robustness.get("benchmarks"))
    matches = benchmark_id == declared or (
        isinstance(declared, list) and benchmark_id in map(str, declared)
    )
    if not matches or robustness.get("evidence_class") != "ROBUSTNESS":
        raise V6ConfigurationError("robustness config does not match the run benchmark/evidence")
    result = dict(contract)
    generation = dict(result["generation_parameters"])
    condition = str(robustness["condition"])
    if "prompt" in robustness:
        result["prompt_instruction"] = str(robustness["prompt"])
    if condition == "option_log_likelihood":
        if benchmark_id != "mmlu":
            raise V6ConfigurationError("option log-likelihood is implemented only for MMLU")
        result["generation_mode"] = "option_log_likelihood"
        result["generation_config_id"] = "mmlu_option_log_likelihood_v7"
        result["extraction_version"] = "mmlu_option_log_likelihood_v7"
        result["scoring_version"] = "mmlu_exact_choice_v7"
    elif condition == "alternate_prompt_and_saved_output_parser":
        result["extraction_version"] = "final_answer_marker_strict_v7"
        result["prompt_template_version"] = "gsm8k_alternate_prompt_v7"
    elif condition == "alternate_zero_shot_prompt":
        result["prompt_template_version"] = "bbh_alternate_zero_shot_v7"
    elif condition == "stochastic_seed_subset":
        generation.update(
            {
                "do_sample": True,
                "temperature": float(robustness["temperature"]),
                "top_p": float(robustness["top_p"]),
            }
        )
    elif condition == "controlled_generation":
        generation.update(
            {
                "do_sample": bool(robustness["do_sample"]),
                "temperature": float(robustness["temperature"]),
                "max_new_tokens": int(robustness["max_new_tokens"]),
            }
        )
    elif condition == "representative_quantization_sensitivity":
        pass
    else:
        raise V6ConfigurationError(
            f"robustness condition requires a dedicated frozen panel or is unsupported: {condition}"
        )
    result["generation_parameters"] = generation
    result["robustness_condition"] = condition
    return result


def _validate_robustness_panel(panel: Mapping[str, Any], robustness: Mapping[str, Any]) -> None:
    if robustness.get("condition") != "representative_quantization_sensitivity":
        return
    expected = set(map(str, robustness.get("representatives", [])))
    observed = {str(model["repository"]) for model in panel["models"]}
    if observed != expected:
        raise V6ConfigurationError("quantization panel does not match frozen representatives")
    observed_precisions = {str(model["quantization"]) for model in panel["models"]}
    allowed = {
        "none" if value == "float16" else "nf4" if value == "bitsandbytes_nf4" else str(value)
        for value in robustness.get("precisions", [])
    }
    if len(observed_precisions) != 1 or not observed_precisions.issubset(allowed):
        raise V6ConfigurationError("quantization panel must freeze exactly one allowed precision")


def _validate_item_contract(
    items: Sequence[FrozenBenchmarkItem],
    contract: Mapping[str, Any],
) -> None:
    expected_value = contract.get("expected_item_count")
    if expected_value is None:
        expected_value = contract["expected_s1_item_count"]
    expected = int(expected_value)
    if len(items) != expected:
        raise DatasetResolutionError(f"expected {expected} frozen items, got {len(items)}")
    ids = [item.public.item_id for item in items]
    if len(set(ids)) != len(ids):
        raise DatasetResolutionError("duplicate frozen item ID")
    if any(item.public.benchmark_id != contract["benchmark_id"] for item in items):
        raise DatasetResolutionError("mixed benchmark item set")


def _initialize_run_directory(
    run_dir: Path,
    *,
    config: Any,
    config_hash: str,
    resume: bool,
) -> None:
    if run_dir.exists():
        if not resume:
            raise V6ConfigurationError(f"run directory exists and resume is disabled: {run_dir}")
        snapshot = run_dir / "config_snapshot.yaml"
        if snapshot.is_file():
            observed = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
            if not isinstance(observed, dict) or semantic_config_hash(observed) != config_hash:
                raise V6ConfigurationError("existing run configuration does not match resume")
        return
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = run_dir.with_name(f".{run_dir.name}.initializing")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=False)
    atomic_write_text(
        temporary / "config_snapshot.yaml",
        yaml.safe_dump(_frozen_config_payload(config), sort_keys=True),
    )
    os.replace(temporary, run_dir)


def _environment_payload(
    config: Any,
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": config.schema_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "package_version": __version__,
        "execution_schema_version": EXECUTION_SCHEMA_VERSION,
        "source_commit": preflight["source_commit"],
        "config_hash": preflight["config_hash"],
        "backend": config.execution.backend,
        "visible_gpu_count": preflight["visible_gpu_count"],
        "configured_gpu_ids": preflight["configured_gpu_ids"],
        "free_disk_bytes_at_preflight": preflight["free_disk_bytes"],
        "required_disk_bytes": preflight["required_disk_bytes"],
        "dependencies": preflight["dependencies"],
    }


def _dependency_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for distribution in _DEPENDENCIES:
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    return versions


def _prompt_hash(contract: Mapping[str, Any]) -> str:
    keys = (
        "prompt_template_version",
        "prompt_instruction",
        "task_prompt_policies",
        "few_shot_policy",
        "few_shot_examples_hash",
        "generation_config_id",
        "generation_parameters",
    )
    return sha256_bytes(canonical_json_bytes({key: contract.get(key) for key in keys}))


def _validate_prediction_coverage(
    rows: Sequence[Mapping[str, Any]],
    items: Sequence[FrozenBenchmarkItem],
    panel: Mapping[str, Any],
    failed_jobs: Sequence[Mapping[str, Any]],
) -> None:
    expected_items = {item.public.item_id for item in items}
    failed_task_ids = {str(row["task_id"]) for row in failed_jobs}
    model_ids = {str(model["canonical_model_id"]) for model in panel["models"]}
    failed_models = {
        model_id for model_id in model_ids if _safe_task_id(model_id) in failed_task_ids
    }
    by_model: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        by_model[str(row["model_id"])].add(str(row["item_id"]))
    for model_id in model_ids - failed_models:
        if by_model.get(model_id, set()) != expected_items:
            missing = expected_items.difference(by_model.get(model_id, set()))
            extra = by_model.get(model_id, set()).difference(expected_items)
            raise IncompleteShardError(
                f"coverage mismatch for {model_id}: missing={len(missing)}, extra={len(extra)}"
            )
    if set(by_model).difference(model_ids):
        raise IncompleteShardError("predictions contain an undeclared model")


def _write_matrix(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    frame = pd.DataFrame(rows)
    matrix = frame.pivot(index="model_id", columns="item_id", values="is_correct")
    matrix = matrix.sort_index().sort_index(axis=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    matrix.to_csv(temporary)
    os.replace(temporary, path)


def _write_failure_summary(
    rows: Sequence[Mapping[str, Any]],
    failed_jobs: Sequence[Mapping[str, Any]],
    path: Path,
) -> None:
    counts = Counter(str(row["failure_type"]) for row in rows)
    for failure in failed_jobs:
        counts[str(failure["failure_type"])] += 1
    lines = ["failure_type,count\n"]
    for failure_type, count in sorted(counts.items()):
        lines.append(f"{failure_type},{count}\n")
    atomic_write_text(path, "".join(lines))


def _build_shard_status(
    rows: Sequence[Mapping[str, Any]],
    logical_shards: Sequence[Any],
    model_count: int,
    failed_jobs: Sequence[Mapping[str, Any]],
    config_hash: str,
) -> dict[str, Any]:
    counts = Counter(str(row["shard_id"]) for row in rows)
    failed_count = len(failed_jobs)
    return {
        "schema_version": "6.0",
        "config_hash": config_hash,
        "failed_model_jobs": list(failed_jobs),
        "shards": [
            {
                "shard_id": shard.shard_id,
                "status": "complete_with_recorded_model_failures" if failed_count else "complete",
                "item_count": shard.item_count,
                "model_count": model_count,
                "expected_rows": shard.item_count * model_count,
                "observed_rows": counts[shard.shard_id],
                "allowed_missing_rows": shard.item_count * failed_count,
            }
            for shard in logical_shards
        ],
    }


def _safe_task_id(model_id: str) -> str:
    return "model-" + "".join(
        character if character.isalnum() or character in "._-" else "_" for character in model_id
    )


def _frozen_config_payload(config: Any) -> dict[str, Any]:
    payload = config.model_dump(mode="json")
    if payload["mode"] in {"resume", "validate_only", "package_only"}:
        if (
            payload.get("schema_version") == "7.0"
            and payload.get("execution", {}).get("backend") == "mock"
        ):
            payload["mode"] = "fixture"
        elif payload.get("schema_version") == "7.0":
            payload["mode"] = {
                "S2": "pilot",
                "S3": "minimum_scientific",
                "S4": "full_common_panel",
                "S5": "robustness",
            }[payload["stage"]]
        else:
            payload["mode"] = "smoke"
    return payload


def _terminal(status: str, **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": "6.0",
        "status": status,
        **payload,
    }
