from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from valideval.domains.base import (
    DiagnosticFactory,
    DomainPack,
    RepairPolicy,
    ThreatSpec,
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
from valideval.schemas import DiagnosticResult


def list_domain_packs() -> list[DomainPack]:
    return [get_domain_pack(domain_id) for domain_id in sorted(_PACK_DEFINITIONS)]


def get_domain_pack(domain_id: str) -> DomainPack:
    if domain_id not in _PACK_DEFINITIONS:
        raise ValueError(f"Unknown domain pack: {domain_id}")
    definition = _PACK_DEFINITIONS[domain_id]
    threats = [threat for threat in load_threat_specs() if threat.domain == domain_id]
    return DomainPack(
        domain_id=domain_id,
        description=definition["description"],
        supported_item_types=list(definition["supported_item_types"]),
        threat_library=threats,
        diagnostics=list(definition["diagnostics"]),
        report_sections=[render_domain_report_section],
        repair_policies=list(definition["repair_policies"]),
    )


def domain_diagnostic_names(domain_id: str) -> list[str]:
    return get_domain_pack(domain_id).diagnostic_names


def all_domain_diagnostic_names() -> set[str]:
    names: set[str] = set()
    for pack in list_domain_packs():
        names.update(pack.diagnostic_names)
    return names


def describe_domain_pack(domain_id: str) -> dict[str, object]:
    return get_domain_pack(domain_id).to_json_dict()


@lru_cache(maxsize=1)
def load_threat_specs() -> list[ThreatSpec]:
    path = Path(__file__).with_name("threats.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [ThreatSpec.from_dict(item) for item in payload]


def render_domain_report_section(results: list[DiagnosticResult]) -> str:
    domain_results = [
        result
        for result in results
        if result.summary_metrics.get("domain_id")
        or result.diagnostic_name in all_domain_diagnostic_names()
    ]
    if not domain_results:
        return ""
    lines = ["## Domain pack validity", ""]
    for result in domain_results:
        domain_id = result.summary_metrics.get("domain_id", "unknown")
        lines.append(f"### {domain_id}: {result.diagnostic_name}")
        interpretation = result.summary_metrics.get("interpretation")
        if interpretation:
            lines.append(f"- Interpretation: {interpretation}")
        signals = result.summary_metrics.get("signals", {})
        if signals:
            for name, signal in signals.items():
                status = signal.get("status", "n/a") if isinstance(signal, dict) else "n/a"
                detail = _signal_detail(signal) if isinstance(signal, dict) else ""
                lines.append(f"- {name}: {status}{detail}")
        else:
            lines.append("- No domain-pack signals were recorded.")
        if result.warnings:
            lines.append(f"- Warnings: {len(result.warnings)}")
        lines.append("")
    lines.append(
        "Domain-pack sections are conditional evidence under their local schemas and metadata; "
        "they are not a total validity score."
    )
    lines.append("")
    return "\n".join(lines)


def _signal_detail(signal: dict[str, object]) -> str:
    if "score_delta" in signal:
        return f", score delta={float(signal['score_delta']):.3f}"
    if "value" in signal:
        return f", value={float(signal['value']):.3f}"
    if "answer_support_fraction" in signal:
        return f", support fraction={float(signal['answer_support_fraction']):.3f}"
    if "mean_prediction_instability" in signal:
        return f", instability={float(signal['mean_prediction_instability']):.3f}"
    return ""


def _policy(policy_id: str, description: str, actions: list[str]) -> RepairPolicy:
    return RepairPolicy(policy_id=policy_id, description=description, actions=actions)


_PACK_DEFINITIONS = {
    "abstention": {
        "description": "Cross-domain selective prediction, refusal, and deferral validity pack.",
        "supported_item_types": ["mcq", "open_ended", "rag", "safety", "medical"],
        "diagnostics": [
            DiagnosticFactory(
                "abstention_validity",
                "Selective risk, coverage, refusal correctness, uncertainty, and deferral utility.",
                AbstentionValidityDiagnostic,
            )
        ],
        "repair_policies": [
            _policy(
                "review_inappropriate_refusals",
                "Review high-confidence refusals and answered high-risk errors separately.",
                ["human validate", "calibrate deferral threshold", "report risk-coverage"],
            )
        ],
    },
    "agent": {
        "description": "Agent trace, tool-call, environment, and reward validity scaffold.",
        "supported_item_types": ["agent_trace", "tool_task"],
        "diagnostics": [
            DiagnosticFactory(
                "agent_validity",
                "Trace replay completeness, state hashes, reward hacking, and tool schema checks.",
                AgentValidityDiagnostic,
            )
        ],
        "repair_policies": [
            _policy(
                "trace_replay_review",
                "Require replayable traces with state hashes before interpreting agent success.",
                ["record trace", "validate tool schema", "review reward hacking risk"],
            )
        ],
    },
    "code": {
        "description": "Code benchmark validity scaffold for hidden tests, overlap, pass@k, and dependencies.",
        "supported_item_types": ["code_task", "unit_test_task"],
        "diagnostics": [
            DiagnosticFactory(
                "code_validity",
                "Hidden-test strength, flaky tests, dependency locks, and language coverage.",
                CodeValidityDiagnostic,
            )
        ],
        "repair_policies": [
            _policy(
                "strengthen_hidden_tests",
                "Flag weak or flaky tests before interpreting pass rates.",
                ["increase hidden tests", "rerun flaky tests", "lock dependencies"],
            )
        ],
    },
    "graph_fraud": {
        "description": "Graph and fraud validity scaffold for leakage, structure shortcuts, and imbalance.",
        "supported_item_types": ["node_classification", "edge_classification", "fraud_ranking"],
        "diagnostics": [
            DiagnosticFactory(
                "graph_fraud_validity",
                "Temporal splits, entity overlap, degree baselines, and neighborhood leakage.",
                GraphFraudValidityDiagnostic,
            )
        ],
        "repair_policies": [
            _policy(
                "temporal_split_review",
                "Review entity overlap and temporal integrity before interpreting graph scores.",
                ["enforce temporal split", "run degree baseline", "report precision@k"],
            )
        ],
    },
    "medical": {
        "description": "Medical and segmentation validity scaffold for ambiguity, site shift, and utility.",
        "supported_item_types": ["segmentation", "clinical_classification"],
        "diagnostics": [
            DiagnosticFactory(
                "medical_validity",
                "Site diversity, annotator coverage, severity balance, and clinical utility metadata.",
                MedicalValidityDiagnostic,
            )
        ],
        "repair_policies": [
            _policy(
                "clinical_utility_review",
                "Separate metric gains from clinically meaningful utility before score claims.",
                ["site-stratify", "severity-weight", "adjudicate ambiguous labels"],
            )
        ],
    },
    "multimodal": {
        "description": "Optional multimodal scaffold for image, OCR, chart, video, and audio tasks.",
        "supported_item_types": ["image_qa", "ocr", "chart_qa", "medical_image", "video", "audio"],
        "diagnostics": [
            DiagnosticFactory(
                "multimodal_validity",
                "Modality coverage, OCR leakage, crop sensitivity, and asset completeness.",
                MultimodalValidityDiagnostic,
            )
        ],
        "repair_policies": [
            _policy(
                "modality_ablation_review",
                "Report text-only and modality-removed baselines before multimodal claims.",
                ["run text-only baseline", "check OCR leakage", "report crop sensitivity"],
            )
        ],
    },
    "rag": {
        "description": "Retrieval-augmented generation validity pack for context, evidence, citations, and abstention.",
        "supported_item_types": ["rag_qa", "open_ended_qa", "mcq_with_context"],
        "diagnostics": [
            DiagnosticFactory(
                "rag_validity",
                "Context reliance, support span, citation, unanswerable, and evidence-position diagnostics.",
                RAGValidityDiagnostic,
            ),
            DiagnosticFactory(
                "abstention_validity",
                "Abstention calibration signals for answerable and unanswerable cases.",
                AbstentionValidityDiagnostic,
            ),
        ],
        "repair_policies": [
            _policy(
                "evidence_support_review",
                "Review unsupported answers, citations, and context-sensitive failures.",
                ["add support spans", "remove leaked context", "balance answerability"],
            )
        ],
    },
    "safety": {
        "description": "Safety benchmark validity scaffold for policy versions, refusal, judges, and adversarial phrasing.",
        "supported_item_types": ["single_turn_safety", "multi_turn_safety"],
        "diagnostics": [
            DiagnosticFactory(
                "safety_validity",
                "Policy versions, expected refusal metadata, adversarial coverage, and calibration.",
                SafetyValidityDiagnostic,
            )
        ],
        "repair_policies": [
            _policy(
                "policy_version_review",
                "Require policy metadata and judge sensitivity before safety claims.",
                ["version policy", "adjudicate rubric ambiguity", "report refusal calibration"],
            )
        ],
    },
}
