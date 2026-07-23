from __future__ import annotations

import json
from pathlib import Path

import pytest

from valideval.execution.manifest import ConfigurationMismatchError
from valideval.execution.shards import (
    ShardConflictError,
    T4x2Scheduler,
    merge_jsonl_shards,
    plan_worker_assignments,
)


def _worker(task, gpu_id):
    return {"value": task["value"], "gpu_id": gpu_id}


def _oom_until_batch_one(task, gpu_id):
    if task["batch_size"] > 1:
        raise MemoryError("CUDA out of memory")
    return {"batch_size": task["batch_size"], "gpu_id": gpu_id}


def test_two_gpu_assignment_resume_and_config_refusal(tmp_path: Path) -> None:
    tasks = [{"task_id": f"task-{index}", "value": index} for index in range(4)]
    assignments = plan_worker_assignments(tasks, gpu_ids=["0", "1"])
    assert [assignment.task_ids for assignment in assignments] == [
        ("task-0", "task-2"),
        ("task-1", "task-3"),
    ]
    scheduler = T4x2Scheduler(tmp_path, gpu_ids=["0", "1"], use_processes=False)
    first = scheduler.run(tasks, _worker, config={"revision": "v1"})
    second = scheduler.run(tasks, _worker, config={"revision": "v1"})
    assert first["success_count"] == 4
    assert second["resumed_count"] == 4
    assert (tmp_path / "worker-00" / "heartbeat.json").exists()
    with pytest.raises(ConfigurationMismatchError):
        scheduler.run(tasks, _worker, config={"revision": "changed"})


def test_process_worker_per_gpu_path_uses_isolated_directories(tmp_path: Path) -> None:
    tasks = [{"task_id": "task-0", "value": 0}, {"task_id": "task-1", "value": 1}]
    scheduler = T4x2Scheduler(
        tmp_path,
        gpu_ids=["0", "1"],
        use_processes=True,
    )
    result = scheduler.run(tasks, _worker, config={"revision": "process-v1"})
    assert result["success_count"] == 2
    assert (tmp_path / "worker-00" / "status" / "task-0.json").exists()
    assert (tmp_path / "worker-01" / "status" / "task-1.json").exists()


def test_oom_fallback_is_bounded_recorded_and_preserves_conditions(tmp_path: Path) -> None:
    scheduler = T4x2Scheduler(
        tmp_path,
        gpu_ids=["0"],
        max_retries=1,
        use_processes=False,
    )
    result = scheduler.run(
        [
            {
                "task_id": "oom-task",
                "batch_size": 2,
                "max_sequence_length": 512,
                "dtype": "float16",
                "quantization": "none",
            }
        ],
        _oom_until_batch_one,
        config={"revision": "oom-v1"},
    )
    row = result["results"][0]
    assert row["status"] == "success"
    assert row["output"]["batch_size"] == 1
    assert row["fallbacks"] == [
        {
            "failure_type": "OOM",
            "attempt": 1,
            "dtype": "float16",
            "quantization": "none",
            "action": "reduce_batch_size",
            "before": 2,
            "after": 1,
        }
    ]


def test_merge_is_deterministic_and_rejects_contradictions(tmp_path: Path) -> None:
    base = {
        "study_id": "study",
        "run_id": "run",
        "benchmark_id": "mmlu",
        "task_id": "task",
        "subtask_id": "default",
        "model_id": "model",
        "item_id": "item",
        "seed": 0,
        "prompt_template_id": "prompt",
        "shard_id": "shard-000",
        "item_hash": "a" * 64,
        "is_correct": True,
    }
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    first.write_text(json.dumps(base) + "\n", encoding="utf-8")
    second.write_text(json.dumps(base) + "\n", encoding="utf-8")
    summary = merge_jsonl_shards([second, first], tmp_path / "merged.jsonl")
    assert summary["row_count"] == 1
    assert summary["identical_duplicates_removed"] == 1

    changed = {**base, "is_correct": False}
    second.write_text(json.dumps(changed) + "\n", encoding="utf-8")
    with pytest.raises(ShardConflictError, match="Contradictory"):
        merge_jsonl_shards([first, second], tmp_path / "conflict.jsonl")
