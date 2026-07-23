from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from valideval.cross_benchmark.analysis import run_cross_benchmark_analysis
from valideval.execution.manifest import atomic_write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the fail-closed ValidEval V5 cross-benchmark analysis.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/analysis/cross_benchmark_confirmatory_v5.yaml"),
    )
    parser.add_argument(
        "--matrix",
        action="append",
        default=[],
        metavar="BENCHMARK=PATH",
        help="Override/add an exact-checkpoint response matrix.",
    )
    parser.add_argument(
        "--metadata",
        action="append",
        default=[],
        metavar="BENCHMARK=JSON",
        help="Importer receipt or gate metadata JSON for one benchmark.",
    )
    parser.add_argument("--output", type=Path, default=Path("results/cross_benchmark_v5"))
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute after all matrices and exact-overlap metadata are present.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = _load_yaml(args.config)
    matrices = {
        str(key): Path(value)
        for key, value in config.get("matrices", {}).items()
        if value not in (None, "", "RESULT_REQUIRED")
    }
    matrices.update(_parse_assignments(args.matrix, path_values=True))
    metadata: dict[str, dict[str, Any]] = {
        str(key): dict(value)
        for key, value in config.get("benchmark_metadata", {}).items()
        if isinstance(value, dict)
    }
    for benchmark_id, path in _parse_assignments(args.metadata, path_values=True).items():
        metadata[benchmark_id] = _metadata_from_json(Path(path))

    requested = [
        str(key) for key in config.get("matrices", {}) if str(key) in {"mmlu", "gsm8k", "bbh"}
    ]
    missing = sorted(benchmark for benchmark in requested if benchmark not in matrices)
    args.output.mkdir(parents=True, exist_ok=True)
    if missing:
        payload = {
            "schema_version": "valideval.cross_benchmark_analysis.v5",
            "status": "blocked",
            "transfer_conclusion": "BLOCKED",
            "blocked_reason": f"Missing declared matrices: {missing}",
            "missing_benchmarks": missing,
            "execute_requested": args.execute,
            "evidence_state": "RESULT_REQUIRED",
        }
        atomic_write_json(args.output / "analysis_manifest_v5.json", payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2 if args.execute else 0

    payload = run_cross_benchmark_analysis(
        matrices,
        output_dir=args.output,
        benchmark_metadata=metadata,
        gate_thresholds=config.get("gate_thresholds"),
        analysis_config=config.get("analysis"),
        execute=args.execute,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] in {"ok", "dry_run_only"} else 2


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Cross-benchmark config does not exist: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Cross-benchmark config must contain a mapping: {path}")
    return payload


def _parse_assignments(
    values: list[str],
    *,
    path_values: bool,
) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Expected BENCHMARK=PATH, got {value!r}")
        benchmark_id, raw = value.split("=", 1)
        benchmark_id = benchmark_id.strip()
        if not benchmark_id or benchmark_id in parsed:
            raise ValueError(f"Duplicate or empty benchmark assignment: {value!r}")
        parsed[benchmark_id] = Path(raw) if path_values else raw
    return parsed


def _metadata_from_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Metadata JSON must contain an object: {path}")
    if isinstance(payload.get("cross_benchmark_eligibility"), dict):
        metadata = dict(payload["cross_benchmark_eligibility"])
        metadata.setdefault("study_id", payload.get("study_id"))
        metadata.setdefault("evidence_state", payload.get("evidence_state", "ARTIFACT_GATED"))
        return metadata
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
