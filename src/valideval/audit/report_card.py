from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.domains.registry import render_domain_report_section
from valideval.human.reporting import read_human_artifacts
from valideval.repair.recommendations import build_author_checklist, generate_misuse_warnings
from valideval.schemas import DiagnosticResult, ReportCardManifest


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if value != value:
            return "n/a"
        return f"{value:.3f}"
    return str(value)


def _find(results: list[DiagnosticResult], name: str) -> DiagnosticResult | None:
    return next((result for result in results if result.diagnostic_name == name), None)


def _forensics_signal(
    result: DiagnosticResult | None,
    name: str,
) -> dict[str, Any]:
    if not result:
        return {}
    signals = result.summary_metrics.get("signals", {})
    value = signals.get(name, {})
    return value if isinstance(value, dict) else {}


def _signal_status(value: dict[str, Any]) -> str:
    if not value:
        return "not run"
    return f"{value.get('status', 'n/a')} / {value.get('risk_level', 'n/a')}"


def _warnings(results: list[DiagnosticResult]) -> list[str]:
    output: list[str] = []
    for result in results:
        for warning in result.warnings:
            output.append(f"- **{result.diagnostic_name}:** {warning}")
    return output


def _ranking_lines(irt: DiagnosticResult | None) -> list[str]:
    if not irt:
        return ["Not available. Run the IRT diagnostic to compare raw and proxy rankings."]

    model_metrics = irt.per_model_metrics
    if not model_metrics:
        return ["Not available. IRT result did not include per-model metrics."]

    raw_order = sorted(
        model_metrics,
        key=lambda model_id: model_metrics[model_id].get("raw_accuracy", float("-inf")),
        reverse=True,
    )
    ability_order = sorted(
        model_metrics,
        key=lambda model_id: model_metrics[model_id].get("latent_ability_proxy", float("-inf")),
        reverse=True,
    )
    correlation = irt.summary_metrics.get("ranking_correlation_raw_vs_ability")
    return [
        f"- Raw accuracy order: {', '.join(raw_order)}",
        f"- Latent-ability proxy order: {', '.join(ability_order)}",
        f"- Rank correlation, raw vs proxy: {_fmt(correlation)}",
        (
            "- Interpretation: this is a conditional ranking comparison under the diagnostic "
            "protocol, not a corrected leaderboard."
        ),
    ]


def render_report_card(
    benchmark: Benchmark,
    panel_id: str,
    results: list[DiagnosticResult],
    *,
    artifacts_dir: str | Path | None = None,
    figure_paths: dict[str, str] | None = None,
) -> str:
    shortcut = _find(results, "shortcut")
    irt = _find(results, "irt")
    reliability = _find(results, "reliability")
    baselines = _find(results, "baselines")
    answer_distribution = _find(results, "answer_distribution")
    distractor_quality = _find(results, "distractor_quality")
    prompt_sensitivity = _find(results, "prompt_sensitivity")
    extraction_robustness = _find(results, "extraction_robustness")
    saturation = _find(results, "saturation")
    power = _find(results, "power")
    dif = _find(results, "dif")
    calibration = _find(results, "calibration")
    redundancy = _find(results, "redundancy")
    ranking_uncertainty = _find(results, "ranking_uncertainty")
    contamination = _find(results, "contamination")
    data_forensics = _find(results, "data_forensics")
    coverage = _find(results, "coverage")
    human_summary = read_human_artifacts(artifacts_dir)
    items = benchmark.load_items()
    metadata = benchmark.construct_spec.metadata
    artifact_scope = metadata.get("artifact_scope", "toy/demo")
    item_format_label = metadata.get("item_format_label", "synthetic MCQ items")
    intended_use = metadata.get(
        "intended_use_report_label", "offline software validation of the audit pipeline."
    )

    lines = [
        f"# Validity Report Card: {benchmark.benchmark_id}",
        "",
    ]
    if figure_paths:
        overview = figure_paths.get("diagnostic_overview_svg")
        if overview:
            lines.extend(
                [
                    "## Diagnostic overview figure",
                    "",
                    f"![Diagnostic overview]({overview})",
                    "",
                ]
            )
    lines.extend(
        [
            "## Claimed construct",
            "",
            benchmark.claimed_construct,
            "",
        ]
    )
    lines.extend(
        [
            "## Diagnostics run",
            "",
            ", ".join(result.diagnostic_name for result in results),
            "",
            "## Provenance",
            "",
            f"- Benchmark: {benchmark.benchmark_id}",
            f"- Panel: {panel_id}",
            f"- Items: {len(items)} {item_format_label}",
            f"- Prompt variants: {', '.join(benchmark.available_prompt_variants())}",
            f"- Artifact scope: {artifact_scope}",
            f"- Intended use: {intended_use}",
            "",
            "## Executive summary",
            "",
            (
                "This report summarizes evidence consistent with specific measurement threats. "
                "It does not assign a single validity score and does not prove that the benchmark "
                "is valid or invalid in general."
            ),
            "",
        ]
    )

    lines.extend(["## Shallow baselines", ""])
    if baselines:
        metrics = baselines.summary_metrics
        best = metrics.get("best_shallow_baseline", {})
        lines.append(
            f"- Best shallow baseline: {best.get('baseline_id', 'n/a')} at {_fmt(best.get('score'))}"
        )
        lines.append(f"- Best strong-model score: {_fmt(metrics.get('best_strong_model_score'))}")
        lines.append(f"- Dumb Baseline Gap: {_fmt(metrics.get('dumb_baseline_gap'))}")
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Answer distribution", ""])
    if answer_distribution:
        metrics = answer_distribution.summary_metrics
        lines.append(f"- Label counts: {metrics.get('label_counts', {})}")
        length_bias = metrics.get("answer_length_bias", {})
        lines.append(
            "- Longest-option correctness fraction: "
            f"{_fmt(length_bias.get('longest_option_correct_fraction'))}"
        )
        lines.append(
            "- Repeated-phrase artifact item count: "
            f"{len(metrics.get('repeated_phrase_items', []))}"
        )
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Shortcut validity", ""])
    if shortcut:
        metrics = shortcut.summary_metrics
        lines.append(f"- Full-condition score: {_fmt(metrics.get('full_score'))}")
        high = metrics.get("high_retention_variants", [])
        if high:
            lines.append(
                "- High retained performance under ablation suggests possible shortcut "
                f"availability for: {', '.join(high)}."
            )
        for variant, values in metrics.get("variants", {}).items():
            lines.append(
                f"- {variant}: retained {_fmt(values.get('shortcut_retention'))}, "
                f"drop {_fmt(values.get('absolute_drop'))}"
            )
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Distractor quality", ""])
    if distractor_quality:
        metrics = distractor_quality.summary_metrics
        lines.append(f"- Dead distractor fraction: {_fmt(metrics.get('dead_distractor_fraction'))}")
        lines.append(
            f"- Confusing distractor count: {_fmt(metrics.get('confusing_distractor_count'))}"
        )
        csv_path = distractor_quality.artifacts.get("distractor_quality_csv")
        if csv_path:
            lines.append(f"- CSV artifact: {csv_path}")
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Prompt sensitivity", ""])
    if prompt_sensitivity:
        metrics = prompt_sensitivity.summary_metrics
        lines.append(
            f"- Prompt robustness coefficient: {_fmt(metrics.get('prompt_robustness_coefficient'))}"
        )
        lines.append(
            "- Prompt-specific ranking flips: "
            f"{len(metrics.get('prompt_specific_ranking_flips', []))}"
        )
        lines.append(f"- Prompt templates evaluated: {_fmt(metrics.get('n_prompt_templates'))}")
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Extraction robustness", ""])
    if extraction_robustness:
        metrics = extraction_robustness.summary_metrics
        lines.append(
            f"- Strict vs lenient score shift: {_fmt(metrics.get('strict_vs_lenient_score_shift'))}"
        )
        lines.append(f"- Invalid output rate: {_fmt(metrics.get('invalid_output_rate'))}")
        lines.append(
            f"- Extraction disagreement rate: {_fmt(metrics.get('extraction_disagreement_rate'))}"
        )
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Human validation", ""])
    if human_summary.get("available"):
        lines.append(f"- Annotated items: {_fmt(human_summary.get('annotated_item_count'))}")
        lines.append(f"- Annotated tasks: {_fmt(human_summary.get('annotated_task_count'))}")
        lines.append(f"- Human judgments imported: {_fmt(human_summary.get('judgment_count'))}")
        lines.append(f"- Raw agreement: {_fmt(human_summary.get('raw_agreement'))}")
        lines.append(f"- Cohen kappa: {_fmt(human_summary.get('cohen_kappa'))}")
        lines.append(f"- Fleiss kappa: {_fmt(human_summary.get('fleiss_kappa'))}")
        lines.append(
            "- Interpretation: human labels are protocol evidence and may still require "
            "adjudication; they are not treated as perfect ground truth."
        )
    else:
        lines.append("Not run. No human-validation coverage claim should be made.")
    lines.append("")

    lines.extend(["## Judge reliability", ""])
    if human_summary.get("judge"):
        lines.append(f"- Judge-human agreement: {_fmt(human_summary.get('judge_human_agreement'))}")
        lines.append(f"- Inter-judge agreement: {_fmt(human_summary.get('inter_judge_agreement'))}")
        judge_metrics = human_summary.get("judge", {}).get("metrics", {})
        variance = judge_metrics.get("judge_variance", {})
        lines.append(f"- Judge variance rate: {_fmt(variance.get('task_variance_rate'))}")
        lines.append(
            "- Optional LLM judge: "
            f"{human_summary.get('judge', {}).get('optional_llm_judge', {}).get('status', 'n/a')}"
        )
    else:
        lines.append("Not run. Judge reliability is unmeasured.")
    lines.append("")

    lines.extend(["## Scoring ambiguity", ""])
    if human_summary.get("ambiguity"):
        lines.append(f"- Ambiguous task count: {_fmt(human_summary.get('n_ambiguous_tasks'))}")
        lines.append(f"- Ambiguity rate: {_fmt(human_summary.get('ambiguity_rate'))}")
        examples = human_summary.get("ambiguity", {}).get("examples", [])
        example_ids = [row.get("task_id", "") for row in examples[:5]]
        lines.append(f"- Example tasks: {', '.join(example_ids) or 'none'}")
    else:
        lines.append("Not run. Scoring ambiguity requires human/judge artifacts.")
    lines.append("")

    lines.extend(["## Reliability", ""])
    if reliability:
        metrics = reliability.summary_metrics
        lines.append(
            "- Benchmark-level reliability estimate: "
            f"{_fmt(metrics.get('benchmark_level_reliability_estimate'))}"
        )
        lines.append(
            f"- Mean perturbation sensitivity: {_fmt(metrics.get('mean_perturbation_sensitivity'))}"
        )
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Saturation", ""])
    if saturation:
        metrics = saturation.summary_metrics
        lines.append(f"- Category: {metrics.get('saturation_category', 'n/a')}")
        lines.append(
            "- Fraction solved by all top models: "
            f"{_fmt(metrics.get('fraction_solved_by_all_top_models'))}"
        )
        lines.append(
            "- Effective discriminating item count: "
            f"{_fmt(metrics.get('effective_discriminating_item_count'))}"
        )
        lines.append(f"- Ceiling proximity: {_fmt(metrics.get('ceiling_proximity'))}")
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Power analysis", ""])
    if power:
        metrics = power.summary_metrics
        lines.append(f"- Effective item count: {_fmt(metrics.get('effective_item_count'))}")
        lines.append(
            f"- Minimum detectable difference: {_fmt(metrics.get('minimum_detectable_difference'))}"
        )
        lines.append(
            "- Do not overinterpret within points: "
            f"{_fmt(metrics.get('do_not_overinterpret_within_points'))}"
        )
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## IRT item analysis", ""])
    if irt:
        metrics = irt.summary_metrics
        lines.append(
            "- Near-zero discrimination fraction: "
            f"{_fmt(metrics.get('near_zero_discrimination_fraction'))}"
        )
        lines.append(
            "- Negative-discrimination item count: "
            f"{_fmt(metrics.get('negative_discrimination_items'))}"
        )
        subsets = metrics.get("recommended_subsets", {})
        if subsets:
            first_key = sorted(subsets, key=lambda value: int(value))[0]
            subset = subsets[first_key]
            lines.append(
                f"- Example high-information subset k={first_key}: "
                f"{', '.join(subset.get('selected_items', []))}"
            )
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Ranking comparison", ""])
    lines.extend(_ranking_lines(irt))
    lines.append("")

    lines.extend(["## Advanced psychometrics", ""])
    if dif:
        lines.append(
            f"- DIF suspicious item count: {_fmt(dif.summary_metrics.get('suspicious_item_count'))}"
        )
    if calibration:
        lines.append(f"- Calibration ECE: {_fmt(calibration.summary_metrics.get('ece'))}")
        abstention = calibration.summary_metrics.get("abstention", {})
        lines.append(f"- Abstention coverage: {_fmt(abstention.get('coverage'))}")
    if redundancy:
        lines.append(
            f"- Redundancy fraction: {_fmt(redundancy.summary_metrics.get('redundancy_fraction'))}"
        )
    if ranking_uncertainty:
        lines.append(
            "- Top-k bootstrap stability: "
            f"{_fmt(ranking_uncertainty.summary_metrics.get('top_k_stability'))}"
        )
    if not any([dif, calibration, redundancy, ranking_uncertainty]):
        lines.append("Not run.")
    lines.append("")

    domain_section = render_domain_report_section(results)
    if domain_section:
        lines.append(domain_section)

    lines.extend(["## Data forensics", ""])
    if data_forensics:
        searched = data_forensics.summary_metrics.get("searched", {})
        not_searched = data_forensics.summary_metrics.get("not_searched", [])
        hashes = data_forensics.summary_metrics.get("hashes", {})
        lines.append(f"- Local corpus searched: {searched.get('local_corpus') or 'none supplied'}")
        lines.append(f"- Web searched: {searched.get('web', False)}")
        lines.append(f"- Not searched: {', '.join(not_searched) if not_searched else 'n/a'}")
        lines.append(f"- Dataset hash item count: {_fmt(hashes.get('item_count'))}")
        lines.append(
            "- Interpretation: these are corpus-dependent local signals, not a single "
            "contamination truth."
        )
    else:
        lines.append("Not run. No data-forensics conclusion should be drawn.")
    lines.append("")

    lines.extend(["## Contamination risk signals", ""])
    overlap = _forensics_signal(data_forensics, "corpus_overlap")
    if overlap:
        metrics = overlap.get("metrics", {})
        lines.append(f"- Corpus overlap signal: {_signal_status(overlap)}")
        lines.append(f"- Documents searched: {_fmt(metrics.get('documents_searched'))}")
        lines.append(f"- Exact-match rate: {_fmt(metrics.get('exact_match_rate'))}")
        lines.append(f"- Question-match rate: {_fmt(metrics.get('question_match_rate'))}")
        lines.append(f"- Suspicious item rate: {_fmt(metrics.get('suspicious_item_rate'))}")
        suspicious = metrics.get("suspicious_items", [])
        lines.append(f"- High-suspiciousness local item list: {', '.join(suspicious) or 'none'}")
    elif contamination:
        lines.append(
            "- Intra-benchmark duplicate rate: "
            f"{_fmt(contamination.summary_metrics.get('intra_benchmark_duplicate_rate'))}"
        )
        lines.append(
            "- External exact-overlap rate: "
            f"{_fmt(contamination.summary_metrics.get('external_exact_overlap_rate'))}"
        )
    else:
        lines.append("Not run. No contamination conclusion should be drawn.")
    lines.append("")

    lines.extend(["## Duplicate/redundancy analysis", ""])
    duplicate_signal = _forensics_signal(data_forensics, "internal_duplicates")
    if duplicate_signal:
        metrics = duplicate_signal.get("metrics", {})
        cluster_sizes = metrics.get("cluster_sizes", {})
        lines.append(f"- Internal duplicate signal: {_signal_status(duplicate_signal)}")
        lines.append(f"- Duplicate fraction: {_fmt(metrics.get('duplicate_fraction'))}")
        lines.append(
            "- Effective independent item count: "
            f"{_fmt(metrics.get('effective_independent_item_count'))}"
        )
        lines.append(f"- Exact duplicate cluster sizes: {cluster_sizes.get('exact_prompt', [])}")
        lines.append(f"- Near duplicate cluster sizes: {cluster_sizes.get('near_duplicate', [])}")
        semantic = metrics.get("semantic_duplicates", {})
        lines.append(f"- Semantic duplicate scan: {semantic.get('status', 'n/a')}")
    elif redundancy:
        lines.append(
            f"- Redundancy fraction: {_fmt(redundancy.summary_metrics.get('redundancy_fraction'))}"
        )
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Split validity", ""])
    split_signal = _forensics_signal(data_forensics, "split_leakage")
    if split_signal:
        metrics = split_signal.get("metrics", {})
        lines.append(f"- Split leakage signal: {_signal_status(split_signal)}")
        lines.append(f"- Split counts: {metrics.get('split_counts', {})}")
        high_risk = metrics.get("high_risk_item_list", [])
        lines.append(f"- High-risk item list: {', '.join(high_risk) or 'none'}")
        lines.append(
            "- Temporal split violations: "
            f"{', '.join(metrics.get('temporal_split_violations', [])) or 'none'}"
        )
    else:
        lines.append("Not run or unavailable; split leakage requires split metadata.")
    lines.append("")

    lines.extend(["## Temporal validity", ""])
    temporal_signal = _forensics_signal(data_forensics, "temporal_validity")
    if temporal_signal:
        metrics = temporal_signal.get("metrics", {})
        lines.append(f"- Temporal validity signal: {_signal_status(temporal_signal)}")
        lines.append(
            "- Items with temporal warnings: "
            f"{', '.join(metrics.get('items_with_temporal_warnings', [])) or 'none'}"
        )
        lines.append(f"- Temporal warning rate: {_fmt(metrics.get('temporal_warning_rate'))}")
        lines.append("- Web verification: unavailable for offline toy audits.")
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Provenance completeness", ""])
    provenance_signal = _forensics_signal(data_forensics, "provenance_completeness")
    if provenance_signal:
        metrics = provenance_signal.get("metrics", {})
        missing = metrics.get("field_missing_counts", {})
        lines.append(f"- Provenance signal: {_signal_status(provenance_signal)}")
        lines.append(
            f"- Fully complete item fraction: {_fmt(metrics.get('completeness_fraction'))}"
        )
        lines.append(f"- Missing-field counts: {missing}")
    else:
        lines.append("Not run.")
    lines.append("")

    lines.extend(["## Coverage profile", ""])
    if coverage:
        tag_distribution = coverage.summary_metrics.get("tag_distribution", {})
        lines.append(
            f"- Unique construct tags: {_fmt(coverage.summary_metrics.get('n_unique_tags'))}"
        )
        lines.append(f"- Balance score: {_fmt(coverage.summary_metrics.get('balance_score'))}")
        lines.append(f"- Singleton tags: {coverage.summary_metrics.get('singleton_tags', [])}")
        lines.append(f"- Tag distribution: {tag_distribution}")
    else:
        lines.append("Not run. Content coverage requires tag metadata and, ideally, human review.")
    lines.append("")

    lines.extend(
        [
            "## Diagnostic-sensitive interpretation",
            "",
            (
                "Evidence should be interpreted by diagnostic profile. For this run, ranking and "
                "score interpretations are conditional on the audited panel, prompt variants, "
                "and artifact scope."
            ),
            "",
            "## Misuse warnings",
            "",
        ]
    )
    lines.extend(f"- {warning}" for warning in generate_misuse_warnings(benchmark, results))
    lines.extend(
        [
            "",
            "## Benchmark author checklist",
            "",
        ]
    )
    for item in build_author_checklist(benchmark, results):
        lines.append(f"- {item['check']}: {item['status']} ({item['evidence']})")
    lines.extend(
        [
            "",
            "## Recommended benchmark-author actions",
            "",
            "- Inspect items with high ablated performance or low/negative discrimination.",
            "- Compare strong-model results with shallow baseline results before interpreting rankings.",
            "- Review dead or highly confusing distractors before making item-retention decisions.",
            "- Check extraction-rule sensitivity when strict and lenient scoring disagree.",
            "- Use saturation and power diagnostics before interpreting small model-score gaps.",
            "- Verify construct tags and construct-critical fields with human benchmark authors.",
            "- Treat IRT-selected subsets as audit aids, not replacements for substantive review.",
            "",
            "## Limitations",
            "",
            "- The toy benchmark is synthetic and intended for pipeline validation.",
            "- Mock model behavior is deterministic and does not represent real model capability.",
            "- IRT estimates are layered proxy/Rasch/uncertainty outputs and become fragile with small model panels.",
        ]
    )
    for limitation in benchmark.construct_spec.limitations:
        lines.append(f"- {limitation}")
    for result in results:
        for limitation in result.limitations:
            lines.append(f"- **{result.diagnostic_name}:** {limitation}")
    lines.extend(["", "## Warnings", ""])
    warnings = _warnings(results)
    lines.extend(warnings if warnings else ["No diagnostic warnings."])
    lines.extend(
        [
            "",
            "## Reproduction",
            "",
            "```bash",
            "python3 -m valideval matrices --benchmark toy_mcq --panel mock",
            "python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core",
            "python3 -m valideval report --benchmark toy_mcq --panel mock",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def render_report_card_manifest(
    benchmark: Benchmark,
    panel_id: str,
    results: list[DiagnosticResult],
    *,
    report_path: str,
    result_paths: list[str] | None = None,
) -> ReportCardManifest:
    commands = [
        f"python3 -m valideval matrices --benchmark {benchmark.benchmark_id} --panel {panel_id}",
        (
            f"python3 -m valideval audit --benchmark {benchmark.benchmark_id} "
            f"--panel {panel_id} --diagnostics all-core"
        ),
        f"python3 -m valideval report --benchmark {benchmark.benchmark_id} --panel {panel_id}",
    ]
    return ReportCardManifest(
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel_id,
        report_path=report_path,
        diagnostics_run=[result.diagnostic_name for result in results],
        result_paths=result_paths or [],
        reproduction_commands=commands,
        warnings=[warning for result in results for warning in result.warnings],
        limitations=[
            *benchmark.construct_spec.limitations,
            *[limitation for result in results for limitation in result.limitations],
        ],
        metadata={
            "claimed_construct": benchmark.claimed_construct,
            "prompt_variants": benchmark.available_prompt_variants(),
            "n_items": len(benchmark.load_items()),
            "artifact_scope": benchmark.construct_spec.metadata.get("artifact_scope"),
        },
    )
