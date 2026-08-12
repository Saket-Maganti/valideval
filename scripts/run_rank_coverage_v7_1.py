from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from valideval.statistics.rank_inference_v7_1 import simulate_simultaneous_rank_coverage


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7.1 simultaneous-rank coverage checks.")
    parser.add_argument("--simulations", type=int, default=200)
    parser.add_argument("--bootstrap", type=int, default=300)
    parser.add_argument("--output", type=Path, default=Path("results/v7_1/rank_coverage"))
    args = parser.parse_args()
    started = time.perf_counter()
    rows = []
    for tied in (False, True):
        for correlation in (0.0, 0.6, 0.9):
            rows.append(
                simulate_simultaneous_rank_coverage(
                    simulations=args.simulations,
                    bootstrap_draws=args.bootstrap,
                    family_correlation=correlation,
                    tied_truth=tied,
                    seed=7301 + int(correlation * 100) + int(tied) * 1_000,
                )
            )
    payload = {
        "status": "SIMULTANEOUS_RANK_INFERENCE_READY",
        "method": "BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS",
        "coverage_scenarios": rows,
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": "Coverage evidence is simulation-family-specific, not a universal theorem.",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "coverage_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{payload['status']}: {payload['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
