from __future__ import annotations

import gc
import inspect
import json
import multiprocessing
import os
import queue
import re
import traceback
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from valideval.execution.errors import (
    OperationalFailureType,
    classify_operational_failure,
    retry_directive,
)
from valideval.execution.manifest import (
    EXECUTION_SCHEMA_VERSION,
    ConfigurationMismatchError,
    atomic_write_json,
    atomic_write_text,
    canonical_json_bytes,
    compute_configuration_hash,
    sha256_file,
)


class ShardError(RuntimeError):
    """Base error for deterministic shard execution and merging."""


class ShardConflictError(ShardError):
    """Raised when shard rows or task identities contradict one another."""


class IncompleteShardError(ShardError):
    """Raised when a supposedly complete run is missing a shard."""


def classify_worker_failure(error: BaseException) -> str:
    operational = classify_operational_failure(error)
    if operational in {
        OperationalFailureType.LOAD_OOM,
        OperationalFailureType.GENERATION_OOM,
    }:
        return "OOM"
    if operational in {
        OperationalFailureType.DOWNLOAD_FAILURE,
        OperationalFailureType.CUDA_FAILURE,
    } or type(error).__name__ in {"ModelResolutionError", "ModelLoadError"}:
        return "MODEL_LOAD_FAILURE"
    if operational is OperationalFailureType.DATASET_FAILURE:
        return "DATASET_FAILURE"
    if operational is OperationalFailureType.TIMEOUT:
        return "TIMEOUT"
    if operational is OperationalFailureType.PARSER_FAILURE:
        return "EXTRACTION_FAILURE"
    if operational is OperationalFailureType.SCORER_FAILURE:
        return "SCORING_FAILURE"
    if operational in {
        OperationalFailureType.CHECKSUM_FAILURE,
        OperationalFailureType.CONFIG_FAILURE,
        OperationalFailureType.SOURCE_MISMATCH,
    }:
        return operational.value
    return "GENERATION_FAILURE"


def worker_failure_is_retryable(error: BaseException, *, attempt: int) -> bool:
    directive = retry_directive(classify_operational_failure(error))
    return directive.retryable and attempt <= directive.maximum_retries


def apply_resource_fallback(
    task: Mapping[str, Any],
    *,
    failure_type: str,
    attempt: int,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Apply and record a bounded retry fallback without changing model identity.

    OOM recovery first halves ``batch_size`` and then ``max_sequence_length``.
    Dtype and quantization are never changed implicitly because those are
    controlled experimental conditions, not transparent engineering details.
    """

    updated = dict(task)
    if failure_type != "OOM" or not isinstance(task, Mapping):
        return updated, None
    batch_size = int(updated.get("batch_size", 1))
    sequence_length = int(updated.get("max_sequence_length", 0) or 0)
    fallback: dict[str, Any] = {
        "failure_type": failure_type,
        "attempt": attempt,
        "dtype": updated.get("dtype"),
        "quantization": updated.get("quantization"),
    }
    prior_actions = {
        str(row.get("action"))
        for row in updated.get("resource_fallbacks", [])
        if isinstance(row, Mapping)
    }
    if batch_size > 1 and bool(updated.get("allow_batch_size_fallback", True)):
        reduced = max(1, batch_size // 2)
        updated["batch_size"] = reduced
        fallback.update(
            {
                "action": "reduce_batch_size",
                "before": batch_size,
                "after": reduced,
            }
        )
        return updated, fallback
    minimum_sequence = int(updated.get("minimum_sequence_length", 1))
    sequence_allowed = bool(updated.get("allow_sequence_length_fallback", False))
    if (
        sequence_allowed
        and sequence_length > minimum_sequence
        and "reduce_sequence_length" not in prior_actions
    ):
        reduced = max(minimum_sequence, sequence_length // 2)
        updated["max_sequence_length"] = reduced
        fallback.update(
            {
                "action": "reduce_sequence_length",
                "before": sequence_length,
                "after": reduced,
            }
        )
        return updated, fallback
    fallback.update({"action": "no_safe_fallback_remaining", "before": None, "after": None})
    return updated, fallback


@dataclass(frozen=True, slots=True)
class ShardSpec:
    shard_id: str
    start: int
    stop: int
    item_ids: tuple[str, ...]

    @property
    def item_count(self) -> int:
        return len(self.item_ids)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["item_ids"] = list(self.item_ids)
        payload["item_count"] = self.item_count
        return payload


@dataclass(frozen=True, slots=True)
class WorkerAssignment:
    worker_id: str
    gpu_id: str
    task_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_ids"] = list(self.task_ids)
        return payload


def build_deterministic_shards(
    item_ids: Sequence[str],
    *,
    shard_count: int,
    prefix: str = "shard",
) -> list[ShardSpec]:
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    normalized = [str(item_id) for item_id in item_ids]
    if len(set(normalized)) != len(normalized):
        raise ShardConflictError("item_ids contain duplicates")
    if not normalized:
        raise ValueError("item_ids must not be empty")
    actual_count = min(shard_count, len(normalized))
    base, remainder = divmod(len(normalized), actual_count)
    shards: list[ShardSpec] = []
    start = 0
    width = max(3, len(str(actual_count - 1)))
    for index in range(actual_count):
        size = base + (1 if index < remainder else 0)
        stop = start + size
        shards.append(
            ShardSpec(
                shard_id=f"{prefix}-{index:0{width}d}",
                start=start,
                stop=stop,
                item_ids=tuple(normalized[start:stop]),
            )
        )
        start = stop
    return shards


def shard_definition_hash(shards: Iterable[ShardSpec | Mapping[str, Any]]) -> str:
    normalized = [
        shard.to_dict() if isinstance(shard, ShardSpec) else dict(shard) for shard in shards
    ]
    return compute_configuration_hash({"shards": normalized})


def assert_resume_compatible(
    existing_manifest: Mapping[str, Any],
    expected_config_hash: str,
) -> None:
    actual = str(existing_manifest.get("config_hash", ""))
    if actual != expected_config_hash:
        raise ConfigurationMismatchError(
            f"Refusing resume with config hash {actual!r}; expected {expected_config_hash!r}"
        )


def validate_shard_completeness(
    expected_shards: Iterable[str | Mapping[str, Any] | ShardSpec],
    statuses: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    expected = {_shard_id(item) for item in expected_shards}
    if isinstance(statuses, Mapping):
        status_items = statuses.get("shards", statuses)
        if isinstance(status_items, Mapping):
            records = [dict(value, shard_id=key) for key, value in status_items.items()]
        elif isinstance(status_items, list):
            records = status_items
        else:
            raise ShardError("shard statuses must be a list or mapping")
    else:
        records = [dict(status) for status in statuses]
    by_id: dict[str, Mapping[str, Any]] = {}
    for record in records:
        shard_id = str(record.get("shard_id", ""))
        if not shard_id:
            raise ShardError("shard status missing shard_id")
        if shard_id in by_id:
            raise ShardConflictError(f"duplicate shard status: {shard_id}")
        by_id[shard_id] = record
    stale = sorted(set(by_id).difference(expected))
    missing = sorted(expected.difference(by_id))
    incomplete = sorted(
        shard_id
        for shard_id in expected.intersection(by_id)
        if str(by_id[shard_id].get("status", "")).lower()
        not in {"success", "complete", "completed", "skipped_complete"}
    )
    return {
        "status": "pass" if not stale and not missing and not incomplete else "fail",
        "expected_shards": sorted(expected),
        "observed_shards": sorted(by_id),
        "missing_shards": missing,
        "stale_shards": stale,
        "incomplete_shards": incomplete,
    }


def plan_worker_assignments(
    tasks: Sequence[Mapping[str, Any]],
    *,
    gpu_ids: Sequence[str | int] | None = None,
) -> list[WorkerAssignment]:
    devices = [str(gpu) for gpu in (gpu_ids if gpu_ids is not None else _detect_gpu_ids())]
    if not devices:
        devices = ["cpu"]
    task_ids = [_task_id(task) for task in tasks]
    if len(set(task_ids)) != len(task_ids):
        raise ShardConflictError("scheduler task_id values must be unique")
    buckets: list[list[str]] = [[] for _ in devices]
    loads = [0.0 for _ in devices]
    weighted_tasks = sorted(
        (
            (
                -float(
                    task.get(
                        "estimated_duration",
                        task.get("estimated_download_size", task.get("estimated_weight", 1.0)),
                    )
                ),
                _task_id(task),
            )
            for task in tasks
        ),
        key=lambda value: (value[0], value[1]),
    )
    for negative_weight, task_id in weighted_tasks:
        worker_index = min(range(len(devices)), key=lambda index: (loads[index], index))
        buckets[worker_index].append(task_id)
        loads[worker_index] += -negative_weight
    return [
        WorkerAssignment(
            worker_id=f"worker-{index:02d}",
            gpu_id=device,
            task_ids=tuple(buckets[index]),
        )
        for index, device in enumerate(devices)
    ]


class T4x2Scheduler:
    """One-worker-per-device scheduler with deterministic resume semantics.

    Production callers can use subprocesses (the default). Tests and fixture
    notebooks may use ``use_processes=False`` while exercising the same device
    assignments, status ledger, retry, heartbeat, and deterministic merge logic.
    """

    def __init__(
        self,
        output_root: str | Path,
        *,
        gpu_ids: Sequence[str | int] | None = None,
        max_retries: int = 1,
        use_processes: bool = True,
        process_start_method: str = "spawn",
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be nonnegative")
        self.output_root = Path(output_root)
        self.gpu_ids = tuple(
            str(gpu) for gpu in (gpu_ids if gpu_ids is not None else _detect_gpu_ids())
        ) or ("cpu",)
        self.max_retries = max_retries
        self.use_processes = use_processes
        self.process_start_method = process_start_method

    @property
    def worker_count(self) -> int:
        return len(self.gpu_ids)

    def run(
        self,
        tasks: Sequence[Mapping[str, Any]],
        worker: Callable[[Mapping[str, Any], str], Mapping[str, Any]],
        *,
        config: Mapping[str, Any],
        resume: bool = True,
    ) -> dict[str, Any]:
        normalized_tasks = [dict(task) for task in tasks]
        assignments = plan_worker_assignments(normalized_tasks, gpu_ids=self.gpu_ids)
        task_by_id = {_task_id(task): task for task in normalized_tasks}
        scheduler_config = {
            "execution_config": dict(config),
            "gpu_ids": list(self.gpu_ids),
            "max_retries": self.max_retries,
            "task_ids": sorted(task_by_id),
        }
        config_hash = compute_configuration_hash(scheduler_config)
        self.output_root.mkdir(parents=True, exist_ok=True)
        manifest_path = self.output_root / "scheduler_manifest.json"
        previous = _read_optional_json(manifest_path)
        if previous:
            assert_resume_compatible(previous, config_hash)
            if not resume:
                raise ShardConflictError(
                    f"scheduler output already exists and resume is disabled: {self.output_root}"
                )

        completed = self._completed_results(assignments) if resume else {}
        pending_assignments: list[tuple[WorkerAssignment, list[dict[str, Any]]]] = []
        for assignment in assignments:
            pending = [
                task_by_id[task_id] for task_id in assignment.task_ids if task_id not in completed
            ]
            pending_assignments.append((assignment, pending))

        atomic_write_json(
            manifest_path,
            {
                "schema_version": EXECUTION_SCHEMA_VERSION,
                "status": "running",
                "config_hash": config_hash,
                "gpu_ids": list(self.gpu_ids),
                "worker_count": self.worker_count,
                "assignments": [assignment.to_dict() for assignment in assignments],
                "completed_before_resume": sorted(completed),
            },
        )

        new_results = (
            self._run_processes(pending_assignments, worker, config_hash)
            if self.use_processes
            else self._run_inline(pending_assignments, worker, config_hash)
        )
        results = {**completed, **new_results}
        ordered = [results[task_id] for task_id in sorted(results)]
        failures = [row for row in ordered if row.get("status") != "success"]
        payload = {
            "schema_version": EXECUTION_SCHEMA_VERSION,
            "status": "complete" if not failures else "complete_with_failures",
            "config_hash": config_hash,
            "gpu_ids": list(self.gpu_ids),
            "worker_count": self.worker_count,
            "assignments": [assignment.to_dict() for assignment in assignments],
            "results": ordered,
            "success_count": len(ordered) - len(failures),
            "failure_count": len(failures),
            "resumed_count": len(completed),
        }
        atomic_write_json(manifest_path, payload)
        return payload

    def _completed_results(
        self,
        assignments: Sequence[WorkerAssignment],
    ) -> dict[str, dict[str, Any]]:
        completed: dict[str, dict[str, Any]] = {}
        for assignment in assignments:
            status_dir = self.output_root / assignment.worker_id / "status"
            if not status_dir.exists():
                continue
            for path in sorted(status_dir.glob("*.json")):
                payload = _read_optional_json(path)
                if payload and payload.get("status") == "success":
                    completed[str(payload["task_id"])] = payload
        return completed

    def _run_inline(
        self,
        assignments: Sequence[tuple[WorkerAssignment, list[dict[str, Any]]]],
        worker: Callable[[Mapping[str, Any], str], Mapping[str, Any]],
        config_hash: str,
    ) -> dict[str, dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        for assignment, tasks in assignments:
            produced = _run_worker_tasks(
                assignment=assignment,
                tasks=tasks,
                worker=worker,
                worker_root=self.output_root / assignment.worker_id,
                config_hash=config_hash,
                max_retries=self.max_retries,
            )
            rows.update({str(row["task_id"]): row for row in produced})
        return rows

    def _run_processes(
        self,
        assignments: Sequence[tuple[WorkerAssignment, list[dict[str, Any]]]],
        worker: Callable[[Mapping[str, Any], str], Mapping[str, Any]],
        config_hash: str,
    ) -> dict[str, dict[str, Any]]:
        if inspect.isfunction(worker) and "<locals>" in worker.__qualname__:
            raise ShardError(
                "Process workers must be module-level callables; use_processes=False for mocks"
            )
        context = multiprocessing.get_context(self.process_start_method)
        result_queue = context.Queue()
        processes = []
        for assignment, tasks in assignments:
            if not tasks:
                continue
            process = cast(Any, context).Process(
                target=_process_worker_entry,
                args=(
                    assignment,
                    tasks,
                    worker,
                    self.output_root / assignment.worker_id,
                    config_hash,
                    self.max_retries,
                    result_queue,
                ),
                name=assignment.worker_id,
            )
            process.start()
            processes.append(process)
        expected = sum(len(tasks) for _, tasks in assignments)
        rows: dict[str, dict[str, Any]] = {}
        while len(rows) < expected:
            try:
                row = result_queue.get(timeout=1.0)
                rows[str(row["task_id"])] = row
            except queue.Empty:
                if processes and all(not process.is_alive() for process in processes):
                    break
        for process in processes:
            process.join()
            if process.exitcode != 0:
                raise ShardError(
                    f"Worker process {process.name} exited with code {process.exitcode}"
                )
        if len(rows) != expected:
            missing = sorted(
                _task_id(task)
                for _, tasks in assignments
                for task in tasks
                if _task_id(task) not in rows
            )
            raise ShardError(f"Worker pool ended without results for tasks: {missing}")
        return rows


def merge_jsonl_shards(
    shard_paths: Iterable[str | Path],
    output_path: str | Path,
    *,
    key_fields: Sequence[str] = (
        "study_id",
        "run_id",
        "benchmark_id",
        "task_id",
        "subtask_id",
        "model_id",
        "item_id",
        "seed",
        "prompt_template_id",
    ),
    allow_identical_duplicates: bool = True,
    expected_shards: Iterable[str] | None = None,
) -> dict[str, Any]:
    paths = sorted({Path(path) for path in shard_paths}, key=lambda path: path.as_posix())
    if not paths:
        raise IncompleteShardError("No shard files were supplied")
    by_key: dict[tuple[str, ...], tuple[bytes, dict[str, Any], Path, int]] = {}
    identical_duplicates = 0
    observed_shards: set[str] = set()
    item_hashes: dict[tuple[str, str], str] = {}
    for path in paths:
        if not path.is_file():
            raise IncompleteShardError(f"Shard output is missing: {path}")
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ShardError(f"Malformed JSONL at {path}:{line_number}: {exc}") from exc
                if not isinstance(row, dict):
                    raise ShardError(f"JSONL row is not an object at {path}:{line_number}")
                missing = [field for field in key_fields if field not in row]
                if missing:
                    raise ShardError(
                        f"Shard row missing merge keys at {path}:{line_number}: {missing}"
                    )
                key = tuple(str(row[field]) for field in key_fields)
                signature = canonical_json_bytes(row)
                if key in by_key:
                    prior_signature, _, prior_path, prior_line = by_key[key]
                    if signature != prior_signature:
                        raise ShardConflictError(
                            "Contradictory duplicate row for key "
                            f"{key}: {prior_path}:{prior_line} vs {path}:{line_number}"
                        )
                    identical_duplicates += 1
                    if not allow_identical_duplicates:
                        raise ShardConflictError(f"Duplicate model/item row for key {key}")
                    continue
                by_key[key] = (signature, row, path, line_number)
                shard_id = row.get("shard_id")
                if shard_id is not None:
                    observed_shards.add(str(shard_id))
                item_hash = row.get("item_hash")
                if item_hash:
                    collision_key = (str(row.get("benchmark_id", "")), str(row.get("item_id", "")))
                    previous = item_hashes.setdefault(collision_key, str(item_hash))
                    if previous != str(item_hash):
                        raise ShardConflictError(
                            f"Item ID collision with different hashes: {collision_key}"
                        )
    if expected_shards is not None:
        expected = {str(value) for value in expected_shards}
        missing_shards = sorted(expected.difference(observed_shards))
        stale_shards = sorted(observed_shards.difference(expected))
        if missing_shards or stale_shards:
            raise IncompleteShardError(
                f"Shard coverage mismatch; missing={missing_shards}, stale={stale_shards}"
            )
    ordered_rows = [entry[1] for _, entry in sorted(by_key.items())]
    content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in ordered_rows
    )
    target = atomic_write_text(output_path, content)
    return {
        "status": "pass",
        "output_path": str(target),
        "output_sha256": sha256_file(target),
        "row_count": len(ordered_rows),
        "identical_duplicates_removed": identical_duplicates,
        "observed_shards": sorted(observed_shards),
        "source_files": [str(path) for path in paths],
    }


def _run_worker_tasks(
    *,
    assignment: WorkerAssignment,
    tasks: Sequence[Mapping[str, Any]],
    worker: Callable[[Mapping[str, Any], str], Mapping[str, Any]],
    worker_root: Path,
    config_hash: str,
    max_retries: int,
) -> list[dict[str, Any]]:
    worker_root.mkdir(parents=True, exist_ok=True)
    status_dir = worker_root / "status"
    status_dir.mkdir(parents=True, exist_ok=True)
    if assignment.gpu_id != "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = assignment.gpu_id
    os.environ["VALIDEVAL_WORKER_ID"] = assignment.worker_id
    os.environ["VALIDEVAL_WORKER_HEARTBEAT_PATH"] = str(worker_root / "heartbeat.json")
    rows: list[dict[str, Any]] = []
    for task in tasks:
        task_id = _task_id(task)
        result: dict[str, Any] | None = None
        current_task = dict(task)
        fallbacks: list[dict[str, Any]] = []
        for attempt in range(1, max_retries + 2):
            current_task["attempt_id"] = attempt
            current_task["retry_count"] = attempt - 1
            started_at = datetime.now(timezone.utc).isoformat()
            atomic_write_json(
                worker_root / "heartbeat.json",
                {
                    "worker_id": assignment.worker_id,
                    "gpu_id": assignment.gpu_id,
                    "current_job": task_id,
                    "start_time": started_at,
                    "heartbeat": started_at,
                    "last_completed_item": None,
                    "attempt": attempt,
                    "retry_count": attempt - 1,
                    "memory_failure": False,
                    "exit_state": "running",
                    "config_hash": config_hash,
                },
            )
            try:
                output = worker(dict(current_task), assignment.gpu_id)
                if not isinstance(output, Mapping):
                    raise TypeError("worker must return a mapping")
                result = {
                    "task_id": task_id,
                    "worker_id": assignment.worker_id,
                    "gpu_id": assignment.gpu_id,
                    "status": "success",
                    "attempts": attempt,
                    "start_time": started_at,
                    "heartbeat": datetime.now(timezone.utc).isoformat(),
                    "last_completed_item": _last_completed_item(output),
                    "retry_count": attempt - 1,
                    "memory_failure": any(
                        fallback.get("failure_type") == "OOM" for fallback in fallbacks
                    ),
                    "exit_state": "complete",
                    "config_hash": config_hash,
                    "output": dict(output),
                    "fallbacks": fallbacks,
                }
                break
            except BaseException as exc:
                failure_type = classify_worker_failure(exc)
                if failure_type == "OOM":
                    _release_cuda_after_failure()
                current_task, fallback = apply_resource_fallback(
                    current_task,
                    failure_type=failure_type,
                    attempt=attempt,
                )
                if fallback is not None:
                    fallbacks.append(fallback)
                    current_task["resource_fallbacks"] = list(fallbacks)
                result = {
                    "task_id": task_id,
                    "worker_id": assignment.worker_id,
                    "gpu_id": assignment.gpu_id,
                    "status": "failed",
                    "attempts": attempt,
                    "start_time": started_at,
                    "heartbeat": datetime.now(timezone.utc).isoformat(),
                    "last_completed_item": None,
                    "retry_count": attempt - 1,
                    "memory_failure": failure_type == "OOM",
                    "exit_state": "failed",
                    "config_hash": config_hash,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                    "failure_type": failure_type,
                    "fallbacks": fallbacks,
                }
                if not worker_failure_is_retryable(exc, attempt=attempt):
                    break
        if result is None:
            raise AssertionError("unreachable scheduler result state")
        atomic_write_json(status_dir / f"{_safe_filename(task_id)}.json", result)
        rows.append(result)
    atomic_write_json(
        worker_root / "heartbeat.json",
        {
            "worker_id": assignment.worker_id,
            "gpu_id": assignment.gpu_id,
            "current_job": None,
            "heartbeat": datetime.now(timezone.utc).isoformat(),
            "last_completed_item": _latest_completed_item(rows),
            "retry_count": 0,
            "memory_failure": any(row.get("memory_failure") for row in rows),
            "exit_state": "idle",
            "config_hash": config_hash,
        },
    )
    return rows


def _release_cuda_after_failure() -> None:
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def _process_worker_entry(
    assignment: WorkerAssignment,
    tasks: Sequence[Mapping[str, Any]],
    worker: Callable[[Mapping[str, Any], str], Mapping[str, Any]],
    worker_root: Path,
    config_hash: str,
    max_retries: int,
    result_queue: Any,
) -> None:
    for row in _run_worker_tasks(
        assignment=assignment,
        tasks=tasks,
        worker=worker,
        worker_root=worker_root,
        config_hash=config_hash,
        max_retries=max_retries,
    ):
        result_queue.put(row)


def _detect_gpu_ids() -> list[str]:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    if visible and visible != "-1":
        return [part.strip() for part in visible.split(",") if part.strip()]
    return ["0", "1"] if os.environ.get("VALIDEVAL_ASSUME_T4X2") == "1" else ["cpu"]


def _task_id(task: Mapping[str, Any]) -> str:
    value = task.get("task_id") or task.get("shard_id")
    if value is None or not str(value):
        raise ShardError("scheduler task requires task_id or shard_id")
    return str(value)


def _shard_id(item: str | Mapping[str, Any] | ShardSpec) -> str:
    if isinstance(item, ShardSpec):
        return item.shard_id
    if isinstance(item, str):
        return item
    value = item.get("shard_id")
    if value is None:
        raise ShardError("shard entry is missing shard_id")
    return str(value)


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    if not cleaned:
        raise ShardError(f"task_id cannot be converted to a safe filename: {value!r}")
    return cleaned[:200]


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ShardError(f"Invalid scheduler JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ShardError(f"Scheduler JSON must contain an object: {path}")
    return payload


def heartbeat_is_stale(
    heartbeat: Mapping[str, Any],
    *,
    now: datetime | None = None,
    stale_after_seconds: float = 300.0,
) -> bool:
    if stale_after_seconds <= 0:
        raise ValueError("stale_after_seconds must be positive")
    value = heartbeat.get("heartbeat")
    if not isinstance(value, str):
        return True
    try:
        observed = datetime.fromisoformat(value)
    except ValueError:
        return True
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return (current - observed).total_seconds() > stale_after_seconds


def _last_completed_item(output: Mapping[str, Any]) -> str | None:
    rows = output.get("rows")
    if not isinstance(rows, list) or not rows:
        return None
    final = rows[-1]
    return (
        str(final.get("item_id")) if isinstance(final, Mapping) and final.get("item_id") else None
    )


def _latest_completed_item(rows: Sequence[Mapping[str, Any]]) -> str | None:
    for row in reversed(rows):
        output = row.get("output")
        if isinstance(output, Mapping):
            item_id = _last_completed_item(output)
            if item_id is not None:
                return item_id
    return None
