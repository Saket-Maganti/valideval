from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.benchmarks.base import get_benchmark
from valideval.benchmarks.gpqa_inputs import GPQA_VARIANTS
from valideval.config import load_yaml
from valideval.forensics.provenance import stable_hash
from valideval.io.cache import matrix_metadata_path, matrix_path, prediction_path
from valideval.models.panel import load_panel
from valideval.schemas import utc_now

DEFAULT_REQUIRED_VARIANTS = ["full"]
DEFAULT_RESULT_HINT_DIAGNOSTICS = ["baselines", "answer_distribution", "data_forensics"]


def run_doctor(
    *,
    benchmark_id: str = "toy_mcq",
    panel_id: str = "mock",
    local_path: str | Path | None = None,
    cache_root: str | Path = "cache",
    results_root: str | Path = "results",
    reportcards_root: str | Path = "reportcards",
    config_path: str | Path = "configs/default.yaml",
    required_variants: list[str] | None = None,
    required_diagnostics: list[str] | None = None,
) -> dict[str, Any]:
    """Return a metadata-only readiness report for local audit workflows.

    The report intentionally avoids prompt bodies, answers, raw item text, and raw outputs. It is
    designed to be safe to paste into issue threads or readiness notes for restricted benchmarks.
    """

    checks: list[dict[str, Any]] = []
    commands: list[str] = []
    cache_root_path = Path(cache_root)
    results_root_path = Path(results_root)
    reportcards_root_path = Path(reportcards_root)
    effective_local_path = _effective_local_path(benchmark_id, local_path)
    variants = _required_variants(benchmark_id, required_variants)

    benchmark = None
    panel = None

    config_check = _yaml_check("config", Path(config_path), required=True)
    _add_check(checks, commands, config_check)

    try:
        benchmark = get_benchmark(benchmark_id, local_path=effective_local_path)
        items = benchmark.load_items()
        variants_available = benchmark.available_prompt_variants()
        metadata = getattr(benchmark.construct_spec, "metadata", {}) or {}
        _add_check(
            checks,
            commands,
            {
                "name": "benchmark_load",
                "status": "pass",
                "severity": "required",
                "message": "Benchmark loaded without exposing raw item text.",
                "details": {
                    "benchmark_id": benchmark.benchmark_id,
                    "claimed_construct": benchmark.claimed_construct,
                    "item_count": len(items),
                    "item_ids_hash": stable_hash([item.item_id for item in items]),
                    "construct_tag_count": len(
                        sorted({tag for item in items for tag in item.construct_tags})
                    ),
                    "prompt_variants": variants_available,
                    "artifact_scope": metadata.get("artifact_scope"),
                    "local_path": str(effective_local_path) if effective_local_path else None,
                },
            },
        )
    except Exception as exc:
        next_commands = _benchmark_next_commands(benchmark_id)
        _add_check(
            checks,
            commands,
            {
                "name": "benchmark_load",
                "status": "blocked",
                "severity": "required",
                "message": "Benchmark could not be loaded from local inputs.",
                "details": {
                    "benchmark_id": benchmark_id,
                    "local_path": str(effective_local_path) if effective_local_path else None,
                    "error": str(exc),
                },
                "next_commands": next_commands,
            },
        )

    try:
        panel = load_panel(panel_id)
        model_ids = panel.model_ids
        _add_check(
            checks,
            commands,
            {
                "name": "panel_load",
                "status": "pass",
                "severity": "required",
                "message": "Panel configuration loaded.",
                "details": {
                    "panel_id": panel.panel_id,
                    "model_count": len(model_ids),
                    "model_ids_hash": stable_hash(model_ids),
                    "uses_cached_output_models": panel_id != "mock",
                },
            },
        )
    except Exception as exc:
        _add_check(
            checks,
            commands,
            {
                "name": "panel_load",
                "status": "blocked",
                "severity": "required",
                "message": "Panel could not be loaded.",
                "details": {"panel_id": panel_id, "error": str(exc)},
                "next_commands": ["python3 -m valideval check-panel --panel gpqa_open_local"],
            },
        )

    if panel_id != "mock":
        panel_config = Path("configs/panels") / f"{panel_id}.yaml"
        _add_check(checks, commands, _yaml_check("panel_config", panel_config, required=True))

    if benchmark is not None and panel is not None:
        _add_check(
            checks,
            commands,
            _cache_check(
                benchmark.benchmark_id,
                panel.panel_id,
                cache_root_path,
                variants,
            ),
        )
        _add_check(
            checks,
            commands,
            _results_check(
                benchmark.benchmark_id,
                panel.panel_id,
                results_root_path,
                required_diagnostics,
                effective_local_path,
            ),
        )
        _add_check(
            checks,
            commands,
            _report_card_check(
                benchmark.benchmark_id,
                panel.panel_id,
                reportcards_root_path,
                effective_local_path,
            ),
        )
    else:
        _add_check(
            checks,
            commands,
            {
                "name": "artifact_readiness",
                "status": "warning",
                "severity": "recommended",
                "message": "Artifact checks were skipped because benchmark or panel loading failed.",
                "details": {},
            },
        )

    if benchmark_id == "gpqa_diamond":
        for check in _gpqa_checks(
            panel_id=panel_id,
            local_path=effective_local_path,
            cache_root=cache_root_path,
            results_root=results_root_path,
            variants=variants,
        ):
            _add_check(checks, commands, check)

    _add_check(
        checks,
        commands,
        {
            "name": "claim_guardrails",
            "status": "pass",
            "severity": "required",
            "message": "Readiness reporting is scoped to prerequisites and artifacts, not findings.",
            "details": {
                "validity_profile_not_scalar": True,
                "no_paid_api_required": True,
                "raw_item_text_included": False,
                "empirical_results_invented": False,
            },
        },
    )

    return {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "status": _overall_status(checks),
        "benchmark_id": benchmark_id,
        "panel_id": panel_id,
        "offline_safe": True,
        "metadata_only": True,
        "checks": checks,
        "next_commands": _unique(commands),
        "limitations": [
            "Doctor mode is a local readiness and artifact-hygiene report, not a validity finding.",
            "Missing artifacts are reported as missing evidence rather than failed diagnostics.",
            "The report avoids raw item text, prompts, answers, and raw model outputs.",
        ],
    }


def _effective_local_path(benchmark_id: str, local_path: str | Path | None) -> Path | None:
    if local_path is not None:
        return Path(local_path)
    if benchmark_id == "gpqa_diamond":
        default = Path("data/gpqa/gpqa_diamond.jsonl")
        return default if default.exists() else None
    return None


def _required_variants(benchmark_id: str, required_variants: list[str] | None) -> list[str]:
    if required_variants:
        return _unique(required_variants)
    if benchmark_id == "gpqa_diamond":
        return list(GPQA_VARIANTS)
    return list(DEFAULT_REQUIRED_VARIANTS)


def _yaml_check(name: str, path: Path, *, required: bool) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": name,
            "status": "blocked" if required else "warning",
            "severity": "required" if required else "recommended",
            "message": f"YAML file is missing: {path}",
            "details": {"path": str(path)},
        }
    try:
        data = load_yaml(path)
    except Exception as exc:
        return {
            "name": name,
            "status": "blocked" if required else "warning",
            "severity": "required" if required else "recommended",
            "message": f"YAML file could not be parsed: {path}",
            "details": {"path": str(path), "error": str(exc)},
        }
    return {
        "name": name,
        "status": "pass",
        "severity": "required" if required else "recommended",
        "message": f"YAML file loaded: {path}",
        "details": {"path": str(path), "top_level_keys": sorted(data)},
    }


def _cache_check(
    benchmark_id: str,
    panel_id: str,
    cache_root: Path,
    variants: list[str],
) -> dict[str, Any]:
    existing_matrices: list[str] = []
    missing_matrices: list[str] = []
    existing_predictions: list[str] = []
    missing_predictions: list[str] = []
    missing_metadata: list[str] = []
    for variant in variants:
        matrix = matrix_path(cache_root, benchmark_id, panel_id, variant)
        prediction = prediction_path(cache_root, benchmark_id, panel_id, variant)
        metadata = matrix_metadata_path(cache_root, benchmark_id, panel_id, variant)
        (existing_matrices if matrix.exists() else missing_matrices).append(variant)
        (existing_predictions if prediction.exists() else missing_predictions).append(variant)
        if not metadata.exists():
            missing_metadata.append(variant)

    status = "pass" if not missing_matrices else "warning"
    return {
        "name": "cache_artifacts",
        "status": status,
        "severity": "recommended",
        "message": (
            "Required cached matrices are present."
            if status == "pass"
            else "Some cached matrices are missing; cache-only audits would be blocked."
        ),
        "details": {
            "cache_root": str(cache_root),
            "required_variants": variants,
            "existing_matrices": existing_matrices,
            "missing_matrices": missing_matrices,
            "existing_predictions": existing_predictions,
            "missing_predictions": missing_predictions,
            "missing_matrix_metadata": missing_metadata,
        },
        "next_commands": _cache_next_commands(benchmark_id, panel_id, missing_matrices),
    }


def _results_check(
    benchmark_id: str,
    panel_id: str,
    results_root: Path,
    required_diagnostics: list[str] | None,
    local_path: Path | None,
) -> dict[str, Any]:
    output_dir = results_root / benchmark_id / panel_id
    existing_results = sorted(path.stem for path in output_dir.glob("*.json"))
    if required_diagnostics:
        missing = [name for name in required_diagnostics if name not in existing_results]
        return {
            "name": "diagnostic_results",
            "status": "pass" if not missing else "warning",
            "severity": "recommended",
            "message": (
                "Required diagnostic result files are present."
                if not missing
                else "Some requested diagnostic result files are missing."
            ),
            "details": {
                "results_dir": str(output_dir),
                "required_diagnostics": required_diagnostics,
                "existing_results": existing_results,
                "missing_results": missing,
            },
            "next_commands": [
                (
                    "python3 -m valideval audit "
                    f"--benchmark {benchmark_id} --panel {panel_id}"
                    f"{_local_path_arg(local_path)} "
                    f"--diagnostics {' '.join(required_diagnostics)}"
                )
            ]
            if missing
            else [],
        }
    return {
        "name": "diagnostic_results",
        "status": "pass" if existing_results else "warning",
        "severity": "recommended",
        "message": (
            "Diagnostic result files exist."
            if existing_results
            else "No diagnostic result files found yet."
        ),
        "details": {
            "results_dir": str(output_dir),
            "existing_results": existing_results,
            "suggested_minimum_diagnostics": DEFAULT_RESULT_HINT_DIAGNOSTICS,
        },
        "next_commands": [
            (
                "python3 -m valideval audit "
                f"--benchmark {benchmark_id} --panel {panel_id}"
                f"{_local_path_arg(local_path)} --diagnostics all-core"
            )
        ]
        if not existing_results
        else [],
    }


def _report_card_check(
    benchmark_id: str,
    panel_id: str,
    reportcards_root: Path,
    local_path: Path | None,
) -> dict[str, Any]:
    path = reportcards_root / f"{benchmark_id}_{panel_id}.md"
    return {
        "name": "report_card",
        "status": "pass" if path.exists() else "warning",
        "severity": "recommended",
        "message": "Report card exists." if path.exists() else "Report card has not been rendered.",
        "details": {"path": str(path), "exists": path.exists()},
        "next_commands": [
            (
                f"python3 -m valideval report --benchmark {benchmark_id} --panel {panel_id}"
                f"{_local_path_arg(local_path)}"
            )
        ]
        if not path.exists()
        else [],
    }


def _gpqa_checks(
    *,
    panel_id: str,
    local_path: Path | None,
    cache_root: Path,
    results_root: Path,
    variants: list[str],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    item_path = local_path or Path("data/gpqa/gpqa_diamond.jsonl")
    checks.append(
        {
            "name": "gpqa_item_file_presence",
            "status": "pass" if item_path.exists() else "blocked",
            "severity": "required",
            "message": (
                "GPQA item file exists locally."
                if item_path.exists()
                else "GPQA item file is missing; stop at readiness reporting."
            ),
            "details": {"items_path": str(item_path), "exists": item_path.exists()},
            "next_commands": [
                (
                    "python3 -m valideval export-gpqa-diamond "
                    "--source-file data/raw/gpqa_source.csv "
                    "--output data/gpqa/gpqa_diamond.jsonl"
                )
            ]
            if not item_path.exists()
            else [],
        }
    )
    output_root = Path("local_outputs/gpqa")
    variant_outputs = {
        variant: len(list((output_root / variant).glob("*.jsonl")))
        for variant in variants
        if (output_root / variant).exists()
    }
    missing_output_dirs = [variant for variant in variants if not (output_root / variant).exists()]
    checks.append(
        {
            "name": "gpqa_local_outputs",
            "status": "pass" if not missing_output_dirs else "warning",
            "severity": "recommended",
            "message": (
                "Local output directories exist for required variants."
                if not missing_output_dirs
                else "Some local output directories are missing."
            ),
            "details": {
                "local_outputs_root": str(output_root),
                "variant_jsonl_counts": variant_outputs,
                "missing_variant_dirs": missing_output_dirs,
            },
            "next_commands": [
                (
                    "python3 -m valideval generate-outputs --benchmark gpqa_diamond "
                    "--items data/gpqa/gpqa_diamond.jsonl "
                    f"--panel {panel_id} --prompt-variant full "
                    "--output-dir local_outputs/gpqa/full --limit-items 5"
                )
            ]
            if missing_output_dirs
            else [],
        }
    )
    go_no_go = results_root / "gpqa_diamond" / "input_validation" / "go_no_go.json"
    status = "warning"
    details: dict[str, Any] = {"path": str(go_no_go), "exists": go_no_go.exists()}
    if go_no_go.exists():
        try:
            payload = json.loads(go_no_go.read_text(encoding="utf-8"))
            details["go_no_go_status"] = payload.get("status")
            status = "pass" if payload.get("status") == "go" else "warning"
        except (OSError, json.JSONDecodeError) as exc:
            details["error"] = str(exc)
    checks.append(
        {
            "name": "gpqa_go_no_go",
            "status": status,
            "severity": "recommended",
            "message": (
                "GPQA go/no-go artifact is present and reports go."
                if status == "pass"
                else "GPQA go/no-go artifact is missing or not go."
            ),
            "details": details,
            "next_commands": [
                (
                    "python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond "
                    "--items data/gpqa/gpqa_diamond.jsonl "
                    f"--panel {panel_id}"
                )
            ]
            if status != "pass"
            else [],
        }
    )
    full_matrix = matrix_path(cache_root, "gpqa_diamond", panel_id, variants[0])
    checks.append(
        {
            "name": "gpqa_public_content_boundary",
            "status": "pass",
            "severity": "required",
            "message": "Doctor output is metadata-only for GPQA public-report hygiene.",
            "details": {
                "raw_questions_printed": False,
                "raw_model_outputs_printed": False,
                "first_matrix_path": str(full_matrix),
            },
        }
    )
    return checks


def _cache_next_commands(
    benchmark_id: str,
    panel_id: str,
    missing_matrices: list[str],
) -> list[str]:
    if not missing_matrices:
        return []
    if benchmark_id == "gpqa_diamond":
        first = missing_matrices[0]
        return [
            (
                "python3 -m valideval matrix-from-predictions "
                f"--benchmark gpqa_diamond --panel {panel_id} --variant {first}"
            )
        ]
    return [f"python3 -m valideval matrices --benchmark {benchmark_id} --panel {panel_id}"]


def _benchmark_next_commands(benchmark_id: str) -> list[str]:
    if benchmark_id == "gpqa_diamond":
        return [
            (
                "python3 -m valideval validate-benchmark-file "
                "--benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl"
            )
        ]
    if benchmark_id in {"local_jsonl", "mmlu"}:
        return [f"python3 -m valideval audit --benchmark {benchmark_id} --local-path <items.jsonl>"]
    return ["python3 -m valideval toy"]


def _add_check(
    checks: list[dict[str, Any]],
    commands: list[str],
    check: dict[str, Any],
) -> None:
    checks.append(check)
    commands.extend(check.get("next_commands", []))


def _overall_status(checks: list[dict[str, Any]]) -> str:
    if any(check["status"] == "blocked" for check in checks):
        return "blocked"
    if any(check["status"] == "warning" for check in checks):
        return "warning"
    return "pass"


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _local_path_arg(local_path: Path | None) -> str:
    return f" --local-path {local_path}" if local_path else ""
