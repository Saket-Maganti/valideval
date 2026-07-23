from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.importers.lm_eval_details import import_lm_eval_samples
from valideval.importers.wide_matrix import import_wide_predictions

SUPPORTED_DETAIL_FORMATS = {
    "auto",
    "leaderboard_jsonl",
    "leaderboard_csv",
    "helm_jsonl",
    "helm_json",
    "lm_eval",
    "lm_eval_dir",
    "lm_eval_jsonl",
}


def import_published_details(
    input_path: str | Path,
    *,
    benchmark: str,
    output_path: str | Path,
    detail_format: str = "auto",
    mapping_report: str | Path | None = None,
    include_text: bool = False,
) -> dict[str, Any]:
    if detail_format not in SUPPORTED_DETAIL_FORMATS:
        raise ValueError(f"Unsupported published-detail format: {detail_format}")
    source = Path(input_path)
    if detail_format in {"lm_eval", "lm_eval_dir", "lm_eval_jsonl"}:
        return import_lm_eval_samples(
            source,
            benchmark=benchmark,
            output_path=output_path,
            mapping_report=mapping_report,
            include_text=include_text,
        )
    normalized_input = source
    temp_path: Path | None = None
    if detail_format == "helm_json":
        temp_path = source.with_suffix(source.suffix + ".flattened.jsonl")
        _flatten_helm_json(source, temp_path)
        normalized_input = temp_path
        wide_format = "generic_jsonl"
    elif detail_format == "helm_jsonl":
        wide_format = "generic_jsonl"
    elif detail_format == "leaderboard_csv":
        wide_format = "generic_csv"
    elif detail_format == "leaderboard_jsonl":
        wide_format = "generic_jsonl"
    else:
        wide_format = "auto"

    summary = import_wide_predictions(
        normalized_input,
        output_path,
        benchmark=benchmark,
        input_format=wide_format,
        source=f"published_details:{detail_format}",
        include_text=include_text,
        report_path=mapping_report,
    )
    summary["source_detail_file"] = str(source)
    summary["format"] = detail_format
    if temp_path and temp_path.exists():
        temp_path.unlink()
    _write_summary_json(output_path, summary)
    return summary


def _flatten_helm_json(source: Path, destination: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    records = payload.get("request_states") or payload.get("instances") or payload.get("records")
    if records is None and isinstance(payload, list):
        records = payload
    if not isinstance(records, list):
        raise ValueError("HELM JSON must contain request_states, instances, records, or a list.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(_flatten_record(record), sort_keys=True) + "\n")


def _flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    output = dict(record)
    request = output.pop("request", None)
    result = output.pop("result", None)
    instance = output.pop("instance", None)
    if isinstance(instance, dict):
        output.update({f"instance_{key}": value for key, value in instance.items()})
        for source_key, target_key in (
            ("id", "item_id"),
            ("references", "gold"),
            ("input", "prompt"),
        ):
            if source_key in instance and target_key not in output:
                output[target_key] = instance[source_key]
    if isinstance(request, dict):
        output.update({f"request_{key}": value for key, value in request.items()})
    if isinstance(result, dict):
        output.update({f"result_{key}": value for key, value in result.items()})
        if "completions" in result and "prediction" not in output:
            completions = result.get("completions") or []
            if completions:
                first = completions[0]
                output["prediction"] = (
                    first.get("text", first) if isinstance(first, dict) else first
                )
        if "stats" in result and isinstance(result["stats"], dict):
            for key, value in result["stats"].items():
                output.setdefault(key, value)
    if "item_id" not in output:
        output["item_id"] = (
            output.get("doc_id") or output.get("sample_id") or output.get("instance_id")
        )
    return output


def _write_summary_json(output_path: str | Path, summary: dict[str, Any]) -> None:
    path = Path(output_path).with_suffix(Path(output_path).suffix + ".summary.json")
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
