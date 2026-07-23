from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.release.bundle import verify_bundle
from valideval.release.reviewer import reviewer_risk_report
from valideval.schemas import utc_now

PLACEHOLDER_MARKERS = [
    "[TO BE FILLED",
    "TO BE FILLED",
]

EVIDENCE_LOCK_REQUIRED_MARKERS = [
    "Cross-flaw specificity | WEAK",
    "Held-out generator transfer | WEAK",
    "Materiality | WEAK",
    "Numeric calibration without confidence/logprob outputs | BLOCKED",
    "Synthetic-to-real threshold validation | NOT_RUN",
    "Confirmatory synthetic follow-up | RESULT_REQUIRED",
    "HELM MMLU panel | Real input exists; real-panel finding remains RESULT_REQUIRED",
]


def neurips_readiness_report(
    *,
    benchmark: str = "toy_mcq",
    panel: str = "mock",
    paper_dir: str | Path = "paper",
    output_dir: str | Path = "paper",
    report_path: str | Path | None = None,
    bundle_path: str | Path | None = None,
    validation_summary_path: str | Path = "validation_reports/diagnostic_validation_summary.json",
    real_benchmark: str = "gpqa_diamond",
    real_panel: str = "gpqa_minimal_open_local_amended_v2_compliant",
    go_no_go_path: str | Path | None = None,
    evidence_lock_path: str | Path = "NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paper = Path(paper_dir)
    report = Path(report_path) if report_path else Path("reportcards") / f"{benchmark}_{panel}.md"
    bundle = Path(bundle_path) if bundle_path else Path("bundles") / f"{benchmark}_{panel}_bundle"
    go_no_go = (
        Path(go_no_go_path)
        if go_no_go_path
        else Path("results") / real_benchmark / "input_validation" / "go_no_go.json"
    )

    checks = [
        _paper_placeholder_check(paper),
        _required_file_check(
            "claims_ledger",
            paper / "CLAIMS_LEDGER.md",
            "Claims ledger exists.",
            "Claims ledger is missing.",
        ),
        _required_file_check(
            "neurips_submission_plan",
            paper / "NEURIPS_SUBMISSION_PLAN.md",
            "NeurIPS submission plan exists.",
            "NeurIPS submission plan is missing.",
        ),
        _required_file_check(
            "neurips_readiness_plan",
            Path("docs/engineering/NEURIPS_READINESS_PLAN.md"),
            "NeurIPS readiness plan exists.",
            "NeurIPS readiness plan is missing.",
        ),
        _evidence_state_lock_check(Path(evidence_lock_path)),
        _validation_summary_check(Path(validation_summary_path)),
        _bundle_check(bundle),
        _reviewer_risk_check(report, output),
        _real_benchmark_gate_check(go_no_go, real_benchmark=real_benchmark, real_panel=real_panel),
        _public_release_check(),
    ]
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "target": "NeurIPS Evaluations and Datasets",
        "status": _overall_status(checks),
        "benchmark": benchmark,
        "panel": panel,
        "real_benchmark": real_benchmark,
        "real_panel": real_panel,
        "checks": checks,
        "next_commands": _unique(
            command for check in checks for command in check.get("next_commands", [])
        ),
        "publication_boundary": [
            "Do not claim real-benchmark findings while go/no-go is blocked.",
            "Do not print raw restricted benchmark item text in public artifacts.",
            "Report measured, blocked, and not-run diagnostics separately.",
            "Do not collapse validity evidence into one benchmark-health number.",
        ],
    }
    json_path = output / "neurips_readiness_report.json"
    md_path = output / "neurips_readiness_report.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    payload["output_json"] = str(json_path)
    payload["output_markdown"] = str(md_path)
    return payload


def _paper_placeholder_check(paper_dir: Path) -> dict[str, Any]:
    tex_files = sorted(paper_dir.glob("**/*.tex"))
    placeholders: list[str] = []
    missing_files = not tex_files
    for path in tex_files:
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in PLACEHOLDER_MARKERS):
            placeholders.append(str(path))
    if missing_files:
        return _check(
            "paper_draft",
            "blocked",
            "required",
            "No paper TeX files were found.",
            {"paper_dir": str(paper_dir), "placeholder_files": []},
            ["Create or restore paper/main.tex and section files."],
        )
    if placeholders:
        return _check(
            "paper_draft",
            "blocked",
            "required",
            "Paper draft still contains placeholder text.",
            {"paper_dir": str(paper_dir), "placeholder_files": placeholders},
            ["Fill paper placeholders using local artifacts only."],
        )
    return _check(
        "paper_draft",
        "pass",
        "required",
        "Paper draft has no tracked placeholder markers.",
        {"paper_dir": str(paper_dir), "tex_file_count": len(tex_files)},
    )


def _required_file_check(
    name: str, path: Path, pass_message: str, fail_message: str
) -> dict[str, Any]:
    return _check(
        name,
        "pass" if path.exists() else "blocked",
        "required",
        pass_message if path.exists() else fail_message,
        {"path": str(path), "exists": path.exists()},
        [] if path.exists() else [f"Create {path}."],
    )


def _validation_summary_check(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _check(
            "synthetic_validation",
            "blocked",
            "required",
            "Synthetic diagnostic-validation summary is missing.",
            {"path": str(path), "exists": False},
            [
                "python3 -m valideval validate-diagnostics --config configs/validation/all_sweeps.yaml",
                "python3 -m valideval validation-report --report-dir validation_reports",
            ],
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _check(
            "synthetic_validation",
            "blocked",
            "required",
            "Synthetic diagnostic-validation summary is not valid JSON.",
            {"path": str(path), "error": str(exc)},
        )
    quarantined = payload.get("diagnostics_to_quarantine", [])
    n_experiments = int(payload.get("n_experiments") or len(payload.get("experiments", [])))
    if quarantined:
        status = "warning"
        message = "Synthetic validation has diagnostics marked for quarantine."
    elif n_experiments > 0:
        status = "pass"
        message = "Synthetic validation summary is available."
    else:
        status = "blocked"
        message = "Synthetic validation summary has no experiments."
    return _check(
        "synthetic_validation",
        status,
        "required",
        message,
        {
            "path": str(path),
            "n_experiments": n_experiments,
            "diagnostics_validated": payload.get("diagnostics_validated", []),
            "diagnostics_prototype_only": payload.get("diagnostics_prototype_only", []),
            "diagnostics_to_quarantine": quarantined,
        },
    )


def _evidence_state_lock_check(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _check(
            "evidence_state_lock",
            "blocked",
            "required",
            "No-run evidence-state lock is missing.",
            {"path": str(path), "exists": False},
            ["Restore NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md before release review."],
        )
    text = path.read_text(encoding="utf-8")
    missing = [marker for marker in EVIDENCE_LOCK_REQUIRED_MARKERS if marker not in text]
    if missing:
        return _check(
            "evidence_state_lock",
            "blocked",
            "required",
            "No-run evidence-state lock is missing required blocked/weak state markers.",
            {
                "path": str(path),
                "exists": True,
                "missing_markers": missing,
                "required_marker_count": len(EVIDENCE_LOCK_REQUIRED_MARKERS),
            },
            ["Synchronize the evidence-state lock before changing reviewer-facing claims."],
        )
    return _check(
        "evidence_state_lock",
        "pass",
        "required",
        "No-run evidence-state lock preserves required blocked/weak states.",
        {
            "path": str(path),
            "exists": True,
            "required_marker_count": len(EVIDENCE_LOCK_REQUIRED_MARKERS),
        },
    )


def _bundle_check(bundle_path: Path) -> dict[str, Any]:
    if not bundle_path.exists():
        return _check(
            "reproducibility_bundle",
            "blocked",
            "required",
            "Reproducibility bundle is missing.",
            {"bundle_path": str(bundle_path), "exists": False},
            ["python3 -m valideval bundle --benchmark toy_mcq --panel mock"],
        )
    result = verify_bundle(bundle_path)
    if not result.get("valid"):
        return _check(
            "reproducibility_bundle",
            "blocked",
            "required",
            "Reproducibility bundle verification failed.",
            result,
            [f"python3 -m valideval verify-bundle {bundle_path}"],
        )
    status = "warning" if result.get("warnings") else "pass"
    return _check(
        "reproducibility_bundle",
        status,
        "required",
        "Reproducibility bundle verifies."
        if status == "pass"
        else "Reproducibility bundle verifies with warnings.",
        result,
    )


def _reviewer_risk_check(report_path: Path, output_dir: Path) -> dict[str, Any]:
    output_path = output_dir / f"{report_path.stem}.reviewer_risk.json"
    payload = reviewer_risk_report(report=report_path, output_path=output_path)
    high = int(payload.get("high_risk_count", 0))
    total = int(payload.get("risk_count", 0))
    if high:
        status = "blocked"
        message = "Reviewer-risk audit has high-risk findings."
    elif total:
        status = "warning"
        message = "Reviewer-risk audit has non-high-risk findings."
    else:
        status = "pass"
        message = "Reviewer-risk audit has no findings."
    return _check(
        "reviewer_risk",
        status,
        "required",
        message,
        {
            "report": str(report_path),
            "output_path": payload.get("output_path"),
            "risk_count": total,
            "high_risk_count": high,
            "risks": payload.get("risks", []),
        },
        [f"Edit {report_path} to resolve reviewer-risk findings."] if high else [],
    )


def _real_benchmark_gate_check(
    go_no_go_path: Path,
    *,
    real_benchmark: str,
    real_panel: str,
) -> dict[str, Any]:
    if not go_no_go_path.exists():
        return _check(
            "real_benchmark_gate",
            "blocked",
            "required",
            "Real-benchmark go/no-go artifact is missing.",
            {
                "path": str(go_no_go_path),
                "real_benchmark": real_benchmark,
                "real_panel": real_panel,
            },
            [
                (
                    "python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond "
                    "--items data/gpqa/gpqa_diamond.jsonl "
                    f"--panel {real_panel} --config configs/audits/gpqa_diamond_amended_v2.yaml"
                )
            ],
        )
    try:
        payload = json.loads(go_no_go_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _check(
            "real_benchmark_gate",
            "blocked",
            "required",
            "Real-benchmark go/no-go artifact is not valid JSON.",
            {
                "path": str(go_no_go_path),
                "real_benchmark": real_benchmark,
                "real_panel": real_panel,
                "error": str(exc),
            },
        )
    status_value = str(payload.get("status") or payload.get("go_no_go_status") or "unknown")
    blocked_reasons = _blocked_reason_names(payload.get("blocked_reasons", []))
    if status_value == "go":
        status = "pass"
        message = "Real-benchmark go/no-go is pass."
    else:
        status = "blocked"
        message = "Real-benchmark go/no-go is blocked; do not interpret blocked diagnostics."
    return _check(
        "real_benchmark_gate",
        status,
        "required",
        message,
        {
            "path": str(go_no_go_path),
            "real_benchmark": real_benchmark,
            "real_panel": real_panel,
            "go_no_go_status": status_value,
            "primary_full_variant": payload.get("primary_full_variant"),
            "blocked_reasons": blocked_reasons,
            "diagnostics_allowed": payload.get("diagnostics_allowed", []),
            "diagnostics_blocked": payload.get("diagnostics_blocked", {}),
        },
        ["Resolve the real-benchmark gate or keep the case study explicitly blocked in the paper."]
        if status != "pass"
        else [],
    )


def _public_release_check() -> dict[str, Any]:
    required = ["README.md", "LICENSE", "CITATION.cff", "pyproject.toml"]
    missing = [path for path in required if not Path(path).exists()]
    has_git = Path(".git").exists()
    if missing:
        return _check(
            "public_release_metadata",
            "blocked",
            "required",
            "Public-release metadata is incomplete.",
            {"missing": missing, "git_metadata_present": has_git},
        )
    return _check(
        "public_release_metadata",
        "pass" if has_git else "warning",
        "recommended",
        "Public-release metadata exists."
        if has_git
        else "Release metadata exists, but this checkout has no local .git directory.",
        {"required_files": required, "git_metadata_present": has_git},
        ["Prepare a clean public git release/tag."] if not has_git else [],
    )


def _check(
    name: str,
    status: str,
    severity: str,
    message: str,
    details: dict[str, Any],
    next_commands: list[str] | None = None,
) -> dict[str, Any]:
    payload = {
        "name": name,
        "status": status,
        "severity": severity,
        "message": message,
        "details": details,
    }
    if next_commands:
        payload["next_commands"] = next_commands
    return payload


def _overall_status(checks: list[dict[str, Any]]) -> str:
    if any(check["status"] == "blocked" for check in checks):
        return "blocked"
    if any(check["status"] == "warning" for check in checks):
        return "warning"
    return "pass"


def _blocked_reason_names(reasons: Any) -> list[str]:
    if not isinstance(reasons, list):
        return []
    names: list[str] = []
    for reason in reasons:
        if isinstance(reason, dict):
            name = reason.get("name")
            if name:
                names.append(str(name))
        elif reason:
            names.append(str(reason))
    return names


def _unique(values: Any) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if value))


def _render_markdown(payload: dict[str, Any]) -> str:
    rows = [
        "| Check | Status | Severity | Message |",
        "| --- | --- | --- | --- |",
    ]
    for check in payload["checks"]:
        rows.append(
            "| {name} | {status} | {severity} | {message} |".format(
                name=check["name"],
                status=check["status"],
                severity=check["severity"],
                message=str(check["message"]).replace("|", "/"),
            )
        )
    next_commands = payload.get("next_commands", [])
    commands_block = "\n".join(f"- `{command}`" for command in next_commands) or "- None."
    boundaries = "\n".join(f"- {item}" for item in payload["publication_boundary"])
    return "\n".join(
        [
            "# NeurIPS Readiness Report",
            "",
            f"- Target: {payload['target']}",
            f"- Status: {payload['status']}",
            f"- Benchmark artifact: {payload['benchmark']}/{payload['panel']}",
            f"- Real-benchmark gate: {payload['real_benchmark']}/{payload['real_panel']}",
            "",
            "## Checks",
            "",
            *rows,
            "",
            "## Publication Boundary",
            "",
            boundaries,
            "",
            "## Next Commands",
            "",
            commands_block,
            "",
        ]
    )
