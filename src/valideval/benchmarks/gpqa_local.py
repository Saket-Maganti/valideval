from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any

from valideval.benchmarks.gpqa import GPQADiamondJSONLBenchmark
from valideval.benchmarks.gpqa_inputs import (
    ARTIFACT_REAL_INPUT_VALIDATION,
    GPQA_VARIANTS,
    validate_gpqa_item_file,
    validation_dir,
)
from valideval.config import load_yaml
from valideval.forensics.provenance import stable_hash
from valideval.io.jsonl import read_jsonl, write_jsonl
from valideval.models.mock import (
    AlwaysA,
    ContextAwareMock,
    FormatFragile,
    KeywordMatcher,
    MajorityLabel,
)
from valideval.models.ollama_client import OllamaRunner
from valideval.schemas import utc_now

GPQA_DATASET_ID = "Idavidrein/gpqa"
GPQA_DATASET_CONFIG = "gpqa_diamond"
GPQA_DATASET_SPLIT = "train"


def export_gpqa_diamond(
    *,
    output_path: str | Path,
    source: str | None = None,
    source_file: str | Path | None = None,
    seed: int = 0,
    results_root: str | Path = "results",
    hf_path: str = GPQA_DATASET_ID,
    hf_name: str = GPQA_DATASET_CONFIG,
    hf_split: str = GPQA_DATASET_SPLIT,
) -> dict[str, Any]:
    if source == "hf":
        records = _load_hf_records(
            path=hf_path,
            name=hf_name,
            split=hf_split,
        )
        source_label = f"hf:{hf_path}:{hf_name}:{hf_split}"
    elif source_file:
        records = _load_source_file(source_file)
        source_label = str(source_file)
    else:
        raise ValueError("Provide --source hf or --source-file for GPQA export.")

    rows = [
        _normalize_gpqa_record(record, index=index, seed=seed)
        for index, record in enumerate(records, start=1)
    ]
    output = Path(output_path)
    write_jsonl(output, rows)
    validation = validate_gpqa_item_file(
        output,
        output_dir=validation_dir(results_root, "gpqa_diamond"),
    )
    report = _export_report(
        rows,
        output_path=output,
        source_label=source_label,
        validation=validation,
    )
    _write_export_report(report, validation_dir(results_root, "gpqa_diamond"))
    return report


def check_panel_readiness(
    *,
    panel_id: str,
    cache_root: str | Path = "cache",
    results_root: str | Path = "results",
    benchmark_id: str = "gpqa_diamond",
) -> dict[str, Any]:
    config_path = Path("configs/panels") / f"{panel_id}.yaml"
    models = _panel_rows(panel_id)
    cached_prediction_variants = [
        variant
        for variant in GPQA_VARIANTS
        if (Path(cache_root) / benchmark_id / panel_id / f"predictions_{variant}.jsonl").exists()
    ]
    cached_matrix_variants = [
        variant
        for variant in GPQA_VARIANTS
        if (Path(cache_root) / benchmark_id / panel_id / f"matrix_{variant}.csv").exists()
    ]
    rows = []
    for row in models:
        model_id = str(row.get("model_id", ""))
        runner = str(row.get("runner", "cached_or_local"))
        cached_variants = _cached_variants_for_model(
            cache_root=cache_root,
            benchmark_id=benchmark_id,
            panel_id=panel_id,
            model_id=model_id,
        )
        availability = _model_availability(model_id, runner, cached_variants)
        rows.append(
            {
                "model_id": model_id,
                "runner": runner,
                "role": row.get("role"),
                "available": availability["available"],
                "availability_status": availability["status"],
                "cached_output_variants": cached_variants,
                "recommended_command": availability["recommended_command"],
            }
        )
    missing = [row for row in rows if not row["available"]]
    available_model_count = len(rows) - len(missing)
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": ARTIFACT_REAL_INPUT_VALIDATION,
        "benchmark_id": benchmark_id,
        "panel_id": panel_id,
        "panel_config": str(config_path),
        "configured_model_count": len(rows),
        "available_model_count": available_model_count,
        "missing_model_count": len(missing),
        "cached_prediction_variants": cached_prediction_variants,
        "cached_matrix_variants": cached_matrix_variants,
        "models": rows,
        "status": "ready" if rows and not missing else "partial_or_blocked",
        "sufficiency": _panel_sufficiency(
            available_model_count=available_model_count,
            cached_prediction_variants=cached_prediction_variants,
            cached_matrix_variants=cached_matrix_variants,
        ),
        "next_commands": _panel_next_commands(panel_id=panel_id, models=rows),
        "warnings": [
            "Panel readiness checks local configuration and cached-output availability only; they do not run benchmark diagnostics."
        ],
    }
    _write_panel_readiness(payload, validation_dir(results_root, benchmark_id))
    return payload


def generate_gpqa_outputs(
    *,
    items_path: str | Path,
    panel_id: str,
    prompt_variant: str,
    output_dir: str | Path,
    limit_items: int | None = None,
    seed: int = 0,
    temperature: float = 0.0,
    overwrite: bool = False,
    dry_run_mock: bool = False,
) -> dict[str, Any]:
    prompt_path = Path("configs/prompts/gpqa") / f"{prompt_variant}.yaml"
    if prompt_variant not in GPQA_VARIANTS and not prompt_path.exists():
        raise ValueError(f"Unknown GPQA prompt variant: {prompt_variant}")
    validation = validate_gpqa_item_file(items_path)
    if not validation["valid"]:
        preview = "; ".join(validation["errors"][:5])
        raise ValueError(f"Cannot generate outputs; GPQA item file failed validation: {preview}")

    benchmark = GPQADiamondJSONLBenchmark(items_path)
    items = benchmark.load_items()
    if limit_items is not None:
        items = items[: max(0, int(limit_items))]
    prompt_hash = benchmark.prompt_template_hash(prompt_variant)
    prompt_config = load_yaml(prompt_path) if prompt_path.exists() else {}
    artifact_scope = (
        "gpqa_exploratory_extraction_compliance"
        if prompt_variant not in GPQA_VARIANTS
        else ARTIFACT_REAL_INPUT_VALIDATION
    )
    models = _generation_models(panel_id, dry_run_mock=dry_run_mock, temperature=temperature)
    if not models:
        raise ValueError(
            f"No local generatable models are configured for panel '{panel_id}'. "
            "Use gpqa_smoke_local, --dry-run-mock, Ollama-backed models, or provide cached outputs."
        )
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    files = []
    for model_id, runner in models:
        path = output_root / f"{_slug(model_id)}.jsonl"
        existing = _existing_item_ids(path) if path.exists() and not overwrite else set()
        rows = [] if overwrite else read_jsonl(path) if path.exists() else []
        generated = 0
        skipped = 0
        for item in items:
            if item.item_id in existing:
                skipped += 1
                continue
            prompt = benchmark.render_prompt(item, prompt_variant)
            output = runner.generate(prompt, seed=seed)
            rows.append(
                {
                    "model_id": model_id,
                    "item_id": item.item_id,
                    "prompt_variant": prompt_variant,
                    "raw_output": output.raw_output,
                    "metadata": {
                        **output.metadata,
                        "artifact_scope": artifact_scope,
                        "temperature": temperature,
                        "seed": seed,
                        "prompt_template_hash": prompt_hash,
                        "prompt_artifact_class": prompt_config.get("artifact_class"),
                        "source": "local_model_generation",
                        "smoke_test_only": panel_id == "gpqa_smoke_local" or dry_run_mock,
                    },
                }
            )
            generated += 1
            write_jsonl(path, rows)
        write_jsonl(path, rows)
        files.append(
            {
                "model_id": model_id,
                "path": str(path),
                "generated": generated,
                "skipped_existing": skipped,
                "total_records": len(rows),
                "prompt_template_hash": prompt_hash,
            }
        )
    return {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": artifact_scope,
        "panel_id": panel_id,
        "prompt_variant": prompt_variant,
        "items_path": str(items_path),
        "item_count_requested": len(items),
        "limit_items": limit_items,
        "output_dir": str(output_root),
        "files": files,
        "status": "generated",
        "warnings": [
            "Generated raw outputs are cached input artifacts only; they are not GPQA benchmark findings."
        ],
    }


def _load_hf_records(*, path: str, name: str, split: str) -> list[dict[str, Any]]:
    try:
        from datasets import DownloadConfig, load_dataset
    except ImportError as exc:  # pragma: no cover - optional dependency.
        raise RuntimeError("Hugging Face export requires the optional 'datasets' package.") from exc

    dataset = load_dataset(
        path,
        name,
        split=split,
        download_config=DownloadConfig(local_files_only=True),
    )
    return [dict(record) for record in dataset]


def _load_source_file(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"GPQA source file does not exist: {source}")
    if source.suffix.lower() == ".csv":
        with source.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if source.suffix.lower() == ".jsonl":
        return read_jsonl(source)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    raise ValueError("GPQA source file must be CSV, JSONL, or a JSON array.")


def _normalize_gpqa_record(record: dict[str, Any], *, index: int, seed: int) -> dict[str, Any]:
    question = _field(record, ["question", "Question"])
    correct = _field(record, ["correct answer", "Correct Answer", "correct_answer", "answer"])
    incorrect = [
        _field(record, ["incorrect answer 1", "Incorrect Answer 1", "incorrect_answer_1"]),
        _field(record, ["incorrect answer 2", "Incorrect Answer 2", "incorrect_answer_2"]),
        _field(record, ["incorrect answer 3", "Incorrect Answer 3", "incorrect_answer_3"]),
    ]
    if not question or not correct or any(not value for value in incorrect):
        raise ValueError(f"Source record {index} is missing required GPQA question/answer fields.")
    choices = [
        ("correct", correct),
        ("incorrect", incorrect[0]),
        ("incorrect", incorrect[1]),
        ("incorrect", incorrect[2]),
    ]
    rng = random.Random(f"{seed}|{index}|{stable_hash(question)}")
    rng.shuffle(choices)
    labels = ("A", "B", "C", "D")
    choice_map = {label: text for label, (_, text) in zip(labels, choices, strict=True)}
    answer = next(
        label for label, (kind, _) in zip(labels, choices, strict=True) if kind == "correct"
    )
    source_id = (
        _field(record, ["record id", "Record ID", "record_id", "id"]) or f"local_{index:06d}"
    )
    domain = (
        _field(record, ["high-level domain", "High-level domain", "domain"])
        or _field(record, ["subdomain", "Subdomain"])
        or "unknown"
    )
    subdomain = _field(record, ["subdomain", "Subdomain", "discipline"])
    return {
        "item_id": f"gpqa_diamond_{index:06d}",
        "question": question,
        "choices": choice_map,
        "answer": answer,
        "domain": domain,
        "source": "gpqa",
        "split": "diamond",
        "metadata": {
            "discipline": subdomain or domain,
            "source_id": str(source_id),
            "license": _field(record, ["license", "License"]) or "user_supplied_local_export",
            "provenance": "local_export",
        },
    }


def _export_report(
    rows: list[dict[str, Any]],
    *,
    output_path: Path,
    source_label: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    question_hashes = [stable_hash(row["question"]) for row in rows]
    domain_counts = Counter(str(row.get("domain", "unknown")) for row in rows)
    return {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": validation["artifact_scope"],
        "benchmark_id": "gpqa_diamond",
        "source": source_label,
        "output_path": str(output_path),
        "exported_file_hash": _file_hash(output_path),
        "item_count": len(rows),
        "item_ids": [row["item_id"] for row in rows],
        "domain_counts": dict(sorted(domain_counts.items())),
        "duplicate_id_count": len(validation["duplicate_item_ids"]),
        "duplicate_question_hash_count": len(
            {value for value, count in Counter(question_hashes).items() if count > 1}
        ),
        "missing_metadata_warnings": [
            warning
            for warning in validation["warnings"]
            if "metadata" in warning or "domain" in warning or "provenance" in warning
        ],
        "validation_status": validation["status"],
        "warnings": validation["warnings"],
        "errors": validation["errors"],
        "question_text_included": False,
    }


def _write_export_report(payload: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "export_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    lines = [
        "# GPQA Diamond Export Report",
        "",
        f"Artifact scope: **{payload['artifact_scope']}**.",
        "",
        "This report intentionally omits raw GPQA question text.",
        "",
        "## Summary",
        "",
        f"- Source: {payload['source']}",
        f"- Output path: {payload['output_path']}",
        f"- Item count: {payload['item_count']}",
        f"- Exported file hash: {payload['exported_file_hash']}",
        f"- Validation status: {payload['validation_status']}",
        "",
        "## Domain Counts",
        "",
    ]
    lines.extend(f"- {domain}: {count}" for domain, count in payload["domain_counts"].items())
    lines.extend(
        [
            "",
            "## Duplicate Counts",
            "",
            f"- Duplicate item IDs: {payload['duplicate_id_count']}",
            f"- Duplicate question hashes: {payload['duplicate_question_hash_count']}",
            "",
            "## Warnings",
            "",
        ]
    )
    lines.extend([f"- {warning}" for warning in payload["warnings"]] or ["none"])
    lines.extend(["", "No GPQA benchmark validity findings are made by this export artifact.", ""])
    (output_dir / "export_report.md").write_text("\n".join(lines), encoding="utf-8")


def _write_panel_readiness(payload: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "panel_readiness.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    lines = [
        "# GPQA Panel Readiness",
        "",
        f"Artifact scope: **{payload['artifact_scope']}**.",
        "",
        f"- Panel: {payload['panel_id']}",
        f"- Configured models: {payload['configured_model_count']}",
        f"- Available models: {payload['available_model_count']}",
        f"- Missing models: {payload['missing_model_count']}",
        f"- Cached prediction variants: {', '.join(payload['cached_prediction_variants']) or 'none'}",
        f"- Cached matrix variants: {', '.join(payload['cached_matrix_variants']) or 'none'}",
        f"- Status: {payload['status']}",
        "",
        "## Audit Sufficiency",
        "",
        "| Component | Status | Reason |",
        "| --- | --- | --- |",
    ]
    for component, row in payload["sufficiency"].items():
        lines.append(f"| {component} | {row['status']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Models",
            "",
            "| Model | Runner | Availability | Cached Variants | Recommended Command |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["models"]:
        cached = ", ".join(row["cached_output_variants"]) or "none"
        command = str(row["recommended_command"] or "")
        lines.append(
            f"| {row['model_id']} | {row['runner']} | {row['availability_status']} | {cached} | {command} |"
        )
    lines.extend(["", "## Exact Next Commands", ""])
    lines.extend([f"- `{command}`" for command in payload["next_commands"]] or ["none"])
    lines.extend(
        ["", "No GPQA benchmark validity findings are made by this readiness artifact.", ""]
    )
    (output_dir / "panel_readiness.md").write_text("\n".join(lines), encoding="utf-8")


def _panel_rows(panel_id: str) -> list[dict[str, Any]]:
    if panel_id == "mock":
        return [
            {"model_id": "always_a", "runner": "mock", "role": "smoke"},
            {"model_id": "context_aware", "runner": "mock", "role": "smoke"},
        ]
    config_path = Path("configs/panels") / f"{panel_id}.yaml"
    if not config_path.exists():
        return []
    data = load_yaml(config_path)
    return [*data.get("models", []), *data.get("baselines", [])]


def _model_availability(model_id: str, runner: str, cached_variants: list[str]) -> dict[str, Any]:
    if runner == "mock":
        return {"available": True, "status": "available_mock", "recommended_command": None}
    if cached_variants:
        return {
            "available": True,
            "status": "available_cached_outputs",
            "recommended_command": None,
        }
    if runner == "ollama":
        available = _ollama_has_model(model_id)
        return {
            "available": available,
            "status": "available_ollama" if available else "missing_ollama_model",
            "recommended_command": None if available else f"ollama pull {model_id}",
        }
    return {
        "available": False,
        "status": "cached_outputs_or_local_runner_required",
        "recommended_command": "provide cached outputs or configure an Ollama/local runner",
    }


def _cached_variants_for_model(
    *,
    cache_root: str | Path,
    benchmark_id: str,
    panel_id: str,
    model_id: str,
) -> list[str]:
    variants = []
    panel_cache = Path(cache_root) / benchmark_id / panel_id
    for variant in GPQA_VARIANTS:
        aggregate = panel_cache / f"predictions_{variant}.jsonl"
        per_model = panel_cache / f"{_slug(model_id)}_{variant}_predictions.jsonl"
        if per_model.exists():
            variants.append(variant)
            continue
        if not aggregate.exists():
            continue
        try:
            rows = read_jsonl(aggregate)
        except (OSError, json.JSONDecodeError):
            continue
        if any(str(row.get("model_id", "")) == model_id for row in rows):
            variants.append(variant)
    return variants


def _panel_sufficiency(
    *,
    available_model_count: int,
    cached_prediction_variants: list[str],
    cached_matrix_variants: list[str],
) -> dict[str, dict[str, str]]:
    full_ready = "full" in cached_prediction_variants and "full" in cached_matrix_variants
    all_variants_ready = all(
        variant in cached_prediction_variants and variant in cached_matrix_variants
        for variant in GPQA_VARIANTS
    )
    return {
        "full_score_audit": {
            "status": "ready" if full_ready else "blocked",
            "reason": "requires full-prompt predictions and matrix",
        },
        "prompt_variant_diagnostics": {
            "status": "ready" if all_variants_ready else "blocked",
            "reason": "requires predictions and matrices for all preregistered prompt variants",
        },
        "irt_proxy_psychometrics": {
            "status": "ready" if full_ready and available_model_count >= 8 else "blocked",
            "reason": "requires full matrix and at least 8 available real/cached models",
        },
        "saturation": {
            "status": "ready" if full_ready and available_model_count >= 3 else "blocked",
            "reason": "requires full matrix and enough real/cached models for top-model comparison",
        },
        "extraction_robustness": {
            "status": "ready" if "full" in cached_prediction_variants else "blocked",
            "reason": "requires scored full-prompt predictions from real raw outputs",
        },
    }


def _panel_next_commands(*, panel_id: str, models: list[dict[str, Any]]) -> list[str]:
    commands = [
        "python3 -m valideval check-panel --panel gpqa_open_local",
        "python3 -m valideval import-outputs --input <scored_output_file.jsonl> --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --adapter generic-jsonl --benchmark-id gpqa_diamond --prompt-variant full",
        "python3 -m valideval score-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --input <raw_output_file.jsonl> --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --prompt-variant full",
    ]
    ollama_models = [row["model_id"] for row in models if row.get("runner") == "ollama"]
    if ollama_models:
        commands.extend(f"ollama pull {model_id}" for model_id in ollama_models)
        commands.append(
            f"python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel {panel_id} --prompt-variant full --output-dir local_outputs/gpqa/full"
        )
    else:
        commands.append("ollama serve")
        commands.append("ollama pull qwen2.5:1.5b-instruct")
    return commands


def _ollama_has_model(model_id: str) -> bool:
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=1.0)
        response.raise_for_status()
        models = response.json().get("models", [])
        names = {str(model.get("name", "")) for model in models}
        if ":" in model_id:
            return model_id in names
        return model_id in names or model_id in {name.split(":")[0] for name in names}
    except Exception:
        return False


def _generation_models(panel_id: str, *, dry_run_mock: bool, temperature: float):
    if dry_run_mock:
        return [
            ("always_a", AlwaysA()),
            ("context_aware", ContextAwareMock()),
        ]
    rows = _panel_rows(panel_id)
    output = []
    mock_by_id = {
        "always_a": AlwaysA(),
        "majority_label": MajorityLabel(),
        "keyword_matcher": KeywordMatcher(),
        "context_aware": ContextAwareMock(),
        "format_fragile": FormatFragile(),
    }
    for row in rows:
        model_id = str(row.get("model_id", ""))
        runner = str(row.get("runner", "cached_or_local"))
        if runner == "mock" and model_id in mock_by_id:
            output.append((model_id, mock_by_id[model_id]))
        elif runner == "ollama":
            output.append((model_id, OllamaRunner(model_id=model_id, temperature=temperature)))
    return output


def _existing_item_ids(path: Path) -> set[str]:
    try:
        return {str(row.get("item_id", "")) for row in read_jsonl(path)}
    except (OSError, json.JSONDecodeError):
        return set()


def _field(record: dict[str, Any], names: list[str]) -> str:
    normalized = {str(key).strip().lower(): value for key, value in record.items()}
    for name in names:
        key = name.strip().lower()
        if key in normalized and normalized[key] not in {None, ""}:
            return str(normalized[key]).strip()
    return ""


def _file_hash(path: str | Path) -> str | None:
    source = Path(path)
    if not source.exists():
        return None
    return stable_hash(source.read_text(encoding="utf-8"))


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "model"
