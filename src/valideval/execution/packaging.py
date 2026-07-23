from __future__ import annotations

import json
import os
import re
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from valideval.execution.manifest import (
    RUN_REQUIRED_FILES,
    normalize_checksum_payload,
    read_json,
    sha256_file,
    validate_file_checksums,
    validate_prediction_record,
    validate_run_manifest,
)

_FORBIDDEN_MEMBER_PARTS = frozenset(
    {
        ".git",
        ".env",
        "__pycache__",
        "model_cache",
        "models_cache",
        "hf_cache",
        "huggingface",
        "wandb",
        "secrets",
        "tokens",
    }
)
_SECRET_NAME = re.compile(
    r"(?:^|[._-])(secret|token|credential|private[_-]?key|api[_-]?key)(?:[._-]|$)",
    re.I,
)


class PackageValidationError(ValueError):
    """Raised when a run directory is unsafe or incomplete for packaging."""


def validate_run_directory(
    run_dir: str | Path,
    *,
    expected_benchmark: str | None = None,
    expected_config_hash: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    if not root.is_dir():
        raise PackageValidationError(f"run directory does not exist: {root}")
    missing = [name for name in RUN_REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        raise PackageValidationError(f"run directory is missing required files: {missing}")
    manifest = validate_run_manifest(
        read_json(root / "run_manifest.json"),
        expected_benchmark_id=expected_benchmark,
        expected_config_hash=expected_config_hash,
    )
    checksum_payload = normalize_checksum_payload(read_json(root / "file_checksums.json"))
    if checksum_payload != manifest["file_checksums"]:
        raise PackageValidationError("run manifest and file_checksums.json disagree")
    verified = validate_file_checksums(root, checksum_payload)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    with (root / "predictions.jsonl").open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PackageValidationError(
                    f"malformed predictions JSONL at line {line_number}: {exc}"
                ) from exc
            if not isinstance(raw, dict):
                raise PackageValidationError(f"prediction line {line_number} is not an object")
            row = validate_prediction_record(raw, require_full_schema=False)
            required_presence = {
                "study_id",
                "run_id",
                "benchmark_id",
                "item_id",
                "model_id",
                "model_revision",
                "config_hash",
                "prompt_hash",
                "failure_type",
            }
            absent = sorted(required_presence.difference(row))
            if absent:
                raise PackageValidationError(
                    f"prediction line {line_number} missing fields: {absent}"
                )
            if row["benchmark_id"] != manifest["benchmark_id"]:
                raise PackageValidationError("mixed benchmark rows")
            if row["config_hash"] != manifest["config_hash"]:
                raise PackageValidationError("mixed configuration rows")
            key = (str(row["benchmark_id"]), str(row["model_id"]), str(row["item_id"]))
            if key in seen:
                raise PackageValidationError(f"duplicate prediction identity: {key}")
            seen.add(key)
            rows.append(row)
    if not rows:
        raise PackageValidationError("predictions.jsonl contains no rows")
    model_revisions = {
        str(model["model_id"]): str(model.get("revision", model.get("model_revision", "")))
        for model in manifest["models"]
    }
    for row in rows:
        expected_revision = model_revisions.get(str(row["model_id"]))
        if expected_revision is None:
            raise PackageValidationError(f"undeclared model in predictions: {row['model_id']}")
        if str(row["model_revision"]) != expected_revision:
            raise PackageValidationError(f"mixed model revision for {row['model_id']}")
    return {
        "status": "pass",
        "run_id": manifest["run_id"],
        "benchmark_id": manifest["benchmark_id"],
        "config_hash": manifest["config_hash"],
        "row_count": len(rows),
        "verified_files": verified,
        "completion_state": manifest["completion_state"],
        "failure_state": manifest["failure_state"],
    }


def create_deterministic_run_zip(
    run_dir: str | Path,
    zip_path: str | Path,
) -> str:
    root = Path(run_dir).resolve()
    destination = Path(zip_path).resolve()
    validate_run_directory(root)
    files = sorted(path for path in root.rglob("*") if path.is_file())
    _validate_package_members(root, files)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            for path in files:
                relative = path.relative_to(root).as_posix()
                info = zipfile.ZipInfo(relative, date_time=(2000, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        _validate_zip_members(temporary, [path.relative_to(root).as_posix() for path in files])
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return sha256_file(destination)


def validate_zip_archive(path: str | Path) -> dict[str, Any]:
    archive_path = Path(path)
    if not archive_path.is_file():
        raise PackageValidationError(f"ZIP does not exist: {archive_path}")
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if names != sorted(names) or len(names) != len(set(names)):
            raise PackageValidationError("ZIP members must be unique and sorted")
        for name in names:
            _validate_relative_member(name)
            if name.lower().endswith(".zip"):
                raise PackageValidationError(f"nested archive is forbidden: {name}")
    return {
        "status": "pass",
        "zip_path": str(archive_path),
        "zip_sha256": sha256_file(archive_path),
        "members": names,
    }


def _validate_package_members(root: Path, files: Iterable[Path]) -> None:
    for path in files:
        relative = path.relative_to(root).as_posix()
        _validate_relative_member(relative)
        if relative.lower().endswith(".zip"):
            raise PackageValidationError(f"nested archive is forbidden: {relative}")
        if ".tmp" in path.name or path.name.startswith("."):
            raise PackageValidationError(f"temporary or hidden file is forbidden: {relative}")


def _validate_relative_member(name: str) -> None:
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise PackageValidationError(f"unsafe archive member: {name}")
    folded_parts = {part.casefold() for part in relative.parts}
    if folded_parts.intersection(_FORBIDDEN_MEMBER_PARTS):
        raise PackageValidationError(f"forbidden package member: {name}")
    if any(_SECRET_NAME.search(part) for part in relative.parts):
        raise PackageValidationError(f"secret-like package member: {name}")


def _validate_zip_members(path: Path, expected: list[str]) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != expected:
            raise PackageValidationError(
                f"deterministic member list mismatch: expected {expected}, got {names}"
            )
        bad = archive.testzip()
        if bad is not None:
            raise PackageValidationError(f"ZIP CRC validation failed for {bad}")
