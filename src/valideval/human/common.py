from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from valideval.io.jsonl import read_jsonl_as
from valideval.schemas import AnnotationTask, HumanJudgment, JudgePrediction


def stable_json_hash(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def audit_human_dir(results_root: str | Path, benchmark_id: str, panel_id: str) -> Path:
    return Path(results_root) / benchmark_id / panel_id / "human"


def task_key(
    task_id: str | None,
    item_id: str,
    model_id: str | None = None,
) -> str:
    if task_id:
        return task_id
    return f"{item_id}::{model_id or 'item'}"


def bool_from_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def read_json(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        return {}
    return json.loads(source.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output


def load_annotation_tasks(output_dir: str | Path) -> list[AnnotationTask]:
    path = Path(output_dir) / "items.jsonl"
    if not path.exists():
        return []
    return read_jsonl_as(path, AnnotationTask)


def load_human_judgments(output_dir: str | Path) -> list[HumanJudgment]:
    path = Path(output_dir) / "human_judgments.jsonl"
    if not path.exists():
        return []
    return read_jsonl_as(path, HumanJudgment)


def load_judge_predictions(output_dir: str | Path) -> list[JudgePrediction]:
    path = Path(output_dir) / "judge_predictions.jsonl"
    if not path.exists():
        return []
    return read_jsonl_as(path, JudgePrediction)


def task_lookup(tasks: list[AnnotationTask]) -> dict[str, AnnotationTask]:
    return {task.task_id: task for task in tasks}


def tasks_by_item(tasks: list[AnnotationTask]) -> dict[str, list[AnnotationTask]]:
    grouped: dict[str, list[AnnotationTask]] = {}
    for task in tasks:
        grouped.setdefault(task.item_id, []).append(task)
    return grouped
