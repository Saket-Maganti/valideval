from __future__ import annotations

import hashlib
import json
from pathlib import Path

FROZEN = {
    "results/v7/synthetic/confirmatory/summary.json": {
        "sha256": "1510f2d0d4c77b4dad9c1018b0ff3b75e5bad8cbf890c0ac9f4c344ac4dcf60a",
        "field": "acceptance_status",
        "value": "FROZEN_ACCEPTANCE_GATES_FAILED",
    },
    "results/v7_2/claim_policy/confirmation_summary.json": {
        "sha256": "fad39a12eb9fdd40aaf903db0940e85f599eed82648b69d6984fe737d466cb12",
        "field": "status",
        "value": "CLAIM_POLICY_CONFIRMATION_PASS",
    },
    "results/v7_2/v8/development_summary.json": {
        "sha256": "095b3af33ec18a05f41b4129cdccf8ca3b04f2e007555042da21d222747bb267",
        "field": "v8_confirmatory_status",
        "value": "NOT_RUN_NOT_AUTHORIZED_IN_V7_2",
    },
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    problems: list[str] = []
    for relative, contract in FROZEN.items():
        path = root / relative
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != contract["sha256"]:
            problems.append(f"{relative}: hash mismatch")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get(contract["field"]) != contract["value"]:
            problems.append(f"{relative}: frozen state mismatch")
    status = "FROZEN_HISTORY_PASS" if not problems else "FROZEN_HISTORY_FAIL"
    print(json.dumps({"status": status, "checked": sorted(FROZEN), "problems": problems}, indent=2))
    return 0 if not problems else 2


if __name__ == "__main__":
    raise SystemExit(main())
