from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from valideval.transport import analyze_transportability


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7 transportability analysis or build gate.")
    parser.add_argument("--effects", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/v7_1/transport"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.effects is None:
        template = pd.DataFrame(
            columns=[
                "estimand",
                "benchmark",
                "estimate",
                "standard_error",
                "exact_identity",
                "fold_manifest",
                "independent_families",
            ]
        )
        template.to_csv(args.output / "transport_effects_template.csv", index=False)
        result = {
            "overall_status": "BLOCKED",
            "reason": "No exact-model controlled cross-benchmark effects exist before GPU Study C.",
            "build_status": "TRANSPORT_FOLD_PROVENANCE_REQUIRED",
        }
    else:
        result = analyze_transportability(pd.read_csv(args.effects))
        result["build_status"] = "TRANSPORT_FOLD_PROVENANCE_READY"
    (args.output / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(result["build_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
