from __future__ import annotations

import json
from pathlib import Path

from valideval.leakage.audit_v5 import build_leakage_audit_v5

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    payload = build_leakage_audit_v5(ROOT, "results/leakage")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
