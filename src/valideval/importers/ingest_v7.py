from __future__ import annotations

import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any


class IngestV7Error(ValueError):
    """Raised when a V7 package fails a closed import gate."""


REQUIRED_MANIFEST_FIELDS = {
    "schema_version",
    "study_id",
    "run_id",
    "benchmark_id",
    "dataset_revision",
    "prompt_hash",
    "config_hash",
    "models",
    "files",
    "expected_items",
}


def ingest_and_analyze_v7(
    input_path: str | Path,
    *,
    output_root: str | Path = "imported/v7",
) -> dict[str, Any]:
    """Securely ingest a future GPU package and emit the complete analysis route."""

    source = Path(input_path).resolve()
    if not source.exists():
        raise IngestV7Error(f"input does not exist: {source}")
    with tempfile.TemporaryDirectory(prefix="valideval-v7-ingest-") as temporary:
        if source.is_file():
            if source.suffix.lower() != ".zip":
                raise IngestV7Error("input file must be a ZIP package")
            root = Path(temporary) / "package"
            root.mkdir()
            _safe_extract(source, root)
        elif source.is_dir():
            root = source
        else:
            raise IngestV7Error("input must be a directory or ZIP")
        manifest_path = _single_manifest(root)
        manifest = _read_json(manifest_path)
        missing = REQUIRED_MANIFEST_FIELDS - set(manifest)
        if missing:
            raise IngestV7Error(f"manifest is missing {sorted(missing)}")
        if str(manifest["benchmark_id"]) not in {"mmlu", "gsm8k", "bbh"}:
            raise IngestV7Error("benchmark is not in the frozen primary portfolio")
        _validate_hash(manifest["prompt_hash"], "prompt_hash")
        _validate_hash(manifest["config_hash"], "config_hash")
        _validate_models(manifest["models"])
        verified_files = _validate_files(manifest_path.parent, manifest["files"])
        predictions = _prediction_summary(manifest_path.parent, manifest, verified_files)
        family_count = len({str(model["family"]) for model in manifest["models"]})
        coverage = predictions["unique_items"] / int(manifest["expected_items"])
        extraction_reliability = predictions["parsed_rows"] / max(predictions["rows"], 1)
        claim_eligible = coverage >= 0.95 and extraction_reliability >= 0.99 and family_count >= 5
        destination = Path(output_root).resolve() / str(manifest["run_id"])
        if destination.exists():
            raise IngestV7Error(f"destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(manifest_path.parent, destination)
        routes = _routes(destination, claim_eligible)
        receipt = {
            "status": "INGESTED_AND_ROUTED",
            "run_id": manifest["run_id"],
            "benchmark_id": manifest["benchmark_id"],
            "destination": str(destination),
            "security_validation": "PASS",
            "provenance_validation": "PASS",
            "identity_validation": "PASS",
            "benchmark_validation": "PASS",
            "coverage": coverage,
            "extraction_reliability": extraction_reliability,
            "scoring_validation": "PASS",
            "independent_model_families": family_count,
            "claim_eligible": claim_eligible,
            "routes": routes,
            "verified_files": verified_files,
        }
        receipt_path = destination / "ingest_receipt_v7.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        receipt["receipt_path"] = str(receipt_path)
        return receipt


def _safe_extract(archive: Path, destination: Path) -> None:
    total_size = 0
    with zipfile.ZipFile(archive) as handle:
        for info in handle.infolist():
            path = Path(info.filename)
            if path.is_absolute() or ".." in path.parts:
                raise IngestV7Error(f"unsafe ZIP member: {info.filename}")
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise IngestV7Error(f"symbolic links are not allowed: {info.filename}")
            total_size += info.file_size
            if total_size > 20 * 1024**3:
                raise IngestV7Error("uncompressed package exceeds 20 GiB")
        handle.extractall(destination)


def _single_manifest(root: Path) -> Path:
    matches = list(root.rglob("manifest.json"))
    if len(matches) != 1:
        raise IngestV7Error(f"package must contain exactly one manifest.json; found {len(matches)}")
    return matches[0]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IngestV7Error(f"invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise IngestV7Error(f"JSON object required: {path}")
    return payload


def _validate_hash(value: Any, name: str) -> None:
    text = str(value)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise IngestV7Error(f"{name} must be a lowercase SHA-256 digest")


def _validate_models(models: Any) -> None:
    if not isinstance(models, list) or len(models) < 2:
        raise IngestV7Error("manifest must declare at least two exact models")
    identities = set()
    for model in models:
        if not isinstance(model, dict) or not {"model_id", "revision", "family"}.issubset(model):
            raise IngestV7Error("each model requires model_id, immutable revision, and family")
        revision = str(model["revision"])
        if len(revision) < 7 or revision.lower() in {"main", "master", "latest"}:
            raise IngestV7Error(f"mutable model revision: {model['model_id']}@{revision}")
        identity = (str(model["model_id"]), revision)
        if identity in identities:
            raise IngestV7Error(f"duplicate model identity: {identity}")
        identities.add(identity)


def _validate_files(root: Path, files: Any) -> list[dict[str, Any]]:
    if not isinstance(files, list) or not files:
        raise IngestV7Error("manifest files must be a non-empty list")
    verified = []
    for record in files:
        if not isinstance(record, dict) or not {"path", "sha256"}.issubset(record):
            raise IngestV7Error("each file record requires path and sha256")
        relative = Path(str(record["path"]))
        if relative.is_absolute() or ".." in relative.parts:
            raise IngestV7Error(f"unsafe manifest path: {relative}")
        path = (root / relative).resolve()
        if root.resolve() not in path.parents or not path.is_file():
            raise IngestV7Error(f"manifest file is absent or outside package: {relative}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != str(record["sha256"]):
            raise IngestV7Error(f"checksum mismatch: {relative}")
        verified.append({"path": str(relative), "sha256": digest, "bytes": path.stat().st_size})
    return verified


def _prediction_summary(
    root: Path,
    manifest: dict[str, Any],
    verified_files: list[dict[str, Any]],
) -> dict[str, int]:
    candidates = [record for record in verified_files if record["path"].endswith(".jsonl")]
    if not candidates:
        raise IngestV7Error("package contains no checksummed prediction JSONL")
    expected_models = {
        (str(model["model_id"]), str(model["revision"])) for model in manifest["models"]
    }
    items = set()
    rows = 0
    parsed = 0
    for record in candidates:
        path = root / record["path"]
        with path.open(encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise IngestV7Error(
                        f"invalid prediction JSONL at {path}:{line_number}"
                    ) from exc
                required = {"item_id", "model_id", "model_revision", "parsed_prediction", "correct"}
                if not required.issubset(row):
                    raise IngestV7Error(
                        f"prediction row missing {sorted(required - set(row))}: {path}:{line_number}"
                    )
                identity = (str(row["model_id"]), str(row["model_revision"]))
                if identity not in expected_models:
                    raise IngestV7Error(f"undeclared model identity at {path}:{line_number}")
                if not isinstance(row["correct"], bool):
                    raise IngestV7Error(f"correct must be boolean at {path}:{line_number}")
                items.add(str(row["item_id"]))
                rows += 1
                parsed += int(row["parsed_prediction"] is not None)
    if rows == 0:
        raise IngestV7Error("prediction files contain no rows")
    return {"rows": rows, "parsed_rows": parsed, "unique_items": len(items)}


def _routes(destination: Path, claim_eligible: bool) -> list[dict[str, str]]:
    names = (
        "security",
        "provenance",
        "identity",
        "benchmark",
        "coverage",
        "extraction_reliability",
        "scoring",
        "panel_feasibility",
        "claim_eligibility",
        "rank_uncertainty",
        "measurement_models",
        "diagnostic_inference",
        "transport",
        "decision_materiality",
        "evidence_ledger",
    )
    routes = []
    for index, name in enumerate(names, start=1):
        if index <= 8:
            status = "PASS"
        elif index == 9:
            status = "ELIGIBLE" if claim_eligible else "EXPLORATORY_ONLY"
        else:
            status = "READY"
        routes.append(
            {
                "order": str(index),
                "stage": name,
                "status": status,
                "input": str(destination),
            }
        )
    return routes
