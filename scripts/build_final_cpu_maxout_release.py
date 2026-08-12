from __future__ import annotations

import argparse
import json
from pathlib import Path

from valideval.release.final_cpu_maxout import build_final_cpu_maxout_release


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build structured V7.2.1 final CPU-maxout reports and handoff artifacts."
    )
    parser.add_argument("--repository-root", default=".")
    args = parser.parse_args()
    result = build_final_cpu_maxout_release(Path(args.repository_root))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
