#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write a ValidEval V4 venue gate from local artifacts."
    )
    parser.add_argument("--output", default="FINAL_AFTER_KAGGLE_GATE_V4.md")
    args = parser.parse_args()
    output = ROOT / args.output
    state = collect_state()
    output.write_text(render_gate(state), encoding="utf-8")
    print(json.dumps({"gate": str(output), **state}, indent=2, sort_keys=True))
    return 0 if state["status"] != "blocked" else 1


def collect_state() -> dict[str, Any]:
    matrices = {
        "mmlu": ROOT / "cache/mmlu/wide/matrix.csv",
        "gsm8k": ROOT / "cache/gsm8k/wide/matrix.csv",
        "bbh": ROOT / "cache/bbh/wide/matrix.csv",
        "truthfulqa": ROOT / "cache/truthfulqa/wide/matrix.csv",
    }
    available = {name: path.exists() for name, path in matrices.items()}
    cross = load_json(ROOT / "results/cross_benchmark/cross_benchmark_manifest.json")
    if (
        available.get("mmlu")
        and available.get("gsm8k")
        and (available.get("bbh") or available.get("truthfulqa"))
    ):
        verdict = "READY_FOR_THREE_BENCHMARK_REVIEWER_AUDIT"
        status = "ready"
    elif available.get("mmlu") and available.get("gsm8k"):
        verdict = "READY_FOR_TWO_BENCHMARK_REVIEWER_AUDIT"
        status = "ready"
    else:
        verdict = "BLOCKED_NEED_IMPORTED_GSM8K_MATRIX"
        status = "blocked"
    return {
        "status": status,
        "verdict": verdict,
        "available_matrices": available,
        "cross_benchmark_status": cross.get("status", "missing"),
    }


def render_gate(state: dict[str, Any]) -> str:
    lines = [
        "# Final After-Kaggle Gate V4",
        "",
        f"Verdict: `{state['verdict']}`",
        "",
        "This gate is generated from local imported artifacts only. It does not upgrade human-label or external-label claims unless those artifacts exist and validate.",
        "",
        "## Matrix Availability",
    ]
    for name, available in state["available_matrices"].items():
        lines.append(f"- `{name}`: `{available}`")
    lines.extend(
        [
            "",
            f"Cross-benchmark status: `{state['cross_benchmark_status']}`",
            "",
            "Claims remain protocol-scoped and multidimensional.",
        ]
    )
    return "\n".join(lines) + "\n"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
