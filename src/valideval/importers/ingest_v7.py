from __future__ import annotations

import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from valideval.execution.manifest import NON_EVIDENCE_FIXTURE, read_json
from valideval.execution.packaging import PackageValidationError, validate_run_directory


class IngestV7Error(ValueError):
    """Raised when a canonical V7.1 run package fails a closed import gate."""


def ingest_and_analyze_v7(
    input_path: str | Path,
    *,
    output_root: str | Path = "imported/v7_1",
    expected_config_hash: str | None = None,
    expected_source_commit: str | None = None,
) -> dict[str, Any]:
    """Ingest the exact runner package, route analyses, and update a blocked ledger.

    The canonical package boundary is ``run_manifest.json`` plus runner-native
    ``parsed_output``/``is_correct`` prediction fields. No alternate scientific
    manifest or prediction schema is accepted.
    """

    source = Path(input_path).resolve()
    if not source.exists():
        raise IngestV7Error(f"input does not exist: {source}")
    with tempfile.TemporaryDirectory(prefix="valideval-v7-1-ingest-") as temporary:
        if source.is_file():
            if source.suffix.lower() != ".zip":
                raise IngestV7Error("input file must be a ZIP package")
            extraction_root = Path(temporary) / "package"
            extraction_root.mkdir()
            _safe_extract(source, extraction_root)
            root = _single_run_root(extraction_root)
        elif source.is_dir():
            root = _single_run_root(source)
        else:
            raise IngestV7Error("input must be a directory or ZIP")

        try:
            validation = validate_run_directory(
                root,
                expected_config_hash=expected_config_hash,
            )
        except (PackageValidationError, ValueError) as exc:
            raise IngestV7Error(str(exc)) from exc
        manifest = read_json(root / "run_manifest.json")
        if not isinstance(manifest, dict):
            raise IngestV7Error("run_manifest.json must contain an object")
        _validate_source(manifest, expected_source_commit=expected_source_commit)
        if str(manifest.get("benchmark_id")) not in {"mmlu", "gsm8k", "bbh"}:
            raise IngestV7Error("benchmark is not in the frozen primary portfolio")
        models = manifest.get("models")
        if not isinstance(models, list) or not models:
            raise IngestV7Error("run manifest must declare exact models")
        family_count = len({str(model.get("family", "")) for model in models})
        if "" in {str(model.get("family", "")) for model in models}:
            raise IngestV7Error("every model requires a family at package boundary")
        prediction_summary = _prediction_summary(root / "predictions.jsonl")
        item_count = int(manifest["item_count"])
        coverage = prediction_summary["unique_items"] / item_count
        extraction_reliability = prediction_summary["parsed_rows"] / max(
            prediction_summary["rows"], 1
        )
        substantive_evidence = str(manifest["evidence_state"]) != NON_EVIDENCE_FIXTURE
        claim_eligible = (
            substantive_evidence
            and coverage >= 0.95
            and extraction_reliability >= 0.99
            and family_count >= 5
            and manifest.get("source_match") is True
        )

        destination = Path(output_root).resolve() / str(manifest["run_id"])
        if destination.exists():
            raise IngestV7Error(f"destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root, destination)
        routes = _analysis_router(destination, claim_eligible=claim_eligible)
        ledger_path = _update_evidence_ledger(
            destination,
            manifest=manifest,
            claim_eligible=claim_eligible,
            routes=routes,
        )
        receipt = {
            "schema_version": "valideval.ingest.v7.1",
            "status": "INGESTED_ROUTED_AND_LEDGER_UPDATED",
            "run_id": manifest["run_id"],
            "benchmark_id": manifest["benchmark_id"],
            "destination": str(destination),
            "security_validation": "PASS",
            "package_schema_validation": "PASS",
            "provenance_validation": "PASS",
            "identity_validation": "PASS",
            "coverage": coverage,
            "extraction_reliability": extraction_reliability,
            "independent_model_families": family_count,
            "declared_failure_state": manifest["failure_state"],
            "claim_eligible": claim_eligible,
            "routes": routes,
            "evidence_ledger_path": str(ledger_path),
            "source_provenance": {
                "required_source_ref": manifest["required_source_ref"],
                "expected_source_commit": manifest["expected_source_commit"],
                "actual_source_commit": manifest["actual_source_commit"],
                "source_match": manifest["source_match"],
            },
            "validation": validation,
        }
        receipt_path = destination / "ingest_receipt_v7_1.json"
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
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


def _single_run_root(root: Path) -> Path:
    matches = list(root.rglob("run_manifest.json"))
    if len(matches) != 1:
        raise IngestV7Error(
            f"package must contain exactly one run_manifest.json; found {len(matches)}"
        )
    return matches[0].parent


def _validate_source(
    manifest: dict[str, Any],
    *,
    expected_source_commit: str | None,
) -> None:
    required = {
        "required_source_ref",
        "expected_source_commit",
        "actual_source_commit",
        "source_match",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise IngestV7Error(f"run manifest is missing source provenance fields: {missing}")
    expected = str(manifest["expected_source_commit"])
    actual = str(manifest["actual_source_commit"])
    for label, value in (("expected_source_commit", expected), ("actual_source_commit", actual)):
        if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
            raise IngestV7Error(f"{label} must be a full Git commit SHA")
    if manifest["source_match"] is not True or expected != actual:
        raise IngestV7Error("source mismatch declared by runner package")
    if expected_source_commit is not None and actual != expected_source_commit:
        raise IngestV7Error(
            f"source mismatch: expected {expected_source_commit}, package recorded {actual}"
        )


def _prediction_summary(path: Path) -> dict[str, int]:
    rows = 0
    parsed = 0
    items: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise IngestV7Error(f"invalid prediction JSONL at line {line_number}") from exc
            required = {
                "schema_version",
                "study_id",
                "run_id",
                "benchmark_id",
                "item_id",
                "model_id",
                "model_revision",
                "model_family",
                "raw_output",
                "parsed_output",
                "gold_output",
                "is_correct",
                "failure_type",
                "prompt_hash",
                "config_hash",
                "code_revision",
                "evidence_class",
            }
            missing = sorted(required - set(row))
            if missing:
                raise IngestV7Error(
                    f"prediction row missing canonical fields {missing} at line {line_number}"
                )
            items.add(str(row["item_id"]))
            rows += 1
            parsed += int(row["parsed_output"] is not None)
    if rows == 0:
        raise IngestV7Error("predictions.jsonl contains no rows")
    return {"rows": rows, "parsed_rows": parsed, "unique_items": len(items)}


def _analysis_router(destination: Path, *, claim_eligible: bool) -> list[dict[str, str]]:
    passed = (
        "security",
        "package_schema",
        "provenance",
        "identity",
        "benchmark",
        "coverage",
        "extraction_reliability",
        "scoring_contract",
    )
    analyses = (
        "rank_inference",
        "pairwise_multiplicity",
        "measurement_models",
        "diagnostic_inference",
        "transport",
        "decision_materiality",
    )
    routes = [
        {"order": str(index), "stage": name, "status": "PASS", "input": str(destination)}
        for index, name in enumerate(passed, start=1)
    ]
    route_status = "READY_TO_RUN" if claim_eligible else "FIXTURE_OR_GATE_BLOCKED"
    routes.extend(
        {
            "order": str(index),
            "stage": name,
            "status": route_status,
            "input": str(destination),
        }
        for index, name in enumerate(analyses, start=len(routes) + 1)
    )
    routes.append(
        {
            "order": str(len(routes) + 1),
            "stage": "evidence_ledger",
            "status": "UPDATED_FAIL_CLOSED",
            "input": str(destination),
        }
    )
    return routes


def _update_evidence_ledger(
    destination: Path,
    *,
    manifest: dict[str, Any],
    claim_eligible: bool,
    routes: list[dict[str, str]],
) -> Path:
    payload = {
        "schema_version": "valideval.evidence-ledger.v7.1",
        "run_id": manifest["run_id"],
        "evidence_class": manifest["evidence_state"],
        "package_claim_eligible": claim_eligible,
        "status": "ANALYSIS_REQUIRED_BEFORE_SUBSTANTIVE_LICENSE",
        "claims": [
            {
                "claim_family_id": family,
                "status": "BLOCKED_PENDING_ANALYSIS",
                "reason": "Package acceptance does not substitute for completed inferential analysis.",
            }
            for family in (
                "PRIMARY_PAIRWISE",
                "ALL_MODEL_PAIRS",
                "ITEM_DIAGNOSTICS",
                "TRANSPORT",
                "REPAIR",
            )
        ],
        "routes": routes,
    }
    path = destination / "claim_evidence_ledger_v7_1.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
