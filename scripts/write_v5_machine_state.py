from __future__ import annotations

import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict[str, Any]:
    target = ROOT / path
    return json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}


def _command_state(ledger: dict[str, Any], name: str) -> dict[str, Any] | None:
    record = next((row for row in ledger.get("commands", []) if row["name"] == name), None)
    if record is None:
        return None
    return {
        "status": "pass" if record["exit_code"] == 0 else "fail",
        "exit_code": record["exit_code"],
        "duration_seconds": record["duration_seconds"],
        "command": record["command"],
    }


def main() -> int:
    reproduction = _load("results/evidence/mmlu_reproduction_v5/mmlu_reproduction_v5.json")
    ledger = _load("results/v5_validation/command_ledger_v5.json")
    gates = _load("reports/v5/final_gates_v5.json")
    leakage = _load("results/leakage/leakage_checks_v5.json")
    claim_counts: Counter[str] = Counter()
    claim_path = ROOT / "results/evidence/claim_evidence_ledger_v5.csv"
    if claim_path.exists():
        import csv

        with claim_path.open(encoding="utf-8", newline="") as handle:
            claim_counts.update(row["verification_status"] for row in csv.DictReader(handle))
    git_commit = _git(["git", "rev-parse", "HEAD"])
    git_branch = _git(["git", "branch", "--show-current"])
    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(ROOT),
        "git_commit": git_commit,
        "git_branch": git_branch,
        "git_dirty": True,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "unborn_git_repository": git_commit is None,
        },
        "package_install": _command_state(ledger, "clean_editable_install"),
        "tests": _command_state(ledger, "full_tests"),
        "lint": _command_state(ledger, "lint"),
        "format": _command_state(ledger, "format_check"),
        "type_check": _command_state(ledger, "type_check"),
        "package_build": _command_state(ledger, "package_build"),
        "notebook_validation": gates.get("notebook_validation"),
        "paper_build": _command_state(ledger, "paper_pdflatex_3"),
        "release_build": _command_state(ledger, "reviewer_release_build"),
        "primary_input_hashes": reproduction.get("hashes", {}),
        "reproduced_mmlu_metrics": reproduction.get("observed", {}),
        "claim_status_counts": dict(sorted(claim_counts.items())),
        "leakage_gate": gates.get("leakage_gate"),
        "model_identity_gate": gates.get("model_identity_gate"),
        "panel_power_gate": gates.get("panel_power_gate"),
        "notebook_gate": gates.get("notebook_gate"),
        "importer_gate": gates.get("importer_gate"),
        "cross_benchmark_gate": gates.get("cross_benchmark_evidence_gate"),
        "human_protocol_gate": gates.get("human_protocol_gate"),
        "synthetic_protocol_gate": gates.get("synthetic_protocol_gate"),
        "paper_scaffold_gate": gates.get("paper_scaffold_gate"),
        "remaining_blockers": gates.get("remaining_blockers", []),
        "exact_next_commands": gates.get("exact_next_commands", []),
        "overall_pre_execution_gate": gates.get("overall_pre_execution_gate"),
        "leakage_checks": leakage,
        "validation_ledger": "results/v5_validation/command_ledger_v5.json",
    }
    (ROOT / "VALID_EVAL_V5_MACHINE_STATE.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"status": "MACHINE_STATE_WRITTEN", "path": "VALID_EVAL_V5_MACHINE_STATE.json"},
            indent=2,
        )
    )
    return 0


def _git(command: list[str]) -> str | None:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


if __name__ == "__main__":
    raise SystemExit(main())
