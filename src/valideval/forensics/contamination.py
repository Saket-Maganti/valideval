from __future__ import annotations

from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.forensics.duplicates import internal_duplicate_report
from valideval.forensics.overlap import scan_corpus_overlap
from valideval.forensics.provenance import audit_manifest_hashes, provenance_completeness
from valideval.forensics.split_leakage import split_leakage_report
from valideval.forensics.temporal import temporal_validity_report


def run_data_forensics(
    benchmark: Benchmark,
    *,
    corpus_path: str | None = None,
    benchmark_config: dict[str, Any] | None = None,
    diagnostic_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = diagnostic_config or {}
    ngram_n = int(cfg.get("ngram_n", 5))
    near_duplicate_threshold = float(cfg.get("near_duplicate_threshold", 0.82))
    items = benchmark.load_items()
    overlap = scan_corpus_overlap(benchmark, corpus_path, ngram_n=ngram_n)
    duplicates = internal_duplicate_report(
        items,
        near_duplicate_threshold=near_duplicate_threshold,
    )
    splits = split_leakage_report(items)
    temporal = temporal_validity_report(items)
    provenance = provenance_completeness(items)
    hashes = audit_manifest_hashes(
        benchmark,
        benchmark_config=benchmark_config,
        diagnostic_config=diagnostic_config,
    )
    return {
        "signals": {
            "corpus_overlap": overlap,
            "internal_duplicates": duplicates,
            "split_leakage": splits,
            "temporal_validity": temporal,
            "provenance_completeness": {
                "status": "measured",
                "risk_level": _provenance_risk(provenance["completeness_fraction"]),
                "metrics": provenance,
                "warnings": [
                    "Missing provenance fields reduce audit interpretability but are not contamination evidence by themselves."
                ],
            },
        },
        "hashes": hashes,
        "searched": {
            "local_corpus": corpus_path,
            "web": False,
            "remote_model_training_data": False,
        },
        "not_searched": [
            "paid APIs",
            "remote web verification",
            "closed model training corpora",
        ],
        "warnings": [
            "Contamination scans are corpus-dependent evidence, not proof of cleanliness.",
            "Do not combine these signals into a single final contamination truth.",
        ],
    }


def _provenance_risk(completeness: float) -> str:
    if completeness >= 0.95:
        return "low local evidence"
    if completeness >= 0.70:
        return "moderate local evidence"
    return "high local evidence"
