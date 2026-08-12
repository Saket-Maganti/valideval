from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from valideval.execution.config_v7_2 import V7_2_CANONICAL_SOURCE_REF

RUNBOOK_PROVENANCE_COHERENT = "RUNBOOK_PROVENANCE_COHERENT"
RUNBOOK_PROVENANCE_INCOHERENT = "RUNBOOK_PROVENANCE_INCOHERENT"


def resolve_source_commit(repository_root: str | Path, source_ref: str) -> str:
    """Resolve an annotated source tag to a full commit SHA without shell interpolation."""

    completed = subprocess.run(
        ["git", "rev-parse", f"{source_ref}^{{commit}}"],
        cwd=Path(repository_root),
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    commit = completed.stdout.strip().lower()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ValueError(f"source ref did not resolve to a full commit SHA: {source_ref}")
    return commit


def audit_source_coherence(repository_root: str | Path) -> dict[str, Any]:
    """Check every active execution surface against the canonical dynamic source tag."""

    root = Path(repository_root).resolve()
    problems: list[str] = []
    checked: list[str] = []
    release_path = root / "configs/release/source_manifest_v7_2_1.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    checked.append(str(release_path.relative_to(root)))
    if release.get("canonical_source_ref") != V7_2_CANONICAL_SOURCE_REF:
        problems.append("release manifest disagrees with the canonical source constant")
    if release.get("source_commit_resolution") != "DYNAMIC_ANNOTATED_TAG":
        problems.append("release manifest does not require dynamic annotated-tag resolution")

    config_paths = [root / value for value in release.get("s1_configs", [])]
    config_paths.extend(sorted((root / "configs/runs_v7").glob("*.yaml")))
    for path in config_paths:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        checked.append(str(path.relative_to(root)))
        if payload.get("required_source_ref") != V7_2_CANONICAL_SOURCE_REF:
            problems.append(f"{path.relative_to(root)} has a stale source ref")
        if payload.get("expected_source_commit") is not None:
            problems.append(f"{path.relative_to(root)} embeds a source commit")

    for relative in release.get("kaggle_notebooks", []):
        path = root / relative
        notebook = json.loads(path.read_text(encoding="utf-8"))
        checked.append(relative)
        metadata = notebook.get("metadata", {}).get("valideval", {})
        if metadata.get("required_source_ref") != V7_2_CANONICAL_SOURCE_REF:
            problems.append(f"{relative} has stale notebook source metadata")

    runbook_path = root / str(release["runbook"])
    runbook = runbook_path.read_text(encoding="utf-8")
    checked.append(str(runbook_path.relative_to(root)))
    required_fragments = (
        f"git checkout {V7_2_CANONICAL_SOURCE_REF}",
        f"git rev-parse '{V7_2_CANONICAL_SOURCE_REF}^{{commit}}'",
        'test "$ACTUAL_SOURCE_COMMIT" = "$EXPECTED_SOURCE_COMMIT"',
    )
    for fragment in required_fragments:
        if fragment not in runbook:
            problems.append(f"runbook is missing dynamic provenance command: {fragment}")
    if "342d3536cb9858b35288f2456ac2aa0a19c88d6a" in runbook:
        problems.append("runbook embeds the superseded intermediate source SHA")

    machine_path = root / "VALID_EVAL_FINAL_CPU_MAXOUT_MACHINE_STATE.json"
    if machine_path.exists():
        machine = json.loads(machine_path.read_text(encoding="utf-8"))
        checked.append(str(machine_path.relative_to(root)))
        if machine.get("canonical_s1_source_ref") != V7_2_CANONICAL_SOURCE_REF:
            problems.append("machine state disagrees with the canonical S1 source ref")
    return {
        "schema_version": "valideval.source-coherence.v7.2.1",
        "status": (RUNBOOK_PROVENANCE_COHERENT if not problems else RUNBOOK_PROVENANCE_INCOHERENT),
        "canonical_source_ref": V7_2_CANONICAL_SOURCE_REF,
        "checked": sorted(set(checked)),
        "problems": problems,
    }
