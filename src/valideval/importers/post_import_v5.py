"""Fail-closed, receipt-derived V5 post-import routing plans.

This module never runs a scientific analysis as a side effect.  It verifies the
canonical receipt, imported run manifest, configuration hash, and checksummed
files, then emits only the analysis commands whose explicit prerequisites pass.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from valideval.cross_benchmark.gates import evaluate_cross_benchmark_gate
from valideval.execution.manifest import (
    NON_EVIDENCE_FIXTURE,
    atomic_write_json,
    atomic_write_text,
    compute_configuration_hash,
    load_config_snapshot,
    validate_file_checksums,
    validate_run_manifest,
)
from valideval.importers.kaggle_v5 import IMPORTER_READY_VERDICT, IMPORTER_SCHEMA_VERSION

POST_IMPORT_SCHEMA_VERSION = "valideval.post_import_plan.v5"
POST_IMPORT_READY = "POST_IMPORT_V5_PLAN_READY"
POST_IMPORT_FIXTURE_READY = "POST_IMPORT_V5_PLAN_READY_NON_EVIDENCE_FIXTURE"
POST_IMPORT_PARTIALLY_BLOCKED = "POST_IMPORT_V5_PLAN_PARTIALLY_BLOCKED"
POST_IMPORT_BLOCKED_INVALID_RECEIPT = "POST_IMPORT_V5_BLOCKED_RECEIPT_INVALID"

ROUTE_READY = "ROUTE_READY"
ROUTE_READY_FIXTURE = "ROUTE_READY_NON_EVIDENCE_FIXTURE"
ROUTE_BLOCKED = "ROUTE_BLOCKED"
ROUTE_NOT_APPLICABLE = "ROUTE_NOT_APPLICABLE"

ROUTE_IDS = (
    "feasibility",
    "extraction_reliability",
    "coverage",
    "model_accuracy",
    "subject_subtask_analysis",
    "ranking_materiality",
    "measurement_models",
    "cross_benchmark_eligibility",
    "paper_artifact_generation",
)

FORBIDDEN_V4_ROUTES = frozenset(
    {
        "diagnostic_family_ablation",
        "result_consistency_ablation",
        "post-import-analysis",
        "cross-benchmark-analysis",
    }
)

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class PostImportV5ValidationError(ValueError):
    """Raised internally when a receipt no longer proves a valid V5 import."""


def build_post_import_plan_v5(
    receipt_paths: Sequence[str | Path],
    *,
    output_dir: str | Path,
    minimum_extraction_reliability: float = 0.95,
    minimum_coverage: float = 1.0,
) -> dict[str, Any]:
    """Validate V5 import receipts and write a dry-run routing plan.

    A valid plan is not an analysis result.  Commands are recommendations only;
    callers must invoke them explicitly after reviewing the plan.
    """

    if not receipt_paths:
        raise ValueError("at least one V5 import receipt is required")
    if not 0.0 <= minimum_extraction_reliability <= 1.0:
        raise ValueError("minimum_extraction_reliability must be in [0, 1]")
    if not 0.0 < minimum_coverage <= 1.0:
        raise ValueError("minimum_coverage must be in (0, 1]")

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    inspected: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    normalized_paths = sorted({Path(path).resolve() for path in receipt_paths})
    for path in normalized_paths:
        try:
            inspected.append(_inspect_receipt(path))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            invalid.append({"receipt_path": str(path), "error": str(exc)})

    if invalid:
        payload = {
            "schema_version": POST_IMPORT_SCHEMA_VERSION,
            "status": "blocked",
            "final_verdict": POST_IMPORT_BLOCKED_INVALID_RECEIPT,
            "dry_run": True,
            "receipt_count": len(normalized_paths),
            "valid_receipt_count": len(inspected),
            "invalid_receipts": invalid,
            "runs": [],
            "routes": [],
            "recommended_commands": [],
            "excluded_routes": _excluded_routes(),
            "exact_next_command": _plan_command(normalized_paths, destination),
        }
        _write_plan(destination, payload)
        return payload

    runs = [
        _public_run_summary(run, minimum_extraction_reliability, minimum_coverage)
        for run in inspected
    ]
    per_run_routes = [
        route
        for run in inspected
        for route in _build_run_routes(
            run,
            destination=destination,
            minimum_extraction_reliability=minimum_extraction_reliability,
            minimum_coverage=minimum_coverage,
        )
    ]
    cross_route = _build_cross_benchmark_route(inspected, destination)
    routes = [*per_run_routes, cross_route]
    paper_route = _build_paper_route(inspected, routes)
    routes.append(paper_route)
    _assert_no_forbidden_v4_routes(routes)

    ready_commands = [
        str(route["recommended_command"])
        for route in routes
        if route["status"] in {ROUTE_READY, ROUTE_READY_FIXTURE}
        and route.get("recommended_command")
    ]
    any_fixture = any(
        run["manifest"]["evidence_state"] == NON_EVIDENCE_FIXTURE for run in inspected
    )
    any_blocked = any(route["status"] == ROUTE_BLOCKED for route in routes)
    if any_fixture:
        verdict = POST_IMPORT_FIXTURE_READY
    elif any_blocked:
        verdict = POST_IMPORT_PARTIALLY_BLOCKED
    else:
        verdict = POST_IMPORT_READY
    payload = {
        "schema_version": POST_IMPORT_SCHEMA_VERSION,
        "status": "plan_ready",
        "final_verdict": verdict,
        "dry_run": True,
        "receipt_count": len(inspected),
        "valid_receipt_count": len(inspected),
        "thresholds": {
            "minimum_extraction_reliability": minimum_extraction_reliability,
            "minimum_coverage": minimum_coverage,
        },
        "runs": runs,
        "routes": routes,
        "recommended_commands": ready_commands,
        "excluded_routes": _excluded_routes(),
        "claim_limits": [
            "A routing plan is not an analysis result.",
            "NON_EVIDENCE_FIXTURE routes validate plumbing only.",
            "No V4 diagnostic-family ablation is permitted because that artifact is contradicted.",
            "Paper artifacts remain blocked until required analysis artifacts are supplied.",
        ],
        "exact_next_command": ready_commands[0] if ready_commands else None,
    }
    _write_plan(destination, payload)
    return payload


def _inspect_receipt(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PostImportV5ValidationError(f"receipt does not exist: {path}")
    receipt = _read_json_object(path, "receipt")
    if receipt.get("schema_version") != IMPORTER_SCHEMA_VERSION:
        raise PostImportV5ValidationError("receipt schema_version is not V5")
    if receipt.get("final_verdict") != IMPORTER_READY_VERDICT:
        raise PostImportV5ValidationError("receipt does not carry the V5 importer verdict")
    if receipt.get("status") not in {"imported", "already_imported"}:
        raise PostImportV5ValidationError("receipt status is not an accepted import state")
    source_digest = str(receipt.get("source_zip_sha256", "")).lower()
    if not _HEX_64.fullmatch(source_digest):
        raise PostImportV5ValidationError("receipt source_zip_sha256 is invalid")

    import_dir = Path(str(receipt.get("import_dir", ""))).resolve()
    if not import_dir.is_dir():
        raise PostImportV5ValidationError(f"receipt import_dir does not exist: {import_dir}")
    if path.resolve() != (import_dir / "import_receipt_v5.json").resolve():
        raise PostImportV5ValidationError(
            "router requires the canonical import_receipt_v5.json inside import_dir"
        )
    manifest_path = import_dir / "run_manifest.json"
    manifest_raw = _read_json_object(manifest_path, "run manifest")
    manifest = validate_run_manifest(
        manifest_raw,
        expected_study_id=str(receipt.get("study_id", "")),
        expected_run_id=str(receipt.get("run_id", "")),
        expected_benchmark_id=str(receipt.get("benchmark_id", "")),
        expected_config_hash=str(receipt.get("config_hash", "")),
        require_complete=True,
    )
    for field in ("config_class", "evidence_state"):
        if str(receipt.get(field, "")) != str(manifest.get(field, "")):
            raise PostImportV5ValidationError(f"receipt/manifest {field} mismatch")

    config = load_config_snapshot(import_dir / "config_snapshot.yaml")
    if compute_configuration_hash(config) != manifest["config_hash"]:
        raise PostImportV5ValidationError("config_snapshot hash no longer matches manifest")
    validate_file_checksums(import_dir, manifest["file_checksums"])

    prediction = _mapping(receipt.get("prediction_summary"), "prediction_summary")
    shard = _mapping(receipt.get("shard_summary"), "shard_summary")
    matrix = _mapping(receipt.get("matrix_summary"), "matrix_summary")
    eligibility = _mapping(
        receipt.get("cross_benchmark_eligibility"),
        "cross_benchmark_eligibility",
    )
    if prediction.get("status") != "pass" or shard.get("status") != "pass":
        raise PostImportV5ValidationError("receipt prediction or shard validation is not pass")
    if matrix.get("status") != "pass":
        raise PostImportV5ValidationError("receipt matrix validation is not pass")
    if int(prediction.get("row_count", -1)) != int(manifest["expected_prediction_rows"]):
        raise PostImportV5ValidationError("receipt row count differs from run manifest")
    if int(prediction.get("item_count", -1)) != int(manifest["item_count"]):
        raise PostImportV5ValidationError("receipt item count differs from run manifest")
    if int(matrix.get("item_count", -1)) != int(manifest["item_count"]):
        raise PostImportV5ValidationError("matrix item count differs from run manifest")
    if int(matrix.get("model_count", -1)) != len(manifest["models"]):
        raise PostImportV5ValidationError("matrix model count differs from run manifest")
    if eligibility.get("data_integrity") != "pass":
        raise PostImportV5ValidationError("cross-benchmark eligibility integrity is not pass")

    contract = _read_json_object(import_dir / "benchmark_contract.json", "benchmark contract")
    if str(contract.get("benchmark_id", "")) != str(manifest["benchmark_id"]):
        raise PostImportV5ValidationError("benchmark contract identity differs from manifest")
    required_paths = {
        "matrix_path": import_dir / "matrix.csv",
        "predictions_path": import_dir / "predictions.jsonl",
        "contract_path": import_dir / "benchmark_contract.json",
        "manifest_path": manifest_path,
    }
    missing = [name for name, value in required_paths.items() if not value.is_file()]
    if missing:
        raise PostImportV5ValidationError(f"imported run is missing router inputs: {missing}")
    subject_map_path = import_dir / "item_subject_map.csv"
    return {
        "receipt_path": path,
        "import_dir": import_dir,
        "receipt": receipt,
        "manifest": manifest,
        "contract": contract,
        "subject_map_path": subject_map_path if subject_map_path.is_file() else None,
        **required_paths,
    }


def _public_run_summary(
    run: Mapping[str, Any],
    minimum_extraction_reliability: float,
    minimum_coverage: float,
) -> dict[str, Any]:
    receipt = run["receipt"]
    manifest = run["manifest"]
    prediction = receipt["prediction_summary"]
    expected_rows = int(manifest["expected_prediction_rows"])
    observed_rows = int(prediction["row_count"])
    expected_items = int(manifest["item_count"])
    usable_items = int(prediction["usable_item_count"])
    return {
        "study_id": manifest["study_id"],
        "run_id": manifest["run_id"],
        "benchmark_id": manifest["benchmark_id"],
        "evidence_state": manifest["evidence_state"],
        "config_hash": manifest["config_hash"],
        "config_class": manifest["config_class"],
        "receipt_path": str(run["receipt_path"]),
        "manifest_path": str(run["manifest_path"]),
        "matrix_path": str(run["matrix_path"]),
        "predictions_path": str(run["predictions_path"]),
        "model_count": int(prediction["model_count"]),
        "independent_family_count": len(prediction["model_families"]),
        "expected_items": expected_items,
        "usable_items": usable_items,
        "item_coverage": usable_items / expected_items if expected_items else 0.0,
        "row_coverage": observed_rows / expected_rows if expected_rows else 0.0,
        "extraction_reliability": float(prediction["extraction_reliability"]),
        "extraction_gate_passed": (
            float(prediction["extraction_reliability"]) >= minimum_extraction_reliability
        ),
        "coverage_gate_passed": (
            usable_items / expected_items >= minimum_coverage
            and observed_rows / expected_rows >= minimum_coverage
        )
        if expected_items and expected_rows
        else False,
    }


def _build_run_routes(
    run: Mapping[str, Any],
    *,
    destination: Path,
    minimum_extraction_reliability: float,
    minimum_coverage: float,
) -> list[dict[str, Any]]:
    summary = _public_run_summary(run, minimum_extraction_reliability, minimum_coverage)
    fixture = summary["evidence_state"] == NON_EVIDENCE_FIXTURE
    ready_status = ROUTE_READY_FIXTURE if fixture else ROUTE_READY
    benchmark = str(summary["benchmark_id"])
    run_id = str(summary["run_id"])
    matrix = Path(str(summary["matrix_path"]))
    route_command = _stage_plan_command(Path(run["receipt_path"]), destination)
    base = {
        "benchmark_id": benchmark,
        "run_id": run_id,
        "evidence_state": summary["evidence_state"],
    }
    routes: list[dict[str, Any]] = []

    feasibility_min_models = 2 if fixture else 8
    feasibility_min_items = 4 if fixture else 100
    feasibility_ready = (
        int(summary["model_count"]) >= feasibility_min_models
        and int(summary["usable_items"]) >= feasibility_min_items
    )

    routes.append(
        _route(
            "feasibility",
            ready_status if feasibility_ready else ROUTE_BLOCKED,
            base,
            reasons=[
                "Canonical V5 receipt, manifest, config hash, and file checksums passed.",
                f"This route requires at least {feasibility_min_models} models and "
                f"{feasibility_min_items} usable items.",
            ],
            command=(
                f"python3 -m valideval panel-validity --matrix {_q(matrix)} "
                f"--output {_q(destination / run_id / 'panel_validity_v5.json')} "
                f"--min-models {feasibility_min_models} --min-items {feasibility_min_items} "
                "--strict"
            ),
        )
    )
    extraction_passed = bool(summary["extraction_gate_passed"])
    routes.append(
        _route(
            "extraction_reliability",
            ready_status if extraction_passed else ROUTE_BLOCKED,
            base,
            reasons=[
                f"Observed extraction reliability={summary['extraction_reliability']:.6f}; "
                f"required>={minimum_extraction_reliability:.6f}."
            ],
            command=f"{route_command} --stage extraction_reliability",
        )
    )
    coverage_passed = bool(summary["coverage_gate_passed"])
    routes.append(
        _route(
            "coverage",
            ready_status if coverage_passed else ROUTE_BLOCKED,
            base,
            reasons=[
                f"Item coverage={summary['item_coverage']:.6f}; "
                f"row coverage={summary['row_coverage']:.6f}; required>={minimum_coverage:.6f}."
            ],
            command=f"{route_command} --stage coverage",
        )
    )
    dependent_ready = extraction_passed and coverage_passed
    routes.append(
        _route(
            "model_accuracy",
            ready_status if dependent_ready else ROUTE_BLOCKED,
            base,
            reasons=["Requires passed extraction and coverage gates."],
            command=f"{route_command} --stage model_accuracy",
        )
    )
    has_subtasks = bool(run["contract"].get("subtasks") or run["contract"].get("tasks"))
    routes.append(
        _route(
            "subject_subtask_analysis",
            ready_status if dependent_ready and has_subtasks else ROUTE_BLOCKED,
            base,
            reasons=["Requires passed extraction/coverage gates and contract task metadata."],
            command=f"{route_command} --stage subject_subtask_analysis",
        )
    )

    subject_map_path = run.get("subject_map_path")
    subject_arg = f" --subject-map {_q(subject_map_path)}" if subject_map_path else ""
    matrix_subjects_available = bool(subject_map_path) or _matrix_has_subject_prefix(matrix)
    rank_command = (
        f"python3 scripts/run_mmlu_rank_materiality_v5.py --matrix {_q(matrix)} "
        f"--output {_q(destination / run_id / 'rank_materiality_v5')}{subject_arg}"
    )
    rank_ready = (
        benchmark == "mmlu"
        and dependent_ready
        and not fixture
        and int(summary["model_count"]) >= 8
        and int(summary["usable_items"]) >= 100
        and matrix_subjects_available
    )
    rank_reasons = [
        "Requires MMLU, non-fixture evidence, passed extraction/coverage, at least 8 models, and at least 100 usable items."
    ]
    if benchmark != "mmlu":
        rank_reasons.append("The current V5 rank-materiality runner is MMLU-specific.")
    if not matrix_subjects_available:
        rank_reasons.append(
            "The matrix lacks subject::item_id columns and no item_subject_map.csv was imported."
        )
    routes.append(
        _route(
            "ranking_materiality",
            ROUTE_READY if rank_ready else ROUTE_BLOCKED,
            base,
            reasons=rank_reasons,
            command=rank_command,
        )
    )

    measurement_command = (
        f"python3 -m valideval fit-irt --matrix {_q(matrix)} --model 2pl "
        f"--output {_q(destination / run_id / 'measurement_v5')} "
        "--min-models 8 --min-items 100 --strict"
    )
    measurement_ready = (
        dependent_ready
        and not fixture
        and int(summary["model_count"]) >= 8
        and int(summary["independent_family_count"]) >= 3
        and int(summary["usable_items"]) >= 100
    )
    routes.append(
        _route(
            "measurement_models",
            ROUTE_READY if measurement_ready else ROUTE_BLOCKED,
            base,
            reasons=[
                "Requires non-fixture evidence, passed extraction/coverage, at least 8 models, 3 independent families, and 100 usable items."
            ],
            command=measurement_command,
        )
    )
    return routes


def _build_cross_benchmark_route(
    runs: Sequence[Mapping[str, Any]],
    destination: Path,
) -> dict[str, Any]:
    inputs: dict[str, dict[str, Any]] = {}
    duplicate_benchmarks: list[str] = []
    for run in runs:
        receipt = run["receipt"]
        benchmark = str(receipt["benchmark_id"])
        if benchmark in inputs:
            duplicate_benchmarks.append(benchmark)
            continue
        eligibility = receipt["cross_benchmark_eligibility"]
        inputs[benchmark] = {
            "model_ids": eligibility["exact_model_ids"],
            "model_family_by_id": eligibility["model_family_by_id"],
            "config_class": eligibility["config_class"],
            "usable_items": eligibility["usable_items"],
            "extraction_reliability": eligibility["extraction_reliability"],
            "data_integrity": eligibility["data_integrity"],
            "evidence_state": eligibility["evidence_state"],
            "study_id": eligibility["study_id"],
        }
    gate = evaluate_cross_benchmark_gate(inputs)
    receipt_args = " ".join(f"--receipt {_q(run['receipt_path'])}" for run in runs)
    command = (
        f"python3 -m valideval.importers.post_import_v5 {receipt_args} "
        f"--output {_q(destination)} --stage cross_benchmark_eligibility"
    )
    fixture = any(run["manifest"]["evidence_state"] == NON_EVIDENCE_FIXTURE for run in runs)
    exact_ready = gate["status"] == "CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL"
    status = (
        ROUTE_READY_FIXTURE
        if exact_ready and fixture
        else ROUTE_READY
        if exact_ready
        else ROUTE_BLOCKED
    )
    reasons = list(gate.get("reasons", []))
    if duplicate_benchmarks:
        status = ROUTE_BLOCKED
        reasons.append(
            f"Multiple receipts supplied for benchmarks: {sorted(set(duplicate_benchmarks))}."
        )
    return _route(
        "cross_benchmark_eligibility",
        status,
        {
            "benchmark_id": "multi",
            "run_id": "multi",
            "evidence_state": gate.get("evidence_state", "RESULT_REQUIRED"),
            "gate_status": gate["status"],
            "gate": gate,
        },
        reasons=reasons,
        command=command,
    )


def _build_paper_route(
    runs: Sequence[Mapping[str, Any]],
    routes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    scientific = all(run["manifest"]["evidence_state"] != NON_EVIDENCE_FIXTURE for run in runs)
    prerequisite_ids = {
        "model_accuracy",
        "subject_subtask_analysis",
        "ranking_materiality",
        "measurement_models",
        "cross_benchmark_eligibility",
    }
    prerequisites_ready = all(
        route["status"] == ROUTE_READY for route in routes if route["stage_id"] in prerequisite_ids
    )
    # A plan does not prove that recommended commands were executed or that their
    # artifacts passed. Paper generation therefore remains blocked until a later
    # artifact-aware router invocation is implemented.
    reasons = [
        "Paper assets require completed, validated analysis artifacts; a command recommendation is not completion."
    ]
    if not scientific:
        reasons.append("NON_EVIDENCE_FIXTURE artifacts cannot populate empirical paper claims.")
    if not prerequisites_ready:
        reasons.append("One or more prerequisite analysis routes are blocked.")
    return _route(
        "paper_artifact_generation",
        ROUTE_BLOCKED,
        {
            "benchmark_id": "multi",
            "run_id": "multi",
            "evidence_state": "RESULT_REQUIRED",
        },
        reasons=reasons,
        command="python3 scripts/build_paper_v5_assets.py",
    )


def _route(
    stage_id: str,
    status: str,
    base: Mapping[str, Any],
    *,
    reasons: Sequence[str],
    command: str,
) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "status": status,
        **dict(base),
        "prerequisite_reasons": list(reasons),
        "recommended_command": command if status in {ROUTE_READY, ROUTE_READY_FIXTURE} else None,
        "blocked_command": command if status == ROUTE_BLOCKED else None,
    }


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PostImportV5ValidationError(f"receipt {label} must be a mapping")
    return dict(value)


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PostImportV5ValidationError(f"{label} must contain a JSON object: {path}")
    return value


def _matrix_has_subject_prefix(path: Path) -> bool:
    with path.open("r", encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle), [])
    item_columns = header[1:]
    return bool(item_columns) and all(
        "::" in item_id
        and bool(item_id.split("::", 1)[0].strip())
        and bool(item_id.split("::", 1)[1].strip())
        for item_id in item_columns
    )


def _excluded_routes() -> list[dict[str, str]]:
    return [
        {
            "route_id": "v4_diagnostic_family_ablation",
            "status": "CONTRADICTED",
            "reason": "The legacy V4 table reused accuracy as seven diagnostic families and is retired.",
            "replacement": "artifact-derived V5 rank, measurement, and diagnostic-specific analyses only",
        }
    ]


def _assert_no_forbidden_v4_routes(routes: Sequence[Mapping[str, Any]]) -> None:
    serialized = json.dumps(list(routes), sort_keys=True).casefold()
    offenders = sorted(token for token in FORBIDDEN_V4_ROUTES if token in serialized)
    if offenders:
        raise RuntimeError(f"V5 router emitted forbidden V4 route tokens: {offenders}")


def _q(value: str | Path) -> str:
    return shlex.quote(str(value))


def _stage_plan_command(receipt: Path, destination: Path) -> str:
    return (
        f"python3 -m valideval.importers.post_import_v5 --receipt {_q(receipt)} "
        f"--output {_q(destination)}"
    )


def _plan_command(receipts: Sequence[Path], destination: Path) -> str:
    receipt_args = " ".join(f"--receipt {_q(path)}" for path in receipts)
    return (
        f"python3 -m valideval.importers.post_import_v5 {receipt_args} --output {_q(destination)}"
    )


def _write_plan(destination: Path, payload: Mapping[str, Any]) -> None:
    atomic_write_json(destination / "post_import_plan_v5.json", dict(payload))
    atomic_write_text(destination / "post_import_plan_v5.md", _render_plan(payload))


def _render_plan(payload: Mapping[str, Any]) -> str:
    lines = [
        "# ValidEval V5 Post-Import Plan",
        "",
        f"- Verdict: `{payload['final_verdict']}`",
        f"- Dry run: `{payload['dry_run']}`",
        f"- Valid receipts: {payload['valid_receipt_count']}/{payload['receipt_count']}",
        "",
    ]
    if payload.get("invalid_receipts"):
        lines.extend(["## Invalid receipts", ""])
        for row in payload["invalid_receipts"]:
            lines.append(f"- `{row['receipt_path']}`: {row['error']}")
        lines.append("")
    if payload.get("routes"):
        lines.extend(
            [
                "## Routes",
                "",
                "| Run | Benchmark | Stage | Status | Command |",
                "|---|---|---|---|---|",
            ]
        )
        for route in payload["routes"]:
            command = route.get("recommended_command") or route.get("blocked_command") or ""
            lines.append(
                f"| `{route['run_id']}` | `{route['benchmark_id']}` | "
                f"`{route['stage_id']}` | `{route['status']}` | `{command}` |"
            )
        lines.append("")
    lines.extend(
        [
            "## Retired route",
            "",
            "The contradicted V4 diagnostic-family ablation is never invoked by this router.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/post_import_v5"))
    parser.add_argument("--minimum-extraction-reliability", type=float, default=0.95)
    parser.add_argument("--minimum-coverage", type=float, default=1.0)
    parser.add_argument("--stage", choices=ROUTE_IDS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_post_import_plan_v5(
        args.receipt,
        output_dir=args.output,
        minimum_extraction_reliability=args.minimum_extraction_reliability,
        minimum_coverage=args.minimum_coverage,
    )
    printable: dict[str, Any] = payload
    if args.stage:
        printable = {
            "schema_version": payload["schema_version"],
            "final_verdict": payload["final_verdict"],
            "dry_run": True,
            "selected_stage": args.stage,
            "routes": [route for route in payload["routes"] if route["stage_id"] == args.stage],
        }
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 2 if payload["final_verdict"] == POST_IMPORT_BLOCKED_INVALID_RECEIPT else 0


if __name__ == "__main__":
    raise SystemExit(main())
