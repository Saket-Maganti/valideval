from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

from valideval.execution.config import discover_repository_root, load_run_config
from valideval.execution.config_v7_2 import V7_2_CANONICAL_SOURCE_REF
from valideval.execution.manifest import NON_EVIDENCE_FIXTURE, read_json, sha256_file
from valideval.execution.models import load_panel_config
from valideval.importers.ingest_v7 import IngestV7Error, ingest_and_analyze_v7

S1_V7_2_ACCEPTED = "S1_V7_2_ACCEPTED"
S1_V7_2_ACCEPTED_WITH_RECORDED_MODEL_FAILURES = (
    "S1_V7_2_ACCEPTED_WITH_RECORDED_MODEL_FAILURES"
)
S1_V7_2_REQUIRES_RERUN = "S1_V7_2_REQUIRES_RERUN"
S1_V7_2_REJECTED_PROVENANCE = "S1_V7_2_REJECTED_PROVENANCE"
S1_V7_2_REJECTED_IDENTITY = "S1_V7_2_REJECTED_IDENTITY"
S1_V7_2_REJECTED_COVERAGE = "S1_V7_2_REJECTED_COVERAGE"
S1_V7_2_REJECTED_EXTRACTION = "S1_V7_2_REJECTED_EXTRACTION"
S1_V7_2_REJECTED_CONFIG = "S1_V7_2_REJECTED_CONFIG"

_BENCHMARKS = ("mmlu", "gsm8k", "bbh")
_ACCEPTED = {
    S1_V7_2_ACCEPTED,
    S1_V7_2_ACCEPTED_WITH_RECORDED_MODEL_FAILURES,
}


class S1V72AcceptanceError(ValueError):
    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status


def accept_s1_v7_2(
    input_directory: str | Path,
    *,
    repository_root: str | Path | None = None,
    output_root: str | Path | None = None,
    minimum_extraction_reliability: float = 0.95,
    expected_source_commit: str | None = None,
    allow_non_evidence_fixture: bool = False,
) -> dict[str, Any]:
    """Accept exactly one canonical V7.2 S1 package per frozen benchmark.

    The public path accepts only ``ENGINEERING_ONLY`` Kaggle results pinned to the
    final tag. ``allow_non_evidence_fixture`` exists solely for offline integration
    tests; fixture acceptance never advances the real S1 evidence state.
    """

    source = Path(input_directory).resolve()
    root = (
        Path(repository_root).resolve()
        if repository_root
        else discover_repository_root(Path(__file__))
    )
    if not source.is_dir():
        return _result(S1_V7_2_REQUIRES_RERUN, problems=[f"input directory missing: {source}"])
    if not 0 < minimum_extraction_reliability <= 1:
        raise ValueError("minimum_extraction_reliability must be in (0, 1]")

    archives = {
        benchmark: sorted(source.glob(f"valideval_v7_2_s1_{benchmark}_*.zip"))
        for benchmark in _BENCHMARKS
    }
    missing = [benchmark for benchmark, paths in archives.items() if not paths]
    duplicates = [benchmark for benchmark, paths in archives.items() if len(paths) > 1]
    unexpected = sorted(
        path.name
        for path in source.glob("valideval_v7_2_s1_*.zip")
        if path not in {candidate for paths in archives.values() for candidate in paths}
    )
    if missing:
        return _result(
            S1_V7_2_REQUIRES_RERUN,
            problems=[f"missing archive for {benchmark}" for benchmark in missing],
        )
    if duplicates or unexpected:
        problems = [f"multiple candidate archives for {benchmark}" for benchmark in duplicates]
        problems.extend(f"unexpected S1 archive: {name}" for name in unexpected)
        return _result(S1_V7_2_REJECTED_IDENTITY, problems=problems)

    expected_commit = expected_source_commit or _resolve_final_tag(root)
    if expected_commit is None:
        return _result(
            S1_V7_2_REJECTED_PROVENANCE,
            problems=[f"final source tag is not resolvable: {V7_2_CANONICAL_SOURCE_REF}"],
        )
    if len(expected_commit) != 40:
        return _result(
            S1_V7_2_REJECTED_PROVENANCE,
            problems=["expected source commit must be a full Git commit SHA"],
        )

    receipts: list[dict[str, Any]] = []
    fixture_only = False
    try:
        with tempfile.TemporaryDirectory(prefix="valideval-s1-v7-2-validate-") as temp_name:
            import_root = Path(temp_name) / "imported"
            for benchmark in _BENCHMARKS:
                archive = archives[benchmark][0]
                try:
                    ingest = ingest_and_analyze_v7(
                        archive,
                        output_root=import_root,
                        expected_source_commit=expected_commit,
                    )
                except IngestV7Error as exc:
                    raise S1V72AcceptanceError(_classify_ingest_error(str(exc)), str(exc)) from exc
                run_dir = Path(str(ingest["destination"]))
                receipt = _validate_one_run(
                    run_dir,
                    benchmark=benchmark,
                    archive_sha256=sha256_file(archive),
                    repository_root=root,
                    expected_commit=expected_commit,
                    minimum_extraction_reliability=minimum_extraction_reliability,
                    allow_non_evidence_fixture=allow_non_evidence_fixture,
                )
                fixture_only = fixture_only or bool(receipt["fixture_only"])
                receipts.append(receipt)

        any_failures = any(receipt["failed_models"] for receipt in receipts) or any(
            receipt["failure_types"] != {"SUCCESS": receipt["row_count"]}
            for receipt in receipts
        )
        status = (
            S1_V7_2_ACCEPTED_WITH_RECORDED_MODEL_FAILURES
            if any_failures
            else S1_V7_2_ACCEPTED
        )
        accepted_payload = {
            "schema_version": "valideval.s1-acceptance.v7.2",
            "status": status,
            "source_ref": V7_2_CANONICAL_SOURCE_REF,
            "source_commit": expected_commit,
            "fixture_only": fixture_only,
            "authorization_updated": not fixture_only,
            "benchmarks": receipts,
            "health": _health_summary(receipts, any_failures=any_failures),
        }
        if output_root is not None:
            destination = Path(output_root).resolve()
            _write_accepted_import(
                destination,
                archives=archives,
                expected_commit=expected_commit,
                payload=accepted_payload,
            )
            accepted_payload["output_root"] = str(destination)
        return accepted_payload
    except S1V72AcceptanceError as exc:
        return _result(exc.status, problems=[str(exc)], benchmarks=receipts)
    except (OSError, ValueError) as exc:
        return _result(S1_V7_2_REJECTED_IDENTITY, problems=[str(exc)], benchmarks=receipts)


def _validate_one_run(
    run_dir: Path,
    *,
    benchmark: str,
    archive_sha256: str,
    repository_root: Path,
    expected_commit: str,
    minimum_extraction_reliability: float,
    allow_non_evidence_fixture: bool,
) -> dict[str, Any]:
    manifest = read_json(run_dir / "run_manifest.json")
    models_payload = read_json(run_dir / "models.json")
    contract = read_json(run_dir / "benchmark_contract.json")
    snapshot = yaml.safe_load((run_dir / "config_snapshot.yaml").read_text(encoding="utf-8"))
    if not all(isinstance(value, dict) for value in (manifest, models_payload, contract, snapshot)):
        raise S1V72AcceptanceError(S1_V7_2_REJECTED_CONFIG, "package metadata must be objects")

    production = load_run_config(
        repository_root / f"configs/runs_v7_2/{benchmark}_s1_v7_2.yaml",
        repository_root=repository_root,
    )
    if manifest.get("benchmark_id") != benchmark:
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_IDENTITY, f"{benchmark}: archive contains another benchmark"
        )
    if manifest.get("study_id") != "study-c-s1-v7-2":
        raise S1V72AcceptanceError(S1_V7_2_REJECTED_CONFIG, f"{benchmark}: unexpected study_id")
    if manifest.get("config_class") != "s1_engineering_smoke_v7_2":
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_CONFIG, f"{benchmark}: unexpected config class"
        )
    if snapshot.get("schema_version") != "7.2" or snapshot.get("stage") != "S1":
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_CONFIG, f"{benchmark}: config snapshot is not native V7.2 S1"
        )
    if snapshot.get("required_source_ref") != V7_2_CANONICAL_SOURCE_REF:
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_PROVENANCE, f"{benchmark}: wrong required source ref"
        )
    if manifest.get("actual_source_commit") != expected_commit or not manifest.get("source_match"):
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_PROVENANCE, f"{benchmark}: wrong source commit"
        )

    evidence_state = str(manifest.get("evidence_state"))
    fixture_only = evidence_state == NON_EVIDENCE_FIXTURE
    if fixture_only and not allow_non_evidence_fixture:
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_CONFIG, f"{benchmark}: non-evidence fixtures are not accepted by CLI"
        )
    if evidence_state not in {"ENGINEERING_ONLY", NON_EVIDENCE_FIXTURE}:
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_CONFIG, f"{benchmark}: invalid S1 evidence state"
        )
    _validate_snapshot(snapshot, production.model_dump(mode="json"), fixture_only=fixture_only)

    expected_contract = yaml.safe_load(
        (repository_root / production.benchmark_contract).read_text(encoding="utf-8")
    )
    if contract.get("dataset_revision") != expected_contract.get("dataset_revision"):
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_PROVENANCE, f"{benchmark}: dataset revision mismatch"
        )
    if contract.get("prompt_hash") != manifest.get("prompt_hash"):
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_CONFIG, f"{benchmark}: prompt hash mismatch"
        )
    if manifest.get("subset_manifest_sha256") != production.subset_manifest_sha256:
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_IDENTITY, f"{benchmark}: subset identity mismatch"
        )

    panel = load_panel_config(repository_root / production.panel_config)
    expected_models = {
        str(model["canonical_model_id"]): {
            "revision": str(model["revision"]),
            "family": str(model["family"]),
        }
        for model in panel["models"]
    }
    observed_models = {
        str(model["model_id"]): {
            "revision": str(model["revision"]),
            "family": str(model["family"]),
        }
        for model in models_payload.get("models", [])
    }
    if observed_models != expected_models or len(observed_models) != 5:
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_IDENTITY, f"{benchmark}: exact five-checkpoint panel mismatch"
        )

    subset = read_json(repository_root / production.subset_manifest)
    expected_items = {str(item["item_id"]) for item in subset["items"]}
    if len(expected_items) != 50:
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_CONFIG, f"{benchmark}: frozen S1 subset is not 50 items"
        )
    rows = [
        json.loads(line)
        for line in (run_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_model: dict[str, set[str]] = defaultdict(set)
    failure_types: Counter[str] = Counter()
    parse_attempts = 0
    parsed = 0
    for row in rows:
        by_model[str(row["model_id"])].add(str(row["item_id"]))
        failure_types[str(row["failure_type"])] += 1
        if row.get("generation_status") == "success":
            parse_attempts += 1
            parsed += int(row.get("extraction_status") == "success")
    failed_task_ids = set(manifest.get("allowed_failed_models", []))
    failed_models = sorted(
        model_id for model_id in expected_models if _safe_task_id(model_id) in failed_task_ids
    )
    undeclared_missing = sorted(
        model_id
        for model_id in expected_models
        if model_id not in by_model and model_id not in failed_models
    )
    if undeclared_missing:
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_COVERAGE,
            f"{benchmark}: undeclared missing models: {undeclared_missing}",
        )
    for model_id, item_ids in by_model.items():
        if item_ids != expected_items:
            raise S1V72AcceptanceError(
                S1_V7_2_REJECTED_COVERAGE, f"{benchmark}/{model_id}: item coverage mismatch"
            )
    reliability = parsed / parse_attempts if parse_attempts else 0.0
    if reliability < minimum_extraction_reliability:
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_EXTRACTION,
            f"{benchmark}: extraction reliability {reliability:.6f} is below "
            f"{minimum_extraction_reliability:.6f}",
        )
    return {
        "benchmark_id": benchmark,
        "run_id": manifest["run_id"],
        "config_hash": manifest["config_hash"],
        "archive_sha256": archive_sha256,
        "row_count": len(rows),
        "expected_item_count": len(expected_items),
        "failed_models": failed_models,
        "failure_types": dict(sorted(failure_types.items())),
        "extraction_reliability": reliability,
        "fixture_only": fixture_only,
    }


def _validate_snapshot(
    observed: dict[str, Any], expected: dict[str, Any], *, fixture_only: bool
) -> None:
    allowed_fixture_changes = {"mode", "evidence_class", "expected_source_commit", "execution"}
    for key, value in expected.items():
        if fixture_only and key in allowed_fixture_changes:
            continue
        if observed.get(key) != value:
            raise S1V72AcceptanceError(
                S1_V7_2_REJECTED_CONFIG, f"frozen config mismatch at {key}"
            )
    if fixture_only:
        observed_execution = dict(observed.get("execution", {}))
        expected_execution = dict(expected.get("execution", {}))
        allowed_execution_changes = {
            "backend",
            "use_processes",
            "minimum_free_disk_gb",
            "model_download_margin_gb",
        }
        for key, value in expected_execution.items():
            if key not in allowed_execution_changes and observed_execution.get(key) != value:
                raise S1V72AcceptanceError(
                    S1_V7_2_REJECTED_CONFIG, f"fixture config mismatch at execution.{key}"
                )


def _write_accepted_import(
    destination: Path,
    *,
    archives: dict[str, list[Path]],
    expected_commit: str,
    payload: dict[str, Any],
) -> None:
    if destination.exists():
        raise S1V72AcceptanceError(
            S1_V7_2_REJECTED_IDENTITY, f"import destination already exists: {destination}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.accepting-", dir=destination.parent))
    try:
        for benchmark in _BENCHMARKS:
            receipt = ingest_and_analyze_v7(
                archives[benchmark][0],
                output_root=staging / benchmark,
                expected_source_commit=expected_commit,
            )
            payload_benchmark = next(
                item for item in payload["benchmarks"] if item["benchmark_id"] == benchmark
            )
            payload_benchmark["import_destination"] = str(
                destination / benchmark / str(receipt["run_id"])
            )
        (staging / "s1_acceptance_receipt_v7_2.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if not payload["fixture_only"]:
            (staging / "study_c_authorization_v7_2.json").write_text(
                json.dumps(
                    {
                        "schema_version": "valideval.study-c-authorization.v7.2",
                        "s1": "S1_V7_2_ACCEPTED",
                        "s2": "S2_BLOCKED_PENDING_POST_S1_RECALIBRATION",
                        "s3": "S3_BLOCKED_PENDING_S2",
                        "s4": "S4_BLOCKED_PENDING_S3",
                        "source_commit": expected_commit,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        os.replace(staging, destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _health_summary(receipts: list[dict[str, Any]], *, any_failures: bool) -> dict[str, Any]:
    reliability = min(float(receipt["extraction_reliability"]) for receipt in receipts)
    return {
        "status": (
            "S1_HEALTHY_WITH_RECORDED_FAILURES" if any_failures else "S1_HEALTHY"
        ),
        "minimum_extraction_reliability": reliability,
        "peak_gpu_memory_bytes": None,
        "download_volume_bytes": None,
        "runtime_recalibration_required": True,
        "note": (
            "Peak GPU memory and download volume remain unreported unless the production "
            "worker records them; missing metrics are never imputed."
        ),
    }


def _classify_ingest_error(message: str) -> str:
    folded = message.casefold()
    if "source" in folded or "provenance" in folded:
        return S1_V7_2_REJECTED_PROVENANCE
    if "config" in folded or "schema" in folded or "manifest" in folded:
        return S1_V7_2_REJECTED_CONFIG
    if "coverage" in folded or "no rows" in folded:
        return S1_V7_2_REJECTED_COVERAGE
    if "parsed" in folded or "extraction" in folded:
        return S1_V7_2_REJECTED_EXTRACTION
    return S1_V7_2_REJECTED_IDENTITY


def _resolve_final_tag(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", f"{V7_2_CANONICAL_SOURCE_REF}^{{commit}}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _safe_task_id(model_id: str) -> str:
    return "model-" + "".join(
        character if character.isalnum() or character in "._-" else "_" for character in model_id
    )


def _result(status: str, **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": "valideval.s1-acceptance.v7.2",
        "status": status,
        "accepted": status in _ACCEPTED,
        **payload,
    }
