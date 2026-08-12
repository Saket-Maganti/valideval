from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from valideval.execution.manifest import read_json

_ACCEPTED = {
    "S1_V7_2_ACCEPTED",
    "S1_V7_2_ACCEPTED_WITH_RECORDED_MODEL_FAILURES",
}


def recalibrate_study_c_after_s1(
    input_root: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    root = Path(input_root).resolve()
    receipt_path = root / "s1_acceptance_receipt_v7_2.json"
    if not receipt_path.is_file():
        raise FileNotFoundError(f"accepted V7.2 S1 receipt missing: {receipt_path}")
    receipt = read_json(receipt_path)
    if not isinstance(receipt, dict) or receipt.get("status") not in _ACCEPTED:
        raise ValueError("S1 receipt is not accepted")
    if receipt.get("fixture_only") is not False:
        raise ValueError("NON_EVIDENCE_FIXTURE S1 cannot recalibrate or authorize S2")
    benchmark_entries = receipt.get("benchmarks")
    if not isinstance(benchmark_entries, list) or {
        str(entry.get("benchmark_id")) for entry in benchmark_entries
    } != {"mmlu", "gsm8k", "bbh"}:
        raise ValueError("accepted S1 receipt must contain exactly MMLU, GSM8K, and BBH")

    rows: list[dict[str, Any]] = []
    for entry in benchmark_entries:
        run_dir = Path(str(entry["import_destination"]))
        predictions = run_dir / "predictions.jsonl"
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
        "peak_gpu_memory_bytes",
        "download_volume_bytes",
        "cache_status",
        "failure_type",
        "resource_fallbacks",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"accepted S1 runtime fields missing: {missing}")
    if frame["peak_gpu_memory_bytes"].isna().any():
        raise ValueError("real S1 peak GPU memory is incomplete")

    frame["total_tokens"] = frame["input_tokens"] + frame["output_tokens"]
    frame["processing_seconds"] = frame["generation_seconds"] + frame["extraction_seconds"]
    frame["items_per_second"] = np.divide(
        1.0,
        frame["processing_seconds"],
        out=np.full(len(frame), np.nan),
        where=frame["processing_seconds"] > 0,
    )
    frame["tokens_per_second"] = np.divide(
        frame["total_tokens"],
        frame["generation_seconds"],
        out=np.full(len(frame), np.nan),
        where=frame["generation_seconds"] > 0,
    )
    distributions = {
        column: _distribution(frame[column])
        for column in (
            "model_load_seconds",
            "items_per_second",
            "tokens_per_second",
            "output_tokens",
            "peak_gpu_memory_bytes",
        )
    }
    per_scenario: list[dict[str, Any]] = []
    for (benchmark, model_id), group in frame.groupby(["benchmark_id", "model_id"]):
        elapsed = float(group["processing_seconds"].sum())
        per_scenario.append(
            {
                "benchmark_id": str(benchmark),
                "model_id": str(model_id),
                "items": int(len(group)),
                "model_load_seconds": float(group["model_load_seconds"].max()),
                "items_per_second": len(group) / elapsed if elapsed > 0 else None,
                "tokens_per_second": (
                    float(group["total_tokens"].sum()) / float(group["generation_seconds"].sum())
                    if float(group["generation_seconds"].sum()) > 0
                    else None
                ),
                "peak_gpu_memory_bytes": int(group["peak_gpu_memory_bytes"].max()),
                "failure_rate": float(group["failure_type"].ne("SUCCESS").mean()),
                "download_volume_bytes": int(group["download_volume_bytes"].max()),
                "cache_status": sorted(set(group["cache_status"].astype(str))),
                "fallback_count": max(
                    len(value) if isinstance(value, list) else 0
                    for value in group["resource_fallbacks"]
                ),
            }
        )
    median_seconds_per_item = float(frame["processing_seconds"].median())
    p90_seconds_per_item = float(frame["processing_seconds"].quantile(0.90))
    stage_model_item_counts = {"S2": 4_800, "S3": 32_000, "S4": 64_000}
    estimates = {
        stage: {
            "model_item_count": count,
            "p50_generation_hours": count * median_seconds_per_item / 3600.0,
            "p90_generation_hours": count * p90_seconds_per_item / 3600.0,
            "boundary": "Measured S1 scaling range; not a runtime promise.",
        }
        for stage, count in stage_model_item_counts.items()
    }
    failure_rate = float(frame["failure_type"].ne("SUCCESS").mean())
    extraction_success = float(frame["extraction_status"].eq("success").mean())
    systemic_model_failure = any(summary["failure_rate"] >= 0.50 for summary in per_scenario)
    peak_memory = int(frame["peak_gpu_memory_bytes"].max())
    s2_authorized = bool(
        failure_rate <= 0.05
        and extraction_success >= 0.95
        and not systemic_model_failure
        and peak_memory < 16 * 1024**3
    )
    payload = {
        "schema_version": "valideval.study-c-recalibration.v7.2",
        "status": "STUDY_C_RECALIBRATED_AFTER_ACCEPTED_S1",
        "source_commit": receipt["source_commit"],
        "distributions": distributions,
        "scenario_summaries": per_scenario,
        "failure_rate": failure_rate,
        "extraction_success": extraction_success,
        "download_volume_bytes": sum(summary["download_volume_bytes"] for summary in per_scenario),
        "runtime_estimates": estimates,
        "s2_authorization": "S2_AUTHORIZED" if s2_authorized else "S2_ENGINEERING_REPAIR_REQUIRED",
        "s3_authorization": "S3_BLOCKED_PENDING_S2",
        "s4_authorization": "S4_BLOCKED_PENDING_S3",
        "claim_boundary": (
            "S1 engineering measurements recalibrate planning distributions only. They are not "
            "scientific benchmark evidence or portable hardware guarantees."
        ),
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _distribution(values: pd.Series) -> dict[str, float | int]:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        raise ValueError(f"runtime distribution is empty: {values.name}")
    return {
        "count": int(len(numeric)),
        "minimum": float(numeric.min()),
        "p10": float(numeric.quantile(0.10)),
        "p50": float(numeric.quantile(0.50)),
        "p90": float(numeric.quantile(0.90)),
        "maximum": float(numeric.max()),
    }
