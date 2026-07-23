from __future__ import annotations

import json
from pathlib import Path

from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.repair.engine import (
    VALIDITY_CARD_SCHEMA,
    build_item_forensics_table,
    issue_certificate,
    render_checklist,
    render_evidence_matrix,
    render_validity_card,
    run_repair,
)
from valideval.repair.recommendations import (
    build_claim_evidence_matrix,
    generate_misuse_warnings,
)
from valideval.repair.subset_selection import select_subset
from valideval.schemas import DiagnosticResult, ResponseMatrix


def _toy_results() -> list[DiagnosticResult]:
    return [
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="irt",
            version="test",
            summary_metrics={
                "negative_discrimination_items": 1,
                "near_zero_discrimination_fraction": 0.2,
            },
            per_item_metrics={
                "toy_001": {
                    "difficulty": 0.0,
                    "discrimination": 0.7,
                    "negative_discrimination": False,
                    "too_easy": False,
                    "too_hard": False,
                },
                "toy_002": {
                    "difficulty": 1.0,
                    "discrimination": 0.0,
                    "negative_discrimination": False,
                    "too_easy": False,
                    "too_hard": True,
                },
                "toy_003": {
                    "difficulty": -1.0,
                    "discrimination": -0.2,
                    "negative_discrimination": True,
                    "too_easy": False,
                    "too_hard": False,
                },
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="shortcut",
            version="test",
            summary_metrics={"high_retention_variants": ["label_prior_only"]},
            per_item_metrics={
                "toy_001": {"suspiciousness": 0.1},
                "toy_002": {"suspiciousness": 0.8},
                "toy_003": {"suspiciousness": 0.2},
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="reliability",
            version="test",
            summary_metrics={"benchmark_level_reliability_estimate": 0.7},
            per_item_metrics={
                "toy_001": {"mean_item_stability": 0.9},
                "toy_002": {"mean_item_stability": 0.6},
                "toy_003": {"mean_item_stability": 0.95},
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="extraction_robustness",
            version="test",
            summary_metrics={"extraction_disagreement_rate": 0.03},
            per_item_metrics={
                "toy_001": {
                    "extractor_disagreement_rate": 0.0,
                    "scoring_ambiguity_flag": False,
                },
                "toy_002": {
                    "extractor_disagreement_rate": 0.3,
                    "scoring_ambiguity_flag": False,
                },
                "toy_003": {
                    "extractor_disagreement_rate": 0.0,
                    "scoring_ambiguity_flag": False,
                },
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="data_forensics",
            version="test",
            summary_metrics={
                "signals": {
                    "corpus_overlap": {
                        "status": "unavailable",
                        "risk_level": "unknown/unmeasured",
                        "metrics": {},
                    },
                    "internal_duplicates": {
                        "status": "measured",
                        "risk_level": "low local evidence",
                        "metrics": {
                            "duplicate_clusters": {"near_duplicate": [["toy_001", "toy_003"]]}
                        },
                    },
                    "temporal_validity": {
                        "status": "measured",
                        "risk_level": "no local evidence found",
                        "metrics": {},
                    },
                    "provenance_completeness": {
                        "status": "measured",
                        "risk_level": "high local evidence",
                        "metrics": {"completeness_fraction": 0.0},
                    },
                }
            },
            per_item_metrics={
                "toy_001": {
                    "corpus_overlap": {"risk_level": "no local evidence found"},
                    "temporal_validity": {"stale_label_risk": False},
                    "provenance_completeness": {"completeness_fraction": 0.5},
                },
                "toy_002": {
                    "corpus_overlap": {"risk_level": "high local evidence"},
                    "temporal_validity": {"stale_label_risk": True},
                    "provenance_completeness": {"completeness_fraction": 0.0},
                },
                "toy_003": {
                    "corpus_overlap": {"risk_level": "no local evidence found"},
                    "temporal_validity": {"stale_label_risk": False},
                    "provenance_completeness": {"completeness_fraction": 1.0},
                },
            },
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="power",
            version="test",
            summary_metrics={"do_not_overinterpret_within_points": 4.2},
        ),
        DiagnosticResult(
            benchmark_id="toy_mcq",
            diagnostic_name="saturation",
            version="test",
            summary_metrics={"saturation_category": "moderate"},
        ),
    ]


def _matrix() -> ResponseMatrix:
    item_ids = [item.item_id for item in ToyMCQBenchmark().load_items()]
    return ResponseMatrix(
        model_ids=["m1", "m2", "m3"],
        item_ids=item_ids,
        values=[
            [1 if index % 2 == 0 else 0 for index, _ in enumerate(item_ids)],
            [1 if index % 3 != 0 else 0 for index, _ in enumerate(item_ids)],
            [1 if index % 5 != 0 else 0 for index, _ in enumerate(item_ids)],
        ],
    )


def test_item_forensics_merge_and_recommendations():
    rows = build_item_forensics_table(ToyMCQBenchmark(), _toy_results())
    by_id = {row["item_id"]: row for row in rows}

    assert by_id["toy_001"]["difficulty"] == 0.0
    assert by_id["toy_001"]["duplicate_cluster"]
    assert by_id["toy_002"]["contamination_overlap"] == "high local evidence"
    assert by_id["toy_002"]["recommendation"] == "human validate"
    assert by_id["toy_003"]["negative_discrimination"] is True


def test_repair_policies_keep_coverage_critical_items():
    rows = build_item_forensics_table(ToyMCQBenchmark(), _toy_results())
    by_id = {row["item_id"]: row for row in rows}
    by_id["toy_002"]["coverage_tag"] = "unique_tag"
    by_id["toy_002"]["coverage_critical"] = True
    subset = select_subset(list(by_id.values()), policy_name="conservative")
    stable = select_subset(list(by_id.values()), policy_name="stable")

    assert "toy_002" in subset["selected_item_ids"]
    assert "toy_002" in subset["coverage_critical_overrides"]
    assert "toy_003" not in subset["selected_item_ids"]
    assert stable["policy"] == "stable"


def test_run_repair_writes_item_forensics_and_diff(tmp_path: Path):
    output = run_repair(
        ToyMCQBenchmark(),
        "mock",
        _toy_results(),
        _matrix(),
        output_dir=tmp_path,
        policy="conservative",
    )

    assert Path(output["item_forensics_csv"]).exists()
    assert Path(output["repair_report_md"]).exists()
    diff = json.loads(Path(output["repair_diff_json"]).read_text(encoding="utf-8"))
    assert diff["diff"]["ranking_fidelity"]["available"] is True
    assert diff["diff"]["removed_item_count"] >= 1


def test_validity_card_schema_and_certificate_outputs(tmp_path: Path):
    manifest = {"dataset_id": "toy_mcq", "item_count": 36, "item_text_hash": "abc"}
    card_paths = render_validity_card(
        ToyMCQBenchmark(),
        "mock",
        _toy_results(),
        output_dir=tmp_path,
        manifest=manifest,
    )
    cert_paths = issue_certificate(
        ToyMCQBenchmark(),
        "mock",
        _toy_results(),
        output_dir=tmp_path,
        manifest=manifest,
    )

    card = json.loads(Path(card_paths["validity_card_json"]).read_text(encoding="utf-8"))
    certificate = json.loads(
        Path(cert_paths["validity_certificate_json"]).read_text(encoding="utf-8")
    )
    for required in VALIDITY_CARD_SCHEMA["required"]:
        assert required in card
    assert card["version_hash"]["item_text_hash"] == "abc"
    assert certificate["profile_level"] == "core_diagnostics_recorded"
    assert certificate["ordinal_levels_disabled"] is True
    assert "not a validity score or quality grade" in certificate["interpretation"]
    assert certificate["dimension_statuses"]["reliability"] == "moderate"


def test_warnings_checklist_and_evidence_matrix(tmp_path: Path):
    benchmark = ToyMCQBenchmark()
    results = _toy_results()
    warnings = generate_misuse_warnings(benchmark, results)
    evidence = build_claim_evidence_matrix(benchmark, results)
    checklist_paths = render_checklist(benchmark, results, output_dir=tmp_path)
    evidence_paths = render_evidence_matrix(benchmark, "mock", results, output_dir=tmp_path)

    assert any("single scalar" in warning for warning in warnings)
    assert any(row["diagnostic"] == "data_forensics" for row in evidence)
    assert Path(checklist_paths["checklist_md"]).exists()
    assert Path(evidence_paths["evidence_matrix_csv"]).exists()
