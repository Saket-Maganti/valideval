from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from valideval.benchmarks.base import Benchmark, get_benchmark
from valideval.diagnostics import (
    AnswerDistributionDiagnostic,
    BaselineDiagnostic,
    CalibrationDiagnostic,
    ContaminationDiagnostic,
    CoverageDiagnostic,
    DataForensicsDiagnostic,
    DIFDiagnostic,
    DistractorQualityDiagnostic,
    ExtractionRobustnessDiagnostic,
    GoodhartDiagnostic,
    IRTDiagnostic,
    PowerDiagnostic,
    PredictiveDiagnostic,
    PromptSensitivityDiagnostic,
    RankingUncertaintyDiagnostic,
    RedundancyDiagnostic,
    ReliabilityDiagnostic,
    SaturationDiagnostic,
    ShortcutDiagnostic,
)
from valideval.domains.diagnostics import (
    AbstentionValidityDiagnostic,
    AgentValidityDiagnostic,
    CodeValidityDiagnostic,
    GraphFraudValidityDiagnostic,
    MedicalValidityDiagnostic,
    MultimodalValidityDiagnostic,
    RAGValidityDiagnostic,
    SafetyValidityDiagnostic,
)
from valideval.forensics.provenance import audit_manifest_hashes, stable_hash, write_manifest
from valideval.io.cache import (
    build_response_matrix,
    load_matrix,
    matrix_path,
    save_matrix,
    save_predictions,
)
from valideval.models.panel import ModelPanel, load_panel
from valideval.schemas import DiagnosticResult, ModelPrediction, ResponseMatrix, utc_now

DIAGNOSTICS = {
    "answer_distribution": AnswerDistributionDiagnostic,
    "baselines": BaselineDiagnostic,
    "shortcut": ShortcutDiagnostic,
    "irt": IRTDiagnostic,
    "reliability": ReliabilityDiagnostic,
    "saturation": SaturationDiagnostic,
    "power": PowerDiagnostic,
    "dif": DIFDiagnostic,
    "calibration": CalibrationDiagnostic,
    "redundancy": RedundancyDiagnostic,
    "ranking_uncertainty": RankingUncertaintyDiagnostic,
    "distractor_quality": DistractorQualityDiagnostic,
    "prompt_sensitivity": PromptSensitivityDiagnostic,
    "extraction_robustness": ExtractionRobustnessDiagnostic,
    "contamination": ContaminationDiagnostic,
    "data_forensics": DataForensicsDiagnostic,
    "coverage": CoverageDiagnostic,
    "predictive": PredictiveDiagnostic,
    "goodhart": GoodhartDiagnostic,
    "rag_validity": RAGValidityDiagnostic,
    "abstention_validity": AbstentionValidityDiagnostic,
    "agent_validity": AgentValidityDiagnostic,
    "code_validity": CodeValidityDiagnostic,
    "safety_validity": SafetyValidityDiagnostic,
    "medical_validity": MedicalValidityDiagnostic,
    "graph_fraud_validity": GraphFraudValidityDiagnostic,
    "multimodal_validity": MultimodalValidityDiagnostic,
}

LEGENDARY_DIAGNOSTICS = [
    "baselines",
    "answer_distribution",
    "distractor_quality",
    "shortcut",
    "prompt_sensitivity",
    "extraction_robustness",
    "data_forensics",
    "reliability",
    "irt",
    "saturation",
    "power",
    "dif",
    "calibration",
    "redundancy",
    "ranking_uncertainty",
    "contamination",
    "coverage",
    "predictive",
    "goodhart",
]

CORE_DIAGNOSTICS = [
    "baselines",
    "answer_distribution",
    "distractor_quality",
    "shortcut",
    "prompt_sensitivity",
    "extraction_robustness",
    "data_forensics",
    "reliability",
    "irt",
    "saturation",
    "power",
]

PSYCHOMETRIC_DIAGNOSTICS = [
    "irt",
    "saturation",
    "power",
    "dif",
    "calibration",
    "redundancy",
    "ranking_uncertainty",
]


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _benchmark_artifact_scope(benchmark: Benchmark) -> str | None:
    spec = getattr(benchmark, "construct_spec", None)
    metadata = getattr(spec, "metadata", {}) if spec is not None else {}
    if isinstance(metadata, Mapping):
        scope = metadata.get("artifact_scope")
        return str(scope) if scope else None
    return None


def _benchmark_prompt_template_hash(benchmark: Benchmark, variant: str) -> str | None:
    method = getattr(benchmark, "prompt_template_hash", None)
    if not callable(method):
        return None
    return str(method(variant))


class AuditRunner:
    def __init__(
        self,
        *,
        cache_root: str | Path = "cache",
        results_root: str | Path = "results",
        reportcards_root: str | Path = "reportcards",
        seed: int = 0,
    ):
        self.cache_root = Path(cache_root)
        self.results_root = Path(results_root)
        self.reportcards_root = Path(reportcards_root)
        self.seed = seed

    def load_benchmark(
        self, benchmark_id: str, *, local_path: str | Path | None = None
    ) -> Benchmark:
        return get_benchmark(benchmark_id, local_path=local_path)

    def load_panel(self, panel_id: str) -> ModelPanel:
        return load_panel(panel_id)

    def generate_predictions(
        self,
        benchmark: Benchmark,
        panel: ModelPanel,
        *,
        variant: str,
    ) -> list[ModelPrediction]:
        predictions: list[ModelPrediction] = []
        items = benchmark.load_items()
        for model in panel.models:
            for item in items:
                prompt = benchmark.render_prompt(item, variant=variant)
                output = model.generate(prompt, seed=self.seed)
                score = benchmark.score_prediction(item, output.prediction)
                artifact_scope = _benchmark_artifact_scope(benchmark)
                prompt_template_hash = _benchmark_prompt_template_hash(benchmark, variant)
                metadata = {
                    **output.metadata,
                    "normalized_prediction": score.normalized_prediction,
                    "normalized_answer": score.normalized_answer,
                    "prompt_hash": stable_hash(
                        {
                            "benchmark_id": benchmark.benchmark_id,
                            "variant": variant,
                            "prompt": prompt,
                        }
                    ),
                }
                if artifact_scope:
                    metadata["artifact_scope"] = artifact_scope
                if prompt_template_hash:
                    metadata["prompt_template_hash"] = prompt_template_hash
                predictions.append(
                    ModelPrediction(
                        model_id=model.model_id,
                        item_id=item.item_id,
                        prompt_variant=variant,
                        prediction=output.prediction,
                        score=score.score,
                        is_correct=score.is_correct,
                        logprob=None,
                        raw_output=output.raw_output,
                        metadata=metadata,
                    )
                )
        return predictions

    def build_matrices(
        self,
        benchmark: Benchmark,
        panel: ModelPanel,
        *,
        variants: list[str] | None = None,
        overwrite: bool = True,
    ) -> dict[str, ResponseMatrix]:
        selected_variants = variants or benchmark.available_prompt_variants()
        matrices: dict[str, ResponseMatrix] = {}
        for variant in selected_variants:
            path = matrix_path(self.cache_root, benchmark.benchmark_id, panel.panel_id, variant)
            if path.exists() and not overwrite:
                matrices[variant] = load_matrix(
                    self.cache_root,
                    benchmark.benchmark_id,
                    panel.panel_id,
                    variant,
                )
                continue
            predictions = self.generate_predictions(benchmark, panel, variant=variant)
            save_predictions(
                self.cache_root,
                benchmark.benchmark_id,
                panel.panel_id,
                variant,
                predictions,
            )
            matrix = build_response_matrix(
                predictions,
                benchmark_id=benchmark.benchmark_id,
                panel_id=panel.panel_id,
                variant=variant,
                scoring_method="mcq",
                seed=self.seed,
            )
            artifact_scope = _benchmark_artifact_scope(benchmark)
            if artifact_scope:
                matrix.metadata["artifact_scope"] = artifact_scope
                matrix.metadata.setdefault("limitations", []).append(
                    f"Artifact scope: {artifact_scope}."
                )
            save_matrix(self.cache_root, benchmark.benchmark_id, panel.panel_id, variant, matrix)
            matrices[variant] = matrix
        return matrices

    def ensure_matrices(
        self,
        benchmark: Benchmark,
        panel: ModelPanel,
        *,
        variants: list[str] | None = None,
        from_cache_only: bool = False,
    ) -> dict[str, ResponseMatrix]:
        selected_variants = variants or benchmark.available_prompt_variants()
        missing = [
            variant
            for variant in selected_variants
            if not matrix_path(
                self.cache_root, benchmark.benchmark_id, panel.panel_id, variant
            ).exists()
        ]
        if missing:
            if from_cache_only:
                raise ValueError(
                    "Missing cached response matrices for variants: "
                    f"{', '.join(missing)}. Build/import matrices before running --from-cache."
                )
            self.build_matrices(benchmark, panel, variants=missing, overwrite=True)
        return {
            variant: load_matrix(self.cache_root, benchmark.benchmark_id, panel.panel_id, variant)
            for variant in selected_variants
        }

    def run_diagnostics(
        self,
        benchmark: Benchmark,
        panel: ModelPanel,
        *,
        diagnostics: list[str],
        config: dict[str, Any] | None = None,
        from_cache_only: bool = False,
    ) -> list[DiagnosticResult]:
        cfg = config or {}
        primary_full_variant = str(
            cfg.get("amended_primary_full_variant") or cfg.get("primary_full_variant") or "full"
        )
        diagnostics = [
            expanded
            for name in diagnostics
            for expanded in (
                CORE_DIAGNOSTICS
                if name == "all-core"
                else PSYCHOMETRIC_DIAGNOSTICS
                if name == "psychometrics"
                else LEGENDARY_DIAGNOSTICS
                if name == "legendary"
                else [name]
            )
        ]
        required_variants = {primary_full_variant}
        if "shortcut" in diagnostics:
            required_variants.update(
                cfg.get(
                    "shortcut",
                    {},
                ).get(
                    "variants",
                    [
                        "question_only",
                        "choices_only",
                        "context_removed",
                        "context_shuffled",
                        "label_prior_only",
                        "metadata_only",
                        "answer_length_only",
                        "format_only",
                        "irrelevant_context",
                        "retrieval_only",
                    ],
                )
            )
        if "reliability" in diagnostics:
            required_variants.update(
                cfg.get("reliability", {}).get("variants", ["context_removed", "context_shuffled"])
            )
        if "prompt_sensitivity" in diagnostics:
            required_variants.update(
                cfg.get("prompt_sensitivity", {}).get(
                    "variants",
                    [
                        "zero_shot_direct",
                        "few_shot",
                        "chain_of_thought_allowed",
                        "direct_answer_only",
                        "json_only",
                        "answer_letter_only",
                        "randomized_option_order",
                        "alternate_system_prompt",
                        "no_system_prompt",
                        "terse_instructions",
                        "verbose_instructions",
                    ],
                )
            )
        if "calibration" in diagnostics:
            required_variants.update(
                cfg.get("calibration", {}).get(
                    "variants",
                    [
                        "context_removed",
                        "context_shuffled",
                        "terse_instructions",
                        "verbose_instructions",
                    ],
                )
            )
        if "rag_validity" in diagnostics:
            required_variants.update(
                cfg.get("rag_validity", {}).get(
                    "variants",
                    [
                        "context_removed",
                        "context_shuffled",
                        "irrelevant_context",
                        "question_only",
                    ],
                )
            )
        if "abstention_validity" in diagnostics:
            required_variants.update(
                cfg.get("abstention_validity", {}).get(
                    "variants",
                    ["context_removed", "context_shuffled", "terse_instructions"],
                )
            )
        available_variants = set(benchmark.available_prompt_variants())
        if callable(getattr(benchmark, "render_prompt", None)):
            # YAML-backed exploratory/amended GPQA variants can be rendered even when
            # they are intentionally omitted from the primary variant list.
            available_variants.update(required_variants)
        valid_variants = [variant for variant in required_variants if variant in available_variants]
        matrices = self.ensure_matrices(
            benchmark,
            panel,
            variants=valid_variants,
            from_cache_only=from_cache_only,
        )
        diagnostic_matrices = dict(matrices)
        if primary_full_variant != "full" and primary_full_variant in diagnostic_matrices:
            diagnostic_matrices.setdefault("full", diagnostic_matrices[primary_full_variant])

        results: list[DiagnosticResult] = []
        for name in diagnostics:
            if name not in DIAGNOSTICS:
                raise ValueError(f"Unknown diagnostic: {name}")
            diagnostic = DIAGNOSTICS[name]()
            diagnostic_config = {
                **cfg.get(name, {}),
                "cache_root": str(self.cache_root),
                "results_root": str(self.results_root),
                "output_dir": str(self.results_root / benchmark.benchmark_id / panel.panel_id),
                "panel_id": panel.panel_id,
                "seed": self.seed,
                "primary_full_variant": primary_full_variant,
            }
            result = diagnostic.run(benchmark, diagnostic_matrices, config=diagnostic_config)
            artifact_scope = _benchmark_artifact_scope(benchmark)
            audit_metadata = cfg.get("_audit_metadata", {})
            if isinstance(audit_metadata, Mapping):
                artifact_scope = str(audit_metadata.get("artifact_scope") or artifact_scope or "")
                audit_mode = audit_metadata.get("audit_mode")
            else:
                audit_mode = None
            if artifact_scope:
                result.summary_metrics.setdefault("artifact_scope", artifact_scope)
                result.limitations.append(f"Artifact scope: {artifact_scope}.")
            if audit_mode:
                result.summary_metrics.setdefault("audit_mode", str(audit_mode))
            result.summary_metrics.setdefault("primary_full_variant", primary_full_variant)
            self.save_diagnostic_result(panel.panel_id, result)
            results.append(result)
        self.write_audit_manifest(
            benchmark,
            panel,
            diagnostics_run=[result.diagnostic_name for result in results],
            diagnostic_config=cfg,
        )
        return results

    def save_diagnostic_result(self, panel_id: str, result: DiagnosticResult) -> Path:
        output_dir = self.results_root / result.benchmark_id / panel_id
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{result.diagnostic_name}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(
                _json_safe(result.model_dump(mode="json")),
                handle,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        return path

    def load_diagnostic_results(self, benchmark_id: str, panel_id: str) -> list[DiagnosticResult]:
        directory = self.results_root / benchmark_id / panel_id
        if not directory.exists():
            return []
        results = []
        for path in sorted(directory.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if "diagnostic_name" not in payload or "version" not in payload:
                continue
            results.append(DiagnosticResult(**payload))
        return results

    def write_audit_manifest(
        self,
        benchmark: Benchmark,
        panel: ModelPanel,
        *,
        diagnostics_run: list[str],
        diagnostic_config: dict[str, Any],
    ) -> Path:
        benchmark_config = {
            "benchmark_id": benchmark.benchmark_id,
            "claimed_construct": benchmark.claimed_construct,
            "prompt_variants": benchmark.available_prompt_variants(),
        }
        hashes = audit_manifest_hashes(
            benchmark,
            benchmark_config=benchmark_config,
            diagnostic_config=diagnostic_config,
        )
        result_paths = [
            str(self.results_root / benchmark.benchmark_id / panel.panel_id / f"{name}.json")
            for name in diagnostics_run
        ]
        payload = {
            "schema_version": "0.1",
            "created_at": utc_now(),
            "benchmark_id": benchmark.benchmark_id,
            "panel_id": panel.panel_id,
            "diagnostics_run": diagnostics_run,
            "result_paths": result_paths,
            "cache_root": str(self.cache_root),
            "results_root": str(self.results_root),
            "artifact_scope": _benchmark_artifact_scope(benchmark),
            "audit_mode": diagnostic_config.get("_audit_metadata", {}).get("audit_mode")
            if isinstance(diagnostic_config.get("_audit_metadata"), dict)
            else None,
            **hashes,
        }
        return write_manifest(self.results_root / benchmark.benchmark_id / "manifest.json", payload)

    def render_report(self, benchmark: Benchmark, panel: ModelPanel) -> Path:
        from valideval.audit.report_card import render_report_card, render_report_card_manifest
        from valideval.report.figures import write_diagnostic_figures

        results = self.load_diagnostic_results(benchmark.benchmark_id, panel.panel_id)
        if not results:
            raise ValueError(
                "No diagnostic results found. Run `python3 -m valideval audit ...` before report."
            )
        figure_paths = write_diagnostic_figures(
            results,
            self.reportcards_root / "figures",
            benchmark_id=benchmark.benchmark_id,
            panel_id=panel.panel_id,
        )
        markdown = render_report_card(
            benchmark,
            panel.panel_id,
            results,
            artifacts_dir=self.results_root / benchmark.benchmark_id / panel.panel_id,
            figure_paths=figure_paths,
        )
        self.reportcards_root.mkdir(parents=True, exist_ok=True)
        path = self.reportcards_root / f"{benchmark.benchmark_id}_{panel.panel_id}.md"
        path.write_text(markdown, encoding="utf-8")
        result_paths = [
            str(
                self.results_root
                / benchmark.benchmark_id
                / panel.panel_id
                / f"{result.diagnostic_name}.json"
            )
            for result in results
        ]
        manifest = render_report_card_manifest(
            benchmark,
            panel.panel_id,
            results,
            report_path=str(path),
            result_paths=result_paths,
        )
        manifest_path = path.with_suffix(".manifest.json")
        with manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest.model_dump(mode="json"), handle, indent=2, sort_keys=True)
        return path
