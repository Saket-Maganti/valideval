from __future__ import annotations

import argparse
import json

from valideval.planning.s3_proposal_v7_2_1 import propose_s3_from_s2


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a non-authorizing S3 proposal from S2.")
    parser.add_argument("--s2-summary", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = propose_s3_from_s2(args.s2_summary, output=args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "S3_PROPOSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
