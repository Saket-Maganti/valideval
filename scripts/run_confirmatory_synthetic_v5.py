#!/usr/bin/env python3
"""Run V5 synthetic protocol dry-run or non-evidence fixture validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from valideval.synthetic.confirmatory import run_confirmatory_synthetic_v5


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/synthetic/confirmatory_synthetic_v5.yaml"),
    )
    parser.add_argument(
        "--public-output-dir",
        type=Path,
        default=Path("results/synthetic/confirmatory_v5/public"),
    )
    parser.add_argument(
        "--private-output-dir",
        type=Path,
        default=Path("results/synthetic/confirmatory_v5_private"),
    )
    parser.add_argument("--mode", choices=("dry-run", "fixture"), default="dry-run")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_confirmatory_synthetic_v5(
        args.config,
        public_output_dir=args.public_output_dir,
        private_output_dir=args.private_output_dir,
        mode=args.mode,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
