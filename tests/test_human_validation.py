from __future__ import annotations

import csv
from pathlib import Path

from valideval.audit.report_card import render_report_card
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.human.adjudication import create_adjudication_queue
from valideval.human.agreement import compute_agreement_report, write_agreement_report
from valideval.human.ambiguity import detect_scoring_ambiguity
from valideval.human.importer import import_annotations
from valideval.human.judges import (
    build_judge_predictions,
    judge_reliability_report,
    write_judge_reliability_report,
)
from valideval.human.packet import generate_annotation_packet
from valideval.human.ui import render_annotation_viewer
from valideval.io.jsonl import read_jsonl_as
from valideval.schemas import AnnotationTask, HumanJudgment, JudgePrediction


def test_annotation_packet_generation_writes_offline_artifacts(tmp_path: Path):
    output = tmp_path / "human"
    result = generate_annotation_packet(
        ToyMCQBenchmark(),
        "mock",
        output_dir=output,
        sample_size=6,
        strategy="coverage-balanced",
        seed=0,
    )

    assert Path(result["items_jsonl"]).exists()
    assert Path(result["guidelines_md"]).exists()
    assert Path(result["rubric_md"]).exists()
    assert Path(result["manifest_json"]).exists()
    tasks = read_jsonl_as(result["items_jsonl"], AnnotationTask)
    assert len(tasks) == 6
    assert all(task.task_hash for task in tasks)


def test_annotation_import_validates_rows_and_duplicates(tmp_path: Path):
    output = tmp_path / "human"
    generate_annotation_packet(
        ToyMCQBenchmark(),
        "mock",
        output_dir=output,
        sample_size=3,
        seed=0,
    )
    tasks = read_jsonl_as(output / "items.jsonl", AnnotationTask)
    good_csv = tmp_path / "annotations.csv"
    _write_annotations(
        good_csv,
        [
            {
                "task_id": tasks[0].task_id,
                "item_id": tasks[0].item_id,
                "model_id": tasks[0].model_id or "",
                "anonymized_annotator": "ann_a",
                "label": "correct",
                "confidence": "0.9",
                "rationale": "Matches the rubric.",
                "ambiguity_flag": "false",
                "invalid_item_flag": "false",
            },
            {
                "task_id": tasks[0].task_id,
                "item_id": tasks[0].item_id,
                "model_id": tasks[0].model_id or "",
                "anonymized_annotator": "ann_b",
                "label": "correct",
                "confidence": "0.8",
                "rationale": "Same decision.",
                "ambiguity_flag": "false",
                "invalid_item_flag": "false",
            },
        ],
    )

    result = import_annotations(
        good_csv,
        output_dir=output,
        benchmark_id="toy_mcq",
        panel_id="mock",
    )

    assert result["valid"] is True
    assert result["n_imported"] == 2

    bad_csv = tmp_path / "bad_annotations.csv"
    _write_annotations(
        bad_csv,
        [
            {
                "task_id": tasks[0].task_id,
                "item_id": tasks[0].item_id,
                "model_id": tasks[0].model_id or "",
                "anonymized_annotator": "ann_a",
                "label": "correct",
                "confidence": "1.3",
                "rationale": "",
                "ambiguity_flag": "false",
                "invalid_item_flag": "false",
            },
            {
                "task_id": tasks[0].task_id,
                "item_id": tasks[0].item_id,
                "model_id": tasks[0].model_id or "",
                "anonymized_annotator": "ann_a",
                "label": "incorrect",
                "confidence": "0.7",
                "rationale": "",
                "ambiguity_flag": "false",
                "invalid_item_flag": "false",
            },
            {
                "task_id": "unknown",
                "item_id": "unknown",
                "model_id": "",
                "anonymized_annotator": "ann_c",
                "label": "",
                "confidence": "0.5",
                "rationale": "",
                "ambiguity_flag": "false",
                "invalid_item_flag": "false",
            },
        ],
    )

    bad_result = import_annotations(
        bad_csv,
        output_dir=output,
        benchmark_id="toy_mcq",
        panel_id="mock",
    )

    assert bad_result["valid"] is False
    assert bad_result["n_errors"] >= 2


def test_agreement_metrics_compute_kappas_and_bootstrap_ci():
    judgments = [
        _judgment("task_1", "toy_001", "ann_a", "correct"),
        _judgment("task_1", "toy_001", "ann_b", "correct"),
        _judgment("task_2", "toy_002", "ann_a", "correct", ambiguity=True),
        _judgment("task_2", "toy_002", "ann_b", "incorrect"),
    ]
    tasks = [
        AnnotationTask(
            task_id="task_1",
            item_id="toy_001",
            prompt="p",
            model_output="B",
            gold_answer="B",
            rubric="rubric",
            tags=["context_use"],
        ),
        AnnotationTask(
            task_id="task_2",
            item_id="toy_002",
            prompt="p",
            model_output="C",
            gold_answer="C",
            rubric="rubric",
            tags=["quantitative_reasoning"],
        ),
    ]

    report = compute_agreement_report(
        judgments,
        benchmark_id="toy_mcq",
        panel_id="mock",
        tasks=tasks,
        n_boot=25,
        seed=0,
    )

    assert report.raw_agreement == 0.5
    assert report.fleiss_kappa is not None
    assert report.krippendorff_alpha["status"] == "measured"
    assert report.krippendorff_alpha["level"] == "nominal"
    assert report.krippendorff_alpha["value"] is not None
    assert report.bootstrap_ci["status"] == "measured"
    assert report.agreement_by_tag["context_use"]["raw_agreement"] == 1.0
    assert report.ambiguity_rate == 0.5


def test_judge_reliability_and_synthetic_answer_length_bias(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    tasks = [
        AnnotationTask(
            task_id="short",
            item_id="toy_001",
            prompt="p",
            model_output="A",
            gold_answer="B",
            rubric="rubric",
            model_id="m1",
        ),
        AnnotationTask(
            task_id="long",
            item_id="toy_001",
            prompt="p",
            model_output="Answer: B with a long supporting rationale.",
            gold_answer="B",
            rubric="rubric",
            model_id="m1",
        ),
    ]
    judge_predictions = [
        JudgePrediction(
            judge_id="synthetic",
            judge_type="mock",
            variant="mock",
            task_id="short",
            item_id="toy_001",
            model_id="m1",
            label="incorrect",
        ),
        JudgePrediction(
            judge_id="synthetic",
            judge_type="mock",
            variant="mock",
            task_id="long",
            item_id="toy_001",
            model_id="m1",
            label="correct",
        ),
    ]
    report = judge_reliability_report(
        benchmark,
        tasks,
        [
            _judgment("short", "toy_001", "ann", "incorrect"),
            _judgment("long", "toy_001", "ann", "correct"),
        ],
        judge_predictions,
        benchmark_id="toy_mcq",
        panel_id="mock",
    )

    assert report["metrics"]["answer_length_bias"]["long_minus_short_correct_rate"] == 1.0
    assert report["metrics"]["judge_human_agreement"]["agreement"] == 1.0

    generated = build_judge_predictions(benchmark, tasks)
    assert {prediction.variant for prediction in generated} == {
        "strict",
        "lenient",
        "regex",
        "mock",
    }

    output = tmp_path / "human"
    generate_annotation_packet(benchmark, "mock", output_dir=output, sample_size=2)
    judge_output = write_judge_reliability_report(
        benchmark,
        output_dir=output,
        benchmark_id="toy_mcq",
        panel_id="mock",
    )
    assert Path(judge_output["judge_predictions_jsonl"]).exists()


def test_scoring_ambiguity_and_adjudication_queue(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    item = next(item for item in benchmark.load_items() if item.item_id == "toy_029")
    task = AnnotationTask(
        task_id="toy_029::m1",
        item_id=item.item_id,
        prompt="p",
        model_output="Answer: C",
        gold_answer=item.answer,
        rubric="Detailed enough rubric for ambiguity detection.",
        model_id="m1",
        tags=item.construct_tags,
    )
    judgments = [
        _judgment(task.task_id, item.item_id, "ann_a", "correct", ambiguity=True),
        _judgment(task.task_id, item.item_id, "ann_b", "incorrect", ambiguity=True),
    ]
    judges = [
        JudgePrediction(
            judge_id="rule_strict",
            judge_type="rule_based",
            variant="strict",
            task_id=task.task_id,
            item_id=item.item_id,
            model_id="m1",
            label="unscorable",
        ),
        JudgePrediction(
            judge_id="rule_lenient",
            judge_type="rule_based",
            variant="lenient",
            task_id=task.task_id,
            item_id=item.item_id,
            model_id="m1",
            label="correct",
        ),
    ]

    output = detect_scoring_ambiguity(
        benchmark,
        tasks=[task],
        judgments=judgments,
        judge_predictions=judges,
        output_dir=tmp_path / "human",
    )
    queue = create_adjudication_queue(output_dir=tmp_path / "human")

    assert output["n_ambiguous_tasks"] == 1
    assert "multiple_valid_answers" in output["examples"][0]["reasons"]
    assert Path(output["scoring_ambiguity_csv"]).exists()
    assert queue["n_queue_items"] >= 1


def test_report_card_includes_human_sections_when_artifacts_exist(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    audit_dir = tmp_path / "toy_mcq" / "mock"
    human_dir = audit_dir / "human"
    generate_annotation_packet(benchmark, "mock", output_dir=human_dir, sample_size=3, seed=0)
    tasks = read_jsonl_as(human_dir / "items.jsonl", AnnotationTask)
    csv_path = tmp_path / "annotations.csv"
    _write_annotations(
        csv_path,
        [
            {
                "task_id": tasks[0].task_id,
                "item_id": tasks[0].item_id,
                "model_id": tasks[0].model_id or "",
                "anonymized_annotator": "ann_a",
                "label": "correct",
                "confidence": "0.9",
                "rationale": "",
                "ambiguity_flag": "false",
                "invalid_item_flag": "false",
            },
            {
                "task_id": tasks[0].task_id,
                "item_id": tasks[0].item_id,
                "model_id": tasks[0].model_id or "",
                "anonymized_annotator": "ann_b",
                "label": "correct",
                "confidence": "0.8",
                "rationale": "",
                "ambiguity_flag": "false",
                "invalid_item_flag": "false",
            },
        ],
    )
    import_annotations(csv_path, output_dir=human_dir, benchmark_id="toy_mcq", panel_id="mock")
    write_agreement_report(output_dir=human_dir, benchmark_id="toy_mcq", panel_id="mock", n_boot=10)
    write_judge_reliability_report(
        benchmark,
        output_dir=human_dir,
        benchmark_id="toy_mcq",
        panel_id="mock",
    )
    detect_scoring_ambiguity(benchmark, output_dir=human_dir)
    render_annotation_viewer(output_dir=human_dir)

    report = render_report_card(benchmark, "mock", [], artifacts_dir=audit_dir)

    assert "## Human validation" in report
    assert "## Judge reliability" in report
    assert "## Scoring ambiguity" in report
    assert "Human judgments imported: 2" in report
    assert (human_dir / "annotation_viewer.html").exists()


def _judgment(
    task_id: str,
    item_id: str,
    annotator: str,
    label: str,
    *,
    ambiguity: bool = False,
) -> HumanJudgment:
    return HumanJudgment(
        task_id=task_id,
        item_id=item_id,
        anonymized_annotator=annotator,
        label=label,
        confidence=0.8,
        ambiguity_flag=ambiguity,
    )


def _write_annotations(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "task_id",
        "item_id",
        "model_id",
        "anonymized_annotator",
        "label",
        "confidence",
        "rationale",
        "ambiguity_flag",
        "invalid_item_flag",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
