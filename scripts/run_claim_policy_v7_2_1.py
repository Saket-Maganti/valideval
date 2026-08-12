from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from valideval.execution.manifest import atomic_write_text
from valideval.statistics.claim_policy_v7_2_1 import (
    load_native_policy_spec,
    native_policy_confirmation,
    native_policy_development,
    records_sha256,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V7.2.1 native known-truth policy study.")
    parser.add_argument("--phase", choices=("develop", "confirm"), required=True)
    parser.add_argument("--config", default="configs/statistics/claim_policy_v7_2_1.yaml")
    parser.add_argument("--output-root", default="results/final_cpu_maxout/claim_policy")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    args = parser.parse_args()

    started = time.perf_counter()
    spec = load_native_policy_spec(args.config)
    output = Path(args.output_root)
    output.mkdir(parents=True, exist_ok=True)
    if args.phase == "develop":
        records, selection, freeze = native_policy_development(spec, quick=args.quick)
        atomic_write_text(
            output / "development_validation_records.csv",
            records.to_csv(index=False, lineterminator="\n"),
        )
        selection = {
            **selection,
            "records_sha256": records_sha256(records),
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(output / "selection_metrics.json", selection)
        write_json(output / "policy_freeze.json", freeze)
        payload = {"selection": selection, "freeze": freeze}
    else:
        freeze = json.loads((output / "policy_freeze.json").read_text(encoding="utf-8"))
        records, summary = native_policy_confirmation(spec, freeze, quick=args.quick)
        atomic_write_text(
            output / "confirmation_records.csv",
            records.to_csv(index=False, lineterminator="\n"),
        )
        summary = {
            **summary,
            "records_sha256": records_sha256(records),
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(output / "confirmation_summary.json", summary)
        payload = summary
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
