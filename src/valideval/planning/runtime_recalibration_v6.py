from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


def recalibrate_runtime_from_s1(
    input_root: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    root = Path(input_root)
    rows: list[dict[str, Any]] = []
    for benchmark in ("mmlu", "gsm8k", "bbh"):
        predictions = root / benchmark / "predictions.jsonl"
        if not predictions.is_file():
            raise FileNotFoundError(f"accepted S1 predictions missing: {predictions}")
        rows.extend(
            json.loads(line)
            for line in predictions.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    frame = pd.DataFrame(rows)
    required = {
        "benchmark_id",
        "model_id",
        "model_load_seconds",
        "generation_seconds",
        "extraction_seconds",
        "input_tokens",
        "output_tokens",
        "gpu_id",
        "dtype",
        "quantization",
        "retry_count",
        "cache_status",
        "failure_type",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"S1 runtime fields missing: {missing}")
    summaries: list[dict[str, Any]] = []
    for (benchmark, model_id), group in frame.groupby(["benchmark_id", "model_id"]):
        generation_seconds = float(group["generation_seconds"].sum())
        examples = int(group.shape[0])
        summaries.append(
            {
                "benchmark_id": str(benchmark),
                "model_id": str(model_id),
                "examples": examples,
                "successful_examples": int(group["failure_type"].eq("SUCCESS").sum()),
                "model_load_seconds": float(group["model_load_seconds"].max()),
                "generation_seconds": generation_seconds,
                "extraction_seconds": float(group["extraction_seconds"].sum()),
                "examples_per_generation_second": (
                    examples / generation_seconds if generation_seconds > 0 else None
                ),
                "input_tokens": int(group["input_tokens"].sum()),
                "output_tokens": int(group["output_tokens"].sum()),
                "gpu_ids": sorted(set(group["gpu_id"].astype(str))),
                "dtype": sorted(set(group["dtype"].astype(str))),
                "quantization": sorted(set(group["quantization"].astype(str))),
                "retry_count": int(group["retry_count"].sum()),
                "cache_status": sorted(set(group["cache_status"].astype(str))),
            }
        )
    by_benchmark: dict[str, dict[str, Any]] = defaultdict(dict)
    for benchmark, group in frame.groupby("benchmark_id"):
        elapsed = float(group["generation_seconds"].sum() + group["extraction_seconds"].sum())
        by_benchmark[str(benchmark)] = {
            "observed_examples": int(group.shape[0]),
            "observed_processing_seconds": elapsed,
            "observed_examples_per_second": (
                float(group.shape[0]) / elapsed if elapsed > 0 else None
            ),
        }
    payload = {
        "schema_version": "6.0",
        "status": "S1_RUNTIME_RECALIBRATED",
        "evidence_class": "ENGINEERING_ONLY",
        "scenario_summaries": summaries,
        "benchmark_summaries": dict(by_benchmark),
        "planning_rule": (
            "Scale S2-S4 model-item generation components from measured per-scenario throughput; "
            "add observed load/download overhead separately and report ranges, not exact promises."
        ),
        "claim_boundary": (
            "These measurements calibrate engineering plans on the observed Kaggle run only. "
            "They are not scientific benchmark evidence or portable performance guarantees."
        ),
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
