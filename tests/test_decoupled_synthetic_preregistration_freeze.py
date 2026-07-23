from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_decoupled_synthetic_repair_docs_preserve_result_required_boundary() -> None:
    docs = [
        "DECOUPLED_SYNTHETIC_SCHEMA_CONTRACTS.md",
        "DECOUPLED_SYNTHETIC_REVIEWER_AUDIT_CHECKLIST.md",
        "DECOUPLED_SYNTHETIC_FUTURE_COMMANDS.md",
    ]
    combined = "\n".join((REPO_ROOT / doc).read_text(encoding="utf-8") for doc in docs)
    assert "RESULT_REQUIRED" in combined
    assert "paper evidence" in combined.lower()
    assert "primary positive evidence" not in combined.lower()


def test_future_manifest_template_is_not_result_evidence() -> None:
    text = (
        REPO_ROOT / "templates/reports/DECOUPLED_SYNTHETIC_FUTURE_RUN_MANIFEST_TEMPLATE.json"
    ).read_text(encoding="utf-8")
    assert '"result_required": true' in text
    assert '"paper_evidence": false' in text
