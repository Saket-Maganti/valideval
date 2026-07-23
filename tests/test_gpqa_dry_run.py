from __future__ import annotations

import json

from valideval.cli import main


def test_gpqa_fixture_dry_run_generates_labeled_artifacts(tmp_path):
    common = [
        "--benchmark",
        "gpqa_diamond_tiny_fixture",
        "--panel",
        "mock",
        "--cache-root",
        str(tmp_path / "cache"),
        "--results-root",
        str(tmp_path / "results"),
        "--reportcards-root",
        str(tmp_path / "reportcards"),
        "--config",
        "configs/audits/gpqa_diamond_preregistered.yaml",
        "--diagnostics",
        "answer_distribution",
        "distractor_quality",
        "irt",
        "reliability",
        "extraction_robustness",
        "saturation",
        "shortcut",
        "prompt_sensitivity",
        "--dry-run",
    ]

    assert main(["audit", *common]) == 0

    report = tmp_path / "reportcards" / "gpqa_diamond_tiny_fixture_mock.md"
    manifest = tmp_path / "results" / "gpqa_diamond_tiny_fixture" / "manifest.json"
    diagnostic = tmp_path / "results" / "gpqa_diamond_tiny_fixture" / "mock" / "irt.json"
    certificate = (
        tmp_path / "results" / "gpqa_diamond_tiny_fixture" / "mock" / "validity_certificate.md"
    )
    evidence = (
        tmp_path / "results" / "gpqa_diamond_tiny_fixture" / "mock" / "claim_evidence_matrix.md"
    )

    assert report.exists()
    assert manifest.exists()
    assert diagnostic.exists()
    assert certificate.exists()
    assert evidence.exists()

    report_text = report.read_text(encoding="utf-8")
    assert "Artifact scope: gpqa_fixture_dry_run" in report_text
    assert "GPQA fixture dry-run only" in report_text
    assert "does not assign a single validity score" in report_text
    assert "Artifact scope: gpqa_fixture_dry_run" in certificate.read_text(encoding="utf-8")
    assert "Artifact scope: **gpqa_fixture_dry_run**" in evidence.read_text(encoding="utf-8")

    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_payload["audit_mode"] == "dry_run"
    assert manifest_payload["artifact_scope"] == "gpqa_fixture_dry_run"
    assert manifest_payload["prompt_template_hash"]

    diagnostic_payload = json.loads(diagnostic.read_text(encoding="utf-8"))
    assert diagnostic_payload["summary_metrics"]["artifact_scope"] == "gpqa_fixture_dry_run"
    assert diagnostic_payload["summary_metrics"]["audit_mode"] == "dry_run"


def test_matrix_from_predictions_command_builds_cached_matrix(tmp_path):
    source = tmp_path / "outputs.csv"
    source.write_text(
        "\n".join(
            [
                "model_id,item_id,prediction,score,raw_output",
                "m1,gpqa_fixture_0001,B,1,B",
                "m1,gpqa_fixture_0002,A,0,A",
                "m2,gpqa_fixture_0001,A,0,A",
                "m2,gpqa_fixture_0002,C,1,C",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cache_root = tmp_path / "cache"
    output = cache_root / "gpqa_diamond" / "gpqa_open_local" / "predictions_full.jsonl"

    assert (
        main(
            [
                "import-outputs",
                "--input",
                str(source),
                "--output",
                str(output),
                "--adapter",
                "generic-csv",
                "--benchmark-id",
                "gpqa_diamond",
                "--prompt-variant",
                "full",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "matrix-from-predictions",
                "--benchmark",
                "gpqa_diamond",
                "--panel",
                "gpqa_open_local",
                "--cache-root",
                str(cache_root),
            ]
        )
        == 0
    )

    assert (cache_root / "gpqa_diamond" / "gpqa_open_local" / "matrix_full.csv").exists()
