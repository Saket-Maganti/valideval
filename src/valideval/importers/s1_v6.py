from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from valideval.execution.config import (
    discover_repository_root,
    load_run_config,
    semantic_config_hash,
)
from valideval.execution.models import load_panel_config
from valideval.execution.packaging import (
    PackageValidationError,
    validate_run_directory,
    validate_zip_archive,
)

S1_SMOKE_ACCEPTED = "S1_SMOKE_ACCEPTED"
S1_SMOKE_ACCEPTED_WITH_RECORDED_MODEL_FAILURES = "S1_SMOKE_ACCEPTED_WITH_RECORDED_MODEL_FAILURES"
S1_SMOKE_REQUIRES_RERUN = "S1_SMOKE_REQUIRES_RERUN"
S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH = "S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH"
S1_SMOKE_REJECTED_DATA_INTEGRITY = "S1_SMOKE_REJECTED_DATA_INTEGRITY"
S1_SMOKE_REJECTED_EXTRACTION_FAILURE = "S1_SMOKE_REJECTED_EXTRACTION_FAILURE"
S1_SMOKE_REJECTED_INSUFFICIENT_COVERAGE = "S1_SMOKE_REJECTED_INSUFFICIENT_COVERAGE"


class S1AcceptanceError(ValueError):
    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status


def accept_s1_smoke_v6(
    input_directory: str | Path,
    *,
    repository_root: str | Path | None = None,
    output_root: str | Path | None = None,
    minimum_extraction_reliability: float = 0.95,
) -> dict[str, Any]:
    source = Path(input_directory).resolve()
    root = (
        Path(repository_root).resolve()
        if repository_root
        else discover_repository_root(Path(__file__))
    )
    if not source.is_dir():
        return _result(S1_SMOKE_REQUIRES_RERUN, problems=[f"input directory missing: {source}"])
    if not 0 < minimum_extraction_reliability <= 1:
        raise ValueError("minimum_extraction_reliability must be in (0, 1]")
    archives_by_benchmark: dict[str, list[Path]] = {}
    for benchmark in ("mmlu", "gsm8k", "bbh"):
        archives_by_benchmark[benchmark] = sorted(source.glob(f"valideval_v6_s1_{benchmark}_*.zip"))
    missing = [benchmark for benchmark, paths in archives_by_benchmark.items() if not paths]
    duplicates = [benchmark for benchmark, paths in archives_by_benchmark.items() if len(paths) > 1]
    if missing:
        return _result(
            S1_SMOKE_REQUIRES_RERUN,
            problems=[f"missing archive for {benchmark}" for benchmark in missing],
        )
    if duplicates:
        return _result(
            S1_SMOKE_REJECTED_DATA_INTEGRITY,
            problems=[f"multiple candidate archives for {benchmark}" for benchmark in duplicates],
        )

    expected_commit = _resolve_final_tag(root)
    if expected_commit is None:
        return _result(
            S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH,
            problems=["final V6 source tag is not resolvable"],
        )
    receipts: list[dict[str, Any]] = []
    any_failed_models = False
    try:
        with tempfile.TemporaryDirectory(prefix="valideval-s1-v6-import-") as temp_name:
            temp_root = Path(temp_name)
            for benchmark in ("mmlu", "gsm8k", "bbh"):
                archive = archives_by_benchmark[benchmark][0]
                extraction = temp_root / benchmark
                extraction.mkdir()
                validate_zip_archive(archive)
                _safe_extract(archive, extraction)
                receipt = _validate_one_run(
                    extraction,
                    benchmark=benchmark,
                    repository_root=root,
                    expected_commit=expected_commit,
                    minimum_extraction_reliability=minimum_extraction_reliability,
                )
                receipts.append(receipt)
                any_failed_models = any_failed_models or bool(receipt["failed_models"])
                if output_root is not None:
                    destination = Path(output_root).resolve() / benchmark
                    _atomic_copy_directory(extraction, destination)
            if output_root is not None:
                receipt_path = Path(output_root).resolve() / "s1_acceptance_receipt_v6.json"
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(
                    json.dumps(
                        {
                            "schema_version": "6.0",
                            "status": (
                                S1_SMOKE_ACCEPTED_WITH_RECORDED_MODEL_FAILURES
                                if any_failed_models
                                else S1_SMOKE_ACCEPTED
                            ),
                            "evidence_class": "ENGINEERING_ONLY",
                            "source_commit": expected_commit,
                            "benchmarks": receipts,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
    except S1AcceptanceError as exc:
        return _result(exc.status, problems=[str(exc)], benchmarks=receipts)
    except (PackageValidationError, zipfile.BadZipFile, OSError, ValueError) as exc:
        return _result(
            S1_SMOKE_REJECTED_DATA_INTEGRITY,
            problems=[str(exc)],
            benchmarks=receipts,
        )
    return _result(
        (
            S1_SMOKE_ACCEPTED_WITH_RECORDED_MODEL_FAILURES
            if any_failed_models
            else S1_SMOKE_ACCEPTED
        ),
        source_commit=expected_commit,
        benchmarks=receipts,
        output_root=str(Path(output_root).resolve()) if output_root else None,
    )


def _validate_one_run(
    run_dir: Path,
    *,
    benchmark: str,
    repository_root: Path,
    expected_commit: str,
    minimum_extraction_reliability: float,
) -> dict[str, Any]:
    config = load_run_config(
        repository_root / f"configs/runs/{benchmark}_s1_v6.yaml",
        repository_root=repository_root,
    )
    validation = validate_run_directory(
        run_dir,
        expected_benchmark=benchmark,
        expected_config_hash=semantic_config_hash(config),
    )
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    models_payload = json.loads((run_dir / "models.json").read_text(encoding="utf-8"))
    contract = json.loads((run_dir / "benchmark_contract.json").read_text(encoding="utf-8"))
    subset = json.loads((repository_root / config.subset_manifest).read_text(encoding="utf-8"))
    panel = load_panel_config(repository_root / config.panel_config)
    if manifest.get("study_id") != "study-c-s1-v6":
        raise S1AcceptanceError(S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH, "unexpected study_id")
    if manifest.get("evidence_state") != "ENGINEERING_ONLY":
        raise S1AcceptanceError(
            S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH,
            f"{benchmark} run is not labeled ENGINEERING_ONLY",
        )
    if manifest.get("source_commit") != expected_commit:
        raise S1AcceptanceError(
            S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH,
            f"{benchmark} source commit does not match the final V6 tag",
        )
    if contract.get("dataset_revision") != _load_yaml_value(
        repository_root / config.benchmark_contract, "dataset_revision"
    ):
        raise S1AcceptanceError(
            S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH,
            f"{benchmark} dataset revision mismatch",
        )
    if contract.get("prompt_hash") != manifest.get("prompt_hash"):
        raise S1AcceptanceError(
            S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH,
            f"{benchmark} prompt hash mismatch",
        )
    if models_payload.get("evidence_class") != "ENGINEERING_ONLY":
        raise S1AcceptanceError(
            S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH,
            f"{benchmark} evidence class is not ENGINEERING_ONLY",
        )
    expected_models = {
        str(model["canonical_model_id"]): str(model["revision"]) for model in panel["models"]
    }
    observed_models = {
        str(model["model_id"]): str(model["revision"]) for model in models_payload["models"]
    }
    if observed_models != expected_models:
        raise S1AcceptanceError(
            S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH,
            f"{benchmark} exact five-model registry mismatch",
        )
    expected_item_ids = {str(item["item_id"]) for item in subset["items"]}
    rows = [
        json.loads(line)
        for line in (run_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_model: dict[str, set[str]] = defaultdict(set)
    success_count = 0
    extraction_attempt_count = 0
    failure_types: Counter[str] = Counter()
    for row in rows:
        by_model[str(row["model_id"])].add(str(row["item_id"]))
        failure_types[str(row["failure_type"])] += 1
        if row["generation_status"] == "success":
            extraction_attempt_count += 1
            if row["extraction_status"] == "success":
                success_count += 1
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
        raise S1AcceptanceError(
            S1_SMOKE_REJECTED_INSUFFICIENT_COVERAGE,
            f"{benchmark} has undeclared missing models: {undeclared_missing}",
        )
    for model_id, item_ids in by_model.items():
        if item_ids != expected_item_ids:
            raise S1AcceptanceError(
                S1_SMOKE_REJECTED_INSUFFICIENT_COVERAGE,
                f"{benchmark}/{model_id} item coverage mismatch",
            )
    reliability = success_count / extraction_attempt_count if extraction_attempt_count else 0.0
    if reliability < minimum_extraction_reliability:
        raise S1AcceptanceError(
            S1_SMOKE_REJECTED_EXTRACTION_FAILURE,
            f"{benchmark} extraction reliability {reliability:.6f} is below "
            f"{minimum_extraction_reliability:.6f}",
        )
    return {
        "benchmark_id": benchmark,
        "run_id": validation["run_id"],
        "config_hash": validation["config_hash"],
        "row_count": len(rows),
        "expected_item_count": len(expected_item_ids),
        "failed_models": failed_models,
        "failure_types": dict(sorted(failure_types.items())),
        "extraction_reliability": reliability,
        "archive_evidence_class": "ENGINEERING_ONLY",
    }


def _safe_extract(archive_path: Path, destination: Path) -> None:
    root = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            target = (root / info.filename).resolve()
            if not target.is_relative_to(root):
                raise PackageValidationError(f"ZIP member leaves extraction root: {info.filename}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)


def _atomic_copy_directory(source: Path, destination: Path) -> None:
    if destination.exists():
        raise S1AcceptanceError(
            S1_SMOKE_REJECTED_DATA_INTEGRITY,
            f"import destination already exists: {destination}",
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.importing")
    if temporary.exists():
        shutil.rmtree(temporary)
    shutil.copytree(source, temporary)
    os.replace(temporary, destination)


def _resolve_final_tag(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "valideval-v6-controlled-gpu-smoke-ready^{commit}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _load_yaml_value(path: Path, key: str) -> Any:
    import yaml

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return payload[key]


def _safe_task_id(model_id: str) -> str:
    return "model-" + "".join(
        character if character.isalnum() or character in "._-" else "_" for character in model_id
    )


def _result(status: str, **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": "6.0",
        "status": status,
        "evidence_class": "ENGINEERING_ONLY",
        **payload,
    }
