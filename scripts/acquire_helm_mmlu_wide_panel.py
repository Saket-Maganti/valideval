from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests
from discover_helm_mmlu_runs import (
    HELM_BASE_URL,
    HELM_RELEASE,
    HELM_SOURCE_PAGE,
    _get_json,
    _gold_index,
    discover_helm_mmlu_runs,
    helm_run_url,
    write_discovery_reports,
)

CHOICES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Acquire an expanded real HELM MMLU wide panel without model inference."
    )
    parser.add_argument(
        "--output",
        default="data/external/mmlu/prediction_details_wide.jsonl",
    )
    parser.add_argument(
        "--partial-output",
        default="data/external/mmlu/prediction_details_wide_partial.jsonl",
    )
    parser.add_argument(
        "--manifest-output",
        default="data/external/mmlu/wide_source_manifest.json",
    )
    parser.add_argument(
        "--discovery-json",
        default="results/mmlu/helm_wide_acquisition/discovery_report.json",
    )
    parser.add_argument(
        "--discovery-md",
        default="results/mmlu/helm_wide_acquisition/discovery_report.md",
    )
    parser.add_argument(
        "--compatibility-json",
        default="results/mmlu/helm_wide_acquisition/compatibility_report.json",
    )
    parser.add_argument(
        "--compatibility-md",
        default="results/mmlu/helm_wide_acquisition/compatibility_report.md",
    )
    parser.add_argument(
        "--wide-source-status",
        default="data/external/mmlu/WIDE_SOURCE_STATUS.md",
    )
    parser.add_argument(
        "--acquisition-report",
        default="REAL_MMLU_WIDE_INPUT_ACQUISITION_REPORT.md",
    )
    parser.add_argument("--release", default=HELM_RELEASE)
    parser.add_argument("--base-url", default=HELM_BASE_URL)
    parser.add_argument("--min-models", type=int, default=30)
    parser.add_argument("--max-models", type=int, default=40)
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Optional explicit HELM model ids. Defaults to public-artifact allowlist.",
    )
    args = parser.parse_args()

    started = time.monotonic()
    payload = acquire_wide_panel(
        output_path=Path(args.output),
        partial_output_path=Path(args.partial_output),
        manifest_path=Path(args.manifest_output),
        discovery_json=Path(args.discovery_json),
        discovery_md=Path(args.discovery_md),
        compatibility_json=Path(args.compatibility_json),
        compatibility_md=Path(args.compatibility_md),
        wide_source_status=Path(args.wide_source_status),
        acquisition_report=Path(args.acquisition_report),
        release=args.release,
        base_url=args.base_url,
        min_models=args.min_models,
        max_models=args.max_models,
        explicit_models=args.models,
    )
    payload["runtime_seconds"] = round(time.monotonic() - started, 3)
    _rewrite_runtime_reports(
        payload,
        wide_source_status=Path(args.wide_source_status),
        acquisition_report=Path(args.acquisition_report),
    )
    print(json.dumps(_console_summary(payload), indent=2, sort_keys=True))


def acquire_wide_panel(
    *,
    output_path: Path,
    partial_output_path: Path,
    manifest_path: Path,
    discovery_json: Path,
    discovery_md: Path,
    compatibility_json: Path,
    compatibility_md: Path,
    wide_source_status: Path,
    acquisition_report: Path,
    release: str,
    base_url: str,
    min_models: int,
    max_models: int,
    explicit_models: list[str] | None,
) -> dict[str, Any]:
    discovery = discover_helm_mmlu_runs(release=release, base_url=base_url, measure_items=True)
    write_discovery_reports(discovery, discovery_json, discovery_md)
    selected_models = _select_models(
        discovery, explicit_models=explicit_models, max_models=max_models
    )
    if len(selected_models) < min_models:
        raise ValueError(
            f"Only {len(selected_models)} complete default public-artifact models available; need {min_models}."
        )

    run_lookup, run_to_suite = _run_lookup(discovery=discovery, release=release, base_url=base_url)
    expected_subjects = set(discovery["subjects"])
    expected_item_count = int(discovery["expected_item_count_per_complete_model"] or 0)
    existing_complete = _existing_complete_rows(
        output_path=output_path,
        selected_models=set(selected_models),
        expected_item_count=expected_item_count,
        expected_subjects=expected_subjects,
    )

    session = requests.Session()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial_output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_partial = partial_output_path.with_suffix(partial_output_path.suffix + ".tmp")

    complete_models: list[str] = []
    partial_models: list[dict[str, Any]] = []
    model_summaries: dict[str, dict[str, Any]] = {}
    canonical_items: set[str] | None = None
    canonical_gold: dict[str, str] | None = None
    gold_mismatches: list[dict[str, Any]] = []
    item_set_mismatches: list[dict[str, Any]] = []
    duplicate_count = 0
    invalid_gold_count = 0
    invalid_prediction_count = 0
    source_files: list[dict[str, str]] = []
    instance_cache: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}

    with (
        tmp_output.open("w", encoding="utf-8") as out,
        tmp_partial.open("w", encoding="utf-8") as partial_out,
    ):
        for index, model in enumerate(selected_models, start=1):
            if model in existing_complete:
                rows = existing_complete[model]
                source = "existing_output_reused"
            else:
                rows, model_source_files = _fetch_model_rows(
                    session=session,
                    model=model,
                    run_lookup=run_lookup,
                    run_to_suite=run_to_suite,
                    subjects=sorted(expected_subjects),
                    base_url=base_url,
                    release=release,
                    instance_cache=instance_cache,
                )
                source_files.extend(model_source_files)
                source = "downloaded_from_helm_public_artifacts"
            validation = _validate_model_rows(
                model=model,
                rows=rows,
                expected_subjects=expected_subjects,
                expected_item_count=expected_item_count,
            )
            duplicate_count += validation["duplicate_count"]
            invalid_gold_count += validation["invalid_gold_count"]
            invalid_prediction_count += validation["invalid_prediction_count"]
            if validation["status"] != "complete":
                partial_models.append(
                    {
                        "model_id": model,
                        "reason": validation["status"],
                        "row_count": len(rows),
                        "source": source,
                    }
                )
                for row in rows:
                    partial_out.write(json.dumps(row, sort_keys=True) + "\n")
                print(f"[{index}/{len(selected_models)}] partial {model}: {validation['status']}")
                continue

            item_ids = {row["item_id"] for row in rows}
            gold = {row["item_id"]: row["gold"] for row in rows}
            if canonical_items is None:
                canonical_items = item_ids
                canonical_gold = gold
            else:
                missing = sorted((canonical_items or set()) - item_ids)
                extra = sorted(item_ids - (canonical_items or set()))
                if missing or extra:
                    item_set_mismatches.append(
                        {
                            "model_id": model,
                            "missing_count": len(missing),
                            "extra_count": len(extra),
                            "missing_preview": missing[:5],
                            "extra_preview": extra[:5],
                        }
                    )
                    for row in rows:
                        partial_out.write(json.dumps(row, sort_keys=True) + "\n")
                    partial_models.append(
                        {
                            "model_id": model,
                            "reason": "item_set_mismatch",
                            "row_count": len(rows),
                            "source": source,
                        }
                    )
                    print(f"[{index}/{len(selected_models)}] excluded {model}: item_set_mismatch")
                    continue
                mismatches = [
                    item_id
                    for item_id, value in gold.items()
                    if canonical_gold is not None and canonical_gold.get(item_id) != value
                ]
                if mismatches:
                    gold_mismatches.append(
                        {
                            "model_id": model,
                            "mismatch_count": len(mismatches),
                            "mismatch_preview": mismatches[:5],
                        }
                    )
                    for row in rows:
                        partial_out.write(json.dumps(row, sort_keys=True) + "\n")
                    partial_models.append(
                        {
                            "model_id": model,
                            "reason": "gold_label_mismatch",
                            "row_count": len(rows),
                            "source": source,
                        }
                    )
                    print(f"[{index}/{len(selected_models)}] excluded {model}: gold_label_mismatch")
                    continue

            complete_models.append(model)
            model_summaries[model] = {
                "row_count": len(rows),
                "subject_count": len({row["subset"] for row in rows}),
                "item_count": len(item_ids),
                "source": source,
                "mean_accuracy": _mean_accuracy(rows),
            }
            for row in sorted(rows, key=_row_sort_key):
                out.write(json.dumps(row, sort_keys=True) + "\n")
            print(f"[{index}/{len(selected_models)}] complete {model}: {len(rows)} rows")

    shutil.move(tmp_output, output_path)
    shutil.move(tmp_partial, partial_output_path)
    if (
        not partial_models
        and partial_output_path.exists()
        and partial_output_path.stat().st_size == 0
    ):
        partial_output_path.unlink()

    compatibility = {
        "schema_version": "0.1",
        "status": "ok"
        if len(complete_models) >= min_models
        and not gold_mismatches
        and not item_set_mismatches
        and duplicate_count == 0
        and invalid_gold_count == 0
        else "blocked",
        "helm_release": release,
        "base_url": base_url,
        "output_path": str(output_path),
        "partial_output_path": str(partial_output_path) if partial_models else None,
        "selected_model_count": len(selected_models),
        "complete_model_count": len(complete_models),
        "partial_model_count": len(partial_models),
        "complete_models": complete_models,
        "partial_models": partial_models,
        "expected_subject_count": len(expected_subjects),
        "expected_item_count": expected_item_count,
        "row_count": _line_count(output_path),
        "same_helm_release": True,
        "same_subjects": not item_set_mismatches,
        "same_item_ids": not item_set_mismatches,
        "same_gold_labels": not gold_mismatches,
        "duplicate_count": duplicate_count,
        "invalid_gold_count": invalid_gold_count,
        "invalid_prediction_label_count": invalid_prediction_count,
        "gold_mismatches": gold_mismatches,
        "item_set_mismatches": item_set_mismatches,
        "model_summaries": model_summaries,
        "prediction_sha256": _sha256(output_path),
        "raw_question_text_persisted": False,
        "warnings": _compatibility_warnings(
            complete_models=complete_models,
            min_models=min_models,
            partial_models=partial_models,
            invalid_prediction_count=invalid_prediction_count,
        ),
    }
    _write_compatibility_reports(compatibility, compatibility_json, compatibility_md)

    manifest = {
        "schema_version": "0.1",
        "source": "HELM MMLU public release",
        "source_page": HELM_SOURCE_PAGE,
        "helm_release": release,
        "base_url": base_url,
        "output_path": str(output_path),
        "complete_models": complete_models,
        "partial_models": partial_models,
        "source_files": source_files,
        "discovery_report": str(discovery_json),
        "compatibility_report": str(compatibility_json),
        "raw_question_text_persisted": False,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    payload = {
        "schema_version": "0.1",
        "status": compatibility["status"],
        "discovery": {
            "candidate_model_count": discovery["candidate_model_count"],
            "complete_model_count": discovery["complete_model_count"],
            "default_selected_model_count": discovery["default_selected_model_count"],
            "partial_model_count": discovery["partial_model_count"],
        },
        "compatibility": compatibility,
        "manifest_path": str(manifest_path),
    }
    _write_source_status(payload, wide_source_status)
    _write_acquisition_report(payload, acquisition_report)
    return payload


def _select_models(
    discovery: dict[str, Any],
    *,
    explicit_models: list[str] | None,
    max_models: int,
) -> list[str]:
    if explicit_models:
        available = {model["model_id"] for model in discovery["models"]}
        missing = sorted(set(explicit_models) - available)
        if missing:
            raise ValueError(f"Requested HELM models are not in the release: {missing}")
        return sorted(explicit_models)
    return discovery["default_selected_models"][:max_models]


def _run_lookup(
    *,
    discovery: dict[str, Any],
    release: str,
    base_url: str,
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, str]]:
    session = requests.Session()
    run_specs = _get_json(session, f"{base_url}/releases/{release}/run_specs.json")
    run_to_suite = _get_json(session, f"{base_url}/releases/{release}/runs_to_run_suites.json")
    selected_subjects = set(discovery["subjects"])
    lookup = {}
    for run in run_specs:
        scenario = run.get("scenario_spec") or {}
        adapter = run.get("adapter_spec") or {}
        subject = (scenario.get("args") or {}).get("subject")
        if subject not in selected_subjects:
            continue
        if adapter.get("method") != "multiple_choice_joint":
            continue
        if "eval_split=test" not in run.get("name", ""):
            continue
        lookup[(adapter.get("model"), subject)] = run
    return lookup, run_to_suite


def _existing_complete_rows(
    *,
    output_path: Path,
    selected_models: set[str],
    expected_item_count: int,
    expected_subjects: set[str],
) -> dict[str, list[dict[str, Any]]]:
    if not output_path.exists():
        return {}
    rows_by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with output_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            model = str(row.get("model_id") or "")
            if model in selected_models:
                rows_by_model[model].append(row)
    complete = {}
    for model, rows in rows_by_model.items():
        validation = _validate_model_rows(
            model=model,
            rows=rows,
            expected_subjects=expected_subjects,
            expected_item_count=expected_item_count,
        )
        if validation["status"] == "complete":
            complete[model] = rows
    return complete


def _fetch_model_rows(
    *,
    session: requests.Session,
    model: str,
    run_lookup: dict[tuple[str, str], dict[str, Any]],
    run_to_suite: dict[str, str],
    subjects: list[str],
    base_url: str,
    release: str,
    instance_cache: dict[tuple[str, str], dict[str, dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows = []
    source_files = []
    for subject in subjects:
        run = run_lookup.get((model, subject))
        if run is None:
            continue
        run_name = run["name"]
        suite = run_to_suite.get(run_name)
        if suite is None:
            continue
        display_url = helm_run_url(base_url, suite, run_name, "display_predictions.json")
        instances_url = helm_run_url(base_url, suite, run_name, "instances.json")
        predictions = _get_json(session, display_url)
        instance_key = (suite, subject)
        if instance_key not in instance_cache:
            instances = _get_json(session, instances_url)
            instance_cache[instance_key] = {str(instance["id"]): instance for instance in instances}
        instance_by_id = instance_cache[instance_key]
        source_files.append(
            {
                "model": model,
                "subject": subject,
                "suite": suite,
                "display_predictions_url": display_url,
                "instances_url_used_for_gold_only": instances_url,
            }
        )
        for prediction in predictions:
            instance_id = str(prediction["instance_id"])
            instance = instance_by_id.get(instance_id)
            if instance is None:
                continue
            gold_index = _gold_index(instance)
            rows.append(
                {
                    "benchmark": "mmlu",
                    "subset": subject,
                    "item_id": f"mmlu_{subject}_{_safe_id(instance_id)}",
                    "model_id": model,
                    "prediction": _prediction_label(prediction, instance),
                    "gold": _label(gold_index),
                    "correct": _correct(prediction),
                    "source": f"helm_mmlu:{release}",
                    "source_file": display_url,
                    "metadata": {
                        "helm_model": model,
                        "helm_release": release,
                        "helm_suite": suite,
                        "helm_run_name": run_name,
                        "helm_instance_id": instance_id,
                        "helm_source_page": HELM_SOURCE_PAGE,
                        "instances_url_used_for_gold_only": instances_url,
                    },
                }
            )
    return rows, source_files


def _validate_model_rows(
    *,
    model: str,
    rows: list[dict[str, Any]],
    expected_subjects: set[str],
    expected_item_count: int,
) -> dict[str, Any]:
    subjects = {row.get("subset") for row in rows}
    keys = [(row.get("subset"), row.get("item_id")) for row in rows]
    duplicate_count = sum(count - 1 for count in Counter(keys).values() if count > 1)
    invalid_gold_count = sum(1 for row in rows if row.get("gold") not in {"A", "B", "C", "D"})
    invalid_prediction_count = sum(
        1 for row in rows if row.get("prediction") not in {"A", "B", "C", "D"}
    )
    status = "complete"
    if len(rows) != expected_item_count:
        status = "row_count_mismatch"
    elif subjects != expected_subjects:
        status = "subject_set_mismatch"
    elif duplicate_count:
        status = "duplicate_rows"
    elif invalid_gold_count:
        status = "invalid_gold_labels"
    return {
        "model_id": model,
        "status": status,
        "row_count": len(rows),
        "subject_count": len(subjects),
        "duplicate_count": duplicate_count,
        "invalid_gold_count": invalid_gold_count,
        "invalid_prediction_count": invalid_prediction_count,
    }


def _prediction_label(prediction: dict[str, Any], instance: dict[str, Any]) -> str:
    predicted = str(prediction.get("predicted_text") or "").strip().upper()
    if predicted in CHOICES:
        return predicted
    mapped = str(prediction.get("mapped_output") or "").strip()
    for index, reference in enumerate(instance.get("references") or []):
        output = reference.get("output") or {}
        if str(output.get("text") or "").strip() == mapped:
            return _label(index)
    return predicted or mapped or "UNMAPPED"


def _correct(prediction: dict[str, Any]) -> bool | None:
    stats = prediction.get("stats") or {}
    value = stats.get("exact_match")
    if value is None:
        return None
    return float(value) >= 0.5


def _label(index: int | None) -> str:
    if index is None or index < 0 or index >= len(CHOICES):
        return ""
    return CHOICES[index]


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _row_sort_key(row: dict[str, Any]) -> tuple[str, str, int, str]:
    match = re.search(r"(\d+)$", str(row["item_id"]))
    return (
        str(row["model_id"]),
        str(row["subset"]),
        int(match.group(1)) if match else -1,
        str(row["item_id"]),
    )


def _mean_accuracy(rows: list[dict[str, Any]]) -> float:
    values = [1.0 if row.get("correct") else 0.0 for row in rows]
    return sum(values) / len(values) if values else 0.0


def _compatibility_warnings(
    *,
    complete_models: list[str],
    min_models: int,
    partial_models: list[dict[str, Any]],
    invalid_prediction_count: int,
) -> list[str]:
    warnings = [
        "No raw MMLU question text was persisted.",
        "The default model set excludes known closed or paid API provider prefixes when enough public-artifact models are available.",
    ]
    if len(complete_models) < min_models:
        warnings.append("Complete model count is below the requested minimum.")
    if partial_models:
        warnings.append("Some selected models were excluded as partial or incompatible.")
    if invalid_prediction_count:
        warnings.append(
            "Some model predictions are outside A-D; correctness fields remain from HELM."
        )
    return warnings


def _write_compatibility_reports(
    payload: dict[str, Any],
    output_json: Path,
    output_md: Path,
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(_render_compatibility_markdown(payload), encoding="utf-8")


def _render_compatibility_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# HELM MMLU Wide Compatibility Report",
        "",
        "This report is sanitized and does not expose raw MMLU question text.",
        "",
        f"- Status: `{payload['status']}`",
        f"- HELM release: `{payload['helm_release']}`",
        f"- Complete models: {payload['complete_model_count']}",
        f"- Partial/excluded selected models: {payload['partial_model_count']}",
        f"- Expected subjects: {payload['expected_subject_count']}",
        f"- Expected items per complete model: {payload['expected_item_count']}",
        f"- Rows written: {payload['row_count']}",
        f"- Same HELM release: `{payload['same_helm_release']}`",
        f"- Same item IDs: `{payload['same_item_ids']}`",
        f"- Same gold labels: `{payload['same_gold_labels']}`",
        f"- Duplicate rows: {payload['duplicate_count']}",
        f"- Invalid gold labels: {payload['invalid_gold_count']}",
        f"- Invalid prediction labels: {payload['invalid_prediction_label_count']}",
        f"- SHA-256: `{payload['prediction_sha256']}`",
        "",
        "## Complete Models",
        "",
    ]
    lines.extend(f"- `{model}`" for model in payload["complete_models"])
    lines.extend(["", "## Partial Or Excluded Selected Models", ""])
    if payload["partial_models"]:
        lines.extend(
            f"- `{row['model_id']}`: {row['reason']} ({row['row_count']} rows)"
            for row in payload["partial_models"]
        )
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in payload["warnings"])
    return "\n".join(lines) + "\n"


def _write_source_status(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render_source_status(payload), encoding="utf-8")


def _render_source_status(payload: dict[str, Any]) -> str:
    compat = payload["compatibility"]
    lines = [
        "# MMLU Wide Source Status",
        "",
        "This file tracks the expanded real HELM MMLU prediction-detail source. It does not expose raw MMLU question text.",
        "",
        f"- Status: `{payload['status']}`",
        f"- HELM release: `{compat['helm_release']}`",
        f"- Source page: `{HELM_SOURCE_PAGE}`",
        f"- Base URL: `{compat['base_url']}`",
        f"- Output: `{compat['output_path']}`",
        f"- Complete models: {compat['complete_model_count']}",
        f"- Expected items per model: {compat['expected_item_count']}",
        f"- Rows: {compat['row_count']}",
        f"- Partial selected models: {compat['partial_model_count']}",
        f"- SHA-256: `{compat['prediction_sha256']}`",
        f"- Runtime seconds: {payload.get('runtime_seconds', 'pending')}",
        "",
        "## Complete Models",
        "",
    ]
    lines.extend(f"- `{model}`" for model in compat["complete_models"])
    lines.extend(["", "## Claims Boundary", ""])
    lines.extend(
        [
            "- Allowed: real public HELM MMLU per-instance predictions were normalized for the listed models.",
            "- Not allowed: any benchmark-validity, MMLU-Redux detection, or IRT/item-discrimination claim from this file alone.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_acquisition_report(payload: dict[str, Any], path: Path) -> None:
    path.write_text(_render_acquisition_report(payload), encoding="utf-8")


def _render_acquisition_report(payload: dict[str, Any]) -> str:
    compat = payload["compatibility"]
    discovery = payload["discovery"]
    lines = [
        "# Real MMLU Wide Input Acquisition Report",
        "",
        "## Summary",
        "",
        "Expanded real MMLU per-instance prediction details were acquired from public HELM MMLU artifacts without model inference. Raw MMLU question text was not persisted.",
        "",
        "## Discovery",
        "",
        f"- Candidate models: {discovery['candidate_model_count']}",
        f"- Complete by release manifest: {discovery['complete_model_count']}",
        f"- Partial by release manifest: {discovery['partial_model_count']}",
        f"- Default selected models: {discovery['default_selected_model_count']}",
        "",
        "## Expanded Prediction File",
        "",
        f"- Status: `{payload['status']}`",
        f"- Output: `{compat['output_path']}`",
        f"- HELM release: `{compat['helm_release']}`",
        f"- Complete models: {compat['complete_model_count']}",
        f"- Partial selected models: {compat['partial_model_count']}",
        f"- Items per complete model: {compat['expected_item_count']}",
        f"- Rows: {compat['row_count']}",
        f"- SHA-256: `{compat['prediction_sha256']}`",
        f"- Runtime seconds: {payload.get('runtime_seconds', 'pending')}",
        "",
        "## Compatibility",
        "",
        f"- Same HELM release: `{compat['same_helm_release']}`",
        f"- Same subjects: `{compat['same_subjects']}`",
        f"- Same item IDs: `{compat['same_item_ids']}`",
        f"- Same gold labels: `{compat['same_gold_labels']}`",
        f"- Duplicate rows: {compat['duplicate_count']}",
        f"- Invalid gold labels: {compat['invalid_gold_count']}",
        f"- Invalid prediction labels: {compat['invalid_prediction_label_count']}",
        "",
        "## Complete Models",
        "",
    ]
    lines.extend(f"- `{model}`" for model in compat["complete_models"])
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in compat["warnings"])
    return "\n".join(lines) + "\n"


def _rewrite_runtime_reports(
    payload: dict[str, Any],
    *,
    wide_source_status: Path,
    acquisition_report: Path,
) -> None:
    _write_source_status(payload, wide_source_status)
    _write_acquisition_report(payload, acquisition_report)


def _line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _console_summary(payload: dict[str, Any]) -> dict[str, Any]:
    compat = payload["compatibility"]
    return {
        "status": payload["status"],
        "complete_model_count": compat["complete_model_count"],
        "partial_model_count": compat["partial_model_count"],
        "row_count": compat["row_count"],
        "expected_item_count": compat["expected_item_count"],
        "runtime_seconds": payload["runtime_seconds"],
        "output_path": compat["output_path"],
    }


if __name__ == "__main__":
    main()
