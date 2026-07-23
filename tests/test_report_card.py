from valideval.audit.report_card import render_report_card, render_report_card_manifest
from valideval.benchmarks.toy import ToyMCQBenchmark
from valideval.schemas import DiagnosticResult


def test_report_card_renders_multidimensional_language():
    benchmark = ToyMCQBenchmark()
    result = DiagnosticResult(
        benchmark_id="toy_mcq",
        diagnostic_name="shortcut",
        version="0.1",
        summary_metrics={
            "full_score": 0.8,
            "high_retention_variants": ["label_prior_only"],
            "variants": {
                "label_prior_only": {
                    "shortcut_retention": 0.75,
                    "absolute_drop": 0.2,
                }
            },
        },
    )
    data_forensics = DiagnosticResult(
        benchmark_id="toy_mcq",
        diagnostic_name="data_forensics",
        version="0.1",
        summary_metrics={
            "signals": {
                "corpus_overlap": {
                    "status": "insufficient_corpus",
                    "risk_level": "insufficient corpus",
                    "metrics": {"documents_searched": 0, "suspicious_items": []},
                },
                "internal_duplicates": {
                    "status": "measured",
                    "risk_level": "low local evidence",
                    "metrics": {
                        "duplicate_fraction": 0.01,
                        "effective_independent_item_count": 35,
                        "cluster_sizes": {"exact_prompt": [], "near_duplicate": [2]},
                        "semantic_duplicates": {"status": "unavailable"},
                    },
                },
                "split_leakage": {
                    "status": "unavailable",
                    "risk_level": "unknown/unmeasured",
                    "metrics": {},
                },
                "temporal_validity": {
                    "status": "measured",
                    "risk_level": "no local evidence found",
                    "metrics": {
                        "items_with_temporal_warnings": [],
                        "temporal_warning_rate": 0.0,
                    },
                },
                "provenance_completeness": {
                    "status": "measured",
                    "risk_level": "moderate local evidence",
                    "metrics": {
                        "completeness_fraction": 0.5,
                        "field_missing_counts": {"source_url": 36},
                    },
                },
            },
            "searched": {"local_corpus": None, "web": False},
            "not_searched": ["remote web verification"],
            "hashes": {"item_count": 36},
        },
    )

    report = render_report_card(benchmark, "mock", [result, data_forensics])

    assert "# Validity Report Card: toy_mcq" in report
    assert "does not assign a single validity score" in report
    assert "## Provenance" in report
    assert "## Ranking comparison" in report
    assert "## Shallow baselines" in report
    assert "## Prompt sensitivity" in report
    assert "## Extraction robustness" in report
    assert "## Saturation" in report
    assert "## Power analysis" in report
    assert "## Data forensics" in report
    assert "## Contamination risk signals" in report
    assert "## Duplicate/redundancy analysis" in report
    assert "## Split validity" in report
    assert "## Temporal validity" in report
    assert "## Provenance completeness" in report
    assert "## Misuse warnings" in report
    assert "## Benchmark author checklist" in report
    assert "not a single contamination truth" in report
    assert "label_prior_only" in report

    manifest = render_report_card_manifest(
        benchmark,
        "mock",
        [result],
        report_path="reportcards/toy_mcq_mock.md",
    )

    assert manifest.benchmark_id == "toy_mcq"
    assert manifest.diagnostics_run == ["shortcut"]
    assert manifest.metadata["n_items"] == 36
