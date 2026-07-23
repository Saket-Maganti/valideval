from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from valideval.planning.runtime_estimator import GpuRuntimeScenario, write_runtime_estimates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate an explicitly parameterized GPU runtime range. Values are planning "
            "assumptions until recalibrated from an imported S1 smoke."
        )
    )
    parser.add_argument("--scenario-id")
    parser.add_argument("--benchmark")
    parser.add_argument("--model-id")
    parser.add_argument("--model-parameters-billions", type=float)
    parser.add_argument("--item-count", type=int)
    parser.add_argument("--average-input-tokens", type=float)
    parser.add_argument("--average-output-tokens", type=float)
    parser.add_argument("--gpu-count", type=int, choices=(1, 2), default=2)
    parser.add_argument("--dual-gpu-utilization", type=float, default=0.80)
    parser.add_argument("--throughput-optimistic", type=float, default=20.0)
    parser.add_argument("--throughput-expected", type=float, default=12.0)
    parser.add_argument("--throughput-conservative", type=float, default=6.0)
    parser.add_argument("--download-size-gb", type=float, default=0.0)
    parser.add_argument("--quantization", default="unspecified")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/planning/runtime_estimates_v5.csv"),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("configs/models/model_registry_v5.yaml"),
    )
    parser.add_argument(
        "--assumptions-output",
        type=Path,
        default=Path("results/planning/runtime_estimates_v5_assumptions.json"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.scenario_id is None:
        scenarios, assumptions = _frozen_s1_scenarios(args.registry, gpu_count=args.gpu_count)
        frame = write_runtime_estimates(args.output, gpu_scenarios=scenarios)
        args.assumptions_output.parent.mkdir(parents=True, exist_ok=True)
        args.assumptions_output.write_text(
            json.dumps(assumptions, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            f"Wrote {len(frame)} S1-only PLANNED scenarios to {args.output}; "
            "full-run timing remains BLOCKED until S1 calibration"
        )
        return 0
    required = {
        "benchmark": args.benchmark,
        "model_id": args.model_id,
        "model_parameters_billions": args.model_parameters_billions,
        "item_count": args.item_count,
        "average_input_tokens": args.average_input_tokens,
        "average_output_tokens": args.average_output_tokens,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit("single-scenario mode requires: " + ", ".join(missing))
    scenario = GpuRuntimeScenario(
        scenario_id=args.scenario_id,
        benchmark=str(args.benchmark),
        model_id=str(args.model_id),
        model_parameters_billions=float(args.model_parameters_billions),
        item_count=int(args.item_count),
        average_input_tokens=float(args.average_input_tokens),
        average_output_tokens=float(args.average_output_tokens),
        gpu_count=args.gpu_count,
        dual_gpu_utilization=args.dual_gpu_utilization,
        throughput_tps_optimistic=args.throughput_optimistic,
        throughput_tps_expected=args.throughput_expected,
        throughput_tps_conservative=args.throughput_conservative,
        download_size_gb=args.download_size_gb,
        quantization=args.quantization,
    )
    frame = write_runtime_estimates(args.output, gpu_scenarios=[scenario])
    row = frame.iloc[0]
    print(
        "Wrote PLANNED range "
        f"{row['wall_hours_excluding_download_optimistic']:.3f}-"
        f"{row['wall_hours_excluding_download_conservative']:.3f} hours to {args.output}"
    )
    return 0


def _frozen_s1_scenarios(
    registry_path: Path,
    *,
    gpu_count: int,
) -> tuple[list[GpuRuntimeScenario], dict[str, object]]:
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or not isinstance(registry.get("models"), list):
        raise ValueError("model registry must contain a models list")
    models = [
        model
        for model in registry["models"]
        if isinstance(model, dict)
        and model.get("exact_identity_status") == "FROZEN_IMMUTABLE_REVISION"
    ]
    if not models:
        raise ValueError("no frozen immutable Study C models are available for S1 planning")
    token_assumptions = {
        "mmlu": {"average_input_tokens": 160.0, "average_output_tokens": 4.0},
        "gsm8k": {"average_input_tokens": 180.0, "average_output_tokens": 256.0},
        "bbh": {"average_input_tokens": 350.0, "average_output_tokens": 128.0},
    }
    scenarios: list[GpuRuntimeScenario] = []
    for model in models:
        parameters = float(model["parameter_count"])
        revision = str(model["revision"])
        canonical_id = str(model["canonical_model_id"])
        for benchmark, tokens in token_assumptions.items():
            scenarios.append(
                GpuRuntimeScenario(
                    scenario_id=f"s1-{benchmark}-{canonical_id.replace('/', '--')}",
                    benchmark=benchmark,
                    model_id=f"{canonical_id}@{revision}",
                    model_parameters_billions=parameters / 1e9,
                    item_count=50,
                    average_input_tokens=tokens["average_input_tokens"],
                    average_output_tokens=tokens["average_output_tokens"],
                    gpu_count=gpu_count,
                    download_size_gb=parameters * 2.0 * 1.10 / 1e9,
                    quantization="unquantized_bfloat16_assumption",
                )
            )
    assumptions: dict[str, object] = {
        "schema_version": "5.0",
        "scope": "S1 smoke only; 50 items per benchmark and exact frozen checkpoint revision",
        "evidence_status": "PLANNED",
        "planning_only": True,
        "calibration_state": "UNMEASURED_ASSUMPTIONS",
        "benchmark_token_assumptions": token_assumptions,
        "throughput_tps_per_gpu": {
            "optimistic": 20.0,
            "expected": 12.0,
            "conservative": 6.0,
        },
        "dual_gpu_utilization": 0.8,
        "download_size_proxy": (
            "parameter_count * 2 bytes * 1.10 overhead; replace with measured repository bytes"
        ),
        "blocked_outputs": [
            "full_benchmark_runtime",
            "total_compute_budget",
            "scientific_run_schedule",
        ],
        "calibration_next_action": (
            "Import S1 elapsed time, completed/failed item counts, actual token counts, repository "
            "bytes, load time, and OOM/retry rates, then regenerate."
        ),
    }
    return scenarios, assumptions


if __name__ == "__main__":
    raise SystemExit(main())
