from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _add_src_to_path() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def main() -> None:
    _add_src_to_path()
    from valideval.release.paper_assets import generate_paper_assets

    parser = argparse.ArgumentParser(description="Generate paper figures/tables from results/.")
    parser.add_argument("--benchmark", default="toy_mcq")
    parser.add_argument("--panel", default="mock")
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--paper-dir", default="paper")
    args = parser.parse_args()
    payload = generate_paper_assets(
        benchmark=args.benchmark,
        panel=args.panel,
        results_root=args.results_root,
        paper_dir=args.paper_dir,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
