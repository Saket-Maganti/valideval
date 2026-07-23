from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from valideval.io.jsonl import write_jsonl
from valideval.schemas import ModelPrediction

SUPPORTED_IMPORTERS = [
    "generic-jsonl",
    "generic-csv",
    "lm-evaluation-harness",
    "helm",
    "huggingface",
    "openai-evals",
    "inspect-ai",
    "opencompass",
    "lighteval",
    "ragas",
    "deepeval",
]

FIELD_ALIASES = {
    "model_id": [
        "model_id",
        "model",
        "model_name",
        "system",
        "generator",
        "eval_model",
        "run_name",
    ],
    "item_id": [
        "item_id",
        "doc_id",
        "sample_id",
        "example_id",
        "task_id",
        "input_id",
        "id",
    ],
    "prediction": [
        "prediction",
        "pred",
        "output",
        "completion",
        "filtered_resps",
        "response",
        "answer",
        "model_output",
        "generation",
    ],
    "score": [
        "score",
        "acc",
        "accuracy",
        "exact_match",
        "is_correct",
        "correct",
        "metric",
    ],
    "raw_output": [
        "raw_output",
        "raw",
        "full_output",
        "completion",
        "output",
        "response",
        "generation",
    ],
    "prompt_variant": ["prompt_variant", "variant", "prompt_name", "split"],
}


def import_outputs(
    path: str | Path,
    *,
    adapter: str = "generic-jsonl",
    output_path: str | Path | None = None,
    benchmark_id: str = "imported",
    prompt_variant: str = "full",
    require_scores: bool = True,
) -> dict[str, Any]:
    records = load_external_rows(path, adapter=adapter)
    predictions = normalize_prediction_records(
        records,
        benchmark_id=benchmark_id,
        prompt_variant=prompt_variant,
        require_scores=require_scores,
    )
    payload = {
        "adapter": _normalize_adapter(adapter),
        "source_path": str(path),
        "benchmark_id": benchmark_id,
        "n_predictions": len(predictions),
        "warnings": [
            "Imported outputs are treated as local artifacts; ValidEval does not verify external framework scoring semantics."
        ],
    }
    if output_path is not None:
        write_jsonl(output_path, predictions)
        payload["output_path"] = str(output_path)
    return payload


def load_external_rows(path: str | Path, *, adapter: str = "generic-jsonl") -> list[dict[str, Any]]:
    normalized = _normalize_adapter(adapter)
    if normalized not in SUPPORTED_IMPORTERS:
        raise ValueError(
            f"Unsupported importer: {adapter}. Available adapters: {', '.join(SUPPORTED_IMPORTERS)}"
        )
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Importer input does not exist: {input_path}")
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        with input_path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix == ".jsonl":
        return [
            json.loads(line)
            for line in input_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    return _records_from_payload(payload)


def normalize_prediction_records(
    records: list[dict[str, Any]],
    *,
    benchmark_id: str = "imported",
    prompt_variant: str = "full",
    require_scores: bool = True,
) -> list[ModelPrediction]:
    predictions: list[ModelPrediction] = []
    missing_scores: list[str] = []
    for index, record in enumerate(records):
        model_id = str(
            _field(record, "model_id") or record.get("metadata", {}).get("model") or "model"
        )
        item_id = str(_field(record, "item_id") or f"item_{index + 1}")
        prediction = _stringify_prediction(_field(record, "prediction") or "")
        raw_output = _stringify_prediction(_field(record, "raw_output") or prediction)
        score_value = _field(record, "score")
        if score_value is None or score_value == "":
            missing_scores.append(item_id)
            if require_scores:
                continue
            score = 0.0
            is_correct = None
        else:
            score = _score_float(score_value)
            is_correct = bool(score >= 1.0) if score in {0.0, 1.0} else None
        metadata = {
            "source_benchmark_id": benchmark_id,
            "importer_record": {
                key: value
                for key, value in record.items()
                if key not in {"prompt", "context", "choices"}
            },
        }
        if score_value is None or score_value == "":
            metadata["score_status"] = "unscored_external_output"
        predictions.append(
            ModelPrediction(
                model_id=model_id,
                item_id=item_id,
                prompt_variant=str(_field(record, "prompt_variant") or prompt_variant),
                prediction=prediction,
                score=score,
                is_correct=is_correct,
                raw_output=raw_output,
                metadata=metadata,
            )
        )
    if missing_scores and require_scores:
        preview = ", ".join(missing_scores[:5])
        raise ValueError(
            "Imported outputs are missing score fields. "
            f"Missing scores for {len(missing_scores)} records, including: {preview}."
        )
    return predictions


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    if isinstance(payload, dict):
        for key in ("predictions", "outputs", "samples", "records", "results", "logs"):
            value = payload.get(key)
            if isinstance(value, list):
                return [record for record in value if isinstance(record, dict)]
        return [payload]
    raise ValueError("Importer input must contain a JSON object, array, JSONL, or CSV table.")


def _field(record: dict[str, Any], canonical: str) -> Any:
    for key in FIELD_ALIASES[canonical]:
        if key in record:
            value = record[key]
            if canonical == "prediction" and isinstance(value, list) and value:
                return value[0]
            if isinstance(value, dict) and canonical == "score":
                for nested in ("score", "acc", "exact_match", "value"):
                    if nested in value:
                        return value[nested]
            return value
    nested = record.get("metadata")
    if isinstance(nested, dict):
        for key in FIELD_ALIASES[canonical]:
            if key in nested:
                return nested[key]
    return None


def _score_float(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, int | float):
        return float(value)
    text = str(value).strip().lower()
    if text in {"true", "correct", "yes"}:
        return 1.0
    if text in {"false", "incorrect", "no"}:
        return 0.0
    return float(text)


def _stringify_prediction(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, list):
        return _stringify_prediction(value[0]) if value else ""
    return json.dumps(value, sort_keys=True) if isinstance(value, dict) else str(value)


def _normalize_adapter(adapter: str) -> str:
    return str(adapter).strip().lower().replace("_", "-")
