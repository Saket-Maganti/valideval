from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path
from typing import Any

import requests
from datasets import get_dataset_config_names, load_dataset

HELM_RELEASE = "v1.13.0"
HELM_BASE_URL = "https://storage.googleapis.com/crfm-helm-public/gzip/mmlu/benchmark_output"
HELM_SOURCE_PAGE = "https://crfm.stanford.edu/helm/mmlu/latest/"
DEFAULT_HELM_MODELS = [
    "mistralai/mistral-7b-v0.1",
    "google/gemma-7b",
    "qwen/qwen1.5-7b",
]
MMLU_REDUX_DATASET = "edinburgh-dawg/mmlu-redux-2.0"
CHOICES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire real public MMLU detail inputs.")
    parser.add_argument(
        "--predictions-output",
        default="data/external/mmlu/prediction_details.jsonl",
    )
    parser.add_argument(
        "--redux-output",
        default="data/ground_truth/mmlu_redux_issues.normalized.jsonl",
    )
    parser.add_argument(
        "--manifest-output",
        default="data/external/mmlu/source_manifest.json",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_HELM_MODELS,
        help="HELM model ids to download from the public MMLU release.",
    )
    parser.add_argument(
        "--subjects",
        nargs="*",
        default=None,
        help="Optional subject subset. Defaults to all HELM MMLU subjects for the selected models.",
    )
    args = parser.parse_args()

    predictions_summary = acquire_helm_predictions(
        models=args.models,
        subjects=args.subjects,
        output_path=Path(args.predictions_output),
        manifest_path=Path(args.manifest_output),
    )
    redux_summary = acquire_mmlu_redux_labels(Path(args.redux_output))
    print(
        json.dumps(
            {
                "helm_predictions": predictions_summary,
                "mmlu_redux": redux_summary,
            },
            indent=2,
            sort_keys=True,
        )
    )


def acquire_helm_predictions(
    *,
    models: list[str],
    subjects: list[str] | None,
    output_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    session = requests.Session()
    run_specs = _get_json(session, f"{HELM_BASE_URL}/releases/{HELM_RELEASE}/run_specs.json")
    run_to_suite = _get_json(
        session, f"{HELM_BASE_URL}/releases/{HELM_RELEASE}/runs_to_run_suites.json"
    )
    selected = _select_helm_runs(run_specs, models=models, subjects=subjects)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    rows_written = 0
    missing_runs: list[dict[str, str]] = []
    source_files: list[dict[str, str]] = []
    with output_path.open("w", encoding="utf-8") as handle:
        for run in selected:
            run_name = run["name"]
            suite = run_to_suite.get(run_name)
            if not suite:
                missing_runs.append(
                    {
                        "run_name": run_name,
                        "reason": "run missing from HELM release suite map",
                    }
                )
                continue
            subject = run["scenario_spec"]["args"]["subject"]
            helm_model = run["adapter_spec"]["model"]
            display_url = _helm_run_url(suite, run_name, "display_predictions.json")
            instances_url = _helm_run_url(suite, run_name, "instances.json")
            predictions = _get_json(session, display_url)
            instances = _get_json(session, instances_url)
            instance_by_id = {instance["id"]: instance for instance in instances}
            source_files.append(
                {
                    "model": helm_model,
                    "subject": subject,
                    "suite": suite,
                    "display_predictions_url": display_url,
                    "instances_url": instances_url,
                }
            )
            for prediction in predictions:
                instance_id = str(prediction["instance_id"])
                instance = instance_by_id.get(instance_id)
                if instance is None:
                    continue
                gold_index = _gold_index(instance)
                row = {
                    "benchmark": "mmlu",
                    "subset": subject,
                    "item_id": f"mmlu_{subject}_{_safe_id(instance_id)}",
                    "model_id": _model_id(helm_model),
                    "prediction": _prediction_label(prediction, instance),
                    "gold": _label(gold_index),
                    "correct": _correct(prediction),
                    "source": f"helm_mmlu:{HELM_RELEASE}",
                    "source_file": display_url,
                    "metadata": {
                        "helm_model": helm_model,
                        "helm_release": HELM_RELEASE,
                        "helm_suite": suite,
                        "helm_run_name": run_name,
                        "helm_instance_id": instance_id,
                        "helm_source_page": HELM_SOURCE_PAGE,
                        "instances_url_used_for_gold_only": instances_url,
                    },
                }
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                rows_written += 1

    manifest = {
        "schema_version": "0.1",
        "source": "HELM MMLU public release",
        "source_page": HELM_SOURCE_PAGE,
        "helm_release": HELM_RELEASE,
        "models": [_model_id(model) for model in models],
        "subjects": sorted({run["scenario_spec"]["args"]["subject"] for run in selected}),
        "rows_written": rows_written,
        "output_path": str(output_path),
        "missing_runs": missing_runs,
        "source_files": source_files,
        "raw_question_text_persisted": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "status": "ok" if rows_written else "blocked",
        "rows_written": rows_written,
        "model_count": len(models),
        "subject_count": len(manifest["subjects"]),
        "output_path": str(output_path),
        "manifest_path": str(manifest_path),
        "missing_run_count": len(missing_runs),
    }


def acquire_mmlu_redux_labels(output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    configs = get_dataset_config_names(MMLU_REDUX_DATASET)
    rows_written = 0
    subjects_with_labels: list[str] = []
    with output_path.open("w", encoding="utf-8") as handle:
        for subject in configs:
            dataset = load_dataset(MMLU_REDUX_DATASET, subject, split="test")
            subject_rows = 0
            for row_index, record in enumerate(dataset):
                error_type = str(record.get("error_type") or "unknown").strip()
                if error_type == "ok":
                    continue
                normalized = {
                    "benchmark": "mmlu_redux",
                    "subset": subject,
                    "item_id": f"mmlu_redux2_{subject}_{row_index:04d}",
                    "issue_type": "mmlu_redux_flaw",
                    "severity": "unknown",
                    "source": MMLU_REDUX_DATASET,
                    "metadata": {
                        "source_dataset": MMLU_REDUX_DATASET,
                        "source_config": subject,
                        "source_split": "test",
                        "source_row_index": row_index,
                        "mmlu_redux_error_type": error_type,
                        "mmlu_redux_source": record.get("source"),
                        "alignment_note": "Dataset rows do not expose HELM instance ids; item ids are stable source row ids.",
                    },
                }
                handle.write(json.dumps(normalized, sort_keys=True) + "\n")
                rows_written += 1
                subject_rows += 1
            if subject_rows:
                subjects_with_labels.append(subject)
    return {
        "status": "ok" if rows_written else "blocked",
        "rows_written": rows_written,
        "dataset": MMLU_REDUX_DATASET,
        "subject_count": len(subjects_with_labels),
        "output_path": str(output_path),
        "raw_question_text_persisted": False,
    }


def _select_helm_runs(
    run_specs: list[dict[str, Any]],
    *,
    models: list[str],
    subjects: list[str] | None,
) -> list[dict[str, Any]]:
    wanted_subjects = set(subjects or [])
    selected = []
    for spec in run_specs:
        scenario = spec.get("scenario_spec") or {}
        adapter = spec.get("adapter_spec") or {}
        scenario_args = scenario.get("args") or {}
        subject = scenario_args.get("subject")
        if scenario.get("class_name") != "helm.benchmark.scenarios.mmlu_scenario.MMLUScenario":
            continue
        if spec.get("adapter_spec", {}).get("method") != "multiple_choice_joint":
            continue
        if adapter.get("model") not in models:
            continue
        if wanted_subjects and subject not in wanted_subjects:
            continue
        if "eval_split=test" not in spec.get("name", ""):
            continue
        selected.append(spec)
    return sorted(
        selected,
        key=lambda spec: (
            spec["adapter_spec"]["model"],
            spec["scenario_spec"]["args"]["subject"],
        ),
    )


def _get_json(session: requests.Session, url: str) -> Any:
    response = session.get(url, timeout=120)
    response.raise_for_status()
    content = response.content
    if content[:2] == b"\x1f\x8b":
        content = gzip.decompress(content)
    return json.loads(content)


def _helm_run_url(suite: str, run_name: str, filename: str) -> str:
    return f"{HELM_BASE_URL}/runs/{suite}/{run_name}/{filename}"


def _gold_index(instance: dict[str, Any]) -> int | None:
    for index, reference in enumerate(instance.get("references") or []):
        if "correct" in (reference.get("tags") or []):
            return index
    return None


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


def _model_id(helm_model: str) -> str:
    if "_" not in helm_model:
        return helm_model
    org, name = helm_model.split("_", 1)
    return f"{org}/{name}"


if __name__ == "__main__":
    main()
