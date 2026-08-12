from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from valideval.execution.config_v7_2 import V7_2_CANONICAL_SOURCE_REF
from valideval.execution.provenance_v7_2_1 import (
    RUNBOOK_PROVENANCE_COHERENT,
    audit_source_coherence,
    resolve_source_commit,
)

ROOT = Path(__file__).resolve().parents[1]


def test_active_v7_2_1_source_surfaces_are_coherent() -> None:
    result = audit_source_coherence(ROOT)
    assert result["status"] == RUNBOOK_PROVENANCE_COHERENT, result["problems"]
    assert result["canonical_source_ref"] == "valideval-v7.2.1-icml2027-kaggle-s1-ready"


def test_dynamic_source_resolution_uses_peeled_tag(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "ValidEval test"], cwd=tmp_path, check=True)
    (tmp_path / "tracked.txt").write_text("source\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "source"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "tag", "-a", V7_2_CANONICAL_SOURCE_REF, "-m", "source"],
        cwd=tmp_path,
        check=True,
    )
    expected = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert resolve_source_commit(tmp_path, V7_2_CANONICAL_SOURCE_REF) == expected


def test_unresolvable_source_ref_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        resolve_source_commit(tmp_path, V7_2_CANONICAL_SOURCE_REF)
