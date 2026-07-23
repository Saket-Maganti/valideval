from __future__ import annotations

import argparse
import json
from pathlib import Path

from valideval.release.forensics_v5 import build_repository_forensics


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze the ValidEval V5 repository state.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="reports/v5")
    args = parser.parse_args()
    payload = build_repository_forensics(Path(args.root), Path(args.output))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
