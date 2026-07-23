from __future__ import annotations

from pathlib import Path

from valideval.audit.runner import AuditRunner
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.diagnostics.data_forensics import DataForensicsDiagnostic
from valideval.forensics.duplicates import internal_duplicate_report
from valideval.forensics.overlap import scan_corpus_overlap
from valideval.forensics.provenance import (
    audit_manifest_hashes,
    item_text,
    provenance_completeness,
)
from valideval.forensics.split_leakage import split_leakage_report
from valideval.forensics.temporal import temporal_validity_report
from valideval.models.panel import load_panel
from valideval.schemas import BenchmarkItem, ConstructSpec, ResponseMatrix, ScoreResult


class MiniBenchmark:
    benchmark_id = "mini_forensics"
    claimed_construct = "unit-test construct"
    construct_spec = ConstructSpec(claimed_construct=claimed_construct)

    def __init__(self, items: list[BenchmarkItem]):
        self.items = items

    def load_items(self) -> list[BenchmarkItem]:
        return self.items

    def render_prompt(self, item: BenchmarkItem, variant: str = "full") -> str:
        return item.prompt

    def score_prediction(self, item: BenchmarkItem, prediction: str) -> ScoreResult:
        return ScoreResult(score=1.0 if prediction == item.answer else 0.0)

    def available_prompt_variants(self) -> list[str]:
        return ["full"]


def _item(
    item_id: str,
    prompt: str,
    *,
    answer: str = "A",
    context: str | None = None,
    split: str | None = None,
    source_document: str | None = None,
) -> BenchmarkItem:
    metadata = {}
    if split:
        metadata["split"] = split
    return BenchmarkItem(
        item_id=item_id,
        prompt=prompt,
        answer=answer,
        choices=["A. alpha", "B. beta", "C. gamma", "D. delta"],
        context=context,
        source_document=source_document,
        metadata=metadata,
    )


def test_forensics_overlap_detects_exact_local_corpus_match(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    item = benchmark.load_items()[0]
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "doc.txt").write_text(item_text(item), encoding="utf-8")

    result = scan_corpus_overlap(benchmark, corpus)

    metrics = result["metrics"]
    assert result["status"] == "measured"
    assert metrics["exact_match_rate"] > 0
    assert metrics["question_match_rate"] > 0
    assert metrics["per_item"][item.item_id]["exact_match"] is True
    assert metrics["per_item"][item.item_id]["top_matching_doc"]["path"].endswith("doc.txt")


def test_internal_duplicate_report_detects_duplicate_clusters_and_near_duplicates():
    items = [
        _item("train_1", "How many tokens does Mira have after adding the two piles?"),
        _item("train_2", "How many tokens does Mira have after adding both piles?"),
        _item("train_3", "How many tokens does Mira have after adding the two piles?"),
        _item("train_4", "Which circuit component closed before the lamp turned on?"),
    ]

    result = internal_duplicate_report(items, near_duplicate_threshold=0.45)
    metrics = result["metrics"]

    assert result["status"] == "measured"
    assert metrics["duplicate_fraction"] > 0
    assert any(
        {"train_1", "train_3"} <= set(cluster)
        for cluster in metrics["duplicate_clusters"]["exact_prompt"]
    )
    assert metrics["duplicate_clusters"]["near_duplicate"]
    assert metrics["effective_independent_item_count"] < len(items)


def test_split_leakage_report_detects_train_test_overlap():
    train = _item(
        "train_1",
        "Which source states the clinic was funded?",
        split="train",
        source_document="paper-a",
    )
    test = _item(
        "test_1",
        "Which source states the clinic was funded?",
        split="test",
        source_document="paper-a",
    )
    clean = _item("test_2", "Which material conducted electricity?", split="test")

    result = split_leakage_report([train, test, clean])
    matrix = result["metrics"]["leakage_matrix"]["test__vs__train"]

    assert result["status"] == "measured"
    assert ["test_1", "train_1"] in matrix["exact_overlap_pairs"]
    assert "test_1" in result["metrics"]["high_risk_item_list"]


def test_temporal_validity_warns_on_current_phrasing_and_missing_verification():
    item = _item("temporal_1", "Who is the current chair of the committee?")
    item.metadata["time_sensitive"] = True

    result = temporal_validity_report([item])
    per_item = result["metrics"]["per_item"]["temporal_1"]

    assert result["status"] == "measured"
    assert result["risk_level"] == "high local evidence"
    assert per_item["has_relative_or_current_phrasing"] is True
    assert per_item["stale_label_risk"] is True
    assert per_item["web_verification"]["status"] == "unavailable"


def test_provenance_completeness_reports_missing_fields_and_hashes_are_deterministic():
    item = _item("p1", "Which answer is supported by the passage?")
    benchmark = MiniBenchmark([item])

    provenance = provenance_completeness([item])
    first_hashes = audit_manifest_hashes(benchmark)
    second_hashes = audit_manifest_hashes(benchmark)
    changed_hashes = audit_manifest_hashes(
        MiniBenchmark([_item("p1", "Which answer is contradicted by the passage?")])
    )

    assert provenance["field_missing_counts"]["source_url"] == 1
    assert provenance["completeness_fraction"] == 0
    assert first_hashes == second_hashes
    assert first_hashes["item_text_hash"] != changed_hashes["item_text_hash"]
    assert first_hashes["dataset_id"] == "mini_forensics"


def test_data_forensics_diagnostic_runs_offline_with_empty_matrix(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "toy.md").write_text(item_text(benchmark.load_items()[0]), encoding="utf-8")

    result = DataForensicsDiagnostic().run(
        benchmark,
        ResponseMatrix(model_ids=[], item_ids=[], values=[]),
        config={"corpus_path": str(corpus)},
    )

    assert result.diagnostic_name == "data_forensics"
    assert result.summary_metrics["signals"]["corpus_overlap"]["status"] == "measured"
    assert "item_text_hash" in result.summary_metrics["hashes"]
    assert result.artifacts["manifest_hashes"]["dataset_id"] == "toy_mcq"


def test_audit_runner_writes_manifest_json(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    panel = load_panel("mock")
    runner = AuditRunner(cache_root=tmp_path / "cache", results_root=tmp_path / "results")

    runner.run_diagnostics(benchmark, panel, diagnostics=["data_forensics"], config={})

    manifest_path = tmp_path / "results" / "toy_mcq" / "manifest.json"
    assert manifest_path.exists()
    payload = manifest_path.read_text(encoding="utf-8")
    assert '"dataset_id": "toy_mcq"' in payload
    assert '"item_text_hash"' in payload
