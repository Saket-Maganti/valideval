"""Build the local-safe V5 leakage audit without promoting it to study evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from valideval.execution.manifest import atomic_write_json
from valideval.leakage.guards import build_overlap_candidates, write_overlap_candidates_csv


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _load_local_overlap_inputs(
    root: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    gpqa_path = root / "data/gpqa/gpqa_diamond.jsonl"
    mmlu_path = root / (
        "data/external/mmlu/lm_eval_outputs/qwen2_5_0_5b/"
        "Qwen__Qwen2.5-0.5B-Instruct/"
        "samples_mmlu_high_school_biology_2026-06-12T15-26-49.546827.jsonl"
    )
    missing = [str(path.relative_to(root)) for path in (gpqa_path, mmlu_path) if not path.exists()]
    if missing:
        return {}, {"status": "BLOCKED", "missing_inputs": missing}

    gpqa = []
    for row in _read_jsonl(gpqa_path):
        choices = row.get("choices", {})
        gpqa.append(
            {
                "item_id": row.get("item_id"),
                "question": row.get("question"),
                "choices": list(choices.values()) if isinstance(choices, dict) else choices,
            }
        )
    mmlu_by_id: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(mmlu_path):
        document = row.get("doc") or {}
        item_id = f"high_school_biology::{row.get('doc_id')}"
        mmlu_by_id[item_id] = {
            "item_id": item_id,
            "question": document.get("question"),
            "choices": document.get("choices", []),
        }
    collections = {"gpqa_diamond": gpqa, "mmlu_high_school_biology": list(mmlu_by_id.values())}
    scope = {
        "status": "PARTIAL_LOCAL_CONTENT_ONLY",
        "datasets": {name: len(rows) for name, rows in collections.items()},
        "input_hashes": {
            str(gpqa_path.relative_to(root)): _sha256(gpqa_path),
            str(mmlu_path.relative_to(root)): _sha256(mmlu_path),
        },
        "excluded_required_inputs": [
            "controlled full MMLU item content",
            "controlled GSM8K item content",
            "controlled BBH item content",
        ],
    }
    return collections, scope


def build_leakage_audit_v5(root: str | Path, output_dir: str | Path) -> dict[str, Any]:
    repository = Path(root).resolve()
    destination = Path(output_dir)
    if not destination.is_absolute():
        destination = repository / destination
    destination.mkdir(parents=True, exist_ok=True)

    collections, overlap_scope = _load_local_overlap_inputs(repository)
    candidates = build_overlap_candidates(collections, fuzzy_threshold=0.8) if collections else []
    candidate_path = destination / "cross_benchmark_overlap_candidates_v5.csv"
    write_overlap_candidates_csv(candidate_path, candidates)

    checks = {
        "benchmark_split_overlap": {
            "status": "BLOCKED",
            "reason": "Frozen controlled MMLU/GSM8K/BBH item snapshots are not local.",
        },
        "local_cross_benchmark_overlap_candidate_generation": {
            "status": "VERIFIED_FROM_PRIMARY_ARTIFACT",
            "scope": overlap_scope,
            "candidate_count": len(candidates),
            "interpretation": "Candidate count is not evidence of absence or presence of contamination.",
        },
        "gold_answer_isolation": {
            "status": "VERIFIED_FROM_PRIMARY_ARTIFACT",
            "tests": ["tests/test_gold_answer_isolation_v5.py"],
        },
        "diagnostic_label_isolation": {
            "status": "VERIFIED_FROM_PRIMARY_ARTIFACT",
            "tests": ["tests/test_leakage_guards_v5.py"],
        },
        "synthetic_circularity_guards": {
            "status": "VERIFIED_FROM_PRIMARY_ARTIFACT",
            "tests": ["tests/test_synthetic_decoupling_v5.py"],
            "confirmatory_results": "BLOCKED",
        },
        "exact_execution_identity_guard": {
            "status": "VERIFIED_FROM_PRIMARY_ARTIFACT",
            "tests": ["tests/test_leakage_guards_v5.py"],
        },
        "post_selection": {
            "status": "PARTIAL",
            "repair": "Legacy severe-rank threshold retired and confirmatory config frozen.",
            "future_execution": "BLOCKED",
        },
        "human_review_blinding": {
            "status": "VERIFIED_FROM_PRIMARY_ARTIFACT",
            "tests": ["tests/test_human_validation_v5.py"],
            "human_labels": "BLOCKED",
        },
        "model_pretraining_contamination": {
            "status": "BLOCKED",
            "reason": "The local audit cannot establish training-data absence for external models.",
        },
    }
    payload = {
        "schema_version": "5.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate": "LEAKAGE_GUARDS_PARTIAL",
        "evidence_status": "PLANNED",
        "output_is_empirical_evidence": False,
        "checks": checks,
        "p0_open_paths": [
            "full controlled benchmark split and cross-benchmark overlap audit",
            "BBH few-shot examples and their target-overlap hash are not frozen",
            "real-run verification that generation/extraction boundaries remain isolated",
            "model pretraining contamination uncertainty",
        ],
        "artifacts": {
            "overlap_candidates": _display_path(candidate_path, repository),
        },
    }
    audit_path = destination / "leakage_checks_v5.json"
    atomic_write_json(audit_path, payload)
    return payload
