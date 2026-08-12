from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import yaml

from valideval.transport import (
    leave_one_benchmark_out_folds,
    leave_one_family_out_folds,
    validate_fold_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and validate V7.1 transport folds.")
    parser.add_argument("--panel", type=Path, default=Path("configs/panels/s3_scientific_v7.yaml"))
    parser.add_argument("--output", type=Path, default=Path("results/v7_1/transport/folds"))
    args = parser.parse_args()
    started = time.perf_counter()
    panel = yaml.safe_load(args.panel.read_text(encoding="utf-8"))
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    config_hash = hashlib.sha256(args.panel.read_bytes()).hexdigest()
    family_to_models: dict[str, list[str]] = {}
    for model in panel["models"]:
        family_to_models.setdefault(str(model["family"]), []).append(str(model["repository"]))
    all_models = [model for models in family_to_models.values() for model in models]
    common = {
        "training_families": sorted(family_to_models),
        "held_out_families": [],
        "training_model_ids": all_models,
        "evaluation_model_ids": all_models,
        "discovery_item_ids": ["training-benchmark-items"],
        "evaluation_item_ids": ["held-out-benchmark-items"],
        "source_commit": source_commit,
        "config_hash": config_hash,
    }
    benchmark_folds = leave_one_benchmark_out_folds(
        ("mmlu", "gsm8k", "bbh"),
        **common,
    )
    family_folds = leave_one_family_out_folds(
        family_to_models,
        training_benchmarks=["mmlu", "gsm8k", "bbh"],
        held_out_benchmark=None,
        discovery_item_ids=["discovery-fold-items"],
        evaluation_item_ids=["evaluation-fold-items"],
        source_commit=source_commit,
        config_hash=config_hash,
    )
    folds = [validate_fold_manifest(fold) for fold in benchmark_folds + family_folds]
    payload = {
        "status": "TRANSPORT_FOLD_SPECIFICATION_READY",
        "empirical_status": "BLOCKED_PENDING_EXECUTED_FOLDS",
        "fold_count": len(folds),
        "leave_one_benchmark_out_count": len(benchmark_folds),
        "leave_one_family_out_count": len(family_folds),
        "source_commit": source_commit,
        "config_hash": config_hash,
        "runtime_seconds": time.perf_counter() - started,
        "folds": folds,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "fold_manifests.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{payload['status']}: {payload['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
