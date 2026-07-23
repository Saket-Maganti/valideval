from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

HELM_RELEASE = "v1.13.0"
HELM_BASE_URL = "https://storage.googleapis.com/crfm-helm-public/gzip/mmlu/benchmark_output"
HELM_SOURCE_PAGE = "https://crfm.stanford.edu/helm/mmlu/latest/"
MMLU_SCENARIO = "helm.benchmark.scenarios.mmlu_scenario.MMLUScenario"

DEFAULT_PUBLIC_ARTIFACT_PREFIXES = (
    "01-ai/",
    "allenai/",
    "databricks/",
    "deepseek-ai/",
    "google/gemma",
    "meta/",
    "microsoft/",
    "mistralai/mistral-7b",
    "mistralai/mixtral",
    "mistralai/open-mistral",
    "qwen/",
    "snowflake/",
)

DEFAULT_EXCLUDED_PREFIXES = (
    "ai21/",
    "amazon/",
    "anthropic/",
    "cohere/",
    "google/gemini",
    "google/text-",
    "openai/",
    "upstage/",
    "writer/",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover public HELM MMLU v1.13.0 model runs without model inference."
    )
    parser.add_argument(
        "--output-json",
        default="results/mmlu/helm_wide_acquisition/discovery_report.json",
    )
    parser.add_argument(
        "--output-md",
        default="results/mmlu/helm_wide_acquisition/discovery_report.md",
    )
    parser.add_argument("--release", default=HELM_RELEASE)
    parser.add_argument("--base-url", default=HELM_BASE_URL)
    parser.add_argument(
        "--measure-items",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fetch one instances.json per subject/suite needed to count expected items.",
    )
    args = parser.parse_args()

    payload = discover_helm_mmlu_runs(
        release=args.release,
        base_url=args.base_url,
        measure_items=args.measure_items,
    )
    write_discovery_reports(payload, args.output_json, args.output_md)
    print(json.dumps(_console_summary(payload), indent=2, sort_keys=True))


def discover_helm_mmlu_runs(
    *,
    release: str = HELM_RELEASE,
    base_url: str = HELM_BASE_URL,
    measure_items: bool = True,
) -> dict[str, Any]:
    session = requests.Session()
    run_specs = _get_json(session, f"{base_url}/releases/{release}/run_specs.json")
    run_to_suite = _get_json(session, f"{base_url}/releases/{release}/runs_to_run_suites.json")
    runs = _mmlu_test_runs(run_specs)
    runs_by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    subjects = sorted({run["scenario_spec"]["args"]["subject"] for run in runs})
    for run in runs:
        runs_by_model[run["adapter_spec"]["model"]].append(run)

    subject_item_counts: dict[str, int] = {}
    subject_gold_hashes: dict[str, str] = {}
    item_measurement_source: dict[str, str] = {}
    if measure_items:
        subject_item_counts, subject_gold_hashes, item_measurement_source = _measure_subjects(
            session=session,
            runs=runs,
            run_to_suite=run_to_suite,
            subjects=subjects,
            base_url=base_url,
        )

    models = []
    for model, model_runs in sorted(runs_by_model.items()):
        run_subjects = {run["scenario_spec"]["args"]["subject"] for run in model_runs}
        missing_subjects = sorted(set(subjects) - run_subjects)
        missing_suite_runs = sorted(
            run["name"] for run in model_runs if run["name"] not in run_to_suite
        )
        status = (
            "complete_by_release_manifest"
            if not missing_subjects and not missing_suite_runs
            else "partial_by_release_manifest"
        )
        selected_by_default = _is_default_public_artifact_model(model) and status.startswith(
            "complete"
        )
        excluded_reason = None if selected_by_default else _excluded_reason(model, status)
        models.append(
            {
                "model_id": model,
                "status": status,
                "run_count": len(model_runs),
                "subject_count": len(run_subjects),
                "missing_subject_count": len(missing_subjects),
                "missing_subjects": missing_subjects,
                "missing_suite_run_count": len(missing_suite_runs),
                "selected_by_default": selected_by_default,
                "excluded_reason": excluded_reason,
                "expected_item_count": sum(subject_item_counts.values())
                if subject_item_counts
                else None,
                "subject_coverage": sorted(run_subjects),
            }
        )

    complete = [model for model in models if model["status"] == "complete_by_release_manifest"]
    partial = [model for model in models if model["status"] != "complete_by_release_manifest"]
    selected = [model for model in models if model["selected_by_default"]]
    payload = {
        "schema_version": "0.1",
        "source": "HELM MMLU public benchmark output",
        "source_page": HELM_SOURCE_PAGE,
        "base_url": base_url,
        "helm_release": release,
        "candidate_model_count": len(models),
        "complete_model_count": len(complete),
        "partial_model_count": len(partial),
        "default_selected_model_count": len(selected),
        "excluded_model_count": len(models) - len(selected),
        "subject_count": len(subjects),
        "subjects": subjects,
        "expected_item_count_per_complete_model": sum(subject_item_counts.values())
        if subject_item_counts
        else None,
        "subject_item_counts": subject_item_counts,
        "subject_gold_hashes": subject_gold_hashes,
        "item_measurement_source": item_measurement_source,
        "models": models,
        "default_selected_models": [model["model_id"] for model in selected],
        "raw_question_text_persisted": False,
        "notes": [
            "Completeness here is based on HELM release metadata and suite-map availability.",
            "Acquisition performs row-count, item-set, and gold-label compatibility checks before import.",
        ],
    }
    return payload


def write_discovery_reports(
    payload: dict[str, Any],
    output_json: str | Path,
    output_md: str | Path,
) -> None:
    json_path = Path(output_json)
    md_path = Path(output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_discovery_markdown(payload), encoding="utf-8")


def _mmlu_test_runs(run_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runs = []
    for spec in run_specs:
        scenario = spec.get("scenario_spec") or {}
        adapter = spec.get("adapter_spec") or {}
        if scenario.get("class_name") != MMLU_SCENARIO:
            continue
        if adapter.get("method") != "multiple_choice_joint":
            continue
        if "eval_split=test" not in spec.get("name", ""):
            continue
        runs.append(spec)
    return runs


def _measure_subjects(
    *,
    session: requests.Session,
    runs: list[dict[str, Any]],
    run_to_suite: dict[str, str],
    subjects: list[str],
    base_url: str,
) -> tuple[dict[str, int], dict[str, str], dict[str, str]]:
    subject_runs = {}
    for run in sorted(runs, key=lambda value: value["adapter_spec"]["model"]):
        subject = run["scenario_spec"]["args"]["subject"]
        if subject not in subject_runs and run["name"] in run_to_suite:
            subject_runs[subject] = run
    counts = {}
    gold_hashes = {}
    sources = {}
    for subject in subjects:
        run = subject_runs.get(subject)
        if not run:
            continue
        suite = run_to_suite[run["name"]]
        url = helm_run_url(base_url, suite, run["name"], "instances.json")
        instances = _get_json(session, url)
        counts[subject] = len(instances)
        gold_payload = [
            {
                "id": str(instance.get("id")),
                "gold_index": _gold_index(instance),
            }
            for instance in instances
        ]
        gold_hashes[subject] = _sha256_json(gold_payload)
        sources[subject] = url
    return counts, gold_hashes, sources


def _gold_index(instance: dict[str, Any]) -> int | None:
    for index, reference in enumerate(instance.get("references") or []):
        if "correct" in (reference.get("tags") or []):
            return index
    return None


def _is_default_public_artifact_model(model: str) -> bool:
    return any(model.startswith(prefix) for prefix in DEFAULT_PUBLIC_ARTIFACT_PREFIXES)


def _excluded_reason(model: str, status: str) -> str:
    if status != "complete_by_release_manifest":
        return "partial_release_manifest"
    if any(model.startswith(prefix) for prefix in DEFAULT_EXCLUDED_PREFIXES):
        return "excluded_default_policy_closed_or_paid_api_provider"
    return "excluded_default_policy_not_in_public_artifact_allowlist"


def _get_json(session: requests.Session, url: str, *, attempts: int = 3) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=120)
            response.raise_for_status()
            content = response.content
            if content[:2] == b"\x1f\x8b":
                content = gzip.decompress(content)
            return json.loads(content)
        except Exception as exc:  # pragma: no cover - network retry path.
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"Failed to fetch JSON from {url}: {last_error}") from last_error


def helm_run_url(base_url: str, suite: str, run_name: str, filename: str) -> str:
    return f"{base_url}/runs/{suite}/{run_name}/{filename}"


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _render_discovery_markdown(payload: dict[str, Any]) -> str:
    excluded_reasons = defaultdict(int)
    for model in payload["models"]:
        if model.get("excluded_reason"):
            excluded_reasons[model["excluded_reason"]] += 1
    lines = [
        "# HELM MMLU Wide Acquisition Discovery",
        "",
        "This report uses HELM release metadata and sanitized item counts only. It does not expose raw MMLU question text.",
        "",
        f"- Source: `{payload['source']}`",
        f"- Source page: `{payload['source_page']}`",
        f"- Base URL: `{payload['base_url']}`",
        f"- HELM release: `{payload['helm_release']}`",
        f"- Candidate models: {payload['candidate_model_count']}",
        f"- Complete by release manifest: {payload['complete_model_count']}",
        f"- Partial by release manifest: {payload['partial_model_count']}",
        f"- Default selected models: {payload['default_selected_model_count']}",
        f"- Excluded models: {payload['excluded_model_count']}",
        f"- Subjects: {payload['subject_count']}",
        f"- Expected items per complete model: {payload['expected_item_count_per_complete_model']}",
        "",
        "## Exclusion Reasons",
        "",
    ]
    if excluded_reasons:
        lines.extend(f"- `{reason}`: {count}" for reason, count in sorted(excluded_reasons.items()))
    else:
        lines.append("- none")
    lines.extend(["", "## Default Selected Models", ""])
    lines.extend(f"- `{model}`" for model in payload["default_selected_models"])
    lines.extend(["", "## Model Coverage", ""])
    lines.extend(
        f"- `{model['model_id']}`: {model['status']}, subjects={model['subject_count']}, selected={model['selected_by_default']}"
        for model in payload["models"]
    )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in payload["notes"])
    return "\n".join(lines) + "\n"


def _console_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_model_count": payload["candidate_model_count"],
        "complete_model_count": payload["complete_model_count"],
        "default_selected_model_count": payload["default_selected_model_count"],
        "expected_item_count_per_complete_model": payload["expected_item_count_per_complete_model"],
        "helm_release": payload["helm_release"],
        "partial_model_count": payload["partial_model_count"],
        "subject_count": payload["subject_count"],
    }


if __name__ == "__main__":
    main()
