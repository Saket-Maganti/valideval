from __future__ import annotations

import csv
import io
import json
import os
import shutil
import stat
import tempfile
import zipfile
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import pandas as pd
import yaml

from valideval.execution.manifest import (
    NON_EVIDENCE_FIXTURE,
    RUN_REQUIRED_FILES,
    ManifestValidationError,
    atomic_write_json,
    atomic_write_text,
    canonical_json_bytes,
    compute_configuration_hash,
    normalize_checksum_payload,
    sha256_file,
    validate_prediction_record,
    validate_run_manifest,
)
from valideval.execution.shards import validate_shard_completeness

IMPORTER_SCHEMA_VERSION = "valideval.kaggle_import.v5"
IMPORTER_READY_VERDICT = "IMPORTER_V5_ADVERSARIAL_VALIDATED"

_ARCHIVE_SUFFIXES = {
    ".7z",
    ".bz2",
    ".gz",
    ".rar",
    ".tar",
    ".tgz",
    ".txz",
    ".xz",
    ".zip",
}
_EXECUTABLE_SUFFIXES = {
    ".app",
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".dylib",
    ".exe",
    ".msi",
    ".ps1",
    ".pyc",
    ".sh",
    ".so",
}
_CHECKSUM_SELF_EXCLUSIONS = {"run_manifest.json", "file_checksums.json"}


class KaggleV5ImportError(ValueError):
    """Base error for V5 Kaggle package validation."""


class ArchiveSecurityError(KaggleV5ImportError):
    """Raised before extraction when an archive has an unsafe member."""


class ImportManifestError(KaggleV5ImportError):
    """Raised when declared provenance does not match package contents."""


class ImportDataIntegrityError(KaggleV5ImportError):
    """Raised when prediction, shard, coverage, or matrix integrity fails."""


class ImportConflictError(KaggleV5ImportError):
    """Raised when a run ID is reused for a different archive."""


@dataclass(frozen=True, slots=True)
class ArchiveLimits:
    max_members: int = 10_000
    max_member_uncompressed_bytes: int = 1_000_000_000
    max_total_uncompressed_bytes: int = 2_000_000_000
    max_compression_ratio: float = 200.0
    max_manifest_bytes: int = 5_000_000
    max_prediction_rows: int = 25_000_000


@dataclass(frozen=True, slots=True)
class ValidatedKaggleArchive:
    zip_path: str
    zip_sha256: str
    root_prefix: str
    manifest: dict[str, Any]
    file_checksums: dict[str, str]
    member_count: int
    total_uncompressed_bytes: int
    prediction_summary: dict[str, Any]
    shard_summary: dict[str, Any]
    matrix_summary: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_kaggle_zip(
    zip_path: str | Path,
    *,
    expected_study_id: str | None = None,
    expected_run_id: str | None = None,
    expected_benchmark_id: str | None = None,
    expected_config_hash: str | None = None,
    expected_source_zip_sha256: str | None = None,
    limits: ArchiveLimits | None = None,
    allow_nested_archives: bool = False,
    require_full_prediction_schema: bool = True,
) -> ValidatedKaggleArchive:
    """Validate a V5 package without writing any archive member to disk."""

    source = Path(zip_path)
    if not source.is_file():
        raise FileNotFoundError(f"Kaggle ZIP does not exist: {source}")
    archive_limits = limits or ArchiveLimits()
    zip_digest = sha256_file(source)
    if expected_source_zip_sha256 is not None and zip_digest != expected_source_zip_sha256.lower():
        raise ImportManifestError(
            "Source ZIP hash mismatch: "
            f"expected {expected_source_zip_sha256.lower()}, got {zip_digest}"
        )

    try:
        archive = zipfile.ZipFile(source)
    except zipfile.BadZipFile as exc:
        raise ArchiveSecurityError(f"Invalid ZIP archive: {source}") from exc
    with archive:
        members = _validate_archive_members(
            archive,
            limits=archive_limits,
            allow_nested_archives=allow_nested_archives,
        )
        layout, root_prefix = _resolve_archive_layout(members)
        manifest = _load_json_member(
            archive,
            layout["run_manifest.json"],
            max_bytes=archive_limits.max_manifest_bytes,
        )
        if not isinstance(manifest, dict):
            raise ImportManifestError("run_manifest.json must contain a JSON object")
        try:
            normalized_manifest = validate_run_manifest(
                manifest,
                expected_study_id=expected_study_id,
                expected_run_id=expected_run_id,
                expected_benchmark_id=expected_benchmark_id,
                expected_config_hash=expected_config_hash,
                require_complete=True,
            )
        except ManifestValidationError as exc:
            raise ImportManifestError(str(exc)) from exc
        declared_zip_hash = normalized_manifest.get("source_zip_sha256")
        if declared_zip_hash and str(declared_zip_hash).lower() != zip_digest:
            raise ImportManifestError(
                "Manifest source_zip_sha256 does not match the imported archive"
            )

        config_payload = _load_yaml_member(
            archive,
            layout["config_snapshot.yaml"],
            max_bytes=archive_limits.max_manifest_bytes,
        )
        if not isinstance(config_payload, dict):
            raise ImportManifestError("config_snapshot.yaml must contain a mapping")
        actual_config_hash = compute_configuration_hash(config_payload)
        if actual_config_hash != normalized_manifest["config_hash"]:
            raise ImportManifestError(
                "config_snapshot.yaml hash does not match run_manifest.json: "
                f"{actual_config_hash} != {normalized_manifest['config_hash']}"
            )

        checksum_payload = _load_json_member(
            archive,
            layout["file_checksums.json"],
            max_bytes=archive_limits.max_manifest_bytes,
        )
        try:
            checksums = normalize_checksum_payload(checksum_payload)
        except ManifestValidationError as exc:
            raise ImportManifestError(str(exc)) from exc
        manifest_checksums = normalized_manifest["file_checksums"]
        if manifest_checksums != checksums:
            raise ImportManifestError(
                "run_manifest.json file_checksums differ from file_checksums.json"
            )
        _validate_archive_checksums(archive, layout, checksums)

        models = _load_json_member(
            archive,
            layout["models.json"],
            max_bytes=archive_limits.max_manifest_bytes,
        )
        contract = _load_json_member(
            archive,
            layout["benchmark_contract.json"],
            max_bytes=archive_limits.max_manifest_bytes,
        )
        shard_status = _load_json_member(
            archive,
            layout["shard_status.json"],
            max_bytes=archive_limits.max_manifest_bytes,
        )
        _validate_models_payload(models, normalized_manifest)
        _validate_benchmark_contract(contract, normalized_manifest)
        shard_summary = validate_shard_completeness(
            normalized_manifest["shards"],
            shard_status,
        )
        if shard_summary["status"] != "pass":
            raise ImportDataIntegrityError(
                "Shard completeness validation failed: "
                f"missing={shard_summary['missing_shards']}, "
                f"stale={shard_summary['stale_shards']}, "
                f"incomplete={shard_summary['incomplete_shards']}"
            )

        prediction_rows, prediction_summary = _validate_predictions_member(
            archive,
            layout["predictions.jsonl"],
            manifest=normalized_manifest,
            models_payload=models,
            contract=contract,
            max_rows=archive_limits.max_prediction_rows,
            require_full_schema=require_full_prediction_schema,
        )
        _validate_failure_summary(
            archive,
            layout["failure_summary.csv"],
            prediction_rows,
            normalized_manifest,
        )
        matrix_summary = None
        if "matrix.csv" in layout:
            matrix_summary = _validate_matrix_member(
                archive,
                layout["matrix.csv"],
                prediction_rows,
            )
        return ValidatedKaggleArchive(
            zip_path=str(source),
            zip_sha256=zip_digest,
            root_prefix=root_prefix,
            manifest=normalized_manifest,
            file_checksums=checksums,
            member_count=len([member for member in members if not member.is_dir()]),
            total_uncompressed_bytes=sum(
                member.file_size for member in members if not member.is_dir()
            ),
            prediction_summary=prediction_summary,
            shard_summary=shard_summary,
            matrix_summary=matrix_summary,
        )


def import_kaggle_archive_v5(
    zip_path: str | Path,
    *,
    output_root: str | Path = "data/external/kaggle_imported_v5",
    cache_root: str | Path | None = None,
    expected_study_id: str | None = None,
    expected_run_id: str | None = None,
    expected_benchmark_id: str | None = None,
    expected_config_hash: str | None = None,
    expected_source_zip_sha256: str | None = None,
    limits: ArchiveLimits | None = None,
    allow_nested_archives: bool = False,
    require_full_prediction_schema: bool = True,
) -> dict[str, Any]:
    validated = validate_kaggle_zip(
        zip_path,
        expected_study_id=expected_study_id,
        expected_run_id=expected_run_id,
        expected_benchmark_id=expected_benchmark_id,
        expected_config_hash=expected_config_hash,
        expected_source_zip_sha256=expected_source_zip_sha256,
        limits=limits,
        allow_nested_archives=allow_nested_archives,
        require_full_prediction_schema=require_full_prediction_schema,
    )
    destination_root = Path(output_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    manifest = validated.manifest
    run_key = f"{manifest['study_id']}::{manifest['run_id']}"
    ledger_path = destination_root / "import_ledger_v5.json"
    ledger = _load_import_ledger(ledger_path)
    previous = ledger["runs"].get(run_key)
    if previous:
        if previous.get("source_zip_sha256") != validated.zip_sha256:
            raise ImportConflictError(
                f"Run ID conflict for {run_key}: an archive with a different hash was imported"
            )
        return {
            "schema_version": IMPORTER_SCHEMA_VERSION,
            "status": "already_imported",
            "final_verdict": IMPORTER_READY_VERDICT,
            "idempotent": True,
            **previous,
            "validation": validated.to_dict(),
        }

    destination = (
        destination_root
        / str(manifest["benchmark_id"])
        / str(manifest["study_id"])
        / str(manifest["run_id"])
    )
    if destination.exists():
        receipt_path = destination / "import_receipt_v5.json"
        receipt = _read_json_file(receipt_path) if receipt_path.exists() else None
        if (
            not isinstance(receipt, dict)
            or receipt.get("source_zip_sha256") != validated.zip_sha256
        ):
            raise ImportConflictError(
                f"Import destination already exists with unknown content: {destination}"
            )
    else:
        _extract_validated_archive(Path(zip_path), validated, destination)

    cache_destination = None
    if cache_root is not None:
        cache_destination = (
            Path(cache_root) / str(manifest["benchmark_id"]) / "v5" / str(manifest["run_id"])
        )
        _copy_cache_artifacts(destination, cache_destination)

    receipt = {
        "schema_version": IMPORTER_SCHEMA_VERSION,
        "status": "imported",
        "final_verdict": IMPORTER_READY_VERDICT,
        "idempotent": False,
        "study_id": manifest["study_id"],
        "run_id": manifest["run_id"],
        "benchmark_id": manifest["benchmark_id"],
        "config_hash": manifest["config_hash"],
        "config_class": manifest["config_class"],
        "evidence_state": manifest["evidence_state"],
        "source_zip": str(Path(zip_path)),
        "source_zip_sha256": validated.zip_sha256,
        "import_dir": str(destination),
        "cache_dir": str(cache_destination) if cache_destination else None,
        "prediction_summary": validated.prediction_summary,
        "shard_summary": validated.shard_summary,
        "matrix_summary": validated.matrix_summary,
        "cross_benchmark_eligibility": {
            "exact_model_ids": validated.prediction_summary["model_ids"],
            "model_families": validated.prediction_summary["model_families"],
            "model_family_by_id": validated.prediction_summary["model_family_by_id"],
            "usable_items": validated.prediction_summary["usable_item_count"],
            "extraction_reliability": validated.prediction_summary["extraction_reliability"],
            "config_class": manifest["config_class"],
            "data_integrity": "pass",
            "evidence_state": manifest["evidence_state"],
            "study_id": manifest["study_id"],
        },
    }
    atomic_write_json(destination / "import_receipt_v5.json", receipt)
    if cache_destination is not None:
        shutil.copy2(
            destination / "import_receipt_v5.json",
            cache_destination / "import_receipt_v5.json",
        )
    ledger["runs"][run_key] = {
        key: receipt[key]
        for key in (
            "study_id",
            "run_id",
            "benchmark_id",
            "config_hash",
            "config_class",
            "evidence_state",
            "source_zip",
            "source_zip_sha256",
            "import_dir",
            "cache_dir",
        )
    }
    atomic_write_json(ledger_path, ledger)
    receipt["validation"] = validated.to_dict()
    return receipt


def import_kaggle_outputs_v5(
    *,
    input_dir: str | Path = "kaggle_outputs_v5",
    output_root: str | Path = "data/external/kaggle_imported_v5",
    cache_root: str | Path | None = None,
    results_root: str | Path | None = "results",
    expected_study_id: str | None = None,
    expected_benchmark_id: str | None = None,
    limits: ArchiveLimits | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    input_root = Path(input_dir)
    archives = sorted(input_root.rglob("*.zip")) if input_root.exists() else []
    if not archives:
        payload = {
            "schema_version": IMPORTER_SCHEMA_VERSION,
            "status": "blocked_no_zips",
            "final_verdict": "KAGGLE_IMPORT_V5_BLOCKED_NO_ZIPS",
            "input_dir": str(input_root),
            "zip_count": 0,
            "imports": [],
            "blocked_reason": "No Kaggle ZIP files were found.",
        }
        _write_import_summary(results_root, payload)
        return payload
    imports = [
        import_kaggle_archive_v5(
            archive,
            output_root=output_root,
            cache_root=cache_root,
            expected_study_id=expected_study_id,
            expected_benchmark_id=expected_benchmark_id,
            limits=limits,
            require_full_prediction_schema=strict,
        )
        for archive in archives
    ]
    payload = {
        "schema_version": IMPORTER_SCHEMA_VERSION,
        "status": "ok",
        "final_verdict": IMPORTER_READY_VERDICT,
        "input_dir": str(input_root),
        "zip_count": len(archives),
        "imports": imports,
    }
    _write_import_summary(results_root, payload)
    return payload


# Versioned aliases make CLI integration explicit while leaving kaggle_v4.py untouched.
import_kaggle_outputs = import_kaggle_outputs_v5
import_kaggle_archive = import_kaggle_archive_v5


def _validate_archive_members(
    archive: zipfile.ZipFile,
    *,
    limits: ArchiveLimits,
    allow_nested_archives: bool,
) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    if not members:
        raise ArchiveSecurityError("ZIP archive is empty")
    if len(members) > limits.max_members:
        raise ArchiveSecurityError(
            f"ZIP contains too many members: {len(members)} > {limits.max_members}"
        )
    total_uncompressed = 0
    total_compressed = 0
    seen: set[str] = set()
    seen_casefold: set[str] = set()
    for member in members:
        name = member.filename
        _validate_member_name(name)
        folded = name.casefold()
        if name in seen or folded in seen_casefold:
            raise ArchiveSecurityError(f"Duplicate or case-colliding ZIP member: {name}")
        seen.add(name)
        seen_casefold.add(folded)
        if member.flag_bits & 0x1:
            raise ArchiveSecurityError(f"Encrypted ZIP members are not accepted: {name}")
        mode = (member.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode):
            raise ArchiveSecurityError(f"Symlink ZIP member is not accepted: {name}")
        if not member.is_dir() and mode and mode & 0o111:
            raise ArchiveSecurityError(f"Executable ZIP member is not accepted: {name}")
        suffix = Path(name).suffix.lower()
        if not member.is_dir() and suffix in _EXECUTABLE_SUFFIXES:
            raise ArchiveSecurityError(f"Unexpected executable file in ZIP: {name}")
        if not allow_nested_archives and not member.is_dir() and suffix in _ARCHIVE_SUFFIXES:
            raise ArchiveSecurityError(f"Nested archive is not accepted: {name}")
        if member.file_size > limits.max_member_uncompressed_bytes:
            raise ArchiveSecurityError(
                f"ZIP member exceeds uncompressed size limit: {name} ({member.file_size})"
            )
        if not member.is_dir() and member.file_size:
            ratio = member.file_size / max(member.compress_size, 1)
            if ratio > limits.max_compression_ratio:
                raise ArchiveSecurityError(
                    f"ZIP member compression ratio is unsafe: {name} ({ratio:.1f})"
                )
        total_uncompressed += member.file_size
        total_compressed += member.compress_size
    if total_uncompressed > limits.max_total_uncompressed_bytes:
        raise ArchiveSecurityError(
            "ZIP total uncompressed size exceeds limit: "
            f"{total_uncompressed} > {limits.max_total_uncompressed_bytes}"
        )
    if (
        total_uncompressed
        and total_uncompressed / max(total_compressed, 1) > limits.max_compression_ratio
    ):
        raise ArchiveSecurityError("ZIP aggregate compression ratio exceeds the safety limit")
    return members


def _validate_member_name(name: str) -> None:
    if not name or "\x00" in name:
        raise ArchiveSecurityError("ZIP contains an empty or NUL-containing member name")
    if "\\" in name:
        raise ArchiveSecurityError(f"ZIP member uses an unsafe backslash path: {name}")
    posix = PurePosixPath(name)
    windows = PureWindowsPath(name)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise ArchiveSecurityError(f"ZIP member has an absolute path: {name}")
    raw_parts = name.split("/")
    if name.endswith("/"):
        raw_parts = raw_parts[:-1]
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ArchiveSecurityError(f"ZIP member has an unsafe relative path: {name}")


def _resolve_archive_layout(
    members: list[zipfile.ZipInfo],
) -> tuple[dict[str, str], str]:
    file_names = [member.filename for member in members if not member.is_dir()]
    by_basename: dict[str, list[str]] = defaultdict(list)
    for name in file_names:
        by_basename[PurePosixPath(name).name].append(name)
    missing = [name for name in RUN_REQUIRED_FILES if name not in by_basename]
    if missing:
        raise ImportManifestError(f"Kaggle package missing required files: {missing}")
    ambiguous = {
        name: paths
        for name, paths in by_basename.items()
        if name in RUN_REQUIRED_FILES and len(paths) != 1
    }
    if ambiguous:
        raise ImportManifestError(f"Kaggle package has ambiguous required files: {ambiguous}")
    manifest_name = by_basename["run_manifest.json"][0]
    root = PurePosixPath(manifest_name).parent
    root_prefix = "" if str(root) == "." else root.as_posix() + "/"
    layout: dict[str, str] = {}
    for name in file_names:
        member_path = PurePosixPath(name)
        if str(root) == ".":
            relative = member_path
        else:
            try:
                relative = member_path.relative_to(root)
            except ValueError as exc:
                raise ImportManifestError(
                    f"All package files must share the run root {root.as_posix()!r}: {name}"
                ) from exc
        relative_name = relative.as_posix()
        if relative_name in layout:
            raise ImportManifestError(f"Duplicate relative package path: {relative_name}")
        layout[relative_name] = name
    missing_same_root = [name for name in RUN_REQUIRED_FILES if name not in layout]
    if missing_same_root:
        raise ImportManifestError(
            f"Required files must share the run_manifest.json root: {missing_same_root}"
        )
    return layout, root_prefix


def _validate_archive_checksums(
    archive: zipfile.ZipFile,
    layout: Mapping[str, str],
    checksums: Mapping[str, str],
) -> None:
    relative_members = {basename: member_name for basename, member_name in layout.items()}
    required_checksum_names = set(relative_members).difference(_CHECKSUM_SELF_EXCLUSIONS)
    missing_checksums = sorted(required_checksum_names.difference(checksums))
    if missing_checksums:
        raise ImportManifestError(f"file_checksums.json omits required files: {missing_checksums}")
    unchecked_members = sorted(
        basename
        for basename in relative_members
        if basename not in _CHECKSUM_SELF_EXCLUSIONS and basename not in checksums
    )
    if unchecked_members:
        raise ImportManifestError(f"Package contains unchecked files: {unchecked_members}")
    for relative, expected in sorted(checksums.items()):
        member_name = layout.get(relative)
        if member_name is None:
            raise ImportManifestError(f"Checksummed file is missing from package root: {relative}")
        actual = _sha256_archive_member(archive, member_name)
        if actual != expected.lower():
            raise ImportManifestError(
                f"Checksum mismatch for {relative}: expected {expected.lower()}, got {actual}"
            )


def _validate_models_payload(payload: Any, manifest: Mapping[str, Any]) -> None:
    models = payload.get("models") if isinstance(payload, dict) else payload
    if not isinstance(models, list):
        raise ImportManifestError("models.json must contain a model list")
    declared = {str(model["model_id"]): model for model in manifest["models"]}
    observed: dict[str, Mapping[str, Any]] = {}
    for model in models:
        if not isinstance(model, dict) or not model.get("model_id"):
            raise ImportManifestError("models.json contains an invalid model entry")
        model_id = str(model["model_id"])
        if model_id in observed:
            raise ImportManifestError(f"models.json contains duplicate model_id: {model_id}")
        observed[model_id] = model
    if set(observed) != set(declared):
        raise ImportManifestError(
            "models.json does not match run manifest models: "
            f"missing={sorted(set(declared) - set(observed))}, "
            f"unknown={sorted(set(observed) - set(declared))}"
        )
    for model_id, manifest_model in declared.items():
        for field in ("model_revision", "model_family"):
            expected = manifest_model.get(field)
            actual = observed[model_id].get(field)
            if expected is not None and actual != expected:
                raise ImportManifestError(
                    f"Model metadata mismatch for {model_id} field {field}: {actual!r} != {expected!r}"
                )


def _validate_benchmark_contract(payload: Any, manifest: Mapping[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ImportManifestError("benchmark_contract.json must contain an object")
    benchmark = payload.get("benchmark_id")
    if benchmark != manifest["benchmark_id"]:
        raise ImportManifestError(
            f"Benchmark contract mismatch: {benchmark!r} != {manifest['benchmark_id']!r}"
        )
    version = payload.get("benchmark_version")
    if version != manifest["benchmark_version"]:
        raise ImportManifestError(
            f"Benchmark version mismatch: {version!r} != {manifest['benchmark_version']!r}"
        )


def _validate_predictions_member(
    archive: zipfile.ZipFile,
    member_name: str,
    *,
    manifest: Mapping[str, Any],
    models_payload: Any,
    contract: Mapping[str, Any],
    max_rows: int,
    require_full_schema: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    declared_models_list = (
        models_payload.get("models") if isinstance(models_payload, dict) else models_payload
    )
    if not isinstance(declared_models_list, list):
        raise ImportManifestError("models.json must contain a list or an object with a models list")
    declared_models = {str(model["model_id"]): model for model in declared_models_list}
    declared_shards = {str(shard["shard_id"]) for shard in manifest["shards"]}
    expected_item_shards: dict[str, str] = {}
    shards_with_items = 0
    for shard in manifest["shards"]:
        item_ids = shard.get("item_ids")
        if item_ids is None:
            continue
        if not isinstance(item_ids, list):
            raise ImportManifestError("Manifest shard item_ids must be a list")
        shards_with_items += 1
        for item_id in item_ids:
            normalized_item_id = str(item_id)
            if normalized_item_id in expected_item_shards:
                raise ImportDataIntegrityError(
                    f"Manifest assigns item {normalized_item_id} to multiple shards"
                )
            expected_item_shards[normalized_item_id] = str(shard["shard_id"])
    if shards_with_items not in {0, len(manifest["shards"])}:
        raise ImportManifestError("Either every manifest shard must declare item_ids or none may")
    if expected_item_shards and len(expected_item_shards) != int(manifest["item_count"]):
        raise ImportDataIntegrityError(
            "Manifest shard item coverage does not match declared item_count"
        )
    allowed_subtasks = _allowed_values(contract, "subtasks", "subtask_id")
    allowed_tasks = _allowed_values(contract, "tasks", "task_id")
    seen_keys: dict[tuple[str, ...], bytes] = {}
    item_hashes: dict[str, str] = {}
    model_revisions: dict[str, set[str]] = defaultdict(set)
    model_families: dict[str, set[str]] = defaultdict(set)
    row_config_hashes: set[str] = set()
    observed_models: set[str] = set()
    observed_shards: set[str] = set()
    observed_items: set[str] = set()
    usable_items: set[str] = set()
    extraction_successes = 0
    with archive.open(member_name, "r") as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        for line_number, line in enumerate(text, start=1):
            if not line.strip():
                continue
            if len(rows) >= max_rows:
                raise ImportDataIntegrityError(
                    f"predictions.jsonl exceeds the maximum row count of {max_rows}"
                )
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ImportDataIntegrityError(
                    f"Malformed predictions.jsonl at line {line_number}: {exc}"
                ) from exc
            if not isinstance(row, dict):
                raise ImportDataIntegrityError(f"Prediction row {line_number} is not a JSON object")
            try:
                row = validate_prediction_record(
                    row,
                    require_full_schema=require_full_schema,
                )
            except ManifestValidationError as exc:
                raise ImportDataIntegrityError(f"Prediction row {line_number}: {exc}") from exc
            _validate_row_against_manifest(row, manifest, line_number)
            model_id = str(row["model_id"])
            item_id = str(row["item_id"])
            shard_id = str(row["shard_id"])
            if model_id not in declared_models:
                raise ImportDataIntegrityError(
                    f"Prediction row {line_number} uses unknown model: {model_id}"
                )
            if shard_id not in declared_shards:
                raise ImportDataIntegrityError(
                    f"Prediction row {line_number} uses stale/unknown shard: {shard_id}"
                )
            if expected_item_shards:
                expected_shard = expected_item_shards.get(item_id)
                if expected_shard is None:
                    raise ImportDataIntegrityError(
                        f"Prediction row {line_number} uses undeclared item: {item_id}"
                    )
                if expected_shard != shard_id:
                    raise ImportDataIntegrityError(
                        f"Prediction row {line_number} assigns item {item_id} to "
                        f"{shard_id}, expected {expected_shard}"
                    )
            if allowed_subtasks and str(row["subtask_id"]) not in allowed_subtasks:
                raise ImportDataIntegrityError(
                    f"Prediction row {line_number} uses unknown subtask: {row['subtask_id']}"
                )
            if allowed_tasks and str(row["task_id"]) not in allowed_tasks:
                raise ImportDataIntegrityError(
                    f"Prediction row {line_number} uses unknown task: {row['task_id']}"
                )
            key = (
                str(row["benchmark_id"]),
                str(row["task_id"]),
                str(row["subtask_id"]),
                model_id,
                item_id,
                str(row["seed"]),
                str(row["prompt_template_id"]),
            )
            signature = canonical_json_bytes(row)
            if key in seen_keys:
                qualifier = "contradictory " if seen_keys[key] != signature else ""
                raise ImportDataIntegrityError(
                    f"Duplicate {qualifier}model-item prediction row for key {key}"
                )
            seen_keys[key] = signature
            item_hash = str(row["item_hash"])
            previous_hash = item_hashes.setdefault(item_id, item_hash)
            if previous_hash != item_hash:
                raise ImportDataIntegrityError(
                    f"Item ID collision for {item_id}: multiple item_hash values"
                )
            model_revisions[model_id].add(str(row["model_revision"]))
            model_families[model_id].add(str(row["model_family"]))
            if row.get("config_hash") is not None:
                row_config_hashes.add(str(row["config_hash"]))
            observed_models.add(model_id)
            observed_shards.add(shard_id)
            observed_items.add(item_id)
            if row.get("is_correct") is not None:
                usable_items.add(item_id)
            if str(row.get("extraction_status", "")).lower() in {"success", "pass", "ok"}:
                extraction_successes += 1
            rows.append(row)
    if not rows:
        raise ImportDataIntegrityError("predictions.jsonl has zero rows")
    mixed_revisions = sorted(
        model for model, revisions in model_revisions.items() if len(revisions) != 1
    )
    if mixed_revisions:
        raise ImportDataIntegrityError(f"Mixed model revisions in predictions: {mixed_revisions}")
    mixed_families = sorted(
        model for model, families in model_families.items() if len(families) != 1
    )
    if mixed_families:
        raise ImportDataIntegrityError(f"Mixed model families in predictions: {mixed_families}")
    if row_config_hashes and row_config_hashes != {str(manifest["config_hash"])}:
        raise ImportDataIntegrityError(
            f"Mixed or mismatched config hashes in predictions: {sorted(row_config_hashes)}"
        )
    if observed_models != set(declared_models):
        raise ImportDataIntegrityError(
            "Prediction model coverage differs from manifest: "
            f"missing={sorted(set(declared_models) - observed_models)}, "
            f"unknown={sorted(observed_models - set(declared_models))}"
        )
    if observed_shards != declared_shards:
        raise ImportDataIntegrityError(
            "Prediction shard coverage differs from manifest: "
            f"missing={sorted(declared_shards - observed_shards)}, "
            f"stale={sorted(observed_shards - declared_shards)}"
        )
    if len(observed_items) != int(manifest["item_count"]):
        raise ImportDataIntegrityError(
            f"Item count mismatch: observed {len(observed_items)}, declared {manifest['item_count']}"
        )
    if len(rows) != int(manifest["expected_prediction_rows"]):
        raise ImportDataIntegrityError(
            "Prediction row count mismatch: "
            f"observed {len(rows)}, declared {manifest['expected_prediction_rows']}"
        )
    for model_id in observed_models:
        expected_revision = declared_models[model_id].get("model_revision")
        expected_family = declared_models[model_id].get("model_family")
        if expected_revision is not None and model_revisions[model_id] != {str(expected_revision)}:
            raise ImportDataIntegrityError(f"Model revision mismatch for {model_id}")
        if expected_family is not None and model_families[model_id] != {str(expected_family)}:
            raise ImportDataIntegrityError(f"Model family mismatch for {model_id}")
    summary = {
        "status": "pass",
        "row_count": len(rows),
        "model_count": len(observed_models),
        "model_ids": sorted(observed_models),
        "model_families": sorted(
            {next(iter(model_families[model_id])) for model_id in observed_models}
        ),
        "model_family_by_id": {
            model_id: next(iter(model_families[model_id])) for model_id in sorted(observed_models)
        },
        "item_count": len(observed_items),
        "usable_item_count": len(usable_items),
        "shard_ids": sorted(observed_shards),
        "extraction_reliability": extraction_successes / len(rows),
        "evidence_state": manifest["evidence_state"],
    }
    return rows, summary


def _validate_failure_summary(
    archive: zipfile.ZipFile,
    member_name: str,
    rows: list[dict[str, Any]],
    manifest: Mapping[str, Any],
) -> None:
    try:
        content = archive.read(member_name).decode("utf-8")
        parsed = list(csv.DictReader(io.StringIO(content)))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ImportDataIntegrityError(f"Malformed failure_summary.csv: {exc}") from exc
    if not parsed or not {"failure_type", "count"}.issubset(parsed[0]):
        raise ImportDataIntegrityError(
            "failure_summary.csv must contain failure_type,count columns"
        )
    declared: Counter[str] = Counter()
    for record in parsed:
        failure_type = str(record.get("failure_type", ""))
        try:
            count = int(str(record.get("count", "")))
        except ValueError as exc:
            raise ImportDataIntegrityError(
                f"failure_summary.csv has invalid count for {failure_type!r}"
            ) from exc
        if count < 0 or failure_type in declared:
            raise ImportDataIntegrityError(
                f"failure_summary.csv has duplicate/negative entry for {failure_type!r}"
            )
        declared[failure_type] = count
    observed = Counter(str(row["failure_type"]) for row in rows)
    if declared != observed:
        raise ImportDataIntegrityError(
            f"failure_summary.csv contradicts predictions: declared={dict(declared)}, "
            f"observed={dict(observed)}"
        )
    failed_count = sum(count for failure, count in observed.items() if failure != "SUCCESS")
    failure_state = str(manifest["failure_state"]).lower()
    if failed_count and failure_state in {"none", "success", "no_failures"}:
        raise ImportDataIntegrityError(
            "run_manifest failure_state says no failures but failed prediction rows exist"
        )


def _validate_row_against_manifest(
    row: Mapping[str, Any],
    manifest: Mapping[str, Any],
    line_number: int,
) -> None:
    for field in ("study_id", "run_id", "benchmark_id"):
        if row.get(field) != manifest[field]:
            raise ImportDataIntegrityError(
                f"Prediction row {line_number} {field} mismatch: "
                f"{row.get(field)!r} != {manifest[field]!r}"
            )
    if row.get("benchmark_version") != manifest["benchmark_version"]:
        raise ImportDataIntegrityError(f"Prediction row {line_number} benchmark_version mismatch")
    if manifest["evidence_state"] == NON_EVIDENCE_FIXTURE:
        if row.get("evidence_state") != NON_EVIDENCE_FIXTURE:
            raise ImportDataIntegrityError(
                f"Fixture prediction row {line_number} is missing NON_EVIDENCE_FIXTURE"
            )


def _validate_matrix_member(
    archive: zipfile.ZipFile,
    member_name: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        content = archive.read(member_name).decode("utf-8")
        frame = pd.read_csv(io.StringIO(content))
    except (UnicodeDecodeError, pd.errors.ParserError, csv.Error) as exc:
        raise ImportDataIntegrityError(f"Malformed matrix.csv: {exc}") from exc
    if frame.empty or frame.shape[1] < 2:
        raise ImportDataIntegrityError("matrix.csv must contain models and at least one item")
    model_column = "model_id" if "model_id" in frame.columns else str(frame.columns[0])
    if frame[model_column].duplicated().any():
        raise ImportDataIntegrityError("matrix.csv contains duplicate model rows")
    matrix_models = {str(value) for value in frame[model_column]}
    prediction_models = {str(row["model_id"]) for row in rows}
    if matrix_models != prediction_models:
        raise ImportDataIntegrityError("matrix.csv model coverage does not match predictions")
    matrix_item_map: dict[str, str] = {}
    for column in frame.columns:
        if str(column) == model_column:
            continue
        item_id = str(column).split("::", 1)[-1]
        if item_id in matrix_item_map:
            raise ImportDataIntegrityError(
                f"matrix.csv item columns collide after normalization: {item_id}"
            )
        matrix_item_map[item_id] = str(column)
    prediction_items = {str(row["item_id"]) for row in rows}
    if set(matrix_item_map) != prediction_items:
        raise ImportDataIntegrityError("matrix.csv item coverage does not match predictions")
    indexed = frame.set_index(model_column)
    for row in rows:
        value = indexed.loc[str(row["model_id"]), matrix_item_map[str(row["item_id"])]]
        expected = row.get("is_correct")
        if expected is None:
            if not pd.isna(value):
                raise ImportDataIntegrityError(
                    "matrix.csv must use missing values for unscored prediction rows"
                )
        elif pd.isna(value) or bool(int(float(value))) is not bool(expected):
            raise ImportDataIntegrityError(
                "matrix.csv correctness value contradicts predictions.jsonl for "
                f"model={row['model_id']} item={row['item_id']}"
            )
    return {
        "status": "pass",
        "model_count": len(matrix_models),
        "item_count": len(matrix_item_map),
    }


def _extract_validated_archive(
    zip_path: Path,
    validated: ValidatedKaggleArchive,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                relative = member.filename
                if validated.root_prefix:
                    if not relative.startswith(validated.root_prefix):
                        continue
                    relative = relative[len(validated.root_prefix) :]
                target = (temp_dir / relative).resolve()
                if not target.is_relative_to(temp_dir.resolve()):
                    raise ArchiveSecurityError(f"Unsafe extraction target: {member.filename}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member, "r") as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
        os.replace(temp_dir, destination)
    except BaseException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _copy_cache_artifacts(import_dir: Path, cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    for name in ("predictions.jsonl", "matrix.csv", "run_manifest.json", "import_receipt_v5.json"):
        source = import_dir / name
        if not source.is_file():
            continue
        destination = cache_dir / name
        if destination.exists() and sha256_file(destination) != sha256_file(source):
            raise ImportConflictError(f"Cache artifact conflict: {destination}")
        shutil.copy2(source, destination)


def _load_import_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": IMPORTER_SCHEMA_VERSION, "runs": {}}
    payload = _read_json_file(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("runs"), dict):
        raise ImportConflictError(f"Invalid import ledger: {path}")
    return payload


def _write_import_summary(
    results_root: str | Path | None,
    payload: Mapping[str, Any],
) -> None:
    if results_root is None:
        return
    destination = Path(results_root) / "kaggle_import_v5"
    destination.mkdir(parents=True, exist_ok=True)
    atomic_write_json(destination / "import_summary.json", payload)
    lines = [
        "# Kaggle Output Import V5",
        "",
        f"- Status: `{payload['status']}`",
        f"- Final verdict: `{payload['final_verdict']}`",
        f"- ZIP count: {payload['zip_count']}",
        "",
        "All imported runs remain scoped to their manifest evidence state. Fixture packages are NON_EVIDENCE_FIXTURE.",
    ]
    if payload.get("blocked_reason"):
        lines.extend(["", f"Blocked reason: {payload['blocked_reason']}"])
    atomic_write_text(destination / "import_summary.md", "\n".join(lines) + "\n")


def _load_json_member(
    archive: zipfile.ZipFile,
    member_name: str,
    *,
    max_bytes: int,
) -> Any:
    raw = _read_member_limited(archive, member_name, max_bytes=max_bytes)
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportManifestError(f"Invalid JSON in {member_name}: {exc}") from exc


def _load_yaml_member(
    archive: zipfile.ZipFile,
    member_name: str,
    *,
    max_bytes: int,
) -> Any:
    raw = _read_member_limited(archive, member_name, max_bytes=max_bytes)
    try:
        return yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ImportManifestError(f"Invalid YAML in {member_name}: {exc}") from exc


def _read_member_limited(
    archive: zipfile.ZipFile,
    member_name: str,
    *,
    max_bytes: int,
) -> bytes:
    with archive.open(member_name, "r") as handle:
        data = handle.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ArchiveSecurityError(f"Archive member exceeds read limit: {member_name}")
    return data


def _sha256_archive_member(archive: zipfile.ZipFile, member_name: str) -> str:
    import hashlib

    digest = hashlib.sha256()
    with archive.open(member_name, "r") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _allowed_values(contract: Mapping[str, Any], key: str, id_key: str) -> set[str]:
    values = contract.get(key, [])
    if not isinstance(values, list):
        raise ImportManifestError(f"benchmark_contract.json {key} must be a list")
    allowed: set[str] = set()
    for value in values:
        if isinstance(value, str):
            allowed.add(value)
        elif isinstance(value, dict) and value.get(id_key) is not None:
            allowed.add(str(value[id_key]))
        else:
            raise ImportManifestError(f"benchmark_contract.json has invalid {key} entry")
    return allowed


def _read_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ImportConflictError(f"Invalid JSON at {path}: {exc}") from exc
