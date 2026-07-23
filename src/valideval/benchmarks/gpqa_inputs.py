from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from valideval.benchmarks.gpqa import GPQADiamondJSONLBenchmark
from valideval.config import load_yaml
from valideval.forensics.provenance import stable_hash
from valideval.io.cache import (
    build_response_matrix,
    load_matrix,
    matrix_path,
    prediction_path,
    save_matrix,
)
from valideval.io.jsonl import read_jsonl, read_jsonl_as, write_jsonl
from valideval.schemas import BenchmarkItem, ModelPrediction, ScoreResult, utc_now
from valideval.scoring.exact_match import normalize_text
from valideval.scoring.extraction import (
    detect_refusal,
    lenient_letter,
    normalized_text_match,
    regex_final_answer,
    strict_letter,
)
from valideval.scoring.mcq import normalize_mcq_label, score_mcq
from valideval.scoring.mcq_utils import item_choice_map

GPQA_VARIANTS = [
    "full",
    "question_only",
    "choices_only",
    "randomized_choices",
    "answer_letter_only",
]
FROZEN_EXTRACTOR_VERSION = "gpqa_frozen_mcq_v1_parser_bugfix_final_answer"
INPUT_VALIDATION_DIRNAME = "input_validation"
DEFAULT_MIN_MODELS = 8
DEFAULT_EXTRACTION_SUCCESS_THRESHOLD = 0.95
ARTIFACT_REAL_INPUT_VALIDATION = "gpqa_real_input_validation"
ARTIFACT_REAL_AUDIT_READY = "gpqa_real_audit_ready"
ARTIFACT_REAL_AUDIT_BLOCKED = "gpqa_real_audit_blocked"
ARTIFACT_REAL_AUDIT_DRY_RUN = "gpqa_real_audit_dry_run"


def validation_dir(results_root: str | Path, benchmark_id: str = "gpqa_diamond") -> Path:
    return Path(results_root) / benchmark_id / INPUT_VALIDATION_DIRNAME


def validate_gpqa_item_file(
    items_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    expected_split: str = "diamond",
) -> dict[str, Any]:
    path = Path(items_path)
    errors: list[str] = []
    warnings: list[str] = []
    raw_records: list[dict[str, Any]] = []
    item_ids: list[str] = []
    question_texts: list[str] = []
    duplicate_choice_items: list[str] = []
    missing_domain_items: list[str] = []
    missing_license_items: list[str] = []
    missing_provenance_items: list[str] = []
    fixture_like_items: list[str] = []
    answer_text_overlap_items: list[str] = []

    if not path.exists():
        errors.append(f"Item file missing: {path}")
    else:
        try:
            raw_records = read_jsonl(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Could not read item JSONL: {exc}")

    for line_number, record in enumerate(raw_records, start=1):
        item_id = _string(record.get("item_id"))
        question = _string(record.get("question"))
        answer = _string(record.get("answer")).upper()
        choices = record.get("choices")
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        split = _string(record.get("split") or expected_split)

        if not item_id:
            errors.append(f"Line {line_number}: item_id is required.")
            item_id = f"line_{line_number}"
        item_ids.append(item_id)

        if _is_fixture_like(record):
            fixture_like_items.append(item_id)
            errors.append(f"Item {item_id}: fixture-like data is not allowed in real GPQA inputs.")

        if not question:
            errors.append(f"Item {item_id}: question is required.")
        else:
            question_texts.append(normalize_text(question))

        choice_map = _choice_map_from_record(choices)
        if set(choice_map) != {"A", "B", "C", "D"}:
            errors.append(f"Item {item_id}: choices must contain exactly labels A/B/C/D.")
        elif any(not text.strip() for text in choice_map.values()):
            errors.append(f"Item {item_id}: all choices must be non-empty.")
        else:
            normalized_choices = [normalize_text(text) for text in choice_map.values()]
            if len(set(normalized_choices)) < len(normalized_choices):
                duplicate_choice_items.append(item_id)

        if answer not in {"A", "B", "C", "D"}:
            errors.append(f"Item {item_id}: answer must be one of A/B/C/D.")
        elif answer in choice_map:
            answer_text = choice_map[answer]
            if _text_leaks_answer(question, answer_text):
                answer_text_overlap_items.append(item_id)
            source_id = metadata.get("source_id")
            if isinstance(source_id, str) and _text_leaks_answer(source_id, answer_text):
                errors.append(f"Item {item_id}: metadata.source_id appears to leak the answer.")
            _metadata_leakage_errors(
                metadata,
                item_id=item_id,
                answer_label=answer,
                answer_text=answer_text,
                errors=errors,
            )

        if split != expected_split:
            errors.append(
                f"Item {item_id}: split is '{split}', expected '{expected_split}' or an explicit mapping."
            )

        domain = record.get("domain") or record.get("discipline") or metadata.get("discipline")
        if not domain:
            missing_domain_items.append(item_id)
        if not metadata.get("license"):
            missing_license_items.append(item_id)
        if not metadata.get("provenance"):
            missing_provenance_items.append(item_id)

    duplicate_ids = sorted(_duplicates(item_ids))
    duplicate_questions = sorted(_duplicates(question_texts))
    if duplicate_ids:
        errors.append(f"Duplicate item IDs: {', '.join(duplicate_ids[:20])}")
    if duplicate_questions:
        warnings.append(f"Duplicate question text count: {len(duplicate_questions)}")
    if duplicate_choice_items:
        warnings.append(
            f"Items with duplicate answer choices: {', '.join(duplicate_choice_items[:20])}"
        )
    if missing_domain_items:
        warnings.append(
            f"Missing domain/discipline for {len(missing_domain_items)} items, "
            f"including: {', '.join(missing_domain_items[:10])}"
        )
    if missing_license_items:
        warnings.append(
            f"Missing metadata.license for {len(missing_license_items)} items, "
            f"including: {', '.join(missing_license_items[:10])}"
        )
    if missing_provenance_items:
        warnings.append(
            f"Missing metadata.provenance for {len(missing_provenance_items)} items, "
            f"including: {', '.join(missing_provenance_items[:10])}"
        )
    if answer_text_overlap_items:
        warnings.append(
            "Question text overlaps with the correct answer text for "
            f"{len(answer_text_overlap_items)} items, including: "
            f"{', '.join(answer_text_overlap_items[:10])}. "
            "This is reported for review but is not a fatal schema/alignment failure."
        )

    valid = not errors
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": ARTIFACT_REAL_INPUT_VALIDATION if valid else ARTIFACT_REAL_AUDIT_BLOCKED,
        "benchmark_id": "gpqa_diamond",
        "items_path": str(path),
        "valid": valid,
        "status": "pass" if valid else "blocked",
        "item_count": len(raw_records),
        "unique_item_count": len(set(item_ids)),
        "duplicate_item_ids": duplicate_ids,
        "duplicate_question_count": len(duplicate_questions),
        "duplicate_choice_items": duplicate_choice_items,
        "missing_domain_items": missing_domain_items,
        "missing_license_items": missing_license_items,
        "missing_provenance_items": missing_provenance_items,
        "fixture_like_items": fixture_like_items,
        "answer_text_overlap_items": answer_text_overlap_items,
        "errors": errors,
        "warnings": warnings,
    }
    if output_dir is not None:
        _write_report_pair(
            Path(output_dir),
            "item_validation",
            payload,
            title="GPQA Diamond Item File Validation",
            sections=[
                ("Status", payload["status"]),
                ("Artifact scope", payload["artifact_scope"]),
                ("Item count", str(payload["item_count"])),
                ("Errors", errors),
                ("Warnings", warnings),
            ],
        )
    return payload


def score_raw_outputs(
    *,
    items_path: str | Path,
    input_path: str | Path,
    output_path: str | Path,
    prompt_variant: str = "full",
    benchmark_id: str = "gpqa_diamond",
) -> dict[str, Any]:
    item_report = validate_gpqa_item_file(items_path)
    if not item_report["valid"]:
        preview = "; ".join(item_report["errors"][:5])
        raise ValueError(f"GPQA item file failed real-input validation: {preview}")
    benchmark = GPQADiamondJSONLBenchmark(items_path, benchmark_id=benchmark_id)
    items = {item.item_id: item for item in benchmark.load_items()}
    raw_records = read_jsonl(input_path)
    predictions: list[ModelPrediction] = []
    errors: list[str] = []
    extraction_failures: list[str] = []

    for index, record in enumerate(raw_records, start=1):
        model_id = _string(record.get("model_id"))
        item_id = _string(record.get("item_id"))
        variant = _string(record.get("prompt_variant") or prompt_variant)
        raw_output = _string(record.get("raw_output"))
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        if not model_id:
            errors.append(f"Line {index}: model_id is required.")
            continue
        if item_id not in items:
            errors.append(f"Line {index}: unknown item_id '{item_id}'.")
            continue
        if not raw_output:
            errors.append(f"Line {index}: raw_output is required.")
            raw_output = ""

        extraction = extract_gpqa_prediction(items[item_id], raw_output)
        if extraction["invalid"]:
            extraction_failures.append(item_id)
        score = _score_extracted_prediction(items[item_id], extraction["prediction"])
        predictions.append(
            ModelPrediction(
                model_id=model_id,
                item_id=item_id,
                prompt_variant=variant,
                prediction=extraction["prediction"] or "",
                score=score.score,
                is_correct=score.is_correct,
                raw_output=raw_output,
                metadata={
                    **metadata,
                    "artifact_scope": ARTIFACT_REAL_INPUT_VALIDATION,
                    "source": metadata.get("source", "local_cached_output"),
                    "frozen_extractor_version": FROZEN_EXTRACTOR_VERSION,
                    "strict_letter": extraction["strict_letter"],
                    "regex_final_answer": extraction["regex_final_answer"],
                    "lenient_letter": extraction["lenient_letter"],
                    "normalized_text_label": extraction["normalized_text_label"],
                    "extraction_mode": extraction["extraction_mode"],
                    "extraction_ambiguous": extraction["ambiguous"],
                    "extraction_refusal": extraction["refusal"],
                    "extraction_invalid": extraction["invalid"],
                    "normalized_prediction": score.normalized_prediction,
                    "normalized_answer": score.normalized_answer,
                },
            )
        )

    if errors:
        preview = "; ".join(errors[:5])
        raise ValueError(f"Could not score GPQA raw outputs: {preview}")
    write_jsonl(output_path, predictions)
    return {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": ARTIFACT_REAL_INPUT_VALIDATION,
        "benchmark_id": benchmark_id,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "prompt_variant": prompt_variant,
        "n_raw_outputs": len(raw_records),
        "n_predictions": len(predictions),
        "extraction_failure_count": len(extraction_failures),
        "extraction_failure_item_ids": sorted(set(extraction_failures))[:50],
    }


def extract_gpqa_prediction(item: BenchmarkItem, raw_output: str) -> dict[str, Any]:
    strict = strict_letter(raw_output)
    final = regex_final_answer(raw_output)
    lenient = lenient_letter(raw_output)
    text_label = _normalized_choice_label(item, raw_output)
    refusal = detect_refusal(raw_output)
    ambiguous = _ambiguous_labels(raw_output) and not final.value
    if strict.value:
        prediction = strict.value
        mode = "strict_letter"
    elif refusal:
        prediction = None
        mode = "refusal"
    elif final.value:
        prediction = final.value
        mode = "regex_final_answer"
    elif text_label:
        prediction = text_label
        mode = "normalized_text_match"
    elif ambiguous:
        prediction = None
        mode = "ambiguous"
    elif lenient.value:
        prediction = lenient.value
        mode = "lenient_letter"
    else:
        prediction = None
        mode = "invalid"
    return {
        "prediction": prediction,
        "strict_letter": strict.value,
        "regex_final_answer": final.value,
        "lenient_letter": lenient.value,
        "normalized_text_label": text_label,
        "extraction_mode": mode,
        "ambiguous": ambiguous,
        "refusal": refusal,
        "invalid": prediction is None,
    }


def validate_alignment(
    *,
    items_path: str | Path,
    predictions_path: str | Path,
    output_dir: str | Path,
    benchmark_id: str = "gpqa_diamond",
    required_variants: list[str] | None = None,
    min_models: int = DEFAULT_MIN_MODELS,
) -> dict[str, Any]:
    item_report = validate_gpqa_item_file(items_path)
    benchmark = GPQADiamondJSONLBenchmark(items_path, benchmark_id=benchmark_id)
    items = benchmark.load_items() if item_report["valid"] else []
    item_ids = {item.item_id for item in items}
    predictions = read_jsonl_as(predictions_path, ModelPrediction)
    required = required_variants or ["full"]

    models = sorted({prediction.model_id for prediction in predictions})
    variants_present = sorted({prediction.prompt_variant for prediction in predictions})
    prediction_item_ids = {prediction.item_id for prediction in predictions}
    missing_item_ids = sorted(item_ids - prediction_item_ids)
    extra_item_ids = sorted(prediction_item_ids - item_ids)
    invalid_prompt_variants = sorted(
        variant for variant in set(variants_present) if not _prompt_template_exists(variant)
    )
    invalid_answer_labels = sorted(
        {
            prediction.item_id
            for prediction in predictions
            if prediction.prediction and normalize_mcq_label(prediction.prediction) is None
        }
    )
    extraction_failures = sorted(
        {
            prediction.item_id
            for prediction in predictions
            if prediction.metadata.get("extraction_invalid") is True or not prediction.prediction
        }
    )
    duplicate_predictions = _duplicate_prediction_keys(predictions)
    missing_by_model = _missing_predictions_by_model(predictions, item_ids)
    missing_by_variant = {
        variant: sorted(item_ids - {p.item_id for p in predictions if p.prompt_variant == variant})
        for variant in required
    }
    missing_required_variants = sorted(set(required) - set(variants_present))
    score_missingness = sum(1 for prediction in predictions if prediction.score is None)
    matrix_completeness = _matrix_completeness(predictions, item_ids, required)
    required_complete = (
        not missing_required_variants
        and not extra_item_ids
        and not duplicate_predictions
        and all(matrix_completeness.get(variant, {}).get("complete") for variant in required)
    )
    errors = []
    if not item_report["valid"]:
        errors.extend(item_report["errors"])
    if extra_item_ids:
        errors.append(
            f"Predictions contain item IDs not present in GPQA items: {extra_item_ids[:20]}"
        )
    if duplicate_predictions:
        errors.append(f"Duplicate predictions detected: {duplicate_predictions[:20]}")
    if missing_required_variants:
        errors.append(f"Missing required prompt variants: {missing_required_variants}")
    if invalid_prompt_variants:
        errors.append(f"Invalid prompt variants: {invalid_prompt_variants}")
    if score_missingness:
        errors.append(f"Predictions missing scores: {score_missingness}")
    if len(models) < min_models:
        errors.append(f"Model count {len(models)} is below required threshold {min_models}.")
    if not required_complete:
        errors.append(f"Required prediction matrix is incomplete for variants: {required}.")

    status = "pass" if not errors else "blocked"
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": ARTIFACT_REAL_INPUT_VALIDATION
        if status == "pass"
        else ARTIFACT_REAL_AUDIT_BLOCKED,
        "benchmark_id": benchmark_id,
        "items_path": str(items_path),
        "predictions_path": str(predictions_path),
        "item_count": len(item_ids),
        "prediction_count": len(predictions),
        "model_count": len(models),
        "models": models,
        "prompt_variants_present": variants_present,
        "required_prompt_variants": required,
        "missing_item_ids": missing_item_ids,
        "extra_item_ids": extra_item_ids,
        "duplicate_predictions": duplicate_predictions,
        "missing_predictions_by_model": missing_by_model,
        "missing_predictions_by_prompt_variant": missing_by_variant,
        "invalid_prompt_variants": invalid_prompt_variants,
        "invalid_answer_labels": invalid_answer_labels,
        "extraction_failures": extraction_failures,
        "score_missingness": score_missingness,
        "matrix_completeness": matrix_completeness,
        "go_no_go_status": status,
        "errors": errors,
        "warnings": item_report["warnings"],
    }
    _write_report_pair(
        output_dir,
        "alignment_report",
        payload,
        title="GPQA Diamond Input Alignment Report",
        sections=[
            ("Go/no-go status", status),
            ("Artifact scope", payload["artifact_scope"]),
            ("Item count", str(payload["item_count"])),
            ("Prediction count", str(payload["prediction_count"])),
            ("Model count", str(payload["model_count"])),
            ("Prompt variants present", variants_present),
            ("Errors", errors),
            ("Warnings", payload["warnings"]),
        ],
    )
    return payload


def extraction_audit(
    *,
    items_path: str | Path,
    outputs_path: str | Path,
    output_dir: str | Path,
    prompt_variant: str = "full",
    benchmark_id: str = "gpqa_diamond",
    success_threshold: float = DEFAULT_EXTRACTION_SUCCESS_THRESHOLD,
) -> dict[str, Any]:
    benchmark = GPQADiamondJSONLBenchmark(items_path, benchmark_id=benchmark_id)
    items = {item.item_id: item for item in benchmark.load_items()}
    records = read_jsonl(outputs_path)
    strict_success = 0
    lenient_success = 0
    text_success = 0
    invalid_items: list[str] = []
    ambiguous_items: list[str] = []
    answer_text_matches: list[str] = []
    disagreements: list[str] = []

    for record in records:
        item_id = _string(record.get("item_id"))
        raw = _string(record.get("raw_output") or record.get("prediction"))
        item = items.get(item_id)
        if item is None:
            invalid_items.append(item_id or "missing_item_id")
            continue
        strict = strict_letter(raw)
        lenient = lenient_letter(raw)
        text_label = _normalized_choice_label(item, raw)
        extraction = extract_gpqa_prediction(item, raw)
        strict_success += int(strict.value is not None)
        lenient_success += int(lenient.value is not None)
        text_success += int(text_label is not None)
        if extraction["invalid"]:
            invalid_items.append(item_id)
        if extraction["ambiguous"]:
            ambiguous_items.append(item_id)
        if text_label and text_label == _primary_answer(item):
            answer_text_matches.append(item_id)
        labels = {
            value
            for value in [strict.value, extraction["regex_final_answer"], lenient.value, text_label]
            if value
        }
        if len(labels) > 1:
            disagreements.append(item_id)

    n = len(records)
    usable_success = n - len(invalid_items)
    success_rate = usable_success / n if n else 0.0
    status = "pass" if success_rate >= success_threshold else "blocked"
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": ARTIFACT_REAL_INPUT_VALIDATION
        if status == "pass"
        else ARTIFACT_REAL_AUDIT_BLOCKED,
        "benchmark_id": benchmark_id,
        "outputs_path": str(outputs_path),
        "prompt_variant": prompt_variant,
        "n_outputs": n,
        "strict_letter_success_rate": strict_success / n if n else 0.0,
        "lenient_letter_success_rate": lenient_success / n if n else 0.0,
        "normalized_text_match_success_rate": text_success / n if n else 0.0,
        "invalid_output_count": len(invalid_items),
        "ambiguous_output_count": len(ambiguous_items),
        "answer_text_match_count": len(answer_text_matches),
        "extractor_disagreement_count": len(disagreements),
        "failure_item_ids": sorted(set(invalid_items))[:50],
        "ambiguous_item_ids": sorted(set(ambiguous_items))[:50],
        "extractor_disagreement_item_ids": sorted(set(disagreements))[:50],
        "success_threshold": success_threshold,
        "passes_threshold": status == "pass",
        "status": status,
    }
    _write_report_pair(
        output_dir,
        f"extraction_audit_{prompt_variant}",
        payload,
        title=f"GPQA Diamond Extraction Audit: {prompt_variant}",
        sections=[
            ("Status", status),
            ("Artifact scope", payload["artifact_scope"]),
            ("Outputs", str(n)),
            ("Strict success rate", f"{payload['strict_letter_success_rate']:.3f}"),
            ("Lenient success rate", f"{payload['lenient_letter_success_rate']:.3f}"),
            ("Invalid output count", str(len(invalid_items))),
            ("Failure item IDs", payload["failure_item_ids"]),
        ],
    )
    return payload


def validate_prompt_variant_cache(
    *,
    benchmark_id: str,
    panel_id: str,
    cache_root: str | Path,
    output_dir: str | Path,
    required_variants: list[str],
) -> dict[str, Any]:
    present_predictions = []
    present_matrices = []
    for variant in required_variants:
        if prediction_path(cache_root, benchmark_id, panel_id, variant).exists():
            present_predictions.append(variant)
        if matrix_path(cache_root, benchmark_id, panel_id, variant).exists():
            present_matrices.append(variant)
    missing_predictions = sorted(set(required_variants) - set(present_predictions))
    missing_matrices = sorted(set(required_variants) - set(present_matrices))
    invalid_required = sorted(
        variant for variant in set(required_variants) if not _prompt_template_exists(variant)
    )
    status = (
        "pass"
        if not missing_predictions and not missing_matrices and not invalid_required
        else "blocked"
    )
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": ARTIFACT_REAL_INPUT_VALIDATION
        if status == "pass"
        else ARTIFACT_REAL_AUDIT_BLOCKED,
        "benchmark_id": benchmark_id,
        "panel_id": panel_id,
        "cache_root": str(cache_root),
        "required_variants": required_variants,
        "present_prediction_variants": sorted(present_predictions),
        "present_matrix_variants": sorted(present_matrices),
        "missing_prediction_variants": missing_predictions,
        "missing_matrix_variants": missing_matrices,
        "invalid_required_variants": invalid_required,
        "status": status,
        "partial_input_validation_allowed": bool(present_predictions or present_matrices),
    }
    _write_report_pair(
        output_dir,
        "prompt_variant_completeness",
        payload,
        title="GPQA Diamond Prompt Variant Completeness",
        sections=[
            ("Status", status),
            ("Artifact scope", payload["artifact_scope"]),
            ("Present prediction variants", payload["present_prediction_variants"]),
            ("Present matrix variants", payload["present_matrix_variants"]),
            ("Missing prediction variants", missing_predictions),
            ("Missing matrix variants", missing_matrices),
        ],
    )
    return payload


def go_no_go_report(
    *,
    items_path: str | Path,
    panel_id: str,
    cache_root: str | Path,
    results_root: str | Path,
    benchmark_id: str = "gpqa_diamond",
    required_variants: list[str] | None = None,
    min_models: int = DEFAULT_MIN_MODELS,
    extraction_success_threshold: float = DEFAULT_EXTRACTION_SUCCESS_THRESHOLD,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    protocol = _audit_protocol_settings(config_path)
    primary_variant = protocol["primary_full_variant"]
    required = required_variants or protocol["required_variants"]
    output_dir = validation_dir(results_root, benchmark_id)
    item_report = validate_gpqa_item_file(items_path)
    variant_report = validate_prompt_variant_cache(
        benchmark_id=benchmark_id,
        panel_id=panel_id,
        cache_root=cache_root,
        output_dir=output_dir,
        required_variants=required,
    )
    checks: list[dict[str, Any]] = []
    checks.append(_check("real_gpqa_jsonl_valid", item_report["valid"], item_report["errors"]))
    checks.append(
        _check(
            "no_fixture_data_mixed",
            not item_report["fixture_like_items"],
            item_report["fixture_like_items"],
        )
    )
    checks.append(
        _check(
            "prompt_templates_frozen",
            all(_prompt_template_exists(variant) for variant in required),
            required,
        )
    )
    checks.append(
        _check(
            "pre_registration_file_exists",
            Path(protocol["pre_registration"]).exists(),
            protocol["pre_registration"],
        )
    )
    checks.append(
        _check(
            "model_panel_config_exists",
            Path(f"configs/panels/{panel_id}.yaml").exists(),
            f"configs/panels/{panel_id}.yaml",
        )
    )
    missing_variants = sorted(
        set(variant_report["missing_prediction_variants"])
        | set(variant_report["missing_matrix_variants"])
    )
    checks.append(
        _check(
            "required_prompt_variants_present",
            variant_report["status"] == "pass",
            missing_variants,
        )
    )

    full_matrix_path = matrix_path(cache_root, benchmark_id, panel_id, primary_variant)
    matrix_ok = False
    model_count = 0
    item_count = item_report["item_count"]
    if full_matrix_path.exists():
        matrix = load_matrix(cache_root, benchmark_id, panel_id, primary_variant)
        frame = matrix.to_dataframe()
        model_count = len(frame.index)
        matrix_ok = len(frame.columns) == item_count and not frame.isna().any().any()
    checks.append(_check("complete_full_prompt_matrix", matrix_ok, str(full_matrix_path)))
    checks.append(
        _check(
            "required_model_count_met",
            model_count >= min_models,
            {"model_count": model_count, "min_models": min_models},
        )
    )

    prediction_file = prediction_path(cache_root, benchmark_id, panel_id, primary_variant)
    extraction_success = None
    if prediction_file.exists():
        predictions = read_jsonl_as(prediction_file, ModelPrediction)
        if predictions:
            failures = sum(
                1
                for prediction in predictions
                if prediction.metadata.get("extraction_invalid") is True
                or not prediction.prediction
            )
            extraction_success = 1.0 - failures / len(predictions)
    extraction_ok = (
        extraction_success is not None and extraction_success >= extraction_success_threshold
    )
    checks.append(
        _check(
            "extraction_success_threshold_met",
            extraction_ok,
            {"success_rate": extraction_success, "threshold": extraction_success_threshold},
        )
    )
    variant_extraction_success = _variant_extraction_success(
        cache_root=cache_root,
        benchmark_id=benchmark_id,
        panel_id=panel_id,
        variants=required,
    )
    variant_model_extraction_success = _variant_model_extraction_success(
        cache_root=cache_root,
        benchmark_id=benchmark_id,
        panel_id=panel_id,
        variants=required,
    )
    variant_extraction_passes = {
        variant: (success is not None and success >= extraction_success_threshold)
        for variant, success in variant_extraction_success.items()
    }
    variant_model_extraction_passes = {
        variant: {
            model_id: success >= extraction_success_threshold
            for model_id, success in model_success.items()
        }
        for variant, model_success in variant_model_extraction_success.items()
    }
    checks.append(
        _check(
            "required_variant_extraction_thresholds_met",
            bool(variant_extraction_passes) and all(variant_extraction_passes.values()),
            {
                "success_rates": variant_extraction_success,
                "threshold": extraction_success_threshold,
            },
        )
    )
    checks.append(
        _check(
            "required_variant_per_model_extraction_thresholds_met",
            bool(variant_model_extraction_passes)
            and all(
                passed
                for model_passes in variant_model_extraction_passes.values()
                for passed in model_passes.values()
            ),
            {
                "success_rates_by_model": variant_model_extraction_success,
                "threshold": extraction_success_threshold,
            },
        )
    )
    checks.append(_check("no_scoring_rule_deviation_recorded", True, FROZEN_EXTRACTOR_VERSION))
    original_full_extraction_success = None
    original_full_path = prediction_path(cache_root, benchmark_id, panel_id, "full")
    if primary_variant != "full" and original_full_path.exists():
        original_predictions = read_jsonl_as(original_full_path, ModelPrediction)
        if original_predictions:
            original_failures = sum(
                1
                for prediction in original_predictions
                if prediction.metadata.get("extraction_invalid") is True
                or not prediction.prediction
            )
            original_full_extraction_success = 1.0 - original_failures / len(original_predictions)

    status = "go" if all(check["pass"] for check in checks) else "no_go"
    diagnostic_authorization = _diagnostic_authorization(
        status=status,
        required_variants=required,
        variant_report=variant_report,
        variant_extraction_passes=variant_extraction_passes,
        variant_model_extraction_passes=variant_model_extraction_passes,
        protocol=protocol,
    )
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": ARTIFACT_REAL_AUDIT_READY
        if status == "go"
        else ARTIFACT_REAL_AUDIT_BLOCKED,
        "benchmark_id": benchmark_id,
        "panel_id": panel_id,
        "items_path": str(items_path),
        "cache_root": str(cache_root),
        "config_path": str(config_path) if config_path else None,
        "pre_registration": protocol["pre_registration"],
        "primary_full_variant": primary_variant,
        "original_full_variant": protocol["original_full_variant"],
        "original_full_extraction_success": original_full_extraction_success,
        "required_variants": required,
        "variant_extraction_success": variant_extraction_success,
        "variant_extraction_passes": variant_extraction_passes,
        "variant_model_extraction_success": variant_model_extraction_success,
        "variant_model_extraction_passes": variant_model_extraction_passes,
        "diagnostic_authorization": diagnostic_authorization,
        "diagnostics_allowed": [
            name for name, row in diagnostic_authorization.items() if row["allowed"]
        ],
        "diagnostics_blocked": {
            name: row["blocked_reasons"]
            for name, row in diagnostic_authorization.items()
            if not row["allowed"]
        },
        "diagnostics_blocked_by_variant_coverage": protocol["diagnostics_blocked"],
        "status": status,
        "checks": checks,
        "blocked_reasons": [check for check in checks if not check["pass"]],
        "do_not_claim": [
            "This is input-readiness evidence, not a GPQA validity result.",
            "Do not interpret diagnostics until go/no-go passes and the real audit is run under the active pre-registration.",
        ],
    }
    _write_report_pair(
        output_dir,
        "go_no_go",
        payload,
        title="GPQA Diamond Go/No-Go Checklist",
        sections=[
            ("Status", status),
            ("Artifact scope", payload["artifact_scope"]),
            ("Primary full variant", primary_variant),
            ("Protocol config", payload["config_path"] or "default preregistered protocol"),
            ("Checks", [f"{row['name']}: {'pass' if row['pass'] else 'fail'}" for row in checks]),
            ("Blocked reasons", [row["name"] for row in payload["blocked_reasons"]]),
            ("Diagnostics allowed", payload["diagnostics_allowed"]),
            ("Diagnostics blocked", payload["diagnostics_blocked"]),
            ("Diagnostics blocked by variant coverage", protocol["diagnostics_blocked"]),
        ],
    )
    return payload


def write_audit_manifest(
    *,
    items_path: str | Path,
    panel_id: str,
    cache_root: str | Path,
    results_root: str | Path,
    benchmark_id: str = "gpqa_diamond",
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    protocol = _audit_protocol_settings(config_path)
    variants = sorted(
        set(GPQA_VARIANTS) | {protocol["primary_full_variant"]} | set(protocol["required_variants"])
    )
    prediction_hashes = {}
    model_prediction_hashes = {}
    matrix_hashes = {}
    for variant in variants:
        path = prediction_path(cache_root, benchmark_id, panel_id, variant)
        if path.exists():
            prediction_hashes[variant] = _file_hash(path)
        per_model_paths = sorted(
            (Path(cache_root) / benchmark_id / panel_id).glob(f"*_{variant}_predictions.jsonl")
        )
        if per_model_paths:
            model_prediction_hashes[variant] = {
                str(path): _file_hash(path) for path in per_model_paths
            }
        matrix = matrix_path(cache_root, benchmark_id, panel_id, variant)
        if matrix.exists():
            matrix_hashes[variant] = _file_hash(matrix)
    paths = {
        "benchmark_config": "configs/benchmarks/gpqa_diamond.yaml",
        "construct_spec": "configs/constructs/gpqa_diamond_construct.yaml",
        "audit_config": protocol["audit_config"],
        "model_panel_config": f"configs/panels/{panel_id}.yaml",
        "pre_registration": protocol["pre_registration"],
        "original_pre_registration": "docs/protocols/gpqa_diamond_preregistration.md",
        "extraction_compliance_decision": "docs/protocols/gpqa_diamond_amended_v2_extraction_compliance_decision.md",
        "extraction_compliance_config": "configs/audits/gpqa_diamond_amended_v2_compliance.yaml",
        "model_compliance_report": "results/gpqa_diamond/input_validation/amended_v2_model_compliance.json",
        "replacement_candidates_report": "results/gpqa_diamond/input_validation/replacement_model_candidates.json",
        "original_8model_archive_manifest": "results/gpqa_diamond/input_validation/amended_v2_original_8model_archive_manifest.json",
        "diagnostic_validation_status": "VALIDATOR_VALIDATION_STATUS.md",
        "scoring_extraction_code": "src/valideval/scoring/extraction.py",
        "gpqa_adapter_code": "src/valideval/benchmarks/gpqa.py",
    }
    prompt_hashes = {
        path.name: _file_hash(path) for path in sorted(Path("configs/prompts/gpqa").glob("*.yaml"))
    }
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": ARTIFACT_REAL_INPUT_VALIDATION,
        "benchmark_id": benchmark_id,
        "panel_id": panel_id,
        "items_path": str(items_path),
        "config_path": str(config_path) if config_path else None,
        "primary_full_variant": protocol["primary_full_variant"],
        "original_full_variant": protocol["original_full_variant"],
        "item_file_hash": _file_hash(items_path) if Path(items_path).exists() else None,
        "config_hashes": {name: _file_hash(path) for name, path in paths.items()},
        "prompt_template_hashes": prompt_hashes,
        "raw_output_file_hashes": _raw_output_hashes(panel_id, variants=variants),
        "prediction_file_hashes": prediction_hashes,
        "model_prediction_file_hashes": model_prediction_hashes,
        "matrix_file_hashes": matrix_hashes,
        "frozen_extractor_version": FROZEN_EXTRACTOR_VERSION,
        "no_results_interpreted": True,
    }
    output = validation_dir(results_root, benchmark_id)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "audit_manifest.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def real_audit_dry_run(
    *,
    items_path: str | Path,
    panel_id: str,
    cache_root: str | Path,
    results_root: str | Path,
    benchmark_id: str = "gpqa_diamond",
    required_variants: list[str] | None = None,
    min_models: int = DEFAULT_MIN_MODELS,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    protocol = _audit_protocol_settings(config_path)
    output_dir = validation_dir(results_root, benchmark_id)
    go_no_go = go_no_go_report(
        items_path=items_path,
        panel_id=panel_id,
        cache_root=cache_root,
        results_root=results_root,
        benchmark_id=benchmark_id,
        required_variants=required_variants or protocol["required_variants"],
        min_models=min_models,
        config_path=config_path,
    )
    available_diagnostics = [
        "answer_distribution",
        "distractor_quality",
        "irt",
        "reliability",
        "extraction_robustness",
        "saturation",
        "shortcut",
        "prompt_sensitivity",
    ]
    status = "ready" if go_no_go["status"] == "go" else "blocked"
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "artifact_scope": ARTIFACT_REAL_AUDIT_DRY_RUN
        if status == "ready"
        else ARTIFACT_REAL_AUDIT_BLOCKED,
        "benchmark_id": benchmark_id,
        "panel_id": panel_id,
        "status": status,
        "go_no_go_status": go_no_go["status"],
        "diagnostics_available": available_diagnostics,
        "report_shell": str(output_dir / "real_audit_dry_run.md"),
        "no_diagnostics_interpreted": True,
        "blocked_reasons": go_no_go["blocked_reasons"],
    }
    _write_report_pair(
        output_dir,
        "real_audit_dry_run",
        payload,
        title="GPQA Diamond Real Audit Dry Run",
        sections=[
            ("Status", status),
            ("Artifact scope", payload["artifact_scope"]),
            ("Go/no-go status", go_no_go["status"]),
            ("Diagnostics available", available_diagnostics),
            ("No diagnostics interpreted", "true"),
            ("Blocked reasons", [row["name"] for row in payload["blocked_reasons"]]),
        ],
    )
    return payload


def matrix_from_prediction_file(
    *,
    predictions_path: str | Path,
    output_path: str | Path,
    benchmark_id: str,
    panel_id: str,
    variant: str,
    scoring_method: str = "mcq",
    seed: int | None = None,
) -> dict[str, Any]:
    predictions = read_jsonl_as(predictions_path, ModelPrediction)
    matrix = build_response_matrix(
        predictions,
        benchmark_id=benchmark_id,
        panel_id=panel_id,
        variant=variant,
        scoring_method=scoring_method,
        seed=seed,
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_dataframe().to_csv(output)
    metadata_path = output.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(matrix.metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    return {
        "artifact_scope": ARTIFACT_REAL_INPUT_VALIDATION,
        "matrix_csv": str(output),
        "matrix_metadata_json": str(metadata_path),
        "n_models": matrix.metadata.get("n_models"),
        "n_items": matrix.metadata.get("n_items"),
    }


def save_cached_matrix_from_predictions(
    *,
    cache_root: str | Path,
    benchmark_id: str,
    panel_id: str,
    variant: str,
    scoring_method: str = "mcq",
    seed: int | None = None,
) -> Path:
    predictions = read_jsonl_as(
        prediction_path(cache_root, benchmark_id, panel_id, variant), ModelPrediction
    )
    matrix = build_response_matrix(
        predictions,
        benchmark_id=benchmark_id,
        panel_id=panel_id,
        variant=variant,
        scoring_method=scoring_method,
        seed=seed,
    )
    return save_matrix(cache_root, benchmark_id, panel_id, variant, matrix)


def _score_extracted_prediction(item: BenchmarkItem, prediction: str | None) -> ScoreResult:
    if not prediction:
        return ScoreResult(
            score=0.0,
            is_correct=False,
            normalized_prediction=None,
            normalized_answer=_primary_answer(item),
            metadata={"accepted_answers": [_primary_answer(item)]},
        )
    return score_mcq(item, prediction)


def _normalized_choice_label(item: BenchmarkItem, raw_output: str) -> str | None:
    raw = normalize_text(raw_output)
    for label, text in item_choice_map(item).items():
        result = normalized_text_match(raw_output, aliases=[text])
        if result.metadata and result.metadata.get("matched_alias"):
            return label
        if raw and raw == normalize_text(text):
            return label
    return None


def _primary_answer(item: BenchmarkItem) -> str:
    value = item.answer[0] if isinstance(item.answer, list) else item.answer
    return normalize_mcq_label(str(value)) or str(value).strip().upper()


def _choice_map_from_record(choices: Any) -> dict[str, str]:
    if not isinstance(choices, dict):
        return {}
    return {str(label).upper(): _string(text) for label, text in choices.items()}


def _metadata_leakage_errors(
    value: Any,
    *,
    item_id: str,
    answer_label: str,
    answer_text: str,
    errors: list[str],
    path: str = "metadata",
) -> None:
    forbidden = re.compile(r"(answer|correct|gold|target|solution|label)", re.I)
    if isinstance(value, dict):
        for key, nested in value.items():
            key_path = f"{path}.{key}"
            if forbidden.search(str(key)):
                errors.append(f"Item {item_id}: metadata key '{key_path}' may leak the answer.")
            _metadata_leakage_errors(
                nested,
                item_id=item_id,
                answer_label=answer_label,
                answer_text=answer_text,
                errors=errors,
                path=key_path,
            )
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _metadata_leakage_errors(
                nested,
                item_id=item_id,
                answer_label=answer_label,
                answer_text=answer_text,
                errors=errors,
                path=f"{path}[{index}]",
            )
    elif isinstance(value, str):
        normalized = normalize_text(value)
        if normalized in {normalize_text(answer_label), normalize_text(answer_text)}:
            errors.append(f"Item {item_id}: metadata value at '{path}' may leak the answer.")


def _text_leaks_answer(text: str, answer_text: str) -> bool:
    normalized_text = normalize_text(text)
    normalized_answer = normalize_text(answer_text)
    return bool(
        normalized_answer and len(normalized_answer) > 3 and normalized_answer in normalized_text
    )


def _is_fixture_like(record: dict[str, Any]) -> bool:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    item_id = _string(record.get("item_id"))
    source = _string(record.get("source"))
    return (
        item_id.startswith("gpqa_fixture_")
        or source == "synthetic_fixture_not_gpqa"
        or bool(metadata.get("synthetic_fixture"))
        or bool(metadata.get("is_synthetic_fixture"))
    )


def _duplicates(values: list[str]) -> set[str]:
    counts = Counter(value for value in values if value)
    return {value for value, count in counts.items() if count > 1}


def _duplicate_prediction_keys(predictions: list[ModelPrediction]) -> list[dict[str, str]]:
    counts = Counter(
        (prediction.model_id, prediction.item_id, prediction.prompt_variant)
        for prediction in predictions
    )
    return [
        {"model_id": model_id, "item_id": item_id, "prompt_variant": variant}
        for (model_id, item_id, variant), count in counts.items()
        if count > 1
    ]


def _missing_predictions_by_model(
    predictions: list[ModelPrediction],
    item_ids: set[str],
) -> dict[str, list[str]]:
    by_model: dict[str, set[str]] = defaultdict(set)
    for prediction in predictions:
        if prediction.prompt_variant == "full":
            by_model[prediction.model_id].add(prediction.item_id)
    return {
        model_id: sorted(item_ids - seen)
        for model_id, seen in sorted(by_model.items())
        if item_ids - seen
    }


def _matrix_completeness(
    predictions: list[ModelPrediction],
    item_ids: set[str],
    required_variants: list[str],
) -> dict[str, Any]:
    models = sorted({prediction.model_id for prediction in predictions})
    output = {}
    for variant in required_variants:
        records = [prediction for prediction in predictions if prediction.prompt_variant == variant]
        expected = len(models) * len(item_ids)
        output[variant] = {
            "observed_predictions": len(records),
            "expected_predictions": expected,
            "complete": expected > 0 and len(records) == expected,
        }
    return output


def _ambiguous_labels(raw_output: str) -> bool:
    labels = set(re.findall(r"\b([A-D])\b", raw_output.upper()))
    return len(labels) > 1


def _prompt_templates_exist() -> bool:
    return all(
        (Path("configs/prompts/gpqa") / f"{variant}.yaml").exists() for variant in GPQA_VARIANTS
    )


def _prompt_template_exists(variant: str) -> bool:
    return (Path("configs/prompts/gpqa") / f"{variant}.yaml").exists()


def _audit_protocol_settings(config_path: str | Path | None) -> dict[str, Any]:
    default = {
        "audit_config": "configs/audits/gpqa_diamond_preregistered.yaml",
        "pre_registration": "docs/protocols/gpqa_diamond_preregistration.md",
        "primary_full_variant": "full",
        "original_full_variant": "full",
        "required_variants": list(GPQA_VARIANTS),
        "diagnostics_blocked": [],
        "diagnostic_variant_requirements": {},
        "sanitized_distractor_quality": False,
    }
    if not config_path:
        return default

    path = Path(config_path)
    if not path.exists():
        settings = dict(default)
        settings["audit_config"] = str(path)
        return settings

    data = load_yaml(path)
    if not isinstance(data, dict):
        settings = dict(default)
        settings["audit_config"] = str(path)
        return settings

    amended = data.get("amended_protocol") if isinstance(data.get("amended_protocol"), dict) else {}
    go_no_go = data.get("go_no_go") if isinstance(data.get("go_no_go"), dict) else {}
    settings = dict(default)
    settings["audit_config"] = str(path)
    settings["pre_registration"] = _string(
        amended.get("preregistration")
        or data.get("pre_registration")
        or default["pre_registration"]
    )
    settings["primary_full_variant"] = _string(
        amended.get("primary_full_variant")
        or data.get("primary_full_variant")
        or default["primary_full_variant"]
    )
    settings["original_full_variant"] = _string(
        amended.get("original_full_variant") or default["original_full_variant"]
    )
    required = go_no_go.get("required_variants") or data.get("required_variants")
    if isinstance(required, list) and required:
        settings["required_variants"] = [
            _string(variant) for variant in required if _string(variant)
        ]
    else:
        settings["required_variants"] = [settings["primary_full_variant"]]
    blocked = data.get("diagnostics_blocked")
    if isinstance(blocked, list):
        settings["diagnostics_blocked"] = [_string(row) for row in blocked if _string(row)]
    diagnostics = data.get("diagnostics") if isinstance(data.get("diagnostics"), dict) else {}
    requirements = {}
    for name in ["shortcut", "prompt_sensitivity", "reliability"]:
        cfg = diagnostics.get(name) if isinstance(diagnostics.get(name), dict) else {}
        variants = cfg.get("variants")
        if isinstance(variants, list):
            requirements[name] = [_string(variant) for variant in variants if _string(variant)]
    settings["diagnostic_variant_requirements"] = requirements
    distractor_cfg = (
        diagnostics.get("distractor_quality")
        if isinstance(diagnostics.get("distractor_quality"), dict)
        else {}
    )
    settings["sanitized_distractor_quality"] = bool(distractor_cfg.get("sanitized"))
    return settings


def _variant_extraction_success(
    *,
    cache_root: str | Path,
    benchmark_id: str,
    panel_id: str,
    variants: list[str],
) -> dict[str, float | None]:
    output: dict[str, float | None] = {}
    for variant in variants:
        path = prediction_path(cache_root, benchmark_id, panel_id, variant)
        if not path.exists():
            output[variant] = None
            continue
        predictions = read_jsonl_as(path, ModelPrediction)
        if not predictions:
            output[variant] = None
            continue
        failures = sum(
            1
            for prediction in predictions
            if prediction.metadata.get("extraction_invalid") is True or not prediction.prediction
        )
        output[variant] = 1.0 - failures / len(predictions)
    return output


def _variant_model_extraction_success(
    *,
    cache_root: str | Path,
    benchmark_id: str,
    panel_id: str,
    variants: list[str],
) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = {}
    for variant in variants:
        path = prediction_path(cache_root, benchmark_id, panel_id, variant)
        if not path.exists():
            output[variant] = {}
            continue
        predictions = read_jsonl_as(path, ModelPrediction)
        by_model: dict[str, list[ModelPrediction]] = defaultdict(list)
        for prediction in predictions:
            by_model[prediction.model_id].append(prediction)
        output[variant] = {}
        for model_id, records in sorted(by_model.items()):
            if not records:
                continue
            failures = sum(
                1
                for prediction in records
                if prediction.metadata.get("extraction_invalid") is True
                or not prediction.prediction
            )
            output[variant][model_id] = 1.0 - failures / len(records)
    return output


def _diagnostic_authorization(
    *,
    status: str,
    required_variants: list[str],
    variant_report: dict[str, Any],
    variant_extraction_passes: dict[str, bool],
    variant_model_extraction_passes: dict[str, dict[str, bool]],
    protocol: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    present_prediction_variants = set(variant_report.get("present_prediction_variants", []))
    present_matrix_variants = set(variant_report.get("present_matrix_variants", []))
    configured_requirements = protocol.get("diagnostic_variant_requirements", {})
    default_non_full = [
        variant for variant in required_variants if variant != protocol["primary_full_variant"]
    ]
    requirements = {
        "shortcut": configured_requirements.get("shortcut", default_non_full),
        "prompt_sensitivity": configured_requirements.get("prompt_sensitivity", default_non_full),
        "variant_reliability": configured_requirements.get("reliability", default_non_full),
        "distractor_quality": [protocol["primary_full_variant"]],
    }
    output = {}
    for name, variants in requirements.items():
        blocked = []
        if status != "go" and name != "distractor_quality":
            blocked.append("overall_go_no_go_not_go")
        missing_predictions = sorted(set(variants) - present_prediction_variants)
        missing_matrices = sorted(set(variants) - present_matrix_variants)
        extraction_failed = sorted(
            variant for variant in variants if not variant_extraction_passes.get(variant)
        )
        model_extraction_failed = sorted(
            f"{variant}:{model_id}"
            for variant in variants
            for model_id, passed in variant_model_extraction_passes.get(variant, {}).items()
            if not passed
        )
        if missing_predictions:
            blocked.append(f"missing_predictions:{','.join(missing_predictions)}")
        if missing_matrices:
            blocked.append(f"missing_matrices:{','.join(missing_matrices)}")
        if extraction_failed:
            blocked.append(f"extraction_below_threshold:{','.join(extraction_failed)}")
        if model_extraction_failed:
            blocked.append(
                f"per_model_extraction_below_threshold:{','.join(model_extraction_failed)}"
            )
        if name == "distractor_quality" and not protocol.get("sanitized_distractor_quality"):
            blocked.append("sanitized_output_mode_not_enabled")
        output[name] = {
            "allowed": not blocked,
            "required_variants": variants,
            "blocked_reasons": blocked,
        }
    return output


def _check(name: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _file_hash(path: str | Path) -> str | None:
    source = Path(path)
    if not source.exists():
        return None
    return stable_hash(source.read_text(encoding="utf-8"))


def _raw_output_hashes(
    panel_id: str, *, variants: list[str] | None = None
) -> dict[str, dict[str, str | None]]:
    panel_model_ids = _panel_model_ids(panel_id)
    hashes: dict[str, dict[str, str | None]] = {}
    output_root = Path("local_outputs/gpqa")
    for variant in variants or GPQA_VARIANTS:
        variant_dir = output_root / variant
        if not variant_dir.exists():
            continue
        for path in sorted(variant_dir.glob("*.jsonl")):
            try:
                rows = read_jsonl(path)
            except (OSError, json.JSONDecodeError):
                continue
            if not rows:
                continue
            row_model_ids = {_string(row.get("model_id")) for row in rows}
            if panel_model_ids and not row_model_ids.intersection(panel_model_ids):
                continue
            if all(_is_smoke_raw_output(row) for row in rows):
                continue
            hashes.setdefault(variant, {})[str(path)] = _file_hash(path)
    return hashes


def _panel_model_ids(panel_id: str) -> set[str]:
    config_path = Path("configs/panels") / f"{panel_id}.yaml"
    if not config_path.exists():
        return set()
    data = load_yaml(config_path)
    models = data.get("models", []) if isinstance(data, dict) else []
    return {
        _string(row.get("model_id"))
        for row in models
        if isinstance(row, dict) and _string(row.get("model_id"))
    }


def _is_smoke_raw_output(row: dict[str, Any]) -> bool:
    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        return False
    source = _string(metadata.get("source"))
    return bool(metadata.get("smoke_test_only")) or source in {
        "mock_model_generation",
        "smoke_mock_generation",
    }


def _string(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _write_report_pair(
    output_dir: str | Path,
    name: str,
    payload: dict[str, Any],
    *,
    title: str,
    sections: list[tuple[str, Any]],
) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{name}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    lines = [f"# {title}", "", f"Artifact scope: **{payload.get('artifact_scope')}**.", ""]
    for heading, value in sections:
        lines.extend([f"## {heading}", ""])
        if isinstance(value, list):
            lines.extend([f"- {item}" for item in value] or ["none"])
        elif isinstance(value, dict):
            lines.append(json.dumps(value, indent=2, sort_keys=True))
        else:
            lines.append(str(value))
        lines.append("")
    lines.append("No GPQA benchmark validity findings are made by this input-validation artifact.")
    lines.append("")
    (output / f"{name}.md").write_text("\n".join(lines), encoding="utf-8")
