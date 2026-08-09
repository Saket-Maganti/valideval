from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from valideval.measurement.regime_study import run_regime_study


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7 measurement-model regime simulation.")
    parser.add_argument("--output", type=Path, default=Path("results/v7/measurement/regime_study"))
    args = parser.parse_args()
    started = time.perf_counter()
    results = run_regime_study()
    args.output.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output / "regime_map.csv", index=False)
    summary = {
        "status": "MEASUREMENT_REGIME_STUDY_COMPLETE",
        "scenarios": len(results),
        "regime_counts": results["regime"].value_counts().to_dict(),
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": (
            "The regime map concerns recovery under declared generators; it does not establish "
            "latent-trait validity in observed benchmarks."
        ),
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
