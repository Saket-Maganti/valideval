from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from valideval.release.v5 import build_deterministic_zip, plan_release

ROOT = Path(__file__).parents[1]


def test_v5_release_is_allowlist_only_and_deterministic(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "safe.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "src" / "unsafe.pyc").write_bytes(b"compiled")
    (tmp_path / ".env").write_text("TOKEN=not-a-real-token\n", encoding="utf-8")
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("src/*\n.env\n", encoding="utf-8")

    plan = plan_release(tmp_path, allowlist)
    assert [row["path"] for row in plan["included"]] == ["src/safe.py"]
    assert {row["path"] for row in plan["excluded"]} == {".env", "src/unsafe.pyc"}

    first = build_deterministic_zip(tmp_path, plan, tmp_path / "first.zip")
    second = build_deterministic_zip(tmp_path, plan, tmp_path / "second.zip")
    assert first["sha256"] == second["sha256"]

    with zipfile.ZipFile(tmp_path / "first.zip") as archive:
        manifest = json.loads(archive.read("V5_RELEASE_MANIFEST.json"))
        for row in manifest["included"]:
            assert hashlib.sha256(archive.read(row["path"])).hexdigest() == row["sha256"]


def test_generated_audit_is_not_self_included(tmp_path: Path) -> None:
    report = tmp_path / "reports" / "audit.md"
    report.parent.mkdir()
    report.write_text("old audit\n", encoding="utf-8")
    (report.parent / "keep.md").write_text("kept\n", encoding="utf-8")
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("reports/*.md\n", encoding="utf-8")

    plan = plan_release(tmp_path, allowlist, excluded_paths={"reports/audit.md"})
    assert [row["path"] for row in plan["included"]] == ["reports/keep.md"]
    assert plan["excluded"] == [
        {
            "path": "reports/audit.md",
            "reason": "generated audit is excluded from its own release plan",
        }
    ]


def test_reviewer_allowlist_contains_final_verification_surfaces() -> None:
    entries = {
        line.strip()
        for line in (ROOT / "configs/release/reviewer_packet_v5.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert {
        "FINAL_V5_PRE_EXECUTION_GATE.md",
        "VALID_EVAL_MAXIMUM_CEILING_EXECUTION_HANDBOOK.md",
        "VALID_EVAL_MAXIMUM_CEILING_PRE_EXECUTION_HANDOFF.md",
        "VALID_EVAL_V5_MACHINE_STATE.json",
        "reports/v5/final_gates_v5.json",
        "results/v5_validation/command_ledger_v5.json",
        "results/v5_validation/command_ledger_v5.md",
    } <= entries
