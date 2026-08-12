from __future__ import annotations

import argparse
import json
from pathlib import Path

from valideval.execution.authorization_v7_1 import (
    StudyCAuthorizationEvidence,
    assess_study_c_authorization,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate sequential Study-C authorization.")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("results/v7_1/study_c_authorization.json")
    )
    args = parser.parse_args()
    supplied = {}
    if args.evidence is not None:
        supplied = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = assess_study_c_authorization(StudyCAuthorizationEvidence(**supplied))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(" ".join(result["stages"][stage]["status"] for stage in ("s1", "s2", "s3", "s4")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
