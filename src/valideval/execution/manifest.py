from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

EXECUTION_SCHEMA_VERSION = "valideval.execution.v7.1"
ACCEPTED_V5_SCHEMA_VERSIONS = frozenset(
    {
        EXECUTION_SCHEMA_VERSION,
        "valideval.execution.v6",
        "valideval.execution.v5",
        "v7.1",
        "7.1",
        "v6",
        "6",
        "v5",
        "5",
    }
)
NON_EVIDENCE_FIXTURE = "NON_EVIDENCE_FIXTURE"

RUN_REQUIRED_FILES = (
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

PREDICTION_REQUIRED_FIELDS = (
    "schema_version",
    "study_id",
    "run_id",
    "benchmark_id",
    "benchmark_version",
    "task_id",
    "subtask_id",
    "split",
    "item_id",
    "item_hash",
    "model_id",
    "model_revision",
    "model_family",
    "prompt_template_id",
    "few_shot_id",
    "chat_template_id",
    "generation_config_id",
    "scoring_version",
    "extraction_version",
    "seed",
    "shard_id",
    "attempt_id",
    "raw_output",
    "parsed_output",
    "gold_output",
    "is_correct",
    "extraction_status",
    "generation_status",
    "failure_type",
    "latency_seconds",
    "input_tokens",
    "output_tokens",
    "device",
    "dtype",
    "quantization",
    "code_revision",
    "environment_hash",
    "created_at",
)

FAILURE_TYPES = frozenset(
    {
        "SUCCESS",
        "MODEL_LOAD_FAILURE",
        "OOM",
        "TIMEOUT",
        "GENERATION_FAILURE",
        "EMPTY_OUTPUT",
        "TRUNCATED_OUTPUT",
        "EXTRACTION_FAILURE",
        "INVALID_FORMAT",
        "SCORING_FAILURE",
        "DATASET_FAILURE",
        "UNKNOWN_FAILURE",
    }
)

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:@+\-]{0,255}$")


class ManifestValidationError(ValueError):
    """Raised when an execution manifest violates the V5 contract."""


class ConfigurationMismatchError(ManifestValidationError):
    """Raised when a resume/import configuration hash does not match."""


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON-compatible input deterministically for hashing."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def compute_configuration_hash(config: Mapping[str, Any]) -> str:
    """Hash the complete immutable execution configuration.

    Callers should include model and benchmark revisions, prompts, generation,
    scoring, extraction, shard definitions, and the code revision. The function
    intentionally hashes every supplied field so adding a condition invalidates
    stale checkpoints instead of silently resuming them.
    """

    return sha256_bytes(canonical_json_bytes(dict(config)))


compute_config_hash = compute_configuration_hash


def load_config_snapshot(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ManifestValidationError(f"Configuration snapshot must be a mapping: {path}")
    return payload


def build_file_checksums(
    root: str | Path,
    relative_paths: Iterable[str | Path],
) -> dict[str, str]:
    base = Path(root).resolve()
    checksums: dict[str, str] = {}
    for relative in sorted({Path(item).as_posix() for item in relative_paths}):
        candidate = (base / relative).resolve()
        if not candidate.is_relative_to(base):
            raise ManifestValidationError(f"Checksum path leaves run root: {relative}")
        if not candidate.is_file():
            raise ManifestValidationError(f"Checksum target is missing or not a file: {relative}")
        checksums[relative] = sha256_file(candidate)
    return checksums


def validate_file_checksums(
    root: str | Path,
    checksums: Mapping[str, str],
    *,
    require_nonempty: bool = True,
) -> dict[str, str]:
    if require_nonempty and not checksums:
        raise ManifestValidationError("file_checksums must not be empty")
    base = Path(root).resolve()
    verified: dict[str, str] = {}
    seen_casefold: set[str] = set()
    for name, expected in sorted(checksums.items()):
        if not isinstance(name, str) or not name:
            raise ManifestValidationError("file_checksums contains an invalid path")
        normalized = Path(name).as_posix()
        folded = normalized.casefold()
        if folded in seen_casefold:
            raise ManifestValidationError(f"Case-colliding checksum paths: {name}")
        seen_casefold.add(folded)
        target = (base / normalized).resolve()
        if not target.is_relative_to(base):
            raise ManifestValidationError(f"Checksum path leaves run root: {name}")
        if not target.is_file():
            raise ManifestValidationError(f"Checksummed file is missing: {name}")
        if not isinstance(expected, str) or not _HEX_64.fullmatch(expected.lower()):
            raise ManifestValidationError(f"Invalid SHA-256 for {name}")
        actual = sha256_file(target)
        if actual != expected.lower():
            raise ManifestValidationError(
                f"Checksum mismatch for {name}: expected {expected.lower()}, got {actual}"
            )
        verified[normalized] = actual
    return verified


def normalize_checksum_payload(payload: Any) -> dict[str, str]:
    """Accept the canonical {files: {...}} form and a legacy flat mapping."""

    if not isinstance(payload, dict):
        raise ManifestValidationError("file_checksums.json must contain a JSON object")
    candidate = payload.get("files", payload)
    if not isinstance(candidate, dict):
        raise ManifestValidationError("file_checksums.json files must be a mapping")
    return {str(key): str(value).lower() for key, value in candidate.items()}


def build_run_manifest(
    *,
    study_id: str,
    run_id: str,
    benchmark_id: str,
    benchmark_version: str,
    config: Mapping[str, Any],
    models: Iterable[Mapping[str, Any] | str],
    shards: Iterable[Mapping[str, Any] | str],
    item_count: int,
    expected_prediction_rows: int,
    completion_state: str = "complete",
    failure_state: str = "none",
    evidence_state: str = "RESULT_REQUIRED",
    config_class: str = "confirmatory_common_panel_v5",
    file_checksums: Mapping[str, str] | None = None,
    code_revision: str | None = None,
    created_at: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "study_id": study_id,
        "run_id": run_id,
        "benchmark_id": benchmark_id,
        "benchmark_version": benchmark_version,
        "config_hash": compute_configuration_hash(config),
        "config_class": config_class,
        "models": [
            dict(model) if isinstance(model, Mapping) else {"model_id": model} for model in models
        ],
        "shards": [
            dict(shard) if isinstance(shard, Mapping) else {"shard_id": shard} for shard in shards
        ],
        "item_count": int(item_count),
        "expected_prediction_rows": int(expected_prediction_rows),
        "completion_state": completion_state,
        "failure_state": failure_state,
        "evidence_state": evidence_state,
        "file_checksums": dict(file_checksums or {}),
        "code_revision": code_revision or str(config.get("code_revision", "UNKNOWN")),
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        overlap = set(manifest).intersection(extra)
        if overlap:
            raise ManifestValidationError(
                f"extra manifest fields would overwrite canonical keys: {sorted(overlap)}"
            )
        manifest.update(dict(extra))
    validate_run_manifest(manifest)
    return manifest


def validate_run_manifest(
    manifest: Mapping[str, Any],
    *,
    expected_study_id: str | None = None,
    expected_run_id: str | None = None,
    expected_benchmark_id: str | None = None,
    expected_config_hash: str | None = None,
    require_complete: bool = True,
) -> dict[str, Any]:
    required = {
        "schema_version",
        "study_id",
        "run_id",
        "benchmark_id",
        "benchmark_version",
        "config_hash",
        "config_class",
        "models",
        "shards",
        "item_count",
        "expected_prediction_rows",
        "completion_state",
        "failure_state",
        "evidence_state",
        "file_checksums",
    }
    missing = sorted(required.difference(manifest))
    if missing:
        raise ManifestValidationError(f"Run manifest missing fields: {', '.join(missing)}")
    if str(manifest["schema_version"]) not in ACCEPTED_V5_SCHEMA_VERSIONS:
        raise ManifestValidationError(
            f"Unsupported execution schema_version: {manifest['schema_version']!r}"
        )

    for key in ("study_id", "run_id", "benchmark_id", "benchmark_version", "config_class"):
        _validate_identifier(key, manifest[key])
    config_hash = str(manifest["config_hash"]).lower()
    if not _HEX_64.fullmatch(config_hash):
        raise ManifestValidationError("config_hash must be a lowercase SHA-256 hex digest")
    if expected_config_hash is not None and config_hash != expected_config_hash.lower():
        raise ConfigurationMismatchError(
            f"Configuration hash mismatch: expected {expected_config_hash}, got {config_hash}"
        )

    comparisons = {
        "study_id": expected_study_id,
        "run_id": expected_run_id,
        "benchmark_id": expected_benchmark_id,
    }
    for key, expected in comparisons.items():
        if expected is not None and str(manifest[key]) != expected:
            raise ManifestValidationError(
                f"Manifest {key} mismatch: expected {expected!r}, got {manifest[key]!r}"
            )

    models = _normalize_id_objects(manifest["models"], "model_id", "models")
    shards = _normalize_id_objects(manifest["shards"], "shard_id", "shards")
    if not models:
        raise ManifestValidationError("Run manifest must declare at least one model")
    if not shards:
        raise ManifestValidationError("Run manifest must declare at least one shard")
    for key in ("item_count", "expected_prediction_rows"):
        value = manifest[key]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ManifestValidationError(f"{key} must be a positive integer")
    completion_state = str(manifest["completion_state"]).lower()
    allowed_completion = {"complete", "completed", "complete_with_declared_failures"}
    if require_complete and completion_state not in allowed_completion:
        raise ManifestValidationError(f"Run is not complete: {manifest['completion_state']!r}")
    if str(manifest["evidence_state"]) == NON_EVIDENCE_FIXTURE:
        mode = str(manifest.get("execution_mode", manifest.get("mode", "fixture"))).lower()
        mocked_production_path = (
            manifest.get("execution_backend") == "mock"
            and manifest.get("mocked_production_path") is True
        )
        if mode != "fixture" and not mocked_production_path:
            raise ManifestValidationError(
                "NON_EVIDENCE_FIXTURE manifests must use fixture mode or explicitly declare "
                "the mocked production path"
            )
    source_hash = manifest.get("source_zip_sha256")
    if source_hash not in (None, "") and not _HEX_64.fullmatch(str(source_hash).lower()):
        raise ManifestValidationError("source_zip_sha256 must be a SHA-256 hex digest")
    normalized = dict(manifest)
    normalized["schema_version"] = EXECUTION_SCHEMA_VERSION
    normalized["config_hash"] = config_hash
    normalized["models"] = models
    normalized["shards"] = shards
    normalized["file_checksums"] = normalize_checksum_payload(manifest["file_checksums"])
    return normalized


def validate_prediction_record(
    record: Mapping[str, Any],
    *,
    require_full_schema: bool = True,
) -> dict[str, Any]:
    if require_full_schema:
        missing = [
            key for key in PREDICTION_REQUIRED_FIELDS if key not in record or record[key] is None
        ]
        if missing:
            raise ManifestValidationError(
                f"Prediction row missing required fields: {', '.join(missing)}"
            )
    schema_version = str(record.get("schema_version", ""))
    if schema_version not in ACCEPTED_V5_SCHEMA_VERSIONS:
        raise ManifestValidationError(
            f"Prediction row has unsupported schema_version: {schema_version!r}"
        )
    failure_type = str(record.get("failure_type", "UNKNOWN_FAILURE"))
    if failure_type not in FAILURE_TYPES:
        raise ManifestValidationError(f"Unknown failure_type: {failure_type!r}")
    is_correct = record.get("is_correct")
    if is_correct is not None and not isinstance(is_correct, bool):
        raise ManifestValidationError("is_correct must be boolean or null")
    if failure_type != "SUCCESS" and is_correct is True:
        raise ManifestValidationError("Failed generations cannot be marked correct")
    generation_status = str(record.get("generation_status", "")).lower()
    extraction_status = str(record.get("extraction_status", "")).lower()
    success_values = {"success", "pass", "ok"}
    if failure_type == "SUCCESS" and (
        generation_status not in success_values or extraction_status not in success_values
    ):
        raise ManifestValidationError(
            "SUCCESS rows must declare successful generation and extraction statuses"
        )
    if failure_type == "EXTRACTION_FAILURE" and extraction_status in success_values:
        raise ManifestValidationError(
            "EXTRACTION_FAILURE rows cannot declare successful extraction"
        )
    for key in ("study_id", "run_id", "benchmark_id", "item_id", "model_id", "shard_id"):
        if key in record:
            _validate_identifier(key, record[key])
    item_hash = record.get("item_hash")
    if item_hash not in (None, "") and not _HEX_64.fullmatch(str(item_hash).lower()):
        raise ManifestValidationError("item_hash must be a SHA-256 hex digest")
    return dict(record)


def read_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestValidationError(f"Invalid JSON at {path}: {exc}") from exc


def atomic_write_json(path: str | Path, payload: Any) -> Path:
    target = Path(path)
    return atomic_write_text(
        target,
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
    )


def atomic_write_text(path: str | Path, content: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return target


def _validate_identifier(name: str, value: Any) -> None:
    if not isinstance(value, str) or not _SAFE_IDENTIFIER.fullmatch(value):
        raise ManifestValidationError(f"{name} is not a safe non-empty identifier: {value!r}")


def _normalize_id_objects(value: Any, key: str, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ManifestValidationError(f"{label} must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if isinstance(item, str):
            record = {key: item}
        elif isinstance(item, Mapping):
            record = dict(item)
        else:
            raise ManifestValidationError(f"{label} entries must be strings or objects")
        identifier = record.get(key)
        _validate_identifier(key, identifier)
        identifier = str(identifier)
        if identifier in seen:
            raise ManifestValidationError(f"Duplicate {key} in {label}: {identifier}")
        seen.add(identifier)
        normalized.append(record)
    return normalized
