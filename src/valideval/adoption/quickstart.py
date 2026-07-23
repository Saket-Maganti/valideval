from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from valideval.adoption.importers import load_external_rows, normalize_prediction_records
from valideval.benchmarks.local_jsonl import LocalJSONLBenchmark
from valideval.diagnostics.answer_distribution import AnswerDistributionDiagnostic
from valideval.diagnostics.baselines import BaselineDiagnostic
from valideval.diagnostics.data_forensics import DataForensicsDiagnostic
from valideval.forensics.provenance import audit_manifest_hashes, write_manifest
from valideval.io.cache import build_response_matrix
from valideval.io.jsonl import write_jsonl
from valideval.repair.engine import issue_certificate, render_validity_card, run_repair
from valideval.schemas import DiagnosticResult, ModelPrediction, ResponseMatrix, utc_now

QUICKSTART_DIAGNOSTICS = [
    BaselineDiagnostic(),
    AnswerDistributionDiagnostic(),
    DataForensicsDiagnostic(),
]


def run_quickstart_audit(
    *,
    items_path: str | Path,
    outputs_path: str | Path | None = None,
    benchmark_card: str | Path | None = None,
    output_dir: str | Path = "quickstart_audit",
    adapter: str = "generic-jsonl",
    seed: int = 0,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    benchmark = LocalJSONLBenchmark(items_path)
    benchmark.benchmark_id = _slug(Path(items_path).stem)
    if benchmark_card:
        benchmark.claimed_construct = _claimed_construct_from_card(Path(benchmark_card))
        benchmark.construct_spec.claimed_construct = benchmark.claimed_construct
    predictions, matrix, prediction_warnings = _load_and_score_predictions(
        benchmark,
        outputs_path=outputs_path,
        adapter=adapter,
    )
    matrix_input: ResponseMatrix | dict[str, ResponseMatrix] = {"full": matrix} if matrix else {}
    results = _run_quickstart_diagnostics(benchmark, matrix_input, seed=seed)
    manifest = _manifest_payload(
        benchmark,
        outputs_path=outputs_path,
        benchmark_card=benchmark_card,
        diagnostics=[result.diagnostic_name for result in results],
    )
    manifest_path = write_manifest(output / "audit_manifest.json", manifest)
    write_manifest(output / "results" / benchmark.benchmark_id / "manifest.json", manifest)
    diagnostics_dir = output / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        (diagnostics_dir / f"{result.diagnostic_name}.json").write_text(
            json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
    if predictions:
        write_jsonl(output / "normalized_predictions.jsonl", predictions)
    repair_output = run_repair(
        benchmark,
        "quickstart",
        results,
        matrix,
        output_dir=output,
        policy="conservative",
    )
    repair_recommendations = output / "repair_recommendations.md"
    shutil.copyfile(repair_output["repair_report_md"], repair_recommendations)
    card_output = render_validity_card(
        benchmark,
        "quickstart",
        results,
        output_dir=output,
        manifest=manifest,
    )
    certificate_output = issue_certificate(
        benchmark,
        "quickstart",
        results,
        output_dir=output,
        manifest=manifest,
    )
    certificate_json = output / "certificate.json"
    shutil.copyfile(certificate_output["validity_certificate_json"], certificate_json)
    next_steps = output / "README_NEXT_STEPS.md"
    next_steps.write_text(
        _render_next_steps(
            benchmark_id=benchmark.benchmark_id,
            outputs_available=bool(predictions),
            prediction_warnings=prediction_warnings,
        ),
        encoding="utf-8",
    )
    return {
        "benchmark_id": benchmark.benchmark_id,
        "output_dir": str(output),
        "outputs_available": bool(predictions),
        "diagnostics": [result.diagnostic_name for result in results],
        "validity_card_md": card_output["validity_card_md"],
        "validity_card_json": card_output["validity_card_json"],
        "certificate_json": str(certificate_json),
        "item_forensics_csv": repair_output["item_forensics_csv"],
        "repair_recommendations_md": str(repair_recommendations),
        "audit_manifest_json": str(manifest_path),
        "readme_next_steps_md": str(next_steps),
        "warnings": prediction_warnings,
    }


def _load_and_score_predictions(
    benchmark: LocalJSONLBenchmark,
    *,
    outputs_path: str | Path | None,
    adapter: str,
) -> tuple[list[ModelPrediction], ResponseMatrix | None, list[str]]:
    warnings: list[str] = []
    if outputs_path is None:
        warnings.append(
            "No model outputs were supplied; quickstart ran shallow/static diagnostics only."
        )
        return [], None, warnings
    records = load_external_rows(outputs_path, adapter=adapter)
    imported = normalize_prediction_records(
        records,
        benchmark_id=benchmark.benchmark_id,
        prompt_variant="full",
        require_scores=False,
    )
    items_by_id = {item.item_id: item for item in benchmark.load_items()}
    scored: list[ModelPrediction] = []
    unknown_items: list[str] = []
    for prediction in imported:
        item = items_by_id.get(prediction.item_id)
        if item is None:
            unknown_items.append(prediction.item_id)
            continue
        score = benchmark.score_prediction(item, prediction.prediction)
        metadata = {
            **prediction.metadata,
            "external_score": prediction.score,
            "scoring_source": "benchmark.score_prediction",
            "normalized_prediction": score.normalized_prediction,
            "normalized_answer": score.normalized_answer,
        }
        scored.append(
            prediction.model_copy(
                update={
                    "score": score.score,
                    "is_correct": score.is_correct,
                    "metadata": metadata,
                }
            )
        )
    if unknown_items:
        warnings.append(
            "Skipped outputs whose item IDs were not in the local benchmark: "
            + ", ".join(sorted(set(unknown_items))[:10])
        )
    if not scored:
        warnings.append(
            "No supplied outputs could be scored against the local items; no response matrix was built."
        )
        return [], None, warnings
    matrix = build_response_matrix(
        scored,
        benchmark_id=benchmark.benchmark_id,
        panel_id="quickstart",
        variant="full",
        scoring_method="benchmark.score_prediction",
    )
    return scored, matrix, warnings


def _run_quickstart_diagnostics(
    benchmark: LocalJSONLBenchmark,
    matrix_input: ResponseMatrix | dict[str, ResponseMatrix],
    *,
    seed: int,
) -> list[DiagnosticResult]:
    results: list[DiagnosticResult] = []
    config = {"seed": seed}
    for diagnostic in QUICKSTART_DIAGNOSTICS:
        results.append(diagnostic.run(benchmark, matrix_input, config=config))
    return results


def _manifest_payload(
    benchmark: LocalJSONLBenchmark,
    *,
    outputs_path: str | Path | None,
    benchmark_card: str | Path | None,
    diagnostics: list[str],
) -> dict[str, Any]:
    hashes = audit_manifest_hashes(
        benchmark,
        benchmark_config={
            "benchmark_id": benchmark.benchmark_id,
            "items_path": str(benchmark.path),
            "benchmark_card": str(benchmark_card) if benchmark_card else None,
        },
        diagnostic_config={"quickstart_diagnostics": diagnostics},
    )
    return {
        "schema_version": "0.1",
        "created_at": utc_now(),
        **hashes,
        "outputs_path": str(outputs_path) if outputs_path else None,
        "benchmark_card": str(benchmark_card) if benchmark_card else None,
        "diagnostics": diagnostics,
        "limitations": [
            "Quickstart artifacts are a one-hour audit scaffold, not a comprehensive validity audit.",
            "Contamination signals are local/corpus-dependent and do not prove cleanliness.",
            "Model-output scoring uses the local benchmark scorer under this protocol.",
        ],
    }


def _render_next_steps(
    *,
    benchmark_id: str,
    outputs_available: bool,
    prediction_warnings: list[str],
) -> str:
    output_status = (
        "Model outputs were supplied and rescored with the local benchmark scorer."
        if outputs_available
        else "No model outputs were supplied, so the audit did not estimate model performance."
    )
    warnings = "\n".join(f"- {warning}" for warning in prediction_warnings) or "- None."
    return "\n".join(
        [
            f"# Next Steps for {benchmark_id}",
            "",
            output_status,
            "",
            "## Warnings",
            "",
            warnings,
            "",
            "## Recommended Follow-Up",
            "",
            "- Add a benchmark card with intended uses, non-intended uses, and construct-critical fields.",
            "- Run a fuller audit with reliability, shortcut, IRT, and human validation diagnostics when response matrices are available.",
            "- Treat the quickstart validity card as evidence under this protocol, not as a global benchmark verdict.",
            "",
        ]
    )


def _claimed_construct_from_card(path: Path) -> str:
    if not path.exists():
        return "user-provided local benchmark"
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip("# ").strip()
        if stripped:
            return stripped
    return "user-provided local benchmark"


def _slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")
    return slug or "quickstart_benchmark"
