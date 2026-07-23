from __future__ import annotations

import json

from valideval.benchmarks.gpqa_inputs import (
    extraction_audit,
    go_no_go_report,
    validate_alignment,
    validate_gpqa_item_file,
    validate_prompt_variant_cache,
    write_audit_manifest,
)
from valideval.cli import main
from valideval.io.jsonl import read_jsonl_as
from valideval.schemas import ModelPrediction


def test_validate_gpqa_item_file_valid_and_invalid_cases(tmp_path):
    valid = _items_path(tmp_path)
    report = validate_gpqa_item_file(valid, output_dir=tmp_path / "reports")

    assert report["valid"] is True
    assert report["item_count"] == 2
    assert (tmp_path / "reports" / "item_validation.json").exists()

    missing_answer = tmp_path / "missing_answer.jsonl"
    _write_jsonl(
        missing_answer,
        [
            {
                "item_id": "gpqa_diamond_bad_001",
                "question": "Which synthetic option follows the rule?",
                "choices": {"A": "alpha", "B": "beta", "C": "gamma", "D": "delta"},
                "domain": "physics",
                "source": "gpqa",
                "split": "diamond",
                "metadata": _metadata("bad"),
            }
        ],
    )
    assert validate_gpqa_item_file(missing_answer)["valid"] is False

    duplicate = tmp_path / "duplicate.jsonl"
    rows = _item_rows()
    rows[1]["item_id"] = rows[0]["item_id"]
    _write_jsonl(duplicate, rows)
    duplicate_report = validate_gpqa_item_file(duplicate)
    assert duplicate_report["valid"] is False
    assert duplicate_report["duplicate_item_ids"]

    bad_label = tmp_path / "bad_label.jsonl"
    rows = _item_rows()
    rows[0]["answer"] = "E"
    _write_jsonl(bad_label, rows)
    assert validate_gpqa_item_file(bad_label)["valid"] is False


def test_gpqa_item_validation_rejects_fixture_mixing(tmp_path):
    path = tmp_path / "fixture_like.jsonl"
    row = _item_rows()[0]
    row["item_id"] = "gpqa_fixture_0001"
    row["metadata"]["synthetic_fixture"] = True
    _write_jsonl(path, [row])

    report = validate_gpqa_item_file(path)

    assert report["valid"] is False
    assert report["artifact_scope"] == "gpqa_real_audit_blocked"
    assert report["fixture_like_items"] == ["gpqa_fixture_0001"]


def test_gpqa_item_validation_warns_on_question_answer_text_overlap(tmp_path):
    path = tmp_path / "answer_overlap.jsonl"
    row = _item_rows()[0]
    row["question"] = "Which option is isotope gamma under the synthetic rule?"
    row["answer"] = "C"
    _write_jsonl(path, [row])

    report = validate_gpqa_item_file(path)

    assert report["valid"] is True
    assert report["answer_text_overlap_items"] == ["gpqa_diamond_000001"]
    assert any("Question text overlaps" in warning for warning in report["warnings"])


def test_score_outputs_import_alignment_and_extraction_audit(tmp_path):
    items = _items_path(tmp_path)
    raw = _raw_outputs_path(tmp_path)
    predictions = tmp_path / "cache" / "gpqa_diamond" / "gpqa_open_local" / "predictions_full.jsonl"

    assert (
        main(
            [
                "score-outputs",
                "--benchmark",
                "gpqa_diamond",
                "--items",
                str(items),
                "--input",
                str(raw),
                "--output",
                str(predictions),
                "--prompt-variant",
                "full",
            ]
        )
        == 0
    )
    scored = read_jsonl_as(predictions, ModelPrediction)
    assert len(scored) == 4
    assert {record.metadata["artifact_scope"] for record in scored} == {
        "gpqa_real_input_validation"
    }
    assert any(record.metadata["extraction_mode"] == "normalized_text_match" for record in scored)

    alignment = validate_alignment(
        items_path=items,
        predictions_path=predictions,
        output_dir=tmp_path / "results" / "gpqa_diamond" / "input_validation",
        required_variants=["full"],
        min_models=2,
    )
    assert alignment["go_no_go_status"] == "pass"
    assert alignment["matrix_completeness"]["full"]["complete"] is True

    audit = extraction_audit(
        items_path=items,
        outputs_path=raw,
        output_dir=tmp_path / "results" / "gpqa_diamond" / "input_validation",
        prompt_variant="full",
    )
    assert audit["passes_threshold"] is True
    assert audit["invalid_output_count"] == 0
    assert audit["answer_text_match_count"] == 1


def test_validate_alignment_reports_missing_and_extra_ids(tmp_path):
    items = _items_path(tmp_path)
    predictions = tmp_path / "predictions.jsonl"
    _write_scored_predictions(
        predictions,
        [
            ("model_a", "gpqa_diamond_000001", "full", "C", 1.0),
            ("model_a", "gpqa_diamond_extra", "full", "D", 0.0),
        ],
    )

    report = validate_alignment(
        items_path=items,
        predictions_path=predictions,
        output_dir=tmp_path / "reports",
        required_variants=["full"],
        min_models=1,
    )

    assert report["go_no_go_status"] == "blocked"
    assert "gpqa_diamond_extra" in report["extra_item_ids"]
    assert "gpqa_diamond_000002" in report["missing_item_ids"]


def test_import_scored_predictions_and_matrix_commands(tmp_path):
    source = tmp_path / "scored.jsonl"
    _write_jsonl(
        source,
        [
            {
                "model_id": "model_a",
                "item_id": "gpqa_diamond_000001",
                "prompt_variant": "full",
                "prediction": "C",
                "score": 1.0,
                "is_correct": True,
                "raw_output": "The answer is C.",
            }
        ],
    )
    output = tmp_path / "cache" / "gpqa_diamond" / "gpqa_open_local" / "predictions_full.jsonl"
    matrix = tmp_path / "matrix_full.csv"

    assert (
        main(
            [
                "import-outputs",
                "--input",
                str(source),
                "--output",
                str(output),
                "--adapter",
                "generic-jsonl",
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
                "--variant",
                "full",
                "--predictions",
                str(output),
                "--output",
                str(matrix),
            ]
        )
        == 0
    )
    assert matrix.exists()
    assert matrix.with_suffix(".metadata.json").exists()


def test_prompt_variant_go_no_go_manifest_and_dry_run_real(tmp_path):
    items = _items_path(tmp_path)
    raw = _raw_outputs_path(tmp_path)
    cache_root = tmp_path / "cache"
    results_root = tmp_path / "results"
    predictions = cache_root / "gpqa_diamond" / "gpqa_open_local" / "predictions_full.jsonl"

    assert (
        main(
            [
                "score-outputs",
                "--benchmark",
                "gpqa_diamond",
                "--items",
                str(items),
                "--input",
                str(raw),
                "--output",
                str(predictions),
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
                "--variant",
                "full",
                "--cache-root",
                str(cache_root),
            ]
        )
        == 0
    )

    partial = validate_prompt_variant_cache(
        benchmark_id="gpqa_diamond",
        panel_id="gpqa_open_local",
        cache_root=cache_root,
        output_dir=results_root / "gpqa_diamond" / "input_validation",
        required_variants=["full", "choices_only"],
    )
    assert partial["status"] == "blocked"
    assert partial["partial_input_validation_allowed"] is True

    amended_cache = cache_root / "gpqa_diamond" / "gpqa_open_local"
    (amended_cache / "predictions_full_answer_only_v2.jsonl").write_text("", encoding="utf-8")
    (amended_cache / "matrix_full_answer_only_v2.csv").write_text("", encoding="utf-8")
    amended = validate_prompt_variant_cache(
        benchmark_id="gpqa_diamond",
        panel_id="gpqa_open_local",
        cache_root=cache_root,
        output_dir=results_root / "gpqa_diamond" / "input_validation",
        required_variants=["full_answer_only_v2"],
    )
    assert amended["status"] == "pass"
    assert amended["invalid_required_variants"] == []

    ready = go_no_go_report(
        items_path=items,
        panel_id="gpqa_open_local",
        cache_root=cache_root,
        results_root=results_root,
        required_variants=["full"],
        min_models=2,
    )
    assert ready["status"] == "go"
    assert ready["artifact_scope"] == "gpqa_real_audit_ready"

    manifest = write_audit_manifest(
        items_path=items,
        panel_id="gpqa_open_local",
        cache_root=cache_root,
        results_root=results_root,
    )
    assert manifest["item_file_hash"]
    assert manifest["prompt_template_hashes"]
    assert manifest["prediction_file_hashes"]["full"]

    assert (
        main(
            [
                "audit",
                "--benchmark",
                "gpqa_diamond",
                "--panel",
                "gpqa_open_local",
                "--local-path",
                str(items),
                "--cache-root",
                str(cache_root),
                "--results-root",
                str(results_root),
                "--dry-run-real",
                "--required-variants",
                "full",
                "--min-models",
                "2",
            ]
        )
        == 0
    )
    dry_run = json.loads(
        (results_root / "gpqa_diamond" / "input_validation" / "real_audit_dry_run.json").read_text(
            encoding="utf-8"
        )
    )
    assert dry_run["artifact_scope"] == "gpqa_real_audit_dry_run"
    assert dry_run["no_diagnostics_interpreted"] is True


def test_go_no_go_blocks_missing_matrix(tmp_path):
    items = _items_path(tmp_path)
    report = go_no_go_report(
        items_path=items,
        panel_id="gpqa_open_local",
        cache_root=tmp_path / "cache",
        results_root=tmp_path / "results",
        required_variants=["full"],
        min_models=2,
    )

    assert report["status"] == "no_go"
    assert report["artifact_scope"] == "gpqa_real_audit_blocked"


def test_go_no_go_uses_amended_primary_matrix_variant(tmp_path):
    items = _items_path(tmp_path)
    cache_root = tmp_path / "cache"
    results_root = tmp_path / "results"
    predictions = (
        cache_root / "gpqa_diamond" / "gpqa_open_local" / "predictions_full_answer_only_v2.jsonl"
    )
    _write_scored_predictions(
        predictions,
        [
            ("model_a", "gpqa_diamond_000001", "full_answer_only_v2", "C", 1.0),
            ("model_a", "gpqa_diamond_000002", "full_answer_only_v2", "D", 1.0),
            ("model_b", "gpqa_diamond_000001", "full_answer_only_v2", "C", 1.0),
            ("model_b", "gpqa_diamond_000002", "full_answer_only_v2", "A", 0.0),
        ],
    )
    assert (
        main(
            [
                "matrix-from-predictions",
                "--benchmark",
                "gpqa_diamond",
                "--panel",
                "gpqa_open_local",
                "--variant",
                "full_answer_only_v2",
                "--cache-root",
                str(cache_root),
            ]
        )
        == 0
    )
    config = tmp_path / "amended.yaml"
    config.write_text(
        "\n".join(
            [
                "amended_protocol:",
                "  preregistration: docs/protocols/gpqa_diamond_preregistration_amended_v2.md",
                "  primary_full_variant: full_answer_only_v2",
                "  original_full_variant: full",
                "go_no_go:",
                "  required_variants:",
                "    - full_answer_only_v2",
            ]
        ),
        encoding="utf-8",
    )

    report = go_no_go_report(
        items_path=items,
        panel_id="gpqa_open_local",
        cache_root=cache_root,
        results_root=results_root,
        min_models=2,
        config_path=config,
    )

    assert report["status"] == "go"
    assert report["primary_full_variant"] == "full_answer_only_v2"
    assert not (cache_root / "gpqa_diamond" / "gpqa_open_local" / "matrix_full.csv").exists()


def test_audit_from_cache_uses_amended_primary_matrix_variant(tmp_path):
    items = _items_path(tmp_path)
    cache_root = tmp_path / "cache"
    results_root = tmp_path / "results"
    predictions = (
        cache_root / "gpqa_diamond" / "gpqa_open_local" / "predictions_full_answer_only_v2.jsonl"
    )
    _write_scored_predictions(
        predictions,
        [
            ("model_a", "gpqa_diamond_000001", "full_answer_only_v2", "C", 1.0),
            ("model_a", "gpqa_diamond_000002", "full_answer_only_v2", "D", 1.0),
            ("model_b", "gpqa_diamond_000001", "full_answer_only_v2", "C", 1.0),
            ("model_b", "gpqa_diamond_000002", "full_answer_only_v2", "A", 0.0),
        ],
    )
    assert (
        main(
            [
                "matrix-from-predictions",
                "--benchmark",
                "gpqa_diamond",
                "--panel",
                "gpqa_open_local",
                "--variant",
                "full_answer_only_v2",
                "--cache-root",
                str(cache_root),
            ]
        )
        == 0
    )
    config = tmp_path / "amended.yaml"
    config.write_text(
        "\n".join(
            [
                "diagnostics:",
                "  amended_primary_full_variant: full_answer_only_v2",
                "  irt:",
                "    bootstrap_samples: 5",
                "    random_subset_trials: 5",
                "    subset_sizes: [1, 2]",
            ]
        ),
        encoding="utf-8",
    )

    assert (
        main(
            [
                "audit",
                "--benchmark",
                "gpqa_diamond",
                "--panel",
                "gpqa_open_local",
                "--local-path",
                str(items),
                "--cache-root",
                str(cache_root),
                "--results-root",
                str(results_root),
                "--config",
                str(config),
                "--from-cache",
                "--diagnostics",
                "irt",
            ]
        )
        == 0
    )

    payload = json.loads(
        (results_root / "gpqa_diamond" / "gpqa_open_local" / "irt.json").read_text(encoding="utf-8")
    )
    assert payload["summary_metrics"]["primary_full_variant"] == "full_answer_only_v2"
    assert not (cache_root / "gpqa_diamond" / "gpqa_open_local" / "matrix_full.csv").exists()


def _items_path(tmp_path):
    path = tmp_path / "gpqa_diamond.jsonl"
    _write_jsonl(path, _item_rows())
    return path


def _item_rows():
    return [
        {
            "item_id": "gpqa_diamond_000001",
            "question": "Which synthetic isotope follows rule one?",
            "choices": {
                "A": "isotope alpha",
                "B": "isotope beta",
                "C": "isotope gamma",
                "D": "isotope delta",
            },
            "answer": "C",
            "domain": "physics",
            "source": "gpqa",
            "split": "diamond",
            "metadata": _metadata("001"),
        },
        {
            "item_id": "gpqa_diamond_000002",
            "question": "Which synthetic state follows rule two?",
            "choices": {
                "A": "state red",
                "B": "state blue",
                "C": "state green",
                "D": "state violet",
            },
            "answer": "D",
            "domain": "chemistry",
            "source": "gpqa",
            "split": "diamond",
            "metadata": _metadata("002"),
        },
    ]


def _metadata(source_id):
    return {
        "discipline": "synthetic_science",
        "source_id": f"local-{source_id}",
        "license": "synthetic-test-license",
        "provenance": "local_export",
    }


def _raw_outputs_path(tmp_path):
    path = tmp_path / "raw_outputs.jsonl"
    _write_jsonl(
        path,
        [
            {
                "model_id": "model_a",
                "item_id": "gpqa_diamond_000001",
                "prompt_variant": "full",
                "raw_output": "C",
            },
            {
                "model_id": "model_a",
                "item_id": "gpqa_diamond_000002",
                "prompt_variant": "full",
                "raw_output": "The answer is D.",
            },
            {
                "model_id": "model_b",
                "item_id": "gpqa_diamond_000001",
                "prompt_variant": "full",
                "raw_output": "isotope gamma",
            },
            {
                "model_id": "model_b",
                "item_id": "gpqa_diamond_000002",
                "prompt_variant": "full",
                "raw_output": "A",
            },
        ],
    )
    return path


def _write_scored_predictions(path, rows):
    _write_jsonl(
        path,
        [
            {
                "model_id": model_id,
                "item_id": item_id,
                "prompt_variant": variant,
                "prediction": prediction,
                "score": score,
                "is_correct": bool(score),
                "raw_output": prediction,
                "metadata": {"artifact_scope": "gpqa_real_input_validation"},
            }
            for model_id, item_id, variant, prediction, score in rows
        ],
    )


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
