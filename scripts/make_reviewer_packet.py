#!/usr/bin/env python3
"""Build a safe reviewer packet zip without raw/cache artifacts."""

from __future__ import annotations

import argparse
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

MAX_CSV_BYTES = 5 * 1024 * 1024
DEFAULT_OUTPUT = "dist/valideval_reviewer_packet.zip"

REQUIRED_FILES = (
    "README.md",
    "CLAIMS_LEDGER_NEURIPS.md",
    "SYNTHETIC_EVIDENCE_STATUS_TABLE.md",
    "MMLU_EVIDENCE_GATE_REPORT.md",
    "PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md",
    "STATIC_CONFIRMATORY_PREFLIGHT_REPORT.md",
    "RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md",
    "CONFIRMATORY_RUN_COMMAND_MANIFEST.md",
    "REVIEWER_PACKET_MANIFEST.md",
    "REVIEWER_READING_GUIDE.md",
    "ARTIFACT_EXCLUSION_POLICY.md",
    "RELEASE_READINESS_CHECKLIST.md",
    "NO_RUN_RELEASE_AUDIT.md",
)

OPTIONAL_SAFE_FILES = (
    "VALID_EVAL_EVIDENCE_RECONCILIATION_AUDIT.md",
    "CLAIMS_AND_STORY_SYNC_AUDIT.md",
    "NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md",
    "MMLU_REAL_PANEL_CORE_RUN_REPORT.md",
    "MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md",
    "MMLU_IRT_PSYCHOMETRIC_RUN_REPORT.md",
    "MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md",
    "DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md",
    "SECOND_BENCHMARK_SELECTION_AND_EXECUTION_PLAN.md",
    "SECOND_BENCHMARK_RUN_REPORT.md",
    "KAGGLE_NOTEBOOK_BUILD_REPORT.md",
    "KAGGLE_OUTPUT_IMPORT_MANIFEST.md",
    "KAGGLE_OUTPUT_IMPORT_AND_VALIDATION_REPORT.md",
    "ARTIFACT_MANIFEST_FOR_PAPER.md",
    "FIGURE_TABLE_COMPLETENESS_AUDIT.md",
    "PAPER_REWRITE_AND_COMPILE_REPORT.md",
    "BUILD_ONLY_POLISH_AUDIT.md",
    "CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md",
    "DRYRUN_AUDIT_PACKET_INCLUSION_DECISION.md",
    "NO_RUN_DRYRUN_SURFACE_AUDIT.md",
    "PREREGISTRATION_REVIEW_AUDIT.md",
    "REVIEWER_PACKET_POST_DRYRUN_AUDIT.md",
    "REPRODUCIBILITY_AUDIT_TRAIL.md",
    "SYNTHETIC_VALIDATION_ARTIFACT_INVENTORY.md",
    "SYNTHETIC_VALIDATION_NARRATIVE_AUDIT.md",
    "VALIDATOR_VALIDATION_STATUS.md",
    "V4_PRE_EXECUTION_READINESS_AUDIT.md",
    "GSM8K_NOTEBOOK_HARDENING_REPORT.md",
    "THIRD_BENCHMARK_NOTEBOOK_HARDENING_REPORT.md",
    "KAGGLE_OUTPUT_IMPORTER_V4_REPORT.md",
    "POST_IMPORT_ANALYSIS_ROUTER_V4_REPORT.md",
    "CROSS_BENCHMARK_RUNNER_V4_REPORT.md",
    "PAPER_AUTO_UPDATE_V4_REPORT.md",
    "BIBLIOGRAPHY_PIPELINE_REPAIR_V4_REPORT.md",
    "AFTER_KAGGLE_ONE_COMMAND_PIPELINE_V4_REPORT.md",
    "REVIEWER_PACKET_V4_PRE_EXECUTION_AUDIT.md",
    "FINAL_V4_PRE_EXECUTION_GATE.md",
    "CITATION.cff",
    "LICENSE",
    "pyproject.toml",
    "VERSION",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
)

INCLUDE_DIRS = (
    "paper",
    "configs",
    "docs",
    "src",
    "scripts",
    "templates",
    "tests",
    "schemas",
    "examples",
    "kaggle",
    "kaggle_v3",
    "kaggle_gsm8k",
    "kaggle_third_benchmark",
    "kaggle_general",
)

OPTIONAL_SAFE_GLOBS = ("results/no_run_dryrun_surface/*.manifest.json",)

EXCLUDED_DIR_PREFIXES = (
    "cache",
    "kaggle_outputs",
    "data/external",
    "results/mmlu",
    "results/synthetic",
    "dist",
    "build",
    "bundles",
    "dashboard_data",
    "external_review_packet",
    "external_review_packets",
    "leaderboard",
    "local_outputs",
    "reportcards",
    "site",
    "validation_reports/_cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
)

EXCLUDED_FILE_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}


@dataclass(frozen=True)
class PacketBuild:
    output_path: Path
    included_files: tuple[str, ...]
    skipped_files: tuple[str, ...]

    @property
    def file_count(self) -> int:
        return len(self.included_files)


def _is_relative_to(path: Path, prefix: Path) -> bool:
    try:
        path.relative_to(prefix)
    except ValueError:
        return False
    return True


def _has_prefix(rel_path: Path, prefix: str) -> bool:
    prefix_parts = Path(prefix).parts
    return rel_path.parts[: len(prefix_parts)] == prefix_parts


def should_exclude(path: Path, repo_root: Path) -> bool:
    rel_path = path.relative_to(repo_root)
    if any(part == "__pycache__" for part in rel_path.parts):
        return True
    if any(part.startswith(".") for part in rel_path.parts):
        return True
    if any(_has_prefix(rel_path, prefix) for prefix in EXCLUDED_DIR_PREFIXES):
        return True
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if path.suffix in EXCLUDED_SUFFIXES:
        return True
    if path.suffix == ".jsonl":
        return True
    if path.suffix == ".csv" and path.stat().st_size > MAX_CSV_BYTES:
        return True
    return False


def _iter_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.exists():
        return []
    return [path for path in root.rglob("*") if path.is_file()]


def collect_packet_files(repo_root: Path) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    missing = [rel for rel in REQUIRED_FILES if not (repo_root / rel).is_file()]
    missing.extend(rel for rel in INCLUDE_DIRS if not (repo_root / rel).is_dir())
    if missing:
        raise FileNotFoundError("missing required packet paths: " + ", ".join(sorted(missing)))

    candidates: set[Path] = set()
    for rel in REQUIRED_FILES + OPTIONAL_SAFE_FILES:
        path = repo_root / rel
        if path.is_file():
            candidates.add(path)
    for pattern in OPTIONAL_SAFE_GLOBS:
        candidates.update(path for path in repo_root.glob(pattern) if path.is_file())
    for rel in INCLUDE_DIRS:
        candidates.update(_iter_files(repo_root / rel))

    included: list[Path] = []
    skipped: list[str] = []
    for path in sorted(candidates):
        if should_exclude(path, repo_root):
            skipped.append(path.relative_to(repo_root).as_posix())
            continue
        included.append(path)
    return tuple(included), tuple(skipped)


def build_reviewer_packet(
    repo_root: Path | str, output_path: Path | str | None = None
) -> PacketBuild:
    root = Path(repo_root).resolve()
    output = Path(output_path) if output_path is not None else root / DEFAULT_OUTPUT
    if not output.is_absolute():
        output = root / output
    output = output.resolve()

    if not _is_relative_to(output, root):
        raise ValueError(f"output path must be inside repo root: {output}")

    included, skipped = collect_packet_files(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in included:
            archive.write(path, path.relative_to(root).as_posix())

    return PacketBuild(
        output_path=output,
        included_files=tuple(path.relative_to(root).as_posix() for path in included),
        skipped_files=skipped,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the safe ValidEval reviewer packet zip.")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root to package.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        type=Path,
        help=f"Output zip path, relative to repo root by default. Default: {DEFAULT_OUTPUT}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packet = build_reviewer_packet(args.repo_root, args.output)
    print(f"Created {packet.output_path}")
    print(f"Included files: {packet.file_count}")
    print(f"Skipped files: {len(packet.skipped_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
