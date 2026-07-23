#!/usr/bin/env python3
"""Static no-run preflight for future synthetic confirmatory validation."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_PREREGISTRATION_DOCS = (
    "PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md",
    "PREREGISTRATION_REVIEW_AUDIT.md",
    "CONFIRMATORY_RUN_COMMAND_MANIFEST.md",
    "RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md",
    "paper/appendices/cross_flaw_heldout_preregistration_note.md",
)

REQUIRED_CONFIGS = (
    "configs/validation/synthetic_default.yaml",
    "configs/validation/heldout_default.yaml",
)

REQUIRED_TEMPLATES = (
    "templates/reports/CROSS_FLAW_CONFIRMATORY_REPORT_TEMPLATE.md",
    "templates/reports/HELDOUT_CONFIRMATORY_REPORT_TEMPLATE.md",
    "templates/reports/SYNTHETIC_CONFIRMATORY_CLAIM_STATUS_REPORT_TEMPLATE.md",
    "templates/reports/SYNTHETIC_CONFIRMATORY_REVIEWER_APPENDIX_TEMPLATE.md",
)

OUTPUT_DIRS = (
    "results/synthetic/cross_flaw_confirmatory",
    "results/synthetic/heldout_confirmatory",
)

FAILURE_CASE_DOC = "CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md"
CLAIMS_LEDGERS = ("CLAIMS_LEDGER_NEURIPS.md", "paper/CLAIMS_LEDGER.md")

EXPECTED_FAILURE_IDS = (
    "CF-01",
    "CF-02",
    "CF-03",
    "CF-04",
    "CF-05",
    "CF-06",
    "CF-07",
    "HO-01",
    "HO-02",
    "HO-03",
)

BLOCKED_CLAIMS = (
    "All diagnostics generalize across flaw families.",
    "Synthetic validation proves real benchmark validity.",
    "Cross-flaw specificity is solved.",
    "Held-out transfer is solved.",
    "ValidEval detects real benchmark errors.",
    "MMLU-Redux validates the diagnostics.",
    "GPQA establishes broad validity evidence.",
)

FUTURE_COMMANDS = (
    (
        "python3 -m valideval validate-diagnostics-cross-flaw \\\n"
        "  --config configs/validation/synthetic_default.yaml \\\n"
        "  --output results/synthetic/cross_flaw_confirmatory"
    ),
    (
        "python3 -m valideval validate-diagnostics-heldout \\\n"
        "  --config configs/validation/heldout_default.yaml \\\n"
        "  --output results/synthetic/heldout_confirmatory"
    ),
)


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class PreflightResult:
    repo_root: Path
    checks: tuple[Check, ...]
    future_commands: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return all(check.ok for check in self.checks)


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _missing_paths(repo_root: Path, paths: tuple[str, ...]) -> list[str]:
    return [rel for rel in paths if not (repo_root / rel).is_file()]


def _check_files(repo_root: Path, label: str, paths: tuple[str, ...]) -> Check:
    missing = _missing_paths(repo_root, paths)
    if missing:
        return Check(label, False, "missing: " + ", ".join(missing))
    return Check(label, True, f"found {len(paths)} required files")


def _nearest_existing_parent(path: Path) -> Path | None:
    current = path
    while current != current.parent:
        if current.exists():
            return current
        current = current.parent
    return current if current.exists() else None


def _check_output_dirs(repo_root: Path) -> Check:
    details: list[str] = []
    failures: list[str] = []
    for rel in OUTPUT_DIRS:
        path = repo_root / rel
        if path.exists() and not path.is_dir():
            failures.append(f"{rel} exists but is not a directory")
            continue
        target = path if path.exists() else _nearest_existing_parent(path)
        if target is None:
            failures.append(f"{rel} has no existing writable parent")
            continue
        if not os.access(target, os.W_OK | os.X_OK):
            failures.append(f"{rel} parent is not writable: {target.relative_to(repo_root)}")
            continue
        if path.exists():
            details.append(f"{rel} exists and is writable")
        else:
            details.append(f"{rel} can be created under {target.relative_to(repo_root)}")
    if failures:
        return Check("future output directories", False, "; ".join(failures))
    return Check("future output directories", True, "; ".join(details))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check_failure_cases(repo_root: Path) -> Check:
    path = repo_root / FAILURE_CASE_DOC
    if not path.is_file():
        return Check("documented failure cases", False, f"missing: {FAILURE_CASE_DOC}")
    text = _read_text(path)
    missing_ids = [case_id for case_id in EXPECTED_FAILURE_IDS if case_id not in text]
    required_phrases = (
        "Cross-flaw specificity remains `WEAK`",
        "Held-out generator transfer remains `WEAK`",
    )
    missing_phrases = [phrase for phrase in required_phrases if phrase not in text]
    problems = missing_ids + missing_phrases
    if problems:
        return Check("documented failure cases", False, "missing: " + ", ".join(problems))
    return Check(
        "documented failure cases",
        True,
        "found CF-01 through CF-07, HO-01 through HO-03, and WEAK status language",
    )


def _check_claims_ledgers(repo_root: Path) -> Check:
    problems: list[str] = []
    for rel in CLAIMS_LEDGERS:
        path = repo_root / rel
        if not path.is_file():
            problems.append(f"{rel} missing")
            continue
        text = _read_text(path).lower()
        for claim in BLOCKED_CLAIMS:
            if claim.lower() not in text:
                problems.append(f"{rel} missing blocked claim: {claim}")
    if problems:
        return Check("blocked claims in ledgers", False, "; ".join(problems))
    return Check(
        "blocked claims in ledgers",
        True,
        f"all {len(BLOCKED_CLAIMS)} blocked claims appear in both ledgers",
    )


def run_preflight(repo_root: Path | str | None = None) -> PreflightResult:
    root = Path(repo_root) if repo_root is not None else default_repo_root()
    root = root.resolve()
    checks = (
        _check_files(root, "preregistration and runbook docs", REQUIRED_PREREGISTRATION_DOCS),
        _check_files(root, "frozen validation configs", REQUIRED_CONFIGS),
        _check_files(root, "result report templates", REQUIRED_TEMPLATES),
        _check_output_dirs(root),
        _check_failure_cases(root),
        _check_claims_ledgers(root),
    )
    return PreflightResult(root, checks, FUTURE_COMMANDS)


def format_report(result: PreflightResult) -> str:
    lines = [
        "Confirmatory synthetic validation preflight",
        f"Repo root: {result.repo_root}",
        "Mode: static no-run check",
        (
            "No validation commands were executed; no synthetic generation, inference, downloads, "
            "metric recomputation, or threshold tuning was performed."
        ),
        "",
        "Checks:",
    ]
    for check in result.checks:
        status = "OK" if check.ok else "FAIL"
        lines.append(f"[{status}] {check.name}: {check.detail}")
    lines.extend(
        [
            "",
            "Future commands (not executed):",
        ]
    )
    for command in result.future_commands:
        lines.append("# Future only - print-only preflight; do not run during build-only polish.")
        lines.append(command)
    lines.extend(
        [
            "",
            "Evidence-state reminder:",
            "- Cross-flaw specificity remains WEAK until approved confirmatory artifacts pass gates.",
            "- Held-out generator transfer remains WEAK until approved confirmatory artifacts pass gates.",
            "- MMLU-Redux remains weak/negative external validation.",
            "- GPQA remains protocol/demo unless wide-panel evidence exists.",
            "",
            f"Result: {'PASS' if result.passed else 'FAIL'}",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Static no-run preflight for future confirmatory synthetic validation."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root to check. Defaults to the parent of this script directory.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_preflight(args.repo_root)
    print(format_report(result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
