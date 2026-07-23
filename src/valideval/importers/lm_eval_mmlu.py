from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CHOICE_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TIMESTAMPED_SAMPLE_RE = re.compile(
    r"^samples_(?P<task>.+?)_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(?:\.\d+)?$"
)


def task_from_sample_filename(path: Path) -> str:
    name = path.stem
    match = TIMESTAMPED_SAMPLE_RE.match(name)
    if match:
        return match.group("task")
    if name.startswith("samples_"):
        return name.removeprefix("samples_")
    return name


def model_id_from_results(sample_file: Path) -> str | None:
    for results_file in sorted(sample_file.parent.glob("results_*.json"), reverse=True):
        try:
            payload = json.loads(results_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for value in (
            payload.get("model_name"),
            (payload.get("config") or {}).get("model_args", {}).get("pretrained")
            if isinstance(payload.get("config"), dict)
            else None,
        ):
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def extract_mmlu_prediction(record: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    value = first_present(record, ["filtered_resps", "resps", "prediction", "pred", "answer"])
    prediction, metadata = choice_from_lm_eval_responses(value)
    if prediction is not None:
        return prediction, metadata
    if value is None:
        return None, metadata
    return first_scalar(value), metadata


def extract_mmlu_gold(record: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    value = first_present(record, ["target", "gold", "correct_answer", "answer", "label"])
    if value is None and isinstance(record.get("doc"), dict):
        value = first_present(record["doc"], ["target", "gold", "answer", "answer_key", "label"])
    label, index = normalize_choice_label(value)
    metadata: dict[str, Any] = {}
    if index is not None:
        metadata["gold_index"] = index
    if label is not None:
        return label, metadata
    return first_scalar(value), metadata


def choice_from_lm_eval_responses(value: Any) -> tuple[str | None, dict[str, Any]]:
    metadata: dict[str, Any] = {}
    choices = unwrap_singleton(value)
    if isinstance(choices, list) and len(choices) > 1:
        scores = [first_float(choice) for choice in choices]
        if all(score is not None for score in scores):
            best_index = max(range(len(scores)), key=lambda index: scores[index] or float("-inf"))
            metadata["prediction_index"] = best_index
            metadata["choice_loglikelihoods"] = [
                float(score) for score in scores if score is not None
            ]
            return index_to_label(best_index), metadata
    label, index = normalize_choice_label(first_scalar(value))
    if index is not None:
        metadata["prediction_index"] = index
    return label, metadata


def normalize_choice_label(value: Any) -> tuple[str | None, int | None]:
    scalar = first_scalar(value)
    if scalar is None:
        return None, None
    text = str(scalar).strip()
    if not text:
        return None, None
    if text.isdigit():
        index = int(text)
        return index_to_label(index), index
    upper = text.upper()
    if len(upper) == 1 and upper in CHOICE_LABELS:
        return upper, CHOICE_LABELS.index(upper)
    return text, None


def index_to_label(index: int) -> str | None:
    if 0 <= index < len(CHOICE_LABELS):
        return CHOICE_LABELS[index]
    return None


def unwrap_singleton(value: Any) -> Any:
    current = value
    while isinstance(current, list) and len(current) == 1:
        current = current[0]
    return current


def first_present(record: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def first_scalar(value: Any) -> str | None:
    if isinstance(value, list | tuple):
        for item in value:
            nested = first_scalar(item)
            if nested not in (None, ""):
                return nested
        return None
    if isinstance(value, dict):
        return first_scalar(list(value.values()))
    if value not in (None, ""):
        return str(value)
    return None


def first_float(value: Any) -> float | None:
    scalar = first_scalar(value)
    if scalar is None:
        return None
    try:
        return float(scalar)
    except (TypeError, ValueError):
        return None
