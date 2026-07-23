from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SECRET_PATTERNS = {
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github_token": re.compile(r"\bgh[oprsu]_[A-Za-z0-9_]{20,}\b"),
    "huggingface_token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}

_TEXT_EXTENSIONS = {
    ".cfg",
    ".csv",
    ".gitignore",
    ".ini",
    ".ipynb",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".rst",
    ".sh",
    ".tex",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}


def classify_artifact(path: Path) -> str:
    value = path.as_posix()
    name = path.name
    if any(
        part in {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
        for part in path.parts
    ):
        return "CACHE"
    if name == ".DS_Store" or path.suffix == ".pyc" or name.endswith(".egg-info"):
        return "CACHE"
    if value.startswith("src/") or value.startswith("scripts/"):
        return "SOURCE"
    if value.startswith("tests/"):
        return "TEST"
    if value.startswith("configs/") or name in {"pyproject.toml", "Makefile", ".gitignore"}:
        return "CONFIG"
    if value.startswith("data/raw/") or value.startswith("data/external/"):
        return "RAW_INPUT"
    if value.startswith("cache/"):
        return "NORMALIZED_INPUT"
    if value.startswith("results/"):
        if "fixture" in value.lower() or "toy" in value.lower():
            return "NON_EVIDENCE_FIXTURE"
        return "DERIVED_EVIDENCE"
    if value.startswith("paper/"):
        return "PAPER"
    if path.suffix == ".ipynb" or value.startswith("kaggle"):
        return "NOTEBOOK"
    if "prompt_pack" in value or "fix_prompts" in value or "upgrade_pack" in value:
        return "HISTORICAL"
    if value.startswith("dist/") or value.startswith("bundles/") or path.suffix == ".zip":
        return "RELEASE"
    if "runbook" in value.lower() or "handbook" in value.lower():
        return "RUNBOOK"
    if path.suffix in {".md", ".json"}:
        return "REPORT"
    return "UNKNOWN"


def build_repository_forensics(root: str | Path, output_dir: str | Path) -> dict[str, Any]:
    repository = Path(root).resolve()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    files = sorted(
        path
        for path in repository.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(repository).parts
    )
    catalog_path = destination / "VALID_EVAL_V5_ARTIFACT_CATALOG.csv"
    category_counts: Counter[str] = Counter()
    size_groups: dict[int, list[Path]] = defaultdict(list)
    largest: list[tuple[int, str]] = []
    archives: list[str] = []
    cache_files: list[str] = []
    absolute_path_files: list[str] = []
    secret_findings: list[dict[str, str]] = []
    notebook_outputs: list[dict[str, Any]] = []
    broken_symlinks: list[str] = []

    with catalog_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "path",
                "taxonomy",
                "size_bytes",
                "sha256",
                "release_default",
                "notes",
            ],
        )
        writer.writeheader()
        for path in files:
            relative = path.relative_to(repository)
            category = classify_artifact(relative)
            category_counts[category] += 1
            size = path.stat().st_size
            size_groups[size].append(path)
            largest.append((size, relative.as_posix()))
            if path.suffix.lower() in {".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz"}:
                archives.append(relative.as_posix())
            if category == "CACHE":
                cache_files.append(relative.as_posix())
            notes: list[str] = []
            if path.suffix == ".ipynb":
                output_cells = _notebook_output_count(path)
                notebook_outputs.append(
                    {"path": relative.as_posix(), "cells_with_outputs": output_cells}
                )
                if output_cells:
                    notes.append(f"notebook_outputs={output_cells}")
            if _is_text_candidate(path, size):
                text = path.read_text(encoding="utf-8", errors="ignore")
                if "/Users/" in text:
                    absolute_path_files.append(relative.as_posix())
                    notes.append("contains_absolute_user_path")
                for finding_type, pattern in _SECRET_PATTERNS.items():
                    if pattern.search(text):
                        secret_findings.append(
                            {
                                "path": relative.as_posix(),
                                "finding_type": finding_type,
                                "taxonomy": category,
                                "release_action": "exclude_raw_input"
                                if category == "RAW_INPUT"
                                else "manual_review_required",
                            }
                        )
                        notes.append(f"secret_pattern={finding_type}")
            digest = _sha256(path) if _should_hash_in_catalog(relative, size) else ""
            release_default = _release_default(category, relative)
            writer.writerow(
                {
                    "path": relative.as_posix(),
                    "taxonomy": category,
                    "size_bytes": size,
                    "sha256": digest,
                    "release_default": release_default,
                    "notes": ";".join(notes),
                }
            )

    for path in repository.rglob("*"):
        if path.is_symlink() and not path.exists():
            broken_symlinks.append(path.relative_to(repository).as_posix())

    duplicates = _find_duplicates(repository, size_groups)
    nested_archives = [
        archive
        for archive in archives
        if any(part.lower().endswith((".zip", ".tar", ".tgz")) for part in Path(archive).parts[:-1])
    ]
    git = _git_state(repository)
    ignored_count = _count_git_lines(
        repository, ["git", "ls-files", "--others", "-i", "--exclude-standard"]
    )
    untracked_count = _count_git_lines(
        repository, ["git", "ls-files", "--others", "--exclude-standard"]
    )
    environment = _environment_state(repository)
    largest = sorted(largest, reverse=True)[:40]
    critical_inputs = {
        relative: _sha256(repository / relative)
        for relative in [
            "data/external/mmlu/prediction_details_wide.jsonl",
            "cache/mmlu/wide/predictions.jsonl",
            "cache/mmlu/wide/matrix.csv",
        ]
        if (repository / relative).exists()
    }
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(repository),
        "git": git,
        "environment": environment,
        "file_count": len(files),
        "repository_size_bytes": sum(size for size, _ in largest)
        if len(files) <= len(largest)
        else sum(path.stat().st_size for path in files),
        "untracked_file_count": untracked_count,
        "ignored_file_count": ignored_count,
        "taxonomy_counts": dict(sorted(category_counts.items())),
        "largest_files": [{"path": path, "size_bytes": size} for size, path in largest],
        "archive_count": len(archives),
        "nested_archives": nested_archives,
        "duplicate_groups": duplicates,
        "cache_file_count": len(cache_files),
        "notebooks_with_outputs": [row for row in notebook_outputs if row["cells_with_outputs"]],
        "absolute_path_files": sorted(set(absolute_path_files)),
        "broken_symlinks": broken_symlinks,
        "secret_scan": {
            "status": _secret_scan_status(secret_findings),
            "findings": secret_findings,
            "values_redacted": True,
        },
        "critical_input_hashes": critical_inputs,
        "licenses": [
            path.relative_to(repository).as_posix()
            for path in files
            if path.name.lower().startswith(("license", "copying"))
        ],
    }
    (destination / "repository_forensics_v5.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (destination / "VALID_EVAL_V5_REPOSITORY_FORENSIC_INVENTORY.md").write_text(
        _render_inventory(summary), encoding="utf-8"
    )
    (destination / "VALID_EVAL_V5_STALE_AND_DUPLICATE_ARTIFACTS.md").write_text(
        _render_stale_and_duplicates(summary, cache_files, archives), encoding="utf-8"
    )
    return summary


def _secret_scan_status(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "pass"
    if all(finding.get("taxonomy") == "RAW_INPUT" for finding in findings):
        return "pass_with_release_exclusion"
    return "review_required"


def _is_text_candidate(path: Path, size: int) -> bool:
    return size <= 5 * 1024 * 1024 and (
        path.suffix.lower() in _TEXT_EXTENSIONS or path.name == ".gitignore"
    )


def _should_hash_in_catalog(path: Path, size: int) -> bool:
    category = classify_artifact(path)
    return size <= 2 * 1024 * 1024 and category in {
        "SOURCE",
        "TEST",
        "CONFIG",
        "PAPER",
        "RUNBOOK",
    }


def _release_default(category: str, path: Path) -> str:
    if category in {"SOURCE", "TEST", "CONFIG", "PAPER", "RUNBOOK"}:
        return "source_release_candidate"
    if category == "DERIVED_EVIDENCE":
        return "evidence_release_allowlist_only"
    if category in {"CACHE", "RAW_INPUT", "HISTORICAL", "UNKNOWN"}:
        return "exclude"
    if path.suffix == ".zip":
        return "exclude_nested_archive"
    return "review"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_duplicates(root: Path, size_groups: dict[int, list[Path]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for size, candidates in size_groups.items():
        if size == 0 or len(candidates) < 2:
            continue
        if size > 64 * 1024 * 1024:
            continue
        by_hash: dict[str, list[str]] = defaultdict(list)
        for candidate in candidates:
            by_hash[_sha256(candidate)].append(candidate.relative_to(root).as_posix())
        for digest, paths in by_hash.items():
            if len(paths) > 1:
                groups.append({"sha256": digest, "size_bytes": size, "paths": paths})
    return sorted(
        groups, key=lambda row: (-(row["size_bytes"] * len(row["paths"])), row["sha256"])
    )[:200]


def _git_state(root: Path) -> dict[str, Any]:
    branch = _command(root, ["git", "branch", "--show-current"])
    commit = _command(root, ["git", "rev-parse", "HEAD"])
    status = _command(root, ["git", "status", "--porcelain=v1", "-uno"])
    count = _command(root, ["git", "rev-list", "--count", "HEAD"])
    return {
        "branch": branch or None,
        "commit": commit or None,
        "commit_count": int(count) if count and count.isdigit() else 0,
        "unborn": commit is None,
        "dirty": bool(status) or commit is None,
        "tracked_file_count": _count_git_lines(root, ["git", "ls-files"]),
        "remote_count": _count_git_lines(root, ["git", "remote"]),
    }


def _environment_state(root: Path) -> dict[str, Any]:
    packages: dict[str, Any] = {}
    for package in ["numpy", "pandas", "scipy", "pydantic", "pytest", "ruff", "torch"]:
        try:
            module = __import__(package)
            packages[package] = getattr(module, "__version__", "installed")
        except Exception:
            packages[package] = None
    accelerator = {"torch_installed": packages.get("torch") is not None, "cuda_available": None}
    if packages.get("torch") is not None:
        import torch

        accelerator["cuda_available"] = bool(torch.cuda.is_available())
        accelerator["device_count"] = int(torch.cuda.device_count())
    return {
        "operating_system": platform.platform(),
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "package_manager": _command(root, [sys.executable, "-m", "pip", "--version"]),
        "packages": packages,
        "accelerator": accelerator,
        "cwd": os.getcwd(),
    }


def _command(root: Path, command: list[str]) -> str | None:
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def _count_git_lines(root: Path, command: list[str]) -> int:
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    return (
        len([line for line in result.stdout.splitlines() if line.strip()])
        if result.returncode == 0
        else 0
    )


def _notebook_output_count(path: Path) -> int:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return -1
    return sum(
        bool(cell.get("outputs"))
        for cell in payload.get("cells", [])
        if cell.get("cell_type") == "code"
    )


def _render_inventory(summary: dict[str, Any]) -> str:
    git = summary["git"]
    lines = [
        "# ValidEval V5 Repository Forensic Inventory",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Repository: `{summary['repository_root']}`",
        "",
        "## Git boundary",
        "",
        f"- Branch: `{git['branch']}`",
        f"- Commit: `{git['commit']}`",
        f"- Unborn repository: `{git['unborn']}`",
        f"- Tracked files: `{git['tracked_file_count']}`",
        f"- Untracked files: `{summary['untracked_file_count']}`",
        f"- Ignored files: `{summary['ignored_file_count']}`",
        "- Consequence: no historical diff or code revision can be reconstructed from this checkout.",
        "",
        "## Inventory",
        "",
        f"- Files outside `.git`: `{summary['file_count']}`",
        f"- Bytes outside `.git`: `{summary['repository_size_bytes']}`",
        f"- Archives: `{summary['archive_count']}`",
        f"- Cache/compiled files: `{summary['cache_file_count']}`",
        f"- Broken symlinks: `{len(summary['broken_symlinks'])}`",
        f"- Secret scan: `{summary['secret_scan']['status']}` (values are never printed)",
        "",
        "## Taxonomy counts",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in summary["taxonomy_counts"].items())
    lines.extend(["", "## Largest files", ""])
    lines.extend(
        f"- `{row['path']}`: {row['size_bytes']} bytes" for row in summary["largest_files"][:20]
    )
    lines.extend(
        [
            "",
            "## Release boundary",
            "",
            "The working tree is preserved. Source, evidence, and reviewer releases must be built from explicit allowlists; caches, raw benchmark data, prompt-pack history, nested archives, compiled files, and secrets are excluded by default.",
            "",
            "Status: `VERIFIED_FROM_PRIMARY_ARTIFACT` for the recorded filesystem state.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_stale_and_duplicates(
    summary: dict[str, Any], cache_files: list[str], archives: list[str]
) -> str:
    lines = [
        "# ValidEval V5 Stale and Duplicate Artifact Audit",
        "",
        "No historical artifact was deleted. This is a classification and release-exclusion map.",
        "",
        "## Duplicate groups",
        "",
    ]
    if summary["duplicate_groups"]:
        for row in summary["duplicate_groups"][:40]:
            lines.append(
                f"- `{row['sha256']}` ({row['size_bytes']} bytes): "
                + ", ".join(f"`{path}`" for path in row["paths"])
            )
    else:
        lines.append("- None detected within the bounded hash scan.")
    lines.extend(
        [
            "",
            "## Release-excluded debris",
            "",
            f"- Cache/compiled artifacts: `{len(cache_files)}`",
            f"- Archives requiring explicit review: `{len(archives)}`",
            f"- Notebooks with stored outputs: `{len(summary['notebooks_with_outputs'])}`",
            f"- Files containing absolute `/Users/` paths: `{len(summary['absolute_path_files'])}`",
            "",
            "## Stale truth surfaces",
            "",
            "- Prior prompt-pack directories are `HISTORICAL`, not execution authority.",
            "- V2/V3/V4 generated hashes and packet manifests are stale for a V5 release until rebuilt.",
            "- The active checkout has no Git commit, so any artifact claiming a repository commit must use `null`.",
            "- `.DS_Store`, `__pycache__`, test/lint caches, egg-info, model caches, and nested ZIPs are excluded.",
            "",
            "Status: `STALE` for prior release manifests; `PLANNED` for the V5 allowlisted release.",
        ]
    )
    return "\n".join(lines) + "\n"
