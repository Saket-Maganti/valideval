from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from valideval.cli import main
from valideval.release.bundle import build_reproducibility_bundle, verify_bundle
from valideval.release.environment import capture_environment, write_environment
from valideval.release.neurips import neurips_readiness_report
from valideval.release.paper_assets import PLACEHOLDER, generate_paper_assets
from valideval.release.reviewer import reviewer_risk_report


def test_paper_assets_missing_results_are_labeled_placeholders(tmp_path):
    payload = generate_paper_assets(
        benchmark="missing_benchmark",
        panel="mock",
        results_root=tmp_path / "results",
        paper_dir=tmp_path / "paper",
    )

    shortcut_svg = tmp_path / "paper" / "figures" / "shortcut_retention.svg"
    irt_table = tmp_path / "paper" / "tables" / "irt_item_quality.tex"
    assert shortcut_svg.exists()
    assert irt_table.exists()
    assert PLACEHOLDER in shortcut_svg.read_text(encoding="utf-8")
    assert PLACEHOLDER in irt_table.read_text(encoding="utf-8")
    assert len(payload["figures"]) == 10
    assert len(payload["tables"]) == 10


def test_environment_capture_and_write(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("seed: 0\n", encoding="utf-8")
    payload = capture_environment(
        command="python3 -m valideval audit --benchmark toy_mcq",
        config_paths=[config],
        seed=0,
    )
    assert payload["python"]["version"]
    assert payload["config_hashes"][str(config)] != "missing"

    output = write_environment(tmp_path / "environment.json", config_paths=[config], seed=0)
    assert (tmp_path / "environment.json").exists()
    assert output["environment"]["random_seeds"]["default_seed"] == 0


def test_bundle_build_and_verify(tmp_path):
    _write_minimal_audit_artifacts(tmp_path, benchmark="toy", panel="mock")
    config = tmp_path / "configs" / "default.yaml"
    config.parent.mkdir()
    config.write_text("diagnostics: {}\n", encoding="utf-8")

    bundle = build_reproducibility_bundle(
        benchmark="toy",
        panel="mock",
        output_dir=tmp_path / "bundles",
        results_root=tmp_path / "results",
        reportcards_root=tmp_path / "reportcards",
        configs=[config],
    )
    assert bundle["file_count"] > 0
    verification = verify_bundle(bundle["bundle_dir"])
    assert verification["valid"]
    assert verification["checked_files"] == bundle["file_count"]


def test_neurips_readiness_blocks_failed_real_benchmark_gate(tmp_path):
    _write_minimal_audit_artifacts(tmp_path, benchmark="toy", panel="mock")
    _write_review_safe_report(tmp_path / "reportcards" / "toy_mock.md")
    config = tmp_path / "configs" / "default.yaml"
    config.parent.mkdir()
    config.write_text("diagnostics: {}\n", encoding="utf-8")
    bundle = build_reproducibility_bundle(
        benchmark="toy",
        panel="mock",
        output_dir=tmp_path / "bundles",
        results_root=tmp_path / "results",
        reportcards_root=tmp_path / "reportcards",
        configs=[config],
    )
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    (paper_dir / "main.tex").write_text(
        "\\section{Method}\nAll claims are tied to local artifacts.\n",
        encoding="utf-8",
    )
    (paper_dir / "CLAIMS_LEDGER.md").write_text("# Claims Ledger\n", encoding="utf-8")
    (paper_dir / "NEURIPS_SUBMISSION_PLAN.md").write_text(
        "# Submission Plan\n",
        encoding="utf-8",
    )
    validation_summary = tmp_path / "validation_reports" / "diagnostic_validation_summary.json"
    validation_summary.parent.mkdir()
    validation_summary.write_text(
        json.dumps(
            {
                "n_experiments": 2,
                "diagnostics_validated": ["shortcut", "irt"],
                "diagnostics_prototype_only": [],
                "diagnostics_to_quarantine": [],
            }
        ),
        encoding="utf-8",
    )
    go_no_go = tmp_path / "go_no_go.json"
    go_no_go.write_text(
        json.dumps(
            {
                "status": "no_go",
                "primary_full_variant": "full_answer_only_v2",
                "blocked_reasons": [
                    {"name": "required_variant_per_model_extraction_thresholds_met"}
                ],
                "diagnostics_allowed": ["distractor_quality"],
                "diagnostics_blocked": {"shortcut": ["input_validation_failed"]},
            }
        ),
        encoding="utf-8",
    )
    evidence_lock = tmp_path / "NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md"
    _write_valid_evidence_lock(evidence_lock)

    payload = neurips_readiness_report(
        benchmark="toy",
        panel="mock",
        paper_dir=paper_dir,
        output_dir=tmp_path / "readiness",
        report_path=tmp_path / "reportcards" / "toy_mock.md",
        bundle_path=bundle["bundle_dir"],
        validation_summary_path=validation_summary,
        go_no_go_path=go_no_go,
        evidence_lock_path=evidence_lock,
    )

    checks = {check["name"]: check for check in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["paper_draft"]["status"] == "pass"
    assert checks["evidence_state_lock"]["status"] == "pass"
    assert checks["reproducibility_bundle"]["status"] == "pass"
    assert checks["reviewer_risk"]["status"] == "pass"
    assert checks["real_benchmark_gate"]["status"] == "blocked"
    assert checks["real_benchmark_gate"]["details"]["blocked_reasons"] == [
        "required_variant_per_model_extraction_thresholds_met"
    ]
    assert (tmp_path / "readiness" / "neurips_readiness_report.json").exists()
    assert (tmp_path / "readiness" / "neurips_readiness_report.md").exists()


def test_neurips_readiness_blocks_evidence_lock_drift(tmp_path):
    _write_minimal_audit_artifacts(tmp_path, benchmark="toy", panel="mock")
    _write_review_safe_report(tmp_path / "reportcards" / "toy_mock.md")
    config = tmp_path / "configs" / "default.yaml"
    config.parent.mkdir()
    config.write_text("diagnostics: {}\n", encoding="utf-8")
    bundle = build_reproducibility_bundle(
        benchmark="toy",
        panel="mock",
        output_dir=tmp_path / "bundles",
        results_root=tmp_path / "results",
        reportcards_root=tmp_path / "reportcards",
        configs=[config],
    )
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    (paper_dir / "main.tex").write_text("\\section{Method}\n", encoding="utf-8")
    (paper_dir / "CLAIMS_LEDGER.md").write_text("# Claims Ledger\n", encoding="utf-8")
    (paper_dir / "NEURIPS_SUBMISSION_PLAN.md").write_text("# Submission Plan\n", encoding="utf-8")
    validation_summary = tmp_path / "validation_reports" / "diagnostic_validation_summary.json"
    validation_summary.parent.mkdir()
    validation_summary.write_text(
        json.dumps({"n_experiments": 1, "diagnostics_validated": ["shortcut"]}),
        encoding="utf-8",
    )
    go_no_go = tmp_path / "go_no_go.json"
    go_no_go.write_text(json.dumps({"status": "go"}), encoding="utf-8")
    evidence_lock = tmp_path / "NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md"
    evidence_lock.write_text(
        "# No-Run Rules and Evidence-State Lock\n\nThis file lost its locked-state table.\n",
        encoding="utf-8",
    )

    payload = neurips_readiness_report(
        benchmark="toy",
        panel="mock",
        paper_dir=paper_dir,
        output_dir=tmp_path / "readiness",
        report_path=tmp_path / "reportcards" / "toy_mock.md",
        bundle_path=bundle["bundle_dir"],
        validation_summary_path=validation_summary,
        go_no_go_path=go_no_go,
        evidence_lock_path=evidence_lock,
    )

    checks = {check["name"]: check for check in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["evidence_state_lock"]["status"] == "blocked"
    assert (
        "Cross-flaw specificity | WEAK"
        in checks["evidence_state_lock"]["details"]["missing_markers"]
    )


def test_reviewer_risk_flags_overclaims_and_missing_disclosures(tmp_path):
    report = tmp_path / "report.md"
    report.write_text(
        "# Report\n\nThis proves the true ranking. Validity: 99.\n",
        encoding="utf-8",
    )
    payload = reviewer_risk_report(report=report)
    risk_names = {risk["risk"] for risk in payload["risks"]}
    assert "overclaim" in risk_names
    assert "scalar_validity_score" in risk_names
    assert payload["high_risk_count"] >= 1
    assert (tmp_path / "report.reviewer_risk.json").exists()


def test_release_cli_smoke(tmp_path):
    _write_minimal_audit_artifacts(tmp_path, benchmark="toy", panel="mock")
    _write_review_safe_report(tmp_path / "reportcards" / "toy_mock.md")
    config = tmp_path / "configs" / "default.yaml"
    config.parent.mkdir()
    config.write_text("diagnostics: {}\n", encoding="utf-8")
    report = tmp_path / "reportcards" / "toy_mock.md"
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    (paper_dir / "main.tex").write_text("\\section{Method}\n", encoding="utf-8")
    (paper_dir / "CLAIMS_LEDGER.md").write_text("# Claims Ledger\n", encoding="utf-8")
    (paper_dir / "NEURIPS_SUBMISSION_PLAN.md").write_text(
        "# Submission Plan\n",
        encoding="utf-8",
    )
    validation_summary = tmp_path / "validation_reports" / "diagnostic_validation_summary.json"
    validation_summary.parent.mkdir()
    validation_summary.write_text(
        json.dumps({"n_experiments": 1, "diagnostics_validated": ["shortcut"]}),
        encoding="utf-8",
    )
    go_no_go = tmp_path / "go_no_go.json"
    go_no_go.write_text(json.dumps({"status": "no_go"}), encoding="utf-8")
    evidence_lock = tmp_path / "NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md"
    _write_valid_evidence_lock(evidence_lock)

    assert (
        main(
            [
                "paper-assets",
                "--benchmark",
                "toy",
                "--panel",
                "mock",
                "--results-root",
                str(tmp_path / "results"),
                "--paper-dir",
                str(tmp_path / "paper"),
            ]
        )
        == 0
    )
    assert main(["environment", "--output", str(tmp_path / "environment.json")]) == 0
    assert main(["reviewer-risk", "--report", str(report)]) == 0
    assert (
        main(
            [
                "bundle",
                "--benchmark",
                "toy",
                "--panel",
                "mock",
                "--results-root",
                str(tmp_path / "results"),
                "--reportcards-root",
                str(tmp_path / "reportcards"),
                "--output-dir",
                str(tmp_path / "bundles"),
                "--configs",
                str(config),
            ]
        )
        == 0
    )
    assert main(["verify-bundle", str(tmp_path / "bundles" / "toy_mock_bundle")]) == 0
    assert (
        main(
            [
                "neurips-readiness",
                "--benchmark",
                "toy",
                "--panel",
                "mock",
                "--paper-dir",
                str(paper_dir),
                "--output-dir",
                str(tmp_path / "readiness"),
                "--report",
                str(report),
                "--bundle-path",
                str(tmp_path / "bundles" / "toy_mock_bundle"),
                "--validation-summary",
                str(validation_summary),
                "--go-no-go-path",
                str(go_no_go),
                "--evidence-lock",
                str(evidence_lock),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "neurips-readiness",
                "--benchmark",
                "toy",
                "--panel",
                "mock",
                "--paper-dir",
                str(paper_dir),
                "--output-dir",
                str(tmp_path / "readiness"),
                "--report",
                str(report),
                "--bundle-path",
                str(tmp_path / "bundles" / "toy_mock_bundle"),
                "--validation-summary",
                str(validation_summary),
                "--go-no-go-path",
                str(go_no_go),
                "--evidence-lock",
                str(evidence_lock),
                "--strict",
            ]
        )
        == 1
    )


def test_module_entrypoint_propagates_strict_exit_code(tmp_path):
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "valideval",
            "doctor",
            "--benchmark",
            "toy_mcq",
            "--panel",
            "mock",
            "--cache-root",
            str(tmp_path / "cache"),
            "--results-root",
            str(tmp_path / "results"),
            "--reportcards-root",
            str(tmp_path / "reportcards"),
            "--strict",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert process.returncode == 1
    assert '"status": "warning"' in process.stdout


def test_release_metadata_files_exist():
    assert _exists("paper/CLAIMS_LEDGER.md")
    assert _exists("docs/protocols/statistical_reporting_protocol.md")
    assert _exists("docs/engineering/RELEASE_CHECKLIST.md")
    assert _exists("docs/engineering/GOD_TIER_ROADMAP.md")
    assert _exists("CITATION.cff")
    assert _exists("demo/README.md")


def _write_minimal_audit_artifacts(tmp_path, *, benchmark: str, panel: str) -> None:
    result_root = tmp_path / "results" / benchmark
    result_dir = result_root / panel
    result_dir.mkdir(parents=True)
    (result_root / "manifest.json").write_text(
        json.dumps({"schema_version": "0.1", "item_count": 2, "item_text_hash": "abc"}),
        encoding="utf-8",
    )
    artifacts = {
        "validity_card.json": {"schema_version": "0.1", "diagnostics": ["baselines"]},
        "validity_card.md": "# Validity Card\n\nLimitations and reproduction commands.\n",
        "validity_certificate.json": {"schema_version": "0.1", "profile_level": "Bronze"},
        "validity_certificate.md": "# Certificate\n",
        "item_forensics.csv": "item_id,recommendation\nitem_1,keep\n",
        "repair_report.md": "# Repair Report\n",
        "repair_diff.json": {
            "original_item_count": 2,
            "repaired_item_count": 2,
            "removed_item_count": 0,
            "ranking_fidelity": {"spearman": 1.0},
        },
        "ranking_views.json": {"views": {"raw_accuracy": {"ranking": [{"model_id": "m1"}]}}},
        "ranking_flips.json": {"flips": []},
        "ranking_significance.json": {"top_k_stability": {}},
        "baselines.json": {
            "diagnostic_name": "baselines",
            "version": "0.1",
            "summary_metrics": {
                "best_shallow_baseline": {"baseline_id": "majority", "score": 0.5},
                "dumb_baseline_gap": 0.1,
            },
            "warnings": [],
        },
        "shortcut.json": {
            "diagnostic_name": "shortcut",
            "version": "0.1",
            "summary_metrics": {"retention": 0.2},
            "warnings": [],
        },
        "irt.json": {
            "diagnostic_name": "irt",
            "version": "0.1",
            "per_item_metrics": {
                "item_1": {"difficulty": 0.1, "discrimination": 0.3},
                "item_2": {"difficulty": -0.1, "discrimination": 0.2},
            },
            "warnings": [],
        },
        "reliability.json": {
            "diagnostic_name": "reliability",
            "version": "0.1",
            "summary_metrics": {"benchmark_level_reliability_estimate": 0.8},
            "warnings": [],
        },
        "saturation.json": {
            "diagnostic_name": "saturation",
            "version": "0.1",
            "summary_metrics": {"ceiling_fraction": 0.0},
            "warnings": [],
        },
    }
    for name, payload in artifacts.items():
        path = result_dir / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
    reportcards = tmp_path / "reportcards"
    reportcards.mkdir()
    (reportcards / f"{benchmark}_{panel}.md").write_text(
        "# Report Card\n\nLimitations. Reproduction: python3 -m valideval audit.\n",
        encoding="utf-8",
    )


def _write_review_safe_report(path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Report Card",
                "",
                "Benchmark toy_mcq is summarized with limitations and missing evidence.",
                "Reproduction: python3 -m valideval audit --benchmark toy_mcq --panel mock.",
                "Baselines include the dumb baseline and shallow baseline comparisons.",
                "Confidence interval, bootstrap, and uncertainty fields are reported when available.",
                "Human validation, human agreement, and judge reliability are reported when available.",
                "Contamination, forensics, provenance, and overlap checks are metadata-only evidence.",
                "Preregistration and selection criteria define the audit scope before interpretation.",
                "Multiple comparison and multiplicity correction are discussed for detector sweeps.",
                "Negative result, not run, and unavailable diagnostics are separated from measured results.",
            ]
        ),
        encoding="utf-8",
    )


def _write_valid_evidence_lock(path) -> None:
    path.write_text(
        "\n".join(
            [
                "# No-Run Rules and Evidence-State Lock",
                "",
                "| Evidence block | Locked state |",
                "|---|---|",
                "| Cross-flaw specificity | WEAK |",
                "| Held-out generator transfer | WEAK |",
                "| Materiality | WEAK |",
                "| Numeric calibration without confidence/logprob outputs | BLOCKED |",
                "| Synthetic-to-real threshold validation | NOT_RUN |",
                "| Confirmatory synthetic follow-up | RESULT_REQUIRED |",
                (
                    "| HELM MMLU panel | Real input exists; real-panel finding remains "
                    "RESULT_REQUIRED |"
                ),
            ]
        ),
        encoding="utf-8",
    )


def _exists(path: str) -> bool:
    from pathlib import Path

    return Path(path).exists()
