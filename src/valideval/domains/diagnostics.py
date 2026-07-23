from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.io.cache import load_predictions, prediction_path
from valideval.psychometrics.calibration import abstention_report
from valideval.schemas import BenchmarkItem, DiagnosticResult, ModelPrediction
from valideval.scoring.extraction import invalid_output_detector, refusal_detector
from valideval.scoring.mcq_utils import accepted_labels, item_choice_map


class RAGValidityDiagnostic:
    name = "rag_validity"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        matrices = matrix_mapping(predictions)
        items = benchmark.load_items()
        signals = {
            "context_removed": _score_delta_signal(matrices, "context_removed"),
            "evidence_shuffled": _score_delta_signal(matrices, "context_shuffled"),
            "distractor_injected": _score_delta_signal(matrices, "irrelevant_context"),
            "support_span_coverage": _support_span_signal(items),
            "citation_checks": _citation_signal(items),
            "unanswerable_refusal_correctness": _unanswerable_signal(items),
            "context_reliance": _context_reliance_signal(matrices),
            "evidence_position_sensitivity": _evidence_position_signal(items, matrices),
        }
        per_item = {item.item_id: _rag_item_metrics(item) for item in items}
        warnings = [
            f"{name} is unavailable under this protocol."
            for name, value in signals.items()
            if value["status"] == "unavailable"
        ]
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "domain_id": "rag",
                "signals": signals,
                "measured_signal_count": sum(
                    1 for value in signals.values() if value["status"] == "measured"
                ),
                "unavailable_signal_count": sum(
                    1 for value in signals.values() if value["status"] == "unavailable"
                ),
                "interpretation": (
                    "RAG diagnostics are local evidence under the supplied contexts, "
                    "metadata, and cached perturbation matrices."
                ),
            },
            per_item_metrics=per_item,
            warnings=warnings,
            limitations=[
                "Lexical support and citation checks do not establish semantic faithfulness.",
                "Unavailable RAG signals should be reported as missing evidence, not as passing diagnostics.",
            ],
        )


class AbstentionValidityDiagnostic:
    name = "abstention_validity"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        cfg = dict(config or {})
        matrices = matrix_mapping(predictions)
        records = _load_full_predictions(benchmark.benchmark_id, cfg)
        report = abstention_report(records)
        confidence = _confidence_validity_signal(records)
        paraphrase = _uncertainty_under_paraphrase_signal(matrices)
        per_item = _abstention_per_item(records)
        signals = {
            "selective_risk": _metric_signal(report, "selective_risk"),
            "coverage": _metric_signal(report, "coverage"),
            "risk_coverage_auc": _metric_signal(report, "risk_coverage_auc"),
            "appropriate_abstention": _metric_signal(report, "appropriate_refusal_rate"),
            "inappropriate_refusal": _metric_signal(report, "inappropriate_refusal_rate"),
            "deferral_utility": _metric_signal(report, "deferral_utility"),
            "confidence_validity_correlation": confidence,
            "uncertainty_under_paraphrase": paraphrase,
        }
        warnings = []
        if not records:
            warnings.append(
                "No cached full-prompt predictions were available for abstention checks."
            )
        if confidence["status"] == "unavailable":
            warnings.append(
                "Confidence-validity correlation is unavailable without confidence/logprob metadata."
            )
        if paraphrase["status"] == "unavailable":
            warnings.append(
                "Uncertainty under paraphrase requires at least one non-full matrix variant."
            )
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "domain_id": "abstention",
                "signals": signals,
                "metrics": report,
                "interpretation": (
                    "Abstention diagnostics summarize refusal and invalid-output behavior under "
                    "this protocol; they do not certify deployment readiness."
                ),
            },
            per_item_metrics=per_item,
            warnings=warnings,
            limitations=[
                "Appropriate and inappropriate refusal rates depend on the benchmark scoring rule.",
                "Prompt-consistency uncertainty is a proxy signal, not calibrated confidence.",
            ],
        )


def _score_delta_signal(matrices: dict[str, Any], variant: str) -> dict[str, Any]:
    if "full" not in matrices or variant not in matrices:
        return {
            "status": "unavailable",
            "reason": f"Requires full and {variant} response matrices.",
        }
    full = matrices["full"].to_dataframe().astype(float)
    altered = matrices[variant].to_dataframe().astype(float).reindex_like(full)
    delta = float(full.values.mean() - altered.values.mean())
    return {
        "status": "measured",
        "variant": variant,
        "full_score": float(full.values.mean()),
        "variant_score": float(altered.values.mean()),
        "score_delta": delta,
        "risk_level": _delta_risk(delta),
    }


def _context_reliance_signal(matrices: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        _score_delta_signal(matrices, variant)
        for variant in ["context_removed", "question_only"]
        if variant in matrices
    ]
    measured = [candidate for candidate in candidates if candidate["status"] == "measured"]
    if not measured:
        return {
            "status": "unavailable",
            "reason": "Requires context_removed or question_only matrix.",
        }
    mean_delta = float(np.mean([item["score_delta"] for item in measured]))
    return {
        "status": "measured",
        "mean_context_reliance_delta": mean_delta,
        "signals_used": [item["variant"] for item in measured],
        "risk_level": _delta_risk(mean_delta),
    }


def _support_span_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    rows = [_rag_item_metrics(item) for item in items]
    supported = [
        row["answer_support_found"] for row in rows if row["answer_support_found"] is not None
    ]
    explicit = [row["support_span_count"] for row in rows if row["support_span_count"] > 0]
    if not supported and not explicit:
        return {
            "status": "unavailable",
            "reason": "Requires retrieved context or support-span metadata.",
        }
    coverage = float(np.mean([1.0 if value else 0.0 for value in supported])) if supported else 0.0
    return {
        "status": "measured",
        "answer_support_fraction": coverage,
        "items_with_support_spans": len(explicit),
        "items_checked": len(supported),
        "risk_level": "possible validity threat" if coverage < 0.5 else "low local evidence",
    }


def _citation_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    citation_rows = []
    for item in items:
        citations = item.metadata.get("citations", [])
        if not citations:
            continue
        context = _rag_context(item).lower()
        supported = [str(citation).lower() in context for citation in citations]
        citation_rows.append((item.item_id, citations, supported))
    if not citation_rows:
        return {"status": "unavailable", "reason": "Requires citation metadata."}
    total = sum(len(row[1]) for row in citation_rows)
    unsupported = sum(1 for _, _, supported in citation_rows for value in supported if not value)
    return {
        "status": "measured",
        "citation_count": total,
        "unsupported_citation_count": unsupported,
        "unsupported_citation_rate": unsupported / total if total else 0.0,
        "risk_level": "possible validity threat" if unsupported else "no local evidence found",
    }


def _unanswerable_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    unanswerable = [item for item in items if item.metadata.get("answerable") is False]
    if not unanswerable:
        return {"status": "unavailable", "reason": "Requires unanswerable item metadata."}
    refusals_expected = sum(
        1 for item in unanswerable if item.metadata.get("expected_refusal", True)
    )
    return {
        "status": "measured",
        "unanswerable_item_count": len(unanswerable),
        "expected_refusal_count": refusals_expected,
        "expected_refusal_fraction": refusals_expected / len(unanswerable),
    }


def _evidence_position_signal(
    items: list[BenchmarkItem], matrices: dict[str, Any]
) -> dict[str, Any]:
    positions = [
        item.metadata.get("evidence_position")
        for item in items
        if item.metadata.get("evidence_position")
    ]
    shuffled = _score_delta_signal(matrices, "context_shuffled")
    if not positions and shuffled["status"] != "measured":
        return {
            "status": "unavailable",
            "reason": "Requires evidence_position metadata or context_shuffled matrix.",
        }
    return {
        "status": "measured",
        "position_counts": {
            position: positions.count(position) for position in sorted(set(positions))
        },
        "shuffled_score_delta": shuffled.get("score_delta"),
        "risk_level": shuffled.get("risk_level", "unknown"),
    }


def _rag_item_metrics(item: BenchmarkItem) -> dict[str, Any]:
    context = _rag_context(item)
    answer_texts = _answer_texts(item)
    support_spans = [str(value) for value in item.metadata.get("support_spans", [])]
    answer_support = None
    if context:
        answer_support = any(text and text.lower() in context.lower() for text in answer_texts)
    return {
        "context_present": bool(context),
        "support_span_count": len(support_spans),
        "answer_support_found": answer_support,
        "citation_count": len(item.metadata.get("citations", [])),
        "answerable": item.metadata.get("answerable"),
        "evidence_position": item.metadata.get("evidence_position"),
    }


def _rag_context(item: BenchmarkItem) -> str:
    return str(item.metadata.get("retrieved_context") or item.context or "")


def _answer_texts(item: BenchmarkItem) -> list[str]:
    labels = set(accepted_labels(item))
    choices = item_choice_map(item)
    texts = [choices[label] for label in labels if label in choices]
    raw = item.answer if isinstance(item.answer, list) else [item.answer]
    texts.extend(str(value) for value in raw)
    return texts


def _delta_risk(delta: float) -> str:
    if delta >= 0.20:
        return "high local evidence"
    if delta >= 0.10:
        return "moderate local evidence"
    if delta >= 0.03:
        return "low local evidence"
    return "no local evidence found"


def _load_full_predictions(benchmark_id: str, cfg: dict[str, Any]) -> list[ModelPrediction]:
    cache_root = cfg.get("cache_root")
    panel_id = cfg.get("panel_id")
    if not cache_root or not panel_id:
        return []
    path = prediction_path(cache_root, benchmark_id, panel_id, "full")
    if not path.exists():
        return []
    return load_predictions(cache_root, benchmark_id, panel_id, "full")


def _metric_signal(report: dict[str, Any], key: str) -> dict[str, Any]:
    value = report.get(key)
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return {"status": "unavailable", "metric": key}
    return {"status": "measured", "metric": key, "value": float(value)}


def _confidence_validity_signal(records: list[ModelPrediction]) -> dict[str, Any]:
    pairs = []
    for record in records:
        confidence = record.metadata.get("confidence")
        if confidence is None and record.logprob is not None:
            confidence = math.exp(float(record.logprob))
        if confidence is not None:
            pairs.append((float(confidence), float(record.score)))
    if len(pairs) < 2:
        return {
            "status": "unavailable",
            "reason": "Requires at least two predictions with confidence or logprob metadata.",
        }
    confidences, scores = zip(*pairs, strict=True)
    corr = float(np.corrcoef(confidences, scores)[0, 1])
    return {"status": "measured", "correlation": corr, "n": len(pairs)}


def _uncertainty_under_paraphrase_signal(matrices: dict[str, Any]) -> dict[str, Any]:
    if "full" not in matrices:
        return {"status": "unavailable", "reason": "Requires full matrix."}
    full = matrices["full"].to_dataframe().astype(float)
    variant_frames = [
        matrix.to_dataframe().astype(float).reindex_like(full)
        for variant, matrix in matrices.items()
        if variant != "full"
    ]
    if not variant_frames:
        return {
            "status": "unavailable",
            "reason": "Requires non-full prompt or perturbation matrices.",
        }
    instability = []
    for frame in variant_frames:
        instability.extend((frame.values != full.values).astype(float).ravel().tolist())
    return {
        "status": "measured",
        "mean_prediction_instability": float(np.mean(instability)),
        "variant_count": len(variant_frames),
    }


def _abstention_per_item(records: list[ModelPrediction]) -> dict[str, Any]:
    grouped: dict[str, list[ModelPrediction]] = {}
    for record in records:
        grouped.setdefault(record.item_id, []).append(record)
    output = {}
    for item_id, values in grouped.items():
        abstentions = [
            refusal_detector(record.raw_output or record.prediction).refusal
            or invalid_output_detector(record.raw_output or record.prediction).invalid
            for record in values
        ]
        output[item_id] = {
            "coverage": 1.0 - (sum(abstentions) / len(abstentions)),
            "mean_score": float(np.mean([record.score for record in values])),
            "abstention_count": sum(abstentions),
        }
    return output


class AgentValidityDiagnostic:
    name = "agent_validity"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        items = benchmark.load_items()
        signals = {
            "trace_replay_completeness": _agent_trace_completeness(items),
            "state_hash_coverage": _agent_state_hash_signal(items),
            "reward_hacking_risk": _agent_reward_hacking_signal(items),
            "tool_schema_consistency": _agent_tool_schema_signal(items),
            "environment_seed_coverage": _agent_seed_signal(items),
        }
        warnings = [
            f"{name} is unavailable under this protocol."
            for name, value in signals.items()
            if value["status"] == "unavailable"
        ]
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "domain_id": "agent",
                "signals": signals,
                "interpretation": (
                    "Agent diagnostics summarize trace metadata under this protocol; "
                    "they do not certify deployment safety or task success."
                ),
            },
            per_item_metrics={item.item_id: _agent_item_metrics(item) for item in items},
            warnings=warnings,
            limitations=[
                "Trace replay requires complete step metadata and state hashes.",
                "Reward signals are local proxies and may not detect all hacking patterns.",
            ],
        )


class CodeValidityDiagnostic:
    name = "code_validity"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        items = benchmark.load_items()
        signals = {
            "hidden_test_strength": _code_hidden_test_signal(items),
            "flaky_test_risk": _code_flaky_test_signal(items),
            "dependency_lock_coverage": _code_dependency_lock_signal(items),
            "public_hidden_ratio": _code_test_ratio_signal(items),
            "language_coverage": _code_language_signal(items),
        }
        warnings = [
            f"{name} is unavailable under this protocol."
            for name, value in signals.items()
            if value["status"] == "unavailable"
        ]
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "domain_id": "code",
                "signals": signals,
                "interpretation": (
                    "Code diagnostics audit test-suite metadata and dependency signals; "
                    "they do not replace execution-based validation."
                ),
            },
            per_item_metrics={item.item_id: _code_item_metrics(item) for item in items},
            warnings=warnings,
            limitations=[
                "Hidden-test counts are metadata-only evidence.",
                "Flaky-test reruns require benchmark-author logging.",
            ],
        )


class SafetyValidityDiagnostic:
    name = "safety_validity"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        items = benchmark.load_items()
        matrices = matrix_mapping(predictions)
        signals = {
            "policy_version_consistency": _safety_policy_signal(items),
            "expected_refusal_coverage": _safety_refusal_metadata_signal(items),
            "adversarial_style_coverage": _safety_adversarial_signal(items),
            "rubric_version_consistency": _safety_rubric_signal(items),
            "refusal_calibration": _safety_refusal_calibration_signal(items, matrices),
        }
        warnings = [
            f"{name} is unavailable under this protocol."
            for name, value in signals.items()
            if value["status"] == "unavailable"
        ]
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "domain_id": "safety",
                "signals": signals,
                "interpretation": (
                    "Safety diagnostics summarize policy metadata and refusal behavior; "
                    "they do not certify deployment readiness."
                ),
            },
            per_item_metrics={item.item_id: _safety_item_metrics(item) for item in items},
            warnings=warnings,
            limitations=[
                "Policy-version metadata is necessary but not sufficient for safety claims.",
                "Refusal calibration depends on benchmark scoring rules and judge variants.",
            ],
        )


class MedicalValidityDiagnostic:
    name = "medical_validity"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        items = benchmark.load_items()
        signals = {
            "site_diversity": _medical_site_signal(items),
            "annotator_coverage": _medical_annotator_signal(items),
            "severity_coverage": _medical_severity_signal(items),
            "clinical_utility_weighting": _medical_utility_signal(items),
            "uncertainty_reporting": _medical_uncertainty_signal(items),
        }
        warnings = [
            f"{name} is unavailable under this protocol."
            for name, value in signals.items()
            if value["status"] == "unavailable"
        ]
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "domain_id": "medical",
                "signals": signals,
                "interpretation": (
                    "Medical diagnostics audit metadata coverage and site diversity; "
                    "they do not establish clinical utility or regulatory compliance."
                ),
            },
            per_item_metrics={item.item_id: _medical_item_metrics(item) for item in items},
            warnings=warnings,
            limitations=[
                "Clinical utility requires domain expert review beyond benchmark metadata.",
                "Site diversity signals depend on author-supplied site identifiers.",
            ],
        )


class GraphFraudValidityDiagnostic:
    name = "graph_fraud_validity"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        items = benchmark.load_items()
        signals = {
            "temporal_split_integrity": _graph_temporal_signal(items),
            "entity_overlap_risk": _graph_entity_overlap_signal(items),
            "degree_baseline_risk": _graph_degree_signal(items),
            "neighborhood_label_leakage": _graph_neighborhood_signal(items),
            "split_coverage": _graph_split_signal(items),
        }
        warnings = [
            f"{name} is unavailable under this protocol."
            for name, value in signals.items()
            if value["status"] == "unavailable"
        ]
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "domain_id": "graph_fraud",
                "signals": signals,
                "interpretation": (
                    "Graph/fraud diagnostics audit leakage and structure metadata; "
                    "they do not replace temporal holdout validation."
                ),
            },
            per_item_metrics={item.item_id: _graph_item_metrics(item) for item in items},
            warnings=warnings,
            limitations=[
                "Entity overlap signals are metadata-only under this protocol.",
                "Degree baselines require graph structure not always present in item metadata.",
            ],
        )


class MultimodalValidityDiagnostic:
    name = "multimodal_validity"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        items = benchmark.load_items()
        signals = {
            "modality_coverage": _multimodal_modality_signal(items),
            "text_only_fallback_metadata": _multimodal_text_only_signal(items),
            "ocr_leakage_risk": _multimodal_ocr_signal(items),
            "crop_sensitivity_metadata": _multimodal_crop_signal(items),
            "asset_path_completeness": _multimodal_asset_signal(items),
        }
        warnings = [
            f"{name} is unavailable under this protocol."
            for name, value in signals.items()
            if value["status"] == "unavailable"
        ]
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "domain_id": "multimodal",
                "signals": signals,
                "interpretation": (
                    "Multimodal diagnostics audit modality metadata and text-only fallback signals; "
                    "they do not replace modality-ablation experiments."
                ),
            },
            per_item_metrics={item.item_id: _multimodal_item_metrics(item) for item in items},
            warnings=warnings,
            limitations=[
                "OCR leakage checks are lexical proxies only.",
                "Modality-ablation requires cached perturbation matrices.",
            ],
        )


def _metadata_field(item: BenchmarkItem, key: str) -> Any:
    return item.metadata.get(key)


def _items_with_metadata(items: list[BenchmarkItem], key: str) -> list[BenchmarkItem]:
    return [item for item in items if _metadata_field(item, key) is not None]


def _agent_item_metrics(item: BenchmarkItem) -> dict[str, Any]:
    trace = item.metadata.get("agent_trace", {})
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    return {
        "step_count": len(steps),
        "has_state_hashes": all(step.get("state_hash") for step in steps) if steps else False,
        "environment_seed": trace.get("environment_seed") if isinstance(trace, dict) else None,
        "success": trace.get("success") if isinstance(trace, dict) else None,
    }


def _agent_trace_completeness(items: list[BenchmarkItem]) -> dict[str, Any]:
    traced = [item for item in items if item.metadata.get("agent_trace")]
    if not traced:
        return {"status": "unavailable", "reason": "Requires agent_trace metadata."}
    complete = sum(
        1
        for item in traced
        if _agent_item_metrics(item)["step_count"] > 0
        and _agent_item_metrics(item)["has_state_hashes"]
    )
    fraction = complete / len(traced)
    return {
        "status": "measured",
        "trace_complete_fraction": fraction,
        "items_with_traces": len(traced),
        "risk_level": "possible validity threat" if fraction < 0.8 else "low local evidence",
    }


def _agent_state_hash_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    traced = [item for item in items if item.metadata.get("agent_trace")]
    if not traced:
        return {"status": "unavailable", "reason": "Requires agent_trace metadata."}
    with_hashes = sum(1 for item in traced if _agent_item_metrics(item)["has_state_hashes"])
    fraction = with_hashes / len(traced)
    return {
        "status": "measured",
        "state_hash_fraction": fraction,
        "risk_level": "possible validity threat" if fraction < 0.9 else "low local evidence",
    }


def _agent_reward_hacking_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    rewards = []
    for item in items:
        trace = item.metadata.get("agent_trace", {})
        if not isinstance(trace, dict):
            continue
        for step in trace.get("steps", []):
            reward = step.get("reward")
            if reward is not None:
                rewards.append(float(reward))
    if not rewards:
        return {"status": "unavailable", "reason": "Requires step reward metadata."}
    high_reward_fraction = sum(1 for value in rewards if value >= 0.99) / len(rewards)
    return {
        "status": "measured",
        "high_reward_fraction": high_reward_fraction,
        "reward_count": len(rewards),
        "risk_level": "possible validity threat"
        if high_reward_fraction > 0.5
        else "low local evidence",
    }


def _agent_tool_schema_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    tool_calls = 0
    named_calls = 0
    for item in items:
        trace = item.metadata.get("agent_trace", {})
        if not isinstance(trace, dict):
            continue
        for step in trace.get("steps", []):
            tool_call = step.get("tool_call", {})
            if tool_call:
                tool_calls += 1
                if tool_call.get("name"):
                    named_calls += 1
    if not tool_calls:
        return {"status": "unavailable", "reason": "Requires tool_call metadata."}
    return {
        "status": "measured",
        "named_tool_call_fraction": named_calls / tool_calls,
        "tool_call_count": tool_calls,
        "risk_level": "low local evidence"
        if named_calls == tool_calls
        else "possible validity threat",
    }


def _agent_seed_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    seeds = [
        item.metadata.get("agent_trace", {}).get("environment_seed")
        for item in items
        if isinstance(item.metadata.get("agent_trace"), dict)
        and item.metadata["agent_trace"].get("environment_seed") is not None
    ]
    if not seeds:
        return {"status": "unavailable", "reason": "Requires environment_seed metadata."}
    return {
        "status": "measured",
        "unique_seed_count": len(set(seeds)),
        "items_with_seeds": len(seeds),
        "risk_level": "low local evidence",
    }


def _code_item_metrics(item: BenchmarkItem) -> dict[str, Any]:
    return {
        "hidden_test_count": _metadata_field(item, "hidden_test_count"),
        "public_test_count": _metadata_field(item, "public_test_count"),
        "flaky_rerun_count": _metadata_field(item, "flaky_rerun_count"),
        "package_lock_hash": _metadata_field(item, "package_lock_hash"),
        "language": _metadata_field(item, "language"),
    }


def _code_hidden_test_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    counts = [
        int(_metadata_field(item, "hidden_test_count"))
        for item in items
        if _metadata_field(item, "hidden_test_count") is not None
    ]
    if not counts:
        return {"status": "unavailable", "reason": "Requires hidden_test_count metadata."}
    weak = sum(1 for value in counts if value < 3)
    return {
        "status": "measured",
        "mean_hidden_tests": float(np.mean(counts)),
        "weak_hidden_test_fraction": weak / len(counts),
        "risk_level": "possible validity threat"
        if weak / len(counts) > 0.3
        else "low local evidence",
    }


def _code_flaky_test_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    counts = [
        int(_metadata_field(item, "flaky_rerun_count"))
        for item in items
        if _metadata_field(item, "flaky_rerun_count") is not None
    ]
    if not counts:
        return {"status": "unavailable", "reason": "Requires flaky_rerun_count metadata."}
    flaky = sum(1 for value in counts if value > 0)
    return {
        "status": "measured",
        "flaky_item_fraction": flaky / len(counts),
        "risk_level": "possible validity threat" if flaky else "no local evidence found",
    }


def _code_dependency_lock_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    locked = [item for item in items if _metadata_field(item, "package_lock_hash")]
    if not items:
        return {"status": "unavailable", "reason": "No items loaded."}
    if not locked:
        return {"status": "unavailable", "reason": "Requires package_lock_hash metadata."}
    return {
        "status": "measured",
        "lock_hash_fraction": len(locked) / len(items),
        "unique_lock_hashes": len({_metadata_field(item, "package_lock_hash") for item in locked}),
        "risk_level": "low local evidence"
        if len(locked) == len(items)
        else "possible validity threat",
    }


def _code_test_ratio_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    ratios = []
    for item in items:
        hidden = _metadata_field(item, "hidden_test_count")
        public = _metadata_field(item, "public_test_count")
        if hidden is not None and public is not None and public > 0:
            ratios.append(float(hidden) / float(public))
    if not ratios:
        return {"status": "unavailable", "reason": "Requires hidden and public test counts."}
    return {
        "status": "measured",
        "mean_hidden_public_ratio": float(np.mean(ratios)),
        "risk_level": "possible validity threat"
        if float(np.mean(ratios)) < 0.5
        else "low local evidence",
    }


def _code_language_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    languages = [
        _metadata_field(item, "language") for item in items if _metadata_field(item, "language")
    ]
    if not languages:
        return {"status": "unavailable", "reason": "Requires language metadata."}
    return {
        "status": "measured",
        "unique_languages": sorted(set(languages)),
        "language_count": len(set(languages)),
        "risk_level": "low local evidence",
    }


def _safety_item_metrics(item: BenchmarkItem) -> dict[str, Any]:
    return {
        "policy_version": _metadata_field(item, "policy_version"),
        "risk_category": _metadata_field(item, "risk_category"),
        "expected_refusal": _metadata_field(item, "expected_refusal"),
        "adversarial_style": _metadata_field(item, "adversarial_style"),
        "rubric_version": _metadata_field(item, "rubric_version"),
    }


def _safety_policy_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    versions = [
        _metadata_field(item, "policy_version")
        for item in items
        if _metadata_field(item, "policy_version")
    ]
    if not versions:
        return {"status": "unavailable", "reason": "Requires policy_version metadata."}
    return {
        "status": "measured",
        "unique_policy_versions": sorted(set(versions)),
        "policy_version_count": len(set(versions)),
        "risk_level": "possible validity threat"
        if len(set(versions)) > 1
        else "low local evidence",
    }


def _safety_refusal_metadata_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    labeled = [item for item in items if _metadata_field(item, "expected_refusal") is not None]
    if not labeled:
        return {"status": "unavailable", "reason": "Requires expected_refusal metadata."}
    refusal_expected = sum(1 for item in labeled if _metadata_field(item, "expected_refusal"))
    return {
        "status": "measured",
        "expected_refusal_fraction": refusal_expected / len(labeled),
        "labeled_item_count": len(labeled),
        "risk_level": "low local evidence",
    }


def _safety_adversarial_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    styles = [
        _metadata_field(item, "adversarial_style")
        for item in items
        if _metadata_field(item, "adversarial_style")
    ]
    if not styles:
        return {"status": "unavailable", "reason": "Requires adversarial_style metadata."}
    return {
        "status": "measured",
        "unique_adversarial_styles": sorted(set(styles)),
        "adversarial_item_count": len(styles),
        "risk_level": "low local evidence",
    }


def _safety_rubric_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    versions = [
        _metadata_field(item, "rubric_version")
        for item in items
        if _metadata_field(item, "rubric_version")
    ]
    if not versions:
        return {"status": "unavailable", "reason": "Requires rubric_version metadata."}
    return {
        "status": "measured",
        "unique_rubric_versions": sorted(set(versions)),
        "risk_level": "possible validity threat"
        if len(set(versions)) > 1
        else "low local evidence",
    }


def _safety_refusal_calibration_signal(
    items: list[BenchmarkItem], matrices: dict[str, Any]
) -> dict[str, Any]:
    labeled = [item for item in items if _metadata_field(item, "expected_refusal") is not None]
    if not labeled or "full" not in matrices:
        return {
            "status": "unavailable",
            "reason": "Requires expected_refusal metadata and full matrix.",
        }
    frame = matrices["full"].to_dataframe().astype(float)
    expected_refusal_ids = {
        item.item_id for item in labeled if _metadata_field(item, "expected_refusal")
    }
    if not expected_refusal_ids:
        return {"status": "unavailable", "reason": "No items marked with expected_refusal=true."}
    present = [item_id for item_id in expected_refusal_ids if item_id in frame.columns]
    if not present:
        return {"status": "unavailable", "reason": "Expected-refusal items missing from matrix."}
    mean_score_on_refusal_items = float(frame[present].mean().mean())
    return {
        "status": "measured",
        "expected_refusal_item_count": len(present),
        "mean_score_on_refusal_items": mean_score_on_refusal_items,
        "risk_level": (
            "possible validity threat"
            if mean_score_on_refusal_items > 0.3
            else "low local evidence"
        ),
    }


def _medical_item_metrics(item: BenchmarkItem) -> dict[str, Any]:
    return {
        "site_id": _metadata_field(item, "site_id"),
        "severity": _metadata_field(item, "severity"),
        "annotator_count": _metadata_field(item, "annotator_count"),
        "clinical_utility_weight": _metadata_field(item, "clinical_utility_weight"),
        "uncertainty_score": _metadata_field(item, "uncertainty_score"),
    }


def _medical_site_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    sites = [_metadata_field(item, "site_id") for item in items if _metadata_field(item, "site_id")]
    if not sites:
        return {"status": "unavailable", "reason": "Requires site_id metadata."}
    return {
        "status": "measured",
        "unique_site_count": len(set(sites)),
        "site_item_count": len(sites),
        "risk_level": "possible validity threat" if len(set(sites)) < 2 else "low local evidence",
    }


def _medical_annotator_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    counts = [
        int(_metadata_field(item, "annotator_count"))
        for item in items
        if _metadata_field(item, "annotator_count") is not None
    ]
    if not counts:
        return {"status": "unavailable", "reason": "Requires annotator_count metadata."}
    low = sum(1 for value in counts if value < 2)
    return {
        "status": "measured",
        "low_annotator_fraction": low / len(counts),
        "risk_level": "possible validity threat"
        if low / len(counts) > 0.3
        else "low local evidence",
    }


def _medical_severity_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    severities = [
        _metadata_field(item, "severity") for item in items if _metadata_field(item, "severity")
    ]
    if not severities:
        return {"status": "unavailable", "reason": "Requires severity metadata."}
    return {
        "status": "measured",
        "unique_severities": sorted(set(severities)),
        "severity_count": len(set(severities)),
        "risk_level": "low local evidence",
    }


def _medical_utility_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    weights = [
        float(_metadata_field(item, "clinical_utility_weight"))
        for item in items
        if _metadata_field(item, "clinical_utility_weight") is not None
    ]
    if not weights:
        return {"status": "unavailable", "reason": "Requires clinical_utility_weight metadata."}
    return {
        "status": "measured",
        "mean_utility_weight": float(np.mean(weights)),
        "weighted_item_count": len(weights),
        "risk_level": "low local evidence",
    }


def _medical_uncertainty_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    scores = [
        float(_metadata_field(item, "uncertainty_score"))
        for item in items
        if _metadata_field(item, "uncertainty_score") is not None
    ]
    if not scores:
        return {"status": "unavailable", "reason": "Requires uncertainty_score metadata."}
    return {
        "status": "measured",
        "mean_uncertainty": float(np.mean(scores)),
        "high_uncertainty_fraction": sum(1 for value in scores if value >= 0.7) / len(scores),
        "risk_level": "low local evidence",
    }


def _graph_item_metrics(item: BenchmarkItem) -> dict[str, Any]:
    return {
        "entity_id": _metadata_field(item, "entity_id"),
        "timestamp": _metadata_field(item, "timestamp"),
        "degree": _metadata_field(item, "degree"),
        "split": _metadata_field(item, "split"),
        "neighborhood_label_rate": _metadata_field(item, "neighborhood_label_rate"),
    }


def _graph_temporal_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    timestamps = [
        _metadata_field(item, "timestamp") for item in items if _metadata_field(item, "timestamp")
    ]
    if not timestamps:
        return {"status": "unavailable", "reason": "Requires timestamp metadata."}
    return {
        "status": "measured",
        "timestamped_item_count": len(timestamps),
        "unique_timestamps": len(set(timestamps)),
        "risk_level": "low local evidence",
    }


def _graph_entity_overlap_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    entities = [
        _metadata_field(item, "entity_id") for item in items if _metadata_field(item, "entity_id")
    ]
    if not entities:
        return {"status": "unavailable", "reason": "Requires entity_id metadata."}
    duplicate_entities = len(entities) - len(set(entities))
    return {
        "status": "measured",
        "duplicate_entity_count": duplicate_entities,
        "entity_overlap_fraction": duplicate_entities / len(entities) if entities else 0.0,
        "risk_level": "possible validity threat"
        if duplicate_entities
        else "no local evidence found",
    }


def _graph_degree_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    degrees = [
        int(_metadata_field(item, "degree"))
        for item in items
        if _metadata_field(item, "degree") is not None
    ]
    if not degrees:
        return {"status": "unavailable", "reason": "Requires degree metadata."}
    high_degree = sum(1 for value in degrees if value >= 100)
    return {
        "status": "measured",
        "high_degree_fraction": high_degree / len(degrees),
        "mean_degree": float(np.mean(degrees)),
        "risk_level": "possible validity threat"
        if high_degree / len(degrees) > 0.2
        else "low local evidence",
    }


def _graph_neighborhood_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    rates = [
        float(_metadata_field(item, "neighborhood_label_rate"))
        for item in items
        if _metadata_field(item, "neighborhood_label_rate") is not None
    ]
    if not rates:
        return {"status": "unavailable", "reason": "Requires neighborhood_label_rate metadata."}
    leaky = sum(1 for value in rates if value >= 0.9)
    return {
        "status": "measured",
        "high_neighborhood_label_fraction": leaky / len(rates),
        "risk_level": "possible validity threat" if leaky else "no local evidence found",
    }


def _graph_split_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    splits = [_metadata_field(item, "split") for item in items if _metadata_field(item, "split")]
    if not splits:
        return {"status": "unavailable", "reason": "Requires split metadata."}
    return {
        "status": "measured",
        "unique_splits": sorted(set(splits)),
        "split_item_count": len(splits),
        "risk_level": "low local evidence" if len(set(splits)) >= 2 else "possible validity threat",
    }


def _multimodal_item_metrics(item: BenchmarkItem) -> dict[str, Any]:
    return {
        "modality": _metadata_field(item, "modality"),
        "asset_path": _metadata_field(item, "asset_path"),
        "ocr_text": _metadata_field(item, "ocr_text"),
        "crop_id": _metadata_field(item, "crop_id"),
    }


def _multimodal_modality_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    modalities = [
        _metadata_field(item, "modality") for item in items if _metadata_field(item, "modality")
    ]
    if not modalities:
        return {"status": "unavailable", "reason": "Requires modality metadata."}
    return {
        "status": "measured",
        "unique_modalities": sorted(set(modalities)),
        "modality_count": len(set(modalities)),
        "risk_level": "low local evidence",
    }


def _multimodal_text_only_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    with_ocr = [item for item in items if _metadata_field(item, "ocr_text")]
    if not with_ocr:
        return {
            "status": "unavailable",
            "reason": "Requires ocr_text metadata for text-only fallback checks.",
        }
    return {
        "status": "measured",
        "ocr_coverage_fraction": len(with_ocr) / len(items),
        "risk_level": "low local evidence",
    }


def _multimodal_ocr_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    overlaps = []
    for item in items:
        ocr = str(_metadata_field(item, "ocr_text") or "")
        answer = str(item.answer)
        if ocr and answer and answer.lower() in ocr.lower():
            overlaps.append(item.item_id)
    if not items:
        return {"status": "unavailable", "reason": "No items loaded."}
    if not any(_metadata_field(item, "ocr_text") for item in items):
        return {"status": "unavailable", "reason": "Requires ocr_text metadata."}
    return {
        "status": "measured",
        "ocr_answer_overlap_count": len(overlaps),
        "risk_level": "possible validity threat" if overlaps else "no local evidence found",
    }


def _multimodal_crop_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    crops = [_metadata_field(item, "crop_id") for item in items if _metadata_field(item, "crop_id")]
    if not crops:
        return {"status": "unavailable", "reason": "Requires crop_id metadata."}
    return {
        "status": "measured",
        "unique_crop_count": len(set(crops)),
        "crop_item_count": len(crops),
        "risk_level": "low local evidence",
    }


def _multimodal_asset_signal(items: list[BenchmarkItem]) -> dict[str, Any]:
    assets = [
        _metadata_field(item, "asset_path") for item in items if _metadata_field(item, "asset_path")
    ]
    if not assets:
        return {"status": "unavailable", "reason": "Requires asset_path metadata."}
    return {
        "status": "measured",
        "asset_coverage_fraction": len(assets) / len(items),
        "risk_level": "low local evidence"
        if len(assets) == len(items)
        else "possible validity threat",
    }
