from __future__ import annotations

import argparse
import json

from valideval.evidence.ledger import build_claim_evidence_ledger


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the V5 claim-to-evidence ledger.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--csv", default="results/evidence/claim_evidence_ledger_v5.csv")
    parser.add_argument("--report", default="reports/v5/VALID_EVAL_V5_CLAIM_EVIDENCE_LEDGER.md")
    args = parser.parse_args()
    rows = build_claim_evidence_ledger(args.root, args.csv, args.report)
    print(json.dumps({"claim_count": len(rows), "status": "ok"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
