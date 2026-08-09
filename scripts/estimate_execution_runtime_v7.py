from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from valideval.execution.config import load_run_config
from valideval.execution.models import load_panel_config

TOKEN_ASSUMPTIONS = {
    "mmlu": (160.0, 4.0),
    "gsm8k": (180.0, 256.0),
    "bbh": (350.0, 128.0),
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    paths = [root / f"configs/runs/{benchmark}_s1_v6.yaml" for benchmark in TOKEN_ASSUMPTIONS]
    paths.extend(sorted((root / "configs/runs_v7").glob("*.yaml")))
    rows = [_estimate_run(root, path) for path in paths]
    frame = pd.DataFrame(rows)
    output = root / "results/v7/planning/gpu_runtime"
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "run_estimates.csv", index=False)
    primary_route = frame[~frame["run_id"].str.contains("-fallback-")]
    mandatory = primary_route[~primary_route["stage"].isin(["S4", "S5"])]
    all_runs = primary_route
    max_download = float(frame["download_gb"].max())
    summary = {
        "status": "GPU_RUNTIME_PLANNING_COMPLETE_UNCALIBRATED",
        "configured_run_count_including_fallback_alternatives": len(frame),
        "primary_route_run_count": len(primary_route),
        "mandatory_pre_s4_hours_excluding_download": {
            label: float(mandatory[f"runtime_hours_{label}"].sum())
            for label in ("optimistic", "expected", "conservative")
        },
        "all_run_hours_excluding_download": {
            label: float(all_runs[f"runtime_hours_{label}"].sum())
            for label in ("optimistic", "expected", "conservative")
        },
        "maximum_single_run_download_gb": max_download,
        "recommended_free_storage_gb": math.ceil(max_download * 1.25 + 15.0),
        "calibration_state": "UNMEASURED_ASSUMPTIONS",
        "claim_boundary": (
            "Ranges use frozen token/throughput/retry assumptions and are not measured T4x2 "
            "runtime. Recalibrate after accepted S1/S2 outputs. Downloads are excluded from sums."
        ),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _estimate_run(root: Path, path: Path) -> dict[str, object]:
    config = load_run_config(path, repository_root=root)
    panel = load_panel_config(root / config.panel_config)
    item_count = json.loads((root / config.subset_manifest).read_text(encoding="utf-8"))[
        "item_count"
    ]
    input_tokens, output_tokens = TOKEN_ASSUMPTIONS[config.benchmark_id]
    robustness = str(getattr(config, "robustness_config", "") or "")
    if "option_loglikelihood" in robustness:
        input_tokens *= 4.0
        output_tokens = 4.0
    model_count = len(panel["models"])
    weighted_tokens = model_count * item_count * (output_tokens + 0.15 * input_tokens)
    download_gb = sum(float(model["expected_download_size"]) for model in panel["models"]) / 1e9
    waves = math.ceil(model_count / 2)
    runtimes = {}
    for label, throughput, retry, load_minutes in (
        ("optimistic", 20.0, 0.02, 2.0),
        ("expected", 12.0, 0.08, 5.0),
        ("conservative", 6.0, 0.20, 10.0),
    ):
        inference = weighted_tokens / (2 * 0.80 * throughput) / 3600 / (1.0 - retry)
        runtimes[label] = inference + waves * load_minutes / 60.0
    output_gb = model_count * item_count * 4096 / 1e9
    return {
        "run_id": config.run_id,
        "stage": getattr(config, "stage", "S1"),
        "evidence_class": config.evidence_class,
        "benchmark": config.benchmark_id,
        "models": model_count,
        "families": panel.get("family_count", len({m["family"] for m in panel["models"]})),
        "items": item_count,
        "runtime_hours_optimistic": runtimes["optimistic"],
        "runtime_hours_expected": runtimes["expected"],
        "runtime_hours_conservative": runtimes["conservative"],
        "download_gb": download_gb,
        "estimated_output_gb": output_gb,
        "planning_only": True,
        "calibration_state": "UNMEASURED_ASSUMPTIONS",
        "execution_route": "fallback_alternative" if "-fallback-" in config.run_id else "primary",
        "command_or_notebook": _notebook_for(config),
    }


def _notebook_for(config: Any) -> str:
    stage = str(getattr(config, "stage", "S1"))
    benchmark = str(config.benchmark_id)
    if stage == "S1":
        return f"kaggle_max_ceiling/{ {'mmlu': '01', 'gsm8k': '02', 'bbh': '03'}[benchmark] }_valideval_common_panel_{benchmark}_t4x2.ipynb"
    if stage == "S5":
        return "kaggle_v7/10_s5_robustness_t4x2.ipynb"
    number = {
        ("S2", "mmlu"): "01",
        ("S2", "gsm8k"): "02",
        ("S2", "bbh"): "03",
        ("S3", "mmlu"): "04",
        ("S3", "gsm8k"): "05",
        ("S3", "bbh"): "06",
        ("S4", "mmlu"): "07",
        ("S4", "gsm8k"): "08",
        ("S4", "bbh"): "09",
    }[(stage, benchmark)]
    return f"kaggle_v7/{number}_{stage.lower()}_{benchmark}_t4x2.ipynb"


if __name__ == "__main__":
    raise SystemExit(main())
