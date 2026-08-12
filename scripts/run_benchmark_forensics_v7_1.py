from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from valideval.forensics.benchmark_v7_1 import analyze_frozen_manifest_forensics


def main() -> int:
    parser = argparse.ArgumentParser(description="Run source-permitted V7.1 benchmark forensics.")
    parser.add_argument("--freeze-root", type=Path, default=Path("results/freeze/study_c_v7"))
    parser.add_argument("--output", type=Path, default=Path("results/v7_1/forensics"))
    args = parser.parse_args()
    started = time.perf_counter()
    manifests = {
        benchmark: args.freeze_root / f"{benchmark}_scientific_full_v7.json"
        for benchmark in ("mmlu", "gsm8k", "bbh")
    }
    table, summary = analyze_frozen_manifest_forensics(manifests)
    summary["runtime_seconds"] = time.perf_counter() - started
    args.output.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output / "forensic_matches.csv", index=False)
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
