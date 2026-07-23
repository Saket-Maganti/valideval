from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from valideval.repair.engine import VALIDITY_CARD_SCHEMA
from valideval.schemas import (
    BenchmarkItem,
    DiagnosticResult,
    ModelOutput,
    ModelPrediction,
    ResponseMatrix,
)

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "benchmark": BenchmarkItem,
    "prediction": ModelPrediction,
    "model_output": ModelOutput,
    "response_matrix": ResponseMatrix,
    "diagnostic_result": DiagnosticResult,
}

CERTIFICATE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ValidEval Validity Evidence Profile",
    "type": "object",
    "required": [
        "schema_version",
        "created_at",
        "benchmark_id",
        "panel_id",
        "profile_level",
        "dimension_statuses",
        "interpretation",
    ],
    "properties": {
        "schema_version": {"type": "string"},
        "created_at": {"type": "string"},
        "benchmark_id": {"type": "string"},
        "panel_id": {"type": "string"},
        "profile_level": {"type": "string"},
        "audit_completeness_profile": {"type": "string"},
        "ordinal_levels_disabled": {"type": "boolean"},
        "profile_definitions": {"type": "object"},
        "dimension_statuses": {"type": "object"},
        "interpretation": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
}

AUDIT_MANIFEST_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ValidEval Audit Manifest",
    "type": "object",
    "required": [
        "schema_version",
        "created_at",
        "dataset_id",
        "item_count",
        "split_counts",
        "item_ids_hash",
        "item_text_hash",
        "benchmark_config_hash",
        "scorer_hash",
        "prompt_template_hash",
        "diagnostic_config_hash",
        "limitations",
    ],
    "properties": {
        "schema_version": {"type": "string"},
        "created_at": {"type": "string"},
        "dataset_id": {"type": "string"},
        "item_count": {"type": "integer"},
        "split_counts": {"type": "object"},
        "item_ids_hash": {"type": "string"},
        "item_text_hash": {"type": "string"},
        "benchmark_config_hash": {"type": "string"},
        "scorer_hash": {"type": "string"},
        "prompt_template_hash": {"type": "string"},
        "diagnostic_config_hash": {"type": "string"},
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
}

STATIC_SCHEMAS: dict[str, dict[str, Any]] = {
    "validity_card": VALIDITY_CARD_SCHEMA,
    "certificate": CERTIFICATE_SCHEMA,
    "audit_manifest": AUDIT_MANIFEST_SCHEMA,
}


def schema_names() -> list[str]:
    return sorted([*SCHEMA_MODELS, *STATIC_SCHEMAS])


def schema_payload(schema_name: str) -> dict[str, Any]:
    normalized = _normalize_schema_name(schema_name)
    if normalized in SCHEMA_MODELS:
        payload = SCHEMA_MODELS[normalized].model_json_schema()
        payload.setdefault("$schema", "https://json-schema.org/draft/2020-12/schema")
        return payload
    if normalized in STATIC_SCHEMAS:
        return STATIC_SCHEMAS[normalized]
    raise KeyError(f"Unknown schema: {schema_name}. Available schemas: {', '.join(schema_names())}")


def export_schema(schema_name: str, output_dir: str | Path) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    names = schema_names() if schema_name == "all" else [_normalize_schema_name(schema_name)]
    written: dict[str, str] = {}
    for name in names:
        path = output / f"{name}.schema.json"
        path.write_text(
            json.dumps(schema_payload(name), indent=2, sort_keys=True), encoding="utf-8"
        )
        written[name] = str(path)
    return written


def validate_payload(schema_name: str, path: str | Path) -> dict[str, Any]:
    normalized = _normalize_schema_name(schema_name)
    records = _load_records(Path(path))
    errors: list[dict[str, Any]] = []
    if normalized in SCHEMA_MODELS:
        model = SCHEMA_MODELS[normalized]
        for index, record in enumerate(records):
            try:
                model.model_validate(record)
            except ValidationError as exc:
                errors.append({"record_index": index, "errors": exc.errors()})
    elif normalized in STATIC_SCHEMAS:
        schema = STATIC_SCHEMAS[normalized]
        required = schema.get("required", [])
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(
                    {"record_index": index, "errors": ["Expected a JSON object for this schema."]}
                )
                continue
            missing = [field for field in required if field not in record]
            if missing:
                errors.append({"record_index": index, "missing_required": missing})
    else:
        raise KeyError(
            f"Unknown schema: {schema_name}. Available schemas: {', '.join(schema_names())}"
        )
    return {
        "schema": normalized,
        "path": str(path),
        "valid": not errors,
        "n_records": len(records),
        "errors": errors,
    }


def _load_records(path: Path) -> list[Any]:
    if not path.exists():
        raise FileNotFoundError(f"Schema validation input does not exist: {path}")
    if path.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return [payload]


def _normalize_schema_name(name: str) -> str:
    normalized = str(name).strip().replace("-", "_")
    if not normalized:
        raise ValueError("Schema name cannot be empty.")
    return normalized
