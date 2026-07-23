from __future__ import annotations

import inspect
import os
from pathlib import Path

from scripts import preflight_confirmatory_synthetic as preflight


def _write(path: Path, text: str = "placeholder\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _valid_repo(tmp_path: Path) -> Path:
    for rel in preflight.REQUIRED_PREREGISTRATION_DOCS:
        _write(tmp_path / rel)
    for rel in preflight.REQUIRED_CONFIGS:
        _write(tmp_path / rel)
    for rel in preflight.REQUIRED_TEMPLATES:
        _write(tmp_path / rel, "[RESULT REQUIRED]\n")
    _write(
        tmp_path / preflight.FAILURE_CASE_DOC,
        "\n".join(
            [
                *preflight.EXPECTED_FAILURE_IDS,
                "Cross-flaw specificity remains `WEAK`",
                "Held-out generator transfer remains `WEAK`",
            ]
        ),
    )
    for rel in preflight.CLAIMS_LEDGERS:
        _write(tmp_path / rel, "\n".join(preflight.BLOCKED_CLAIMS))
    (tmp_path / "results" / "synthetic").mkdir(parents=True)
    return tmp_path


def test_missing_preregistration_doc_fails(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    (repo / "PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md").unlink()

    result = preflight.run_preflight(repo)

    assert not result.passed
    assert any(
        check.name == "preregistration and runbook docs"
        and "PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md" in check.detail
        for check in result.checks
    )


def test_missing_failure_case_doc_fails(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    (repo / preflight.FAILURE_CASE_DOC).unlink()

    result = preflight.run_preflight(repo)

    assert not result.passed
    assert any(
        check.name == "documented failure cases" and preflight.FAILURE_CASE_DOC in check.detail
        for check in result.checks
    )


def test_missing_templates_fail(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    missing = repo / preflight.REQUIRED_TEMPLATES[0]
    missing.unlink()

    result = preflight.run_preflight(repo)

    assert not result.passed
    assert any(
        check.name == "result report templates" and preflight.REQUIRED_TEMPLATES[0] in check.detail
        for check in result.checks
    )


def test_valid_repo_passes(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)

    result = preflight.run_preflight(repo)

    assert result.passed
    assert len(result.future_commands) == 2


def test_current_repository_passes_preflight() -> None:
    repo = Path(__file__).resolve().parents[1]

    result = preflight.run_preflight(repo)

    assert result.passed, [
        f"{check.name}: {check.detail}" for check in result.checks if not check.ok
    ]


def test_script_does_not_invoke_validation_commands(tmp_path: Path) -> None:
    repo = _valid_repo(tmp_path)
    source = inspect.getsource(preflight)

    result = preflight.run_preflight(repo)

    assert result.passed
    assert "subprocess" not in source
    assert ".system(" not in source
    assert not (repo / "results" / "synthetic" / "cross_flaw_confirmatory").exists()
    assert not (repo / "results" / "synthetic" / "heldout_confirmatory").exists()


def test_output_includes_future_commands_only(tmp_path: Path, capsys) -> None:
    repo = _valid_repo(tmp_path)

    exit_code = preflight.main(["--repo-root", os.fspath(repo)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Future commands (not executed):" in captured.out
    assert "# Future only" in captured.out
    assert "validate-diagnostics-cross-flaw" in captured.out
    assert "validate-diagnostics-heldout" in captured.out
    assert "No validation commands were executed" in captured.out
