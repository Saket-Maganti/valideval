from __future__ import annotations

import json
from pathlib import Path

from valideval.audit.report_card import render_report_card
from valideval.audit.runner import AuditRunner
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.cli import main
from valideval.domains import describe_domain_pack, get_domain_pack, list_domain_packs
from valideval.domains.diagnostics import AbstentionValidityDiagnostic, RAGValidityDiagnostic
from valideval.domains.schemas import (
    AbstentionMetadata,
    AgentTrace,
    CodeEvalMetadata,
    GraphFraudMetadata,
    MedicalSegmentationMetadata,
    MultimodalMetadata,
    RAGItemMetadata,
    SafetyMetadata,
)
from valideval.models.panel import load_panel


def test_domain_pack_registry_lists_and_describes_all_packs():
    packs = {pack.domain_id: pack for pack in list_domain_packs()}

    assert {
        "rag",
        "agent",
        "medical",
        "graph_fraud",
        "code",
        "safety",
        "multimodal",
        "abstention",
    } <= set(packs)
    assert "rag_validity" in packs["rag"].diagnostic_names
    assert "abstention_validity" in packs["abstention"].diagnostic_names
    assert "agent_validity" in packs["agent"].diagnostic_names
    assert "code_validity" in packs["code"].diagnostic_names
    assert "safety_validity" in packs["safety"].diagnostic_names
    assert "medical_validity" in packs["medical"].diagnostic_names
    assert "graph_fraud_validity" in packs["graph_fraud"].diagnostic_names
    assert "multimodal_validity" in packs["multimodal"].diagnostic_names

    description = describe_domain_pack("rag")
    assert description["domain_id"] == "rag"
    assert description["threat_library"]
    assert any(threat["name"] == "retrieval_leakage" for threat in description["threat_library"])


def test_domain_fixture_schemas_validate():
    root = Path("examples/domain_packs")

    assert RAGItemMetadata(**_first_jsonl(root / "rag_items.jsonl")).answerable is True
    assert AgentTrace(**_first_jsonl(root / "agent_traces.jsonl")).steps[0].action == "search"
    assert MedicalSegmentationMetadata(**_first_jsonl(root / "medical_items.jsonl")).site_id
    assert GraphFraudMetadata(**_first_jsonl(root / "graph_items.jsonl")).entity_id
    assert CodeEvalMetadata(**_first_jsonl(root / "code_items.jsonl")).hidden_test_count
    assert SafetyMetadata(**_first_jsonl(root / "safety_items.jsonl")).policy_version
    assert MultimodalMetadata(**_first_jsonl(root / "multimodal_items.jsonl")).modality
    assert AbstentionMetadata(**_first_jsonl(root / "abstention_items.jsonl")).abstention_allowed


def test_rag_and_abstention_diagnostics_work_offline(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    matrices = runner.build_matrices(
        benchmark,
        panel,
        variants=[
            "full",
            "context_removed",
            "context_shuffled",
            "irrelevant_context",
            "question_only",
            "terse_instructions",
        ],
    )

    rag = RAGValidityDiagnostic().run(benchmark, matrices)
    abstention = AbstentionValidityDiagnostic().run(
        benchmark,
        matrices,
        config={"cache_root": str(tmp_path / "cache"), "panel_id": "mock"},
    )

    assert rag.summary_metrics["domain_id"] == "rag"
    assert rag.summary_metrics["signals"]["context_removed"]["status"] == "measured"
    assert rag.summary_metrics["signals"]["support_span_coverage"]["status"] == "measured"
    assert rag.summary_metrics["signals"]["citation_checks"]["status"] == "unavailable"
    assert abstention.summary_metrics["domain_id"] == "abstention"
    assert abstention.summary_metrics["signals"]["coverage"]["status"] == "measured"
    assert (
        abstention.summary_metrics["signals"]["uncertainty_under_paraphrase"]["status"]
        == "measured"
    )


def test_audit_domain_cli_and_report_sections(tmp_path: Path):
    common = [
        "--benchmark",
        "toy_mcq",
        "--panel",
        "mock",
        "--cache-root",
        str(tmp_path / "cache"),
        "--results-root",
        str(tmp_path / "results"),
        "--reportcards-root",
        str(tmp_path / "reportcards"),
    ]

    assert main(["domain", "list"]) == 0
    assert main(["domain", "describe", "rag"]) == 0
    assert main(["audit", *common, "--domain", "rag"]) == 0
    assert main(["report", *common]) == 0

    audit_dir = tmp_path / "results" / "toy_mcq" / "mock"
    assert (audit_dir / "rag_validity.json").exists()
    assert (audit_dir / "abstention_validity.json").exists()
    report = (tmp_path / "reportcards" / "toy_mcq_mock.md").read_text(encoding="utf-8")
    assert "## Domain pack validity" in report
    assert "rag_validity" in report
    assert "abstention_validity" in report


def test_domain_report_renderer_includes_domain_results(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")
    matrices = runner.build_matrices(
        benchmark,
        panel,
        variants=["full", "context_removed", "context_shuffled", "irrelevant_context"],
    )
    result = RAGValidityDiagnostic().run(benchmark, matrices)

    report = render_report_card(benchmark, "mock", [result])

    assert "## Domain pack validity" in report
    assert "rag: rag_validity" in report
    assert "not a total validity score" in report


def test_scaffold_packs_have_threats_and_repair_policies():
    for domain_id in ["agent", "medical", "graph_fraud", "code", "safety", "multimodal"]:
        pack = get_domain_pack(domain_id)
        assert pack.threat_library
        assert pack.repair_policies
        assert pack.supported_item_types


def _first_jsonl(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])
