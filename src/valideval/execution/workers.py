from __future__ import annotations

import os
import time
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from valideval.execution.datasets import PublicInferenceItem, reject_gold_fields
from valideval.execution.errors import (
    RecoverableResourceFailure,
    translate_generation_error,
    translate_model_load_error,
)
from valideval.execution.manifest import EXECUTION_SCHEMA_VERSION, atomic_write_json
from valideval.execution.models import build_text_generator
from valideval.execution.prompts import render_prompt
from valideval.scoring.bbh import parse_bbh_answer, score_bbh_answer
from valideval.scoring.gsm8k import parse_gsm8k_answer, score_gsm8k_answer
from valideval.scoring.mmlu import parse_mmlu_answer, score_mmlu_answer


def production_worker(task: Mapping[str, Any], gpu_id: str) -> dict[str, Any]:
    """Run one exact model across a deterministic item set.

    The task contains private gold only for the final scoring call. Renderer,
    generator, and parser calls receive narrower values that are asserted to be
    gold-free.
    """

    model_record = dict(task["model"])
    benchmark_id = str(task["benchmark_id"])
    contract = dict(task["benchmark_contract"])
    backend = str(task["backend"])
    public_items = [PublicInferenceItem(**_normalize_public_item(item)) for item in task["items"]]
    private_gold = {str(key): str(value) for key, value in dict(task["private_gold"]).items()}
    if set(private_gold) != {item.item_id for item in public_items}:
        raise ValueError("private gold map does not exactly match the public item set")
    for item in public_items:
        reject_gold_fields(item.to_dict())

    cache_root = Path(str(task["model_cache_dir"])) if task.get("model_cache_dir") else None
    cache_bytes_before = _directory_size(cache_root)
    _reset_peak_gpu_memory(backend)
    try:
        generator = build_text_generator(
            model_record,
            backend=backend,
            benchmark_id=benchmark_id,
            gpu_id=gpu_id,
            cache_dir=task.get("model_cache_dir"),
        )
    except BaseException as exc:
        translated = translate_model_load_error(exc)
        if translated is exc:
            raise
        raise translated from exc
    rows: list[dict[str, Any]] = []
    failure_counts: Counter[str] = Counter()
    peak_gpu_memory_bytes: int | None = None
    try:
        for item_index, item in enumerate(public_items):
            row = _run_one_item(
                task=task,
                item=item,
                gold=private_gold[item.item_id],
                model_record=model_record,
                generator=generator,
                gpu_id=gpu_id,
                contract=contract,
            )
            rows.append(row)
            failure_counts[str(row["failure_type"])] += 1
            _write_item_heartbeat(task, item, item_index, len(public_items), gpu_id)
    finally:
        peak_gpu_memory_bytes = _peak_gpu_memory(backend)
        generator.close()
    cache_bytes_after = _directory_size(cache_root)
    download_volume_bytes = max(cache_bytes_after - cache_bytes_before, 0)
    for row in rows:
        row["peak_gpu_memory_bytes"] = peak_gpu_memory_bytes
        row["download_volume_bytes"] = download_volume_bytes
    return {
        "rows": rows,
        "model_id": model_record["canonical_model_id"],
        "model_revision": model_record["revision"],
        "model_load_seconds": generator.model_load_seconds,
        "cache_status": generator.cache_status,
        "peak_gpu_memory_bytes": peak_gpu_memory_bytes,
        "download_volume_bytes": download_volume_bytes,
        "failure_counts": dict(sorted(failure_counts.items())),
        "evidence_class": task["evidence_class"],
    }


def _run_one_item(
    *,
    task: Mapping[str, Any],
    item: PublicInferenceItem,
    gold: str,
    model_record: Mapping[str, Any],
    generator: Any,
    gpu_id: str,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    prompt = render_prompt(item, contract)
    reject_gold_fields({"prompt": prompt, "item": item.to_dict()})
    raw_output = ""
    parsed_value: str | None = None
    extraction_status = "not_run"
    generation_status = "not_run"
    failure_type = "UNKNOWN_FAILURE"
    is_correct: bool | None = None
    input_tokens = 0
    output_tokens = 0
    generation_seconds = 0.0
    extraction_seconds = 0.0
    try:
        generation_parameters = dict(contract["generation_parameters"])
        generation_parameters["max_input_tokens"] = min(
            int(generation_parameters.get("max_input_tokens", task["max_sequence_length"])),
            int(task["max_sequence_length"]),
        )
        if contract.get("generation_mode") == "option_log_likelihood":
            if item.benchmark_id != "mmlu" or len(item.choices) != 4:
                raise ValueError("option log-likelihood requires a four-choice MMLU item")
            generated = generator.score_choices(
                prompt,
                ("A", "B", "C", "D"),
                generation_parameters,
            )
        else:
            generated = generator.generate(prompt, generation_parameters)
        raw_output = str(generated["raw_output"])
        input_tokens = int(generated["input_tokens"])
        output_tokens = int(generated["output_tokens"])
        generation_seconds = float(generated["generation_seconds"])
        generation_status = "success"
        if bool(generated.get("truncated")):
            failure_type = "TRUNCATED_OUTPUT"
            extraction_status = "not_run"
    except RecoverableResourceFailure:
        raise
    except TimeoutError:
        generation_status = "failed"
        failure_type = "TIMEOUT"
    except Exception as exc:
        translated = translate_generation_error(exc)
        if translated is not exc:
            raise translated from exc
        generation_status = "failed"
        failure_type = "GENERATION_FAILURE"
    if generation_status == "success" and failure_type != "TRUNCATED_OUTPUT":
        extraction_started = time.perf_counter()
        try:
            parsed = _parse_without_gold(raw_output, item, contract)
            parsed_value = parsed.value
            extraction_status = parsed.status
            failure_type = parsed.failure_type
        except Exception:
            extraction_status = "failed"
            failure_type = "EXTRACTION_FAILURE"
        finally:
            extraction_seconds = time.perf_counter() - extraction_started
        if extraction_status == "success" and failure_type == "SUCCESS":
            try:
                is_correct = _score_with_gold(parsed, gold, item)
            except Exception:
                failure_type = "SCORING_FAILURE"
    total_seconds = time.perf_counter() - started
    return {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "study_id": task["study_id"],
        "run_id": task["run_id"],
        "benchmark_id": item.benchmark_id,
        "benchmark_version": contract["benchmark_version"],
        "task_id": f"{item.benchmark_id}-{item.subtask_id}",
        "subtask_id": item.subtask_id,
        "split": item.split,
        "item_id": item.item_id,
        "item_hash": item.item_hash,
        "model_id": model_record["canonical_model_id"],
        "model_revision": model_record["revision"],
        "model_family": model_record["family"],
        "prompt_template_id": contract["prompt_template_version"],
        "prompt_hash": task["prompt_hash"],
        "few_shot_id": contract["few_shot_policy"],
        "chat_template_id": model_record["chat_template_policy"],
        "generation_config_id": contract["generation_config_id"],
        "scoring_version": contract["scoring_version"],
        "extraction_version": contract["extraction_version"],
        "seed": int(contract["generation_parameters"]["seed"]),
        "shard_id": task["item_to_shard"][item.item_id],
        "attempt_id": int(task.get("attempt_id", 1)),
        "raw_output": raw_output,
        "parsed_output": parsed_value,
        "gold_output": gold,
        "is_correct": is_correct,
        "extraction_status": extraction_status,
        "generation_status": generation_status,
        "failure_type": failure_type,
        "latency_seconds": total_seconds,
        "model_load_seconds": float(generator.model_load_seconds),
        "generation_seconds": generation_seconds,
        "extraction_seconds": extraction_seconds,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "examples_per_second": 1.0 / total_seconds if total_seconds > 0 else None,
        "device": f"cuda:{gpu_id}" if gpu_id != "cpu" else "cpu",
        "gpu_id": gpu_id,
        "dtype": model_record["dtype"],
        "quantization": model_record["quantization"],
        "batch_size": int(task["batch_size"]),
        "max_sequence_length": int(task["max_sequence_length"]),
        "resource_fallbacks": list(task.get("resource_fallbacks", [])),
        "retry_count": int(task.get("retry_count", 0)),
        "cache_status": generator.cache_status,
        "code_revision": task["code_revision"],
        "config_hash": task["config_hash"],
        "environment_hash": task["environment_hash"],
        "evidence_class": task["evidence_class"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _parse_without_gold(raw_output: str, item: PublicInferenceItem, contract: Mapping[str, Any]):
    reject_gold_fields({"raw_output": raw_output, "item": item.to_dict()})
    if item.benchmark_id == "mmlu":
        return parse_mmlu_answer(raw_output)
    if item.benchmark_id == "gsm8k":
        if contract.get("extraction_version") == "final_answer_marker_strict_v7":
            from valideval.scoring.gsm8k import parse_gsm8k_answer_strict

            return parse_gsm8k_answer_strict(raw_output)
        return parse_gsm8k_answer(raw_output)
    policies = contract.get("task_prompt_policies", {})
    policy = policies.get(item.subtask_id, {}) if isinstance(policies, Mapping) else {}
    return parse_bbh_answer(raw_output, item.subtask_id, policy)


def _score_with_gold(parsed: Any, gold: str, item: PublicInferenceItem) -> bool:
    if item.benchmark_id == "mmlu":
        return score_mmlu_answer(parsed, gold)
    if item.benchmark_id == "gsm8k":
        return score_gsm8k_answer(parsed, gold)
    return score_bbh_answer(parsed, gold, item.subtask_id)


def _normalize_public_item(item: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(item)
    payload["choices"] = tuple(payload.get("choices", ()))
    payload["public_metadata"] = dict(payload.get("public_metadata", {}))
    return payload


def _write_item_heartbeat(
    task: Mapping[str, Any],
    item: PublicInferenceItem,
    item_index: int,
    item_count: int,
    gpu_id: str,
) -> None:
    path_value = os.environ.get("VALIDEVAL_WORKER_HEARTBEAT_PATH", "").strip()
    if not path_value:
        return
    path = Path(path_value)
    atomic_write_json(
        path,
        {
            "worker_id": os.environ.get("VALIDEVAL_WORKER_ID"),
            "gpu_id": gpu_id,
            "current_job": task["task_id"],
            "heartbeat": datetime.now(timezone.utc).isoformat(),
            "last_completed_item": item.item_id,
            "completed_items": item_index + 1,
            "total_items": item_count,
            "retry_count": int(task.get("retry_count", 0)),
            "memory_failure": False,
            "exit_state": "running",
        },
    )


def _directory_size(root: Path | None) -> int:
    if root is None or not root.is_dir():
        return 0
    total = 0
    for path in root.rglob("*"):
        try:
            if path.is_file() and not path.is_symlink():
                total += path.stat().st_size
        except OSError:
            continue
    return total


def _reset_peak_gpu_memory(backend: str) -> None:
    if backend != "transformers":
        return
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
    except (ImportError, RuntimeError):
        return


def _peak_gpu_memory(backend: str) -> int | None:
    if backend != "transformers":
        return None
    try:
        import torch

        if torch.cuda.is_available():
            return int(torch.cuda.max_memory_allocated())
    except (ImportError, RuntimeError):
        return None
    return None
