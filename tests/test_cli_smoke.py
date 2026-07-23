import csv

from valideval.cli import main
from valideval.io.jsonl import read_jsonl_as
from valideval.schemas import AnnotationTask


def test_cli_info_smoke():
    assert main(["info"]) == 0


def test_cli_validate_config_smoke():
    assert main(["validate-config", "configs/default.yaml"]) == 0


def test_cli_core_commands_smoke(tmp_path):
    common = [
        "--cache-root",
        str(tmp_path / "cache"),
        "--results-root",
        str(tmp_path / "results"),
        "--reportcards-root",
        str(tmp_path / "reportcards"),
    ]

    assert main(["baselines", "--benchmark", "toy_mcq", *common]) == 0
    assert main(["diagnostics", "answer-distribution", "--benchmark", "toy_mcq", *common]) == 0
    assert main(["diagnostics", "distractors", "--benchmark", "toy_mcq", *common]) == 0
    assert (
        main(
            [
                "diagnostics",
                "prompt-sensitivity",
                "--benchmark",
                "toy_mcq",
                "--panel",
                "mock",
                *common,
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "diagnostics",
                "extraction-robustness",
                "--benchmark",
                "toy_mcq",
                "--panel",
                "mock",
                *common,
            ]
        )
        == 0
    )
    assert main(["psychometrics", "irt", "--benchmark", "toy_mcq", "--panel", "mock", *common]) == 0
    assert (
        main(["psychometrics", "saturation", "--benchmark", "toy_mcq", "--panel", "mock", *common])
        == 0
    )
    assert (
        main(["psychometrics", "power", "--benchmark", "toy_mcq", "--panel", "mock", *common]) == 0
    )
    assert main(["psychometrics", "dif", "--benchmark", "toy_mcq", "--panel", "mock", *common]) == 0
    assert (
        main(["psychometrics", "calibration", "--benchmark", "toy_mcq", "--panel", "mock", *common])
        == 0
    )


def test_cli_forensics_overlap_smoke(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "doc.md").write_text(
        "Which substance does the plant store as energy after using sunlight?",
        encoding="utf-8",
    )

    assert (
        main(
            [
                "forensics",
                "overlap",
                "--benchmark",
                "toy_mcq",
                "--corpus",
                str(corpus),
                "--results-root",
                str(tmp_path / "results"),
            ]
        )
        == 0
    )
    assert (tmp_path / "results" / "toy_mcq" / "forensics_overlap.json").exists()


def test_cli_human_validation_smoke(tmp_path):
    common = [
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
    ]

    assert main(["human", "packet", *common, "--sample-size", "4"]) == 0
    human_dir = tmp_path / "results" / "toy_mcq" / "mock" / "human"
    tasks = read_jsonl_as(human_dir / "items.jsonl", AnnotationTask)
    annotations = tmp_path / "annotations.csv"
    with annotations.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "task_id",
                "item_id",
                "model_id",
                "anonymized_annotator",
                "label",
                "confidence",
                "rationale",
                "ambiguity_flag",
                "invalid_item_flag",
            ],
        )
        writer.writeheader()
        for annotator in ["ann_a", "ann_b"]:
            writer.writerow(
                {
                    "task_id": tasks[0].task_id,
                    "item_id": tasks[0].item_id,
                    "model_id": tasks[0].model_id or "",
                    "anonymized_annotator": annotator,
                    "label": "correct",
                    "confidence": "0.8",
                    "rationale": "",
                    "ambiguity_flag": "false",
                    "invalid_item_flag": "false",
                }
            )

    assert main(["human", "import", *common, "--path", str(annotations)]) == 0
    assert main(["human", "agreement", *common, "--bootstrap-samples", "10"]) == 0
    assert main(["human", "judge", *common]) == 0
    assert main(["human", "ambiguity", *common]) == 0
    assert main(["human", "adjudication", *common]) == 0
    assert main(["human", "ui", *common]) == 0

    assert (human_dir / "agreement_report.json").exists()
    assert (human_dir / "judge_reliability.json").exists()
    assert (human_dir / "scoring_ambiguity.csv").exists()
    assert (human_dir / "adjudication_queue.jsonl").exists()
    assert (human_dir / "annotation_viewer.html").exists()


def test_cli_repair_card_certificate_checklist_evidence_smoke(tmp_path):
    common = [
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
        "--registry-root",
        str(tmp_path / "registry"),
        "--leaderboard-root",
        str(tmp_path / "leaderboard"),
        "--dashboard-root",
        str(tmp_path / "dashboard_data"),
    ]

    assert main(["audit", *common, "--diagnostics", "all-core"]) == 0
    assert main(["repair", *common, "--policy", "conservative"]) == 0
    assert main(["card", "render", *common]) == 0
    assert main(["certificate", "issue", *common]) == 0
    assert main(["checklist", *common]) == 0
    assert main(["evidence-matrix", *common]) == 0
    assert main(["leaderboard", *common, "--bootstrap-samples", "25"]) == 0
    assert main(["registry", "validate", "--registry-root", str(tmp_path / "registry")]) == 0
    assert main(["registry", "list", "--registry-root", str(tmp_path / "registry")]) == 0
    assert main(["registry", "add", *common]) == 0
    assert main(["atlas", *common]) == 0
    assert main(["dashboard", "export", *common]) == 0
    assert (
        main(
            [
                "site",
                "build",
                "--site-root",
                str(tmp_path / "site"),
                "--registry-root",
                str(tmp_path / "registry"),
                "--leaderboard-root",
                str(tmp_path / "leaderboard"),
                "--results-root",
                str(tmp_path / "results"),
                "--reportcards-root",
                str(tmp_path / "reportcards"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "audit-diff",
                str(tmp_path / "results" / "toy_mcq" / "mock"),
                str(tmp_path / "results" / "toy_mcq" / "mock"),
                "--output",
                str(tmp_path / "audit_diff.json"),
            ]
        )
        == 0
    )
    assert main(["badges", *common]) == 0

    output = tmp_path / "results" / "toy_mcq" / "mock"
    assert (output / "item_forensics.csv").exists()
    assert (output / "repair_diff.json").exists()
    assert (output / "validity_card.json").exists()
    assert (output / "validity_certificate.json").exists()
    assert (output / "author_checklist.md").exists()
    assert (output / "claim_evidence_matrix.csv").exists()
    assert (output / "ranking_views.json").exists()
    assert (output / "ranking_flips.json").exists()
    assert (output / "health_badges.json").exists()
    assert (tmp_path / "leaderboard" / "benchmark_atlas.json").exists()
    assert (tmp_path / "dashboard_data" / "benchmark_profiles.json").exists()
    assert (tmp_path / "site" / "index.html").exists()
    assert (tmp_path / "audit_diff.json").exists()
