from __future__ import annotations

import csv
import json

import pytest

from valideval.benchmarks.gpqa_inputs import validate_gpqa_item_file
from valideval.benchmarks.gpqa_local import (
    check_panel_readiness,
    export_gpqa_diamond,
    generate_gpqa_outputs,
)
from valideval.io.jsonl import read_jsonl


def test_export_gpqa_diamond_from_synthetic_csv(tmp_path):
    source = _source_csv(tmp_path)
    output = tmp_path / "data" / "gpqa" / "gpqa_diamond.jsonl"
    report = export_gpqa_diamond(
        source_file=source,
        output_path=output,
        seed=17,
        results_root=tmp_path / "results",
    )
    rows = read_jsonl(output)

    assert report["validation_status"] == "pass"
    assert report["item_count"] == 2
    assert report["question_text_included"] is False
    assert rows[0]["item_id"] == "gpqa_diamond_000001"
    assert rows[0]["choices"][rows[0]["answer"]] == "phase-red"
    assert rows[1]["choices"][rows[1]["answer"]] == "orbital-tau"
    assert rows[0]["metadata"]["provenance"] == "local_export"
    assert validate_gpqa_item_file(output)["valid"] is True


def test_export_choice_shuffle_is_deterministic_and_remaps_answer(tmp_path):
    source = _source_csv(tmp_path)
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    third = tmp_path / "third.jsonl"

    export_gpqa_diamond(
        source_file=source,
        output_path=first,
        seed=11,
        results_root=tmp_path / "first_results",
    )
    export_gpqa_diamond(
        source_file=source,
        output_path=second,
        seed=11,
        results_root=tmp_path / "second_results",
    )
    export_gpqa_diamond(
        source_file=source,
        output_path=third,
        seed=12,
        results_root=tmp_path / "third_results",
    )

    first_rows = read_jsonl(first)
    second_rows = read_jsonl(second)
    third_rows = read_jsonl(third)

    assert first_rows == second_rows
    assert first_rows[0]["choices"][first_rows[0]["answer"]] == "phase-red"
    assert third_rows[0]["choices"][third_rows[0]["answer"]] == "phase-red"
    assert first_rows[0]["choices"] != third_rows[0]["choices"]


def test_export_report_omits_raw_question_text(tmp_path):
    source = _source_csv(tmp_path)
    output = tmp_path / "gpqa_diamond.jsonl"
    export_gpqa_diamond(
        source_file=source,
        output_path=output,
        seed=0,
        results_root=tmp_path / "results",
    )

    report_dir = tmp_path / "results" / "gpqa_diamond" / "input_validation"
    markdown = (report_dir / "export_report.md").read_text(encoding="utf-8")
    payload = (report_dir / "export_report.json").read_text(encoding="utf-8")

    assert "synthetic reaction pattern P" not in markdown
    assert "synthetic reaction pattern P" not in payload
    assert "synthetic orbital family Q" not in markdown
    assert "synthetic orbital family Q" not in payload
    assert "This report intentionally omits raw GPQA question text." in markdown


def test_panel_readiness_report_for_smoke_panel(tmp_path):
    report = check_panel_readiness(
        panel_id="gpqa_smoke_local",
        results_root=tmp_path / "results",
        cache_root=tmp_path / "cache",
    )

    assert report["status"] == "ready"
    assert report["configured_model_count"] == 2
    assert {row["availability_status"] for row in report["models"]} == {"available_mock"}
    assert (
        tmp_path / "results" / "gpqa_diamond" / "input_validation" / "panel_readiness.md"
    ).exists()


def test_generate_outputs_smoke_limit_resume_and_prompt_hash(tmp_path):
    items = _exported_items(tmp_path)
    output_dir = tmp_path / "local_outputs" / "gpqa" / "full"

    first = generate_gpqa_outputs(
        items_path=items,
        panel_id="gpqa_smoke_local",
        prompt_variant="full",
        output_dir=output_dir,
        limit_items=1,
        seed=3,
    )
    second = generate_gpqa_outputs(
        items_path=items,
        panel_id="gpqa_smoke_local",
        prompt_variant="full",
        output_dir=output_dir,
        limit_items=1,
        seed=3,
    )

    assert first["status"] == "generated"
    assert first["item_count_requested"] == 1
    assert {file["generated"] for file in first["files"]} == {1}
    assert {file["skipped_existing"] for file in second["files"]} == {1}
    assert {file["generated"] for file in second["files"]} == {0}

    rows = read_jsonl(output_dir / "always_a.jsonl")
    assert len(rows) == 1
    assert _valid_raw_output_shape(rows[0]) is True
    assert rows[0]["metadata"]["prompt_template_hash"]
    assert rows[0]["metadata"]["source"] == "local_model_generation"
    assert rows[0]["metadata"]["smoke_test_only"] is True


def test_generate_outputs_allows_yaml_backed_exploratory_variant(tmp_path):
    items = _exported_items(tmp_path)
    output_dir = tmp_path / "local_outputs" / "gpqa" / "full_answer_only_v2"

    report = generate_gpqa_outputs(
        items_path=items,
        panel_id="gpqa_smoke_local",
        prompt_variant="full_answer_only_v2",
        output_dir=output_dir,
        limit_items=1,
        seed=3,
    )

    rows = read_jsonl(output_dir / "always_a.jsonl")
    assert report["artifact_scope"] == "gpqa_exploratory_extraction_compliance"
    assert rows[0]["prompt_variant"] == "full_answer_only_v2"
    assert rows[0]["metadata"]["artifact_scope"] == "gpqa_exploratory_extraction_compliance"
    assert rows[0]["metadata"]["prompt_artifact_class"] == (
        "secondary_exploratory_extraction_compliance"
    )


def test_generate_outputs_rejects_fixture_like_real_input(tmp_path):
    path = tmp_path / "fixture_like.jsonl"
    _write_jsonl(
        path,
        [
            {
                "item_id": "gpqa_fixture_0001",
                "question": "Which option follows the fixture rule?",
                "choices": {
                    "A": "alpha",
                    "B": "beta",
                    "C": "gamma",
                    "D": "delta",
                },
                "answer": "A",
                "domain": "physics",
                "source": "synthetic_fixture_not_gpqa",
                "split": "diamond",
                "metadata": {
                    "synthetic_fixture": True,
                    "license": "synthetic",
                    "provenance": "fixture",
                },
            }
        ],
    )

    with pytest.raises(ValueError, match="fixture-like data"):
        generate_gpqa_outputs(
            items_path=path,
            panel_id="gpqa_smoke_local",
            prompt_variant="full",
            output_dir=tmp_path / "outputs",
        )


def _source_csv(tmp_path):
    path = tmp_path / "gpqa_source.csv"
    rows = [
        {
            "Record ID": "record-001",
            "Question": "Which option follows the hidden synthetic reaction pattern P?",
            "Correct Answer": "phase-red",
            "Incorrect Answer 1": "phase-blue",
            "Incorrect Answer 2": "phase-green",
            "Incorrect Answer 3": "phase-violet",
            "High-level domain": "chemistry",
            "Subdomain": "synthetic kinetics",
            "License": "synthetic-test-license",
        },
        {
            "Record ID": "record-002",
            "Question": "Which option follows the hidden synthetic orbital family Q?",
            "Correct Answer": "orbital-tau",
            "Incorrect Answer 1": "orbital-rho",
            "Incorrect Answer 2": "orbital-sigma",
            "Incorrect Answer 3": "orbital-upsilon",
            "High-level domain": "physics",
            "Subdomain": "synthetic fields",
            "License": "synthetic-test-license",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _exported_items(tmp_path):
    output = tmp_path / "gpqa_diamond.jsonl"
    export_gpqa_diamond(
        source_file=_source_csv(tmp_path),
        output_path=output,
        seed=0,
        results_root=tmp_path / "results",
    )
    return output


def _valid_raw_output_shape(row):
    return (
        isinstance(row.get("model_id"), str)
        and bool(row["model_id"])
        and isinstance(row.get("item_id"), str)
        and bool(row["item_id"])
        and row.get("prompt_variant")
        in {"full", "question_only", "choices_only", "randomized_choices", "answer_letter_only"}
        and isinstance(row.get("raw_output"), str)
        and isinstance(row.get("metadata"), dict)
        and isinstance(row["metadata"].get("prompt_template_hash"), str)
    )


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
