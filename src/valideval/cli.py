from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from valideval import __version__
from valideval.adoption.advisor import advise_benchmark_selection
from valideval.adoption.design import run_design_assistant
from valideval.adoption.doctor import run_doctor
from valideval.adoption.importers import SUPPORTED_IMPORTERS, import_outputs
from valideval.adoption.preregistration import generate_preregistration
from valideval.adoption.quickstart import run_quickstart_audit
from valideval.adoption.schemas import export_schema, schema_names, validate_payload
from valideval.adoption.toolkit import generate_card, init_benchmark, validate_benchmark
from valideval.audit.ranking import ability_ranking, compare_rankings, naive_accuracy_ranking
from valideval.audit.runner import AuditRunner
from valideval.audit.summary import print_audit_summary
from valideval.benchmarks.base import get_benchmark
from valideval.benchmarks.gpqa_inputs import (
    GPQA_VARIANTS,
    extraction_audit,
    go_no_go_report,
    matrix_from_prediction_file,
    real_audit_dry_run,
    save_cached_matrix_from_predictions,
    score_raw_outputs,
    validate_alignment,
    validate_gpqa_item_file,
    validate_prompt_variant_cache,
    validation_dir,
    write_audit_manifest,
)
from valideval.benchmarks.gpqa_local import (
    check_panel_readiness,
    export_gpqa_diamond,
    generate_gpqa_outputs,
)
from valideval.benchmarks.preflight import build_benchmark_preflight
from valideval.calibration.preflight import build_calibration_preflight
from valideval.config import load_default_config, load_yaml
from valideval.cross_benchmark.analysis import run_cross_benchmark_analysis
from valideval.diagnostics.panel_validity import write_panel_validity_report
from valideval.domains import describe_domain_pack, domain_diagnostic_names, list_domain_packs
from valideval.evidence.cpu_replay_v7_2_1 import replay_cpu_evidence
from valideval.evidence.ledger import build_claim_evidence_ledger
from valideval.execution.config import RUN_MODES
from valideval.execution.doctor_v7_2_1 import run_cpu_maxout_doctor
from valideval.execution.runner import run_from_config
from valideval.forensics.overlap import scan_corpus_overlap
from valideval.human import (
    create_adjudication_queue,
    detect_scoring_ambiguity,
    generate_annotation_packet,
    import_annotations,
    render_annotation_viewer,
    write_agreement_report,
    write_judge_reliability_report,
)
from valideval.human.common import load_annotation_tasks, load_judge_predictions
from valideval.importers.ingest_v7 import ingest_and_analyze_v7
from valideval.importers.kaggle_v5 import (
    import_kaggle_outputs_v5,
    validate_kaggle_zip,
)
from valideval.importers.leaderboard_details import (
    SUPPORTED_DETAIL_FORMATS,
    import_published_details,
)
from valideval.importers.post_import_v5 import (
    POST_IMPORT_READY,
    build_post_import_plan_v5,
)
from valideval.importers.s1_v6 import accept_s1_smoke_v6
from valideval.importers.s1_v7_2 import accept_s1_v7_2
from valideval.importers.wide_matrix import (
    build_matrix_from_wide_predictions,
    import_wide_predictions,
)
from valideval.io.cache import load_matrix
from valideval.kaggle_v4 import (
    cross_benchmark_analysis,
    import_kaggle_outputs,
    post_import_analysis,
)
from valideval.leaderboard.atlas import build_benchmark_atlas
from valideval.leaderboard.badges import health_badges
from valideval.leaderboard.dashboard import export_dashboard_data
from valideval.leaderboard.diff import diff_audits
from valideval.leaderboard.platform import build_platform_exports
from valideval.leaderboard.registry import (
    add_audit_to_registry,
    list_audits,
    validate_registry,
)
from valideval.leaderboard.site import build_static_site
from valideval.models.panel import load_panel
from valideval.panels.ollama_panel import build_ollama_panel_preflight
from valideval.planning.runtime_recalibration_v6 import recalibrate_runtime_from_s1
from valideval.planning.runtime_recalibration_v7_2 import recalibrate_study_c_after_s1
from valideval.plugins import PLUGIN_KINDS, list_plugins
from valideval.psychometrics.irt_2pl import fit_irt_from_matrix
from valideval.real_panel.baselines import build_baseline_dry_run_manifest
from valideval.real_panel.execution import (
    run_diagnostic_disagreement_audit,
    run_ranking_disagreement,
    run_real_panel_baselines,
    run_real_panel_ranking_audit,
    run_subject_instability_audit,
)
from valideval.real_panel.finding_engine import build_real_panel_dry_run_manifest
from valideval.release.bundle import build_reproducibility_bundle, verify_bundle
from valideval.release.environment import write_environment
from valideval.release.neurips import neurips_readiness_report
from valideval.release.paper_assets import generate_paper_assets
from valideval.release.reviewer import reviewer_risk_report
from valideval.release.v5 import build_deterministic_zip, plan_release, write_release_audit
from valideval.release.validation_v7_2_1 import validate_cpu_maxout_release
from valideval.repair.engine import (
    issue_certificate,
    render_checklist,
    render_evidence_matrix,
    render_validity_card,
    run_repair,
)
from valideval.repair.policies import policy_names
from valideval.statistics.power_materiality import build_power_materiality_preflight
from valideval.stats.check import run_stats_check
from valideval.validation.cross_flaw import run_cross_flaw_validation
from valideval.validation.decoupled_synthetic import build_decoupled_synthetic_preflight
from valideval.validation.external_flag_validation import (
    export_flags_from_results,
    validate_flags_against_ground_truth,
)
from valideval.validation.external_ground_truth import import_ground_truth
from valideval.validation.gpqa_wide import gpqa_wide_readiness
from valideval.validation.heldout_generators import run_heldout_validation
from valideval.validation.mmlu_redux import import_mmlu_redux_ground_truth
from valideval.validation.mmlu_redux_alignment import align_mmlu_redux
from valideval.validation.mmlu_redux_alignment_preflight import (
    build_mmlu_redux_alignment_preflight,
)
from valideval.validation.mmlu_redux_issue_specific import run_mmlu_redux_issue_validation
from valideval.validation.mmlu_redux_pipeline import run_mmlu_redux_validation
from valideval.validation.synthetic_benchmark import generate_synthetic_benchmark
from valideval.validation.validation_report import summarize_report_directory, write_summary_report
from valideval.validation.validation_runner import (
    run_single_validation,
    run_validation_config,
)

DIAGNOSTIC_ALIASES = {
    "answer-distribution": "answer_distribution",
    "distractor-quality": "distractor_quality",
    "distractors": "distractor_quality",
    "prompt-sensitivity": "prompt_sensitivity",
    "extraction-robustness": "extraction_robustness",
    "data-forensics": "data_forensics",
}
PSYCHOMETRIC_ALIASES = {
    "irt": "irt",
    "saturation": "saturation",
    "power": "power",
    "dif": "dif",
    "calibration": "calibration",
    "all": "psychometrics",
}

try:  # pragma: no cover - cosmetic fallback.
    from rich.console import Console

    console: Any = Console()
except Exception:  # pragma: no cover - cosmetic fallback.
    console = None


def _print(message: Any) -> None:
    if console is not None:
        console.print(message)
    else:
        print(message)


def _runner(args: argparse.Namespace) -> AuditRunner:
    return AuditRunner(
        cache_root=args.cache_root,
        results_root=args.results_root,
        reportcards_root=args.reportcards_root,
        seed=args.seed,
    )


def _load_benchmark_and_panel(args: argparse.Namespace):
    benchmark_id = args.benchmark
    local_path = getattr(args, "local_path", None)
    benchmark_path = getattr(args, "benchmark_path", None)
    if benchmark_path:
        path = Path(benchmark_path)
        if path.is_dir():
            local_path = path / "items.jsonl"
            benchmark_id = "local_jsonl"
        elif path.suffix == ".jsonl":
            local_path = path
            benchmark_id = "local_jsonl"
        else:
            raise ValueError(
                "Benchmark path must be a benchmark directory containing items.jsonl or a JSONL file."
            )
    benchmark = get_benchmark(benchmark_id, local_path=local_path)
    panel = load_panel(args.panel)
    return benchmark, panel


def command_info(args: argparse.Namespace) -> int:
    _print(f"valideval {__version__}")
    _print("Psychometric validity-auditing toolkit for AI benchmarks.")
    _print("Offline demo benchmark: toy_mcq")
    _print("Offline model panel: mock")
    _print("Readiness check: python3 -m valideval doctor --benchmark toy_mcq --panel mock")
    _print("Full audit preset: --diagnostics legendary")
    _print("Quick summary: python3 -m valideval audit-summary --benchmark toy_mcq --panel mock")
    return 0


def command_ingest_and_analyze(args: argparse.Namespace) -> int:
    payload = ingest_and_analyze_v7(args.input, output_root=args.output_root)
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_audit_summary(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = runner.load_diagnostic_results(benchmark.benchmark_id, panel.panel_id)
    if not results:
        raise ValueError("No diagnostic results found. Run `python3 -m valideval audit ...` first.")
    manifest = _load_manifest(Path(args.results_root), benchmark.benchmark_id)
    print_audit_summary(results, manifest=manifest, console=console)
    return 0


def command_toy(args: argparse.Namespace) -> int:
    benchmark = get_benchmark("toy_mcq")
    items = benchmark.load_items()
    _print(f"Benchmark: {benchmark.benchmark_id}")
    _print(f"Claimed construct: {benchmark.claimed_construct}")
    _print(f"Items: {len(items)}")
    _print(f"Prompt variants: {', '.join(benchmark.available_prompt_variants())}")
    _print("First item preview:")
    _print(benchmark.render_prompt(items[0], variant="full"))
    return 0


def command_matrices(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    variants = args.variants if args.variants else benchmark.available_prompt_variants()
    matrices = runner.build_matrices(
        benchmark,
        panel,
        variants=variants,
        overwrite=not args.no_overwrite,
    )
    _print(
        f"Wrote {len(matrices)} response matrices for {benchmark.benchmark_id}/{panel.panel_id}."
    )
    for variant in matrices:
        _print(f"- cache/{benchmark.benchmark_id}/{panel.panel_id}/matrix_{variant}.csv")
    return 0


def command_matrix_from_predictions(args: argparse.Namespace) -> int:
    if args.predictions or args.output:
        if not args.predictions or not args.output:
            raise ValueError("--predictions and --output must be supplied together.")
        panel_id = args.panel
        if panel_id == "mock" and args.benchmark == "gpqa_diamond":
            panel_id = Path(args.predictions).parent.name or panel_id
        payload = matrix_from_prediction_file(
            predictions_path=args.predictions,
            output_path=args.output,
            benchmark_id=args.benchmark,
            panel_id=panel_id,
            variant=args.variant,
            scoring_method=args.scoring_method,
            seed=args.seed,
        )
        _print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    path = save_cached_matrix_from_predictions(
        cache_root=args.cache_root,
        benchmark_id=args.benchmark,
        panel_id=args.panel,
        variant=args.variant,
        scoring_method=args.scoring_method,
        seed=args.seed,
    )
    _print(f"Wrote response matrix from cached predictions: {path}")
    return 0


def command_import_wide_predictions(args: argparse.Namespace) -> int:
    payload = import_wide_predictions(
        args.input,
        args.output,
        benchmark=args.benchmark,
        input_format=args.format,
        source=args.source,
        include_text=args.include_text,
        report_path=args.report,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_matrix_from_wide_predictions(args: argparse.Namespace) -> int:
    payload = build_matrix_from_wide_predictions(
        args.predictions,
        args.output,
        report_path=args.report,
        allow_missing=not args.disallow_missing,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_import_published_details(args: argparse.Namespace) -> int:
    payload = import_published_details(
        args.input,
        benchmark=args.benchmark,
        output_path=args.output,
        detail_format=args.format,
        mapping_report=args.mapping_report,
        include_text=args.include_text,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_import_ground_truth(args: argparse.Namespace) -> int:
    if args.benchmark == "mmlu" and args.format in {"auto", "mmlu_redux_jsonl", "mmlu_redux_csv"}:
        payload = import_mmlu_redux_ground_truth(
            args.input,
            args.output,
            input_format=args.format,
            report_path=args.report,
        )
    else:
        payload = import_ground_truth(
            args.input,
            args.output,
            benchmark=args.benchmark,
            input_format=args.format,
            report_path=args.report,
        )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_export_flags(args: argparse.Namespace) -> int:
    payload = export_flags_from_results(
        args.results,
        args.output,
        benchmark=args.benchmark,
        matrix_path=getattr(args, "matrix", None),
        irt_dir=getattr(args, "irt", None),
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_validate_flags_against_ground_truth(args: argparse.Namespace) -> int:
    payload = validate_flags_against_ground_truth(
        args.flags,
        args.ground_truth,
        args.output,
        benchmark=args.benchmark,
        top_k=args.top_k,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
        group_by=args.group_by,
        restrict_to_ground_truth_subjects=args.restrict_to_ground_truth_subjects,
        issue_types=args.issue_type,
        severities=args.severity,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" else 1


def command_panel_validity(args: argparse.Namespace) -> int:
    payload = write_panel_validity_report(
        args.matrix,
        args.output,
        chance=args.chance,
        min_models=args.min_models,
        min_items=args.min_items,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" or not args.strict else 1


def command_fit_irt(args: argparse.Namespace) -> int:
    model = "1pl" if args.model == "rasch" else args.model
    payload = fit_irt_from_matrix(
        args.matrix,
        args.output,
        model=model,
        chance=args.chance,
        min_models=args.min_models,
        min_items=args.min_items,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" or not args.strict else 1


def command_gpqa_wide_readiness(args: argparse.Namespace) -> int:
    payload = gpqa_wide_readiness(
        predictions_path=args.predictions,
        matrix_path=args.matrix,
        output_path=args.output,
        min_models=args.min_models,
        min_items=args.min_items,
        chance=args.chance,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ready" or not args.strict else 1


def command_mmlu_redux_validation(args: argparse.Namespace) -> int:
    payload = run_mmlu_redux_validation(
        predictions_path=args.predictions,
        matrix_path=args.matrix,
        ground_truth_path=args.ground_truth,
        output_dir=args.output,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" or not args.strict else 1


def command_mmlu_redux_issue_validation(args: argparse.Namespace) -> int:
    payload = run_mmlu_redux_issue_validation(
        predictions_path=args.predictions,
        matrix_path=args.matrix,
        ground_truth_path=args.ground_truth,
        mapping_path=args.mapping,
        output_dir=args.output,
        restrict_to_ground_truth_subjects=args.restrict_to_ground_truth_subjects,
        severities=args.severity,
        issue_types=_split_csv_args(args.issue_type),
        diagnostics=_split_csv_args(args.diagnostics),
        subject_normalize=args.subject_normalize,
        subject_matched_null=args.subject_matched_null,
        min_positive_count=args.min_positive_count,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" else 1


def _split_csv_args(values: list[str] | str | None) -> list[str] | None:
    if values is None:
        return None
    if isinstance(values, str):
        values = [values]
    parsed: list[str] = []
    for value in values:
        parsed.extend(part.strip() for part in value.split(",") if part.strip())
    return parsed or None


def command_align_mmlu_redux(args: argparse.Namespace) -> int:
    payload = align_mmlu_redux(
        predictions_path=args.predictions,
        redux_path=args.redux,
        output_path=args.output,
        report_path=args.report,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" else 1


def command_mmlu_redux_alignment_preflight(args: argparse.Namespace) -> int:
    payload = build_mmlu_redux_alignment_preflight(
        predictions=args.predictions,
        redux=args.redux,
        output=args.output,
        dry_run=args.dry_run,
        execute_alignment=args.execute_alignment,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_real_panel_ranking_audit(args: argparse.Namespace) -> int:
    execute = getattr(args, "execute_confirmatory_real_panel", False) or getattr(
        args, "execute", False
    )
    if execute:
        payload = run_real_panel_ranking_audit(
            matrix=args.matrix,
            predictions=args.predictions,
            output=args.output,
        )
        _print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    payload = build_real_panel_dry_run_manifest(
        audit_name="real_panel_ranking_audit",
        matrix=args.matrix,
        predictions=args.predictions,
        results_dir=args.results_dir,
        mmlu_redux=args.mmlu_redux,
        output=args.output,
        dry_run=args.dry_run,
        execute_confirmatory_real_panel=args.execute_confirmatory_real_panel,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_diagnostic_disagreement_audit(args: argparse.Namespace) -> int:
    execute = getattr(args, "execute_confirmatory_real_panel", False) or getattr(
        args, "execute", False
    )
    if execute:
        payload = run_diagnostic_disagreement_audit(
            matrix=args.matrix,
            predictions=args.predictions,
            output=args.output,
            irt=getattr(args, "irt", None),
        )
        _print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    payload = build_real_panel_dry_run_manifest(
        audit_name="diagnostic_disagreement_audit",
        matrix=args.matrix,
        predictions=args.predictions,
        results_dir=args.results_dir,
        mmlu_redux=args.mmlu_redux,
        output=args.output,
        dry_run=args.dry_run,
        execute_confirmatory_real_panel=args.execute_confirmatory_real_panel,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_subject_instability_audit(args: argparse.Namespace) -> int:
    execute = getattr(args, "execute_confirmatory_real_panel", False) or getattr(
        args, "execute", False
    )
    if execute:
        payload = run_subject_instability_audit(
            matrix=args.matrix,
            predictions=args.predictions,
            output=args.output,
        )
        _print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    payload = build_real_panel_dry_run_manifest(
        audit_name="subject_instability_audit",
        matrix=args.matrix,
        predictions=args.predictions,
        results_dir=args.results_dir,
        mmlu_redux=args.mmlu_redux,
        output=args.output,
        dry_run=args.dry_run,
        execute_confirmatory_real_panel=args.execute_confirmatory_real_panel,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_real_panel_baselines_preflight(args: argparse.Namespace) -> int:
    payload = build_baseline_dry_run_manifest(
        config=args.config,
        output=args.output,
        dry_run=args.dry_run,
        execute_confirmatory_real_panel=args.execute_confirmatory_real_panel,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_ranking_disagreement(args: argparse.Namespace) -> int:
    if not args.execute:
        raise ValueError("ranking-disagreement requires --execute for artifact generation.")
    payload = run_ranking_disagreement(
        matrix=args.matrix,
        irt=args.irt,
        output=args.output,
        bootstrap=args.bootstrap,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_real_panel_baselines(args: argparse.Namespace) -> int:
    if not args.execute:
        raise ValueError("real-panel-baselines requires --execute for artifact generation.")
    payload = run_real_panel_baselines(
        matrix=args.matrix,
        output=args.output,
        bootstrap=args.bootstrap,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_panel_preflight(args: argparse.Namespace) -> int:
    payload = build_ollama_panel_preflight(
        config=args.config,
        output=args.output,
        dry_run=args.dry_run,
        execute_inference=args.execute_inference,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_benchmark_preflight(args: argparse.Namespace) -> int:
    payload = build_benchmark_preflight(
        config=args.config,
        output=args.output,
        dry_run=args.dry_run,
        execute_evaluation=args.execute_evaluation,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_calibration_preflight(args: argparse.Namespace) -> int:
    payload = build_calibration_preflight(
        config=args.config,
        output=args.output,
        dry_run=args.dry_run,
        execute_analysis=args.execute_analysis,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_power_materiality_preflight(args: argparse.Namespace) -> int:
    payload = build_power_materiality_preflight(
        config=args.config,
        output=args.output,
        dry_run=args.dry_run,
        execute_analysis=args.execute_analysis,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_decoupled_synthetic_preflight(args: argparse.Namespace) -> int:
    payload = build_decoupled_synthetic_preflight(
        output=args.output,
        dry_run=args.dry_run,
        execute_decoupled_synthetic=args.execute_decoupled_synthetic,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["preflight_status"] == "dry_run_ready" else 1


def command_import_kaggle_outputs_v4(args: argparse.Namespace) -> int:
    payload = import_kaggle_outputs(
        input_dir=args.input_dir,
        output_root=args.output_root,
        cache_root=args.cache_root,
        results_root=args.results_root,
        strict=args.strict,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" or not args.strict else 1


def command_post_import_analysis_v4(args: argparse.Namespace) -> int:
    payload = post_import_analysis(
        benchmark=args.benchmark,
        matrix=args.matrix,
        predictions=args.predictions,
        output=args.output,
        cache_root=args.cache_root,
        results_root=args.results_root,
        execute=args.execute,
        bootstrap=args.bootstrap,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" or not args.execute else 1


def command_cross_benchmark_analysis_v4(args: argparse.Namespace) -> int:
    payload = cross_benchmark_analysis(
        benchmarks=_split_csv_args(args.benchmarks) or [],
        cache_root=args.cache_root,
        results_root=args.results_root,
        output=args.output,
        execute=args.execute,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" or not args.execute else 1


def command_validate_run_v5(args: argparse.Namespace) -> int:
    source = Path(args.path)
    archives = sorted(source.rglob("*.zip")) if source.is_dir() else [source]
    if not archives or any(not archive.is_file() for archive in archives):
        payload = {
            "schema_version": "valideval.run_validation.v5",
            "status": "blocked_no_zips",
            "path": str(source),
            "archive_count": 0,
            "validations": [],
            "evidence_state": "BLOCKED",
        }
        _print(json.dumps(payload, indent=2, sort_keys=True))
        return 2 if args.strict else 0
    validations = [
        validate_kaggle_zip(
            archive,
            expected_study_id=args.expected_study,
            expected_run_id=args.expected_run,
            expected_benchmark_id=args.expected_benchmark,
            expected_config_hash=args.expected_config_hash,
            expected_source_zip_sha256=(args.expected_zip_sha256 if len(archives) == 1 else None),
            allow_nested_archives=args.allow_nested_archives,
            require_full_prediction_schema=True,
        ).to_dict()
        for archive in archives
    ]
    payload = {
        "schema_version": "valideval.run_validation.v5",
        "status": "ok",
        "path": str(source),
        "archive_count": len(archives),
        "validations": validations,
        "evidence_state": "VERIFIED_FROM_PRIMARY_ARTIFACT",
    }
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_import_kaggle_v5(args: argparse.Namespace) -> int:
    payload = import_kaggle_outputs_v5(
        input_dir=args.input_dir,
        output_root=args.output_root,
        cache_root=args.cache_root,
        results_root=args.results_root,
        expected_study_id=args.expected_study,
        expected_benchmark_id=args.expected_benchmark,
        strict=True,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" or not args.strict else 2


def command_post_import_v5(args: argparse.Namespace) -> int:
    receipt_paths = [Path(path) for path in (args.receipt or [])]
    if not receipt_paths:
        import_root = Path(args.import_root)
        receipt_paths = sorted(import_root.rglob("import_receipt_v5.json"))
    payload = build_post_import_plan_v5(
        receipt_paths,
        output_dir=args.output,
        minimum_extraction_reliability=args.minimum_extraction_reliability,
        minimum_coverage=args.minimum_coverage,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("final_verdict") == POST_IMPORT_READY or not args.strict else 2


def _parse_cli_assignments(values: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Expected BENCHMARK=PATH, got {value!r}")
        benchmark, raw_path = value.split("=", 1)
        benchmark = benchmark.strip()
        if not benchmark or benchmark in parsed:
            raise ValueError(f"Duplicate or empty benchmark assignment: {value!r}")
        parsed[benchmark] = Path(raw_path)
    return parsed


def command_cross_benchmark_v5(args: argparse.Namespace) -> int:
    config = load_yaml(args.config)
    matrices = {
        str(benchmark): Path(path)
        for benchmark, path in config.get("matrices", {}).items()
        if path not in {None, "", "RESULT_REQUIRED"}
    }
    matrices.update(_parse_cli_assignments(args.matrix))
    metadata = {
        str(benchmark): dict(value)
        for benchmark, value in config.get("benchmark_metadata", {}).items()
        if isinstance(value, dict)
    }
    for benchmark, path in _parse_cli_assignments(args.metadata).items():
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"Metadata JSON must contain an object: {path}")
        metadata[benchmark] = dict(value.get("cross_benchmark_eligibility", value))
    required = [str(value) for value in config.get("matrices", {})]
    missing = sorted(benchmark for benchmark in required if benchmark not in matrices)
    if missing:
        payload = {
            "schema_version": "valideval.cross_benchmark_analysis.v5",
            "status": "blocked",
            "transfer_conclusion": "BLOCKED",
            "missing_benchmarks": missing,
            "evidence_state": "BLOCKED",
        }
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        (output / "analysis_manifest_v5.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _print(json.dumps(payload, indent=2, sort_keys=True))
        return 2 if args.execute else 0
    payload = run_cross_benchmark_analysis(
        matrices,
        output_dir=args.output,
        benchmark_metadata=metadata,
        gate_thresholds=config.get("gate_thresholds"),
        analysis_config=config.get("analysis"),
        execute=args.execute,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] in {"ok", "dry_run_only"} else 2


def command_build_evidence_ledger_v5(args: argparse.Namespace) -> int:
    rows = build_claim_evidence_ledger(args.root, args.csv, args.report)
    _print(json.dumps({"claim_count": len(rows), "status": "ok"}, indent=2, sort_keys=True))
    return 0


def command_build_paper_assets_v5(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    result = subprocess.run(
        [sys.executable, str(root / "scripts/build_paper_v5_assets.py")],
        cwd=root,
        check=False,
    )
    return result.returncode


def command_build_release_v5(args: argparse.Namespace) -> int:
    profiles = {
        "source": (
            "configs/release/source_release_v5.txt",
            "dist/valideval_v5_source.zip",
            "reports/v5/VALID_EVAL_V5_SOURCE_RELEASE_AUDIT.md",
        ),
        "evidence": (
            "configs/release/evidence_release_v5.txt",
            "dist/valideval_v5_evidence.zip",
            "reports/v5/VALID_EVAL_V5_EVIDENCE_RELEASE_AUDIT.md",
        ),
        "reviewer": (
            "configs/release/reviewer_packet_v5.txt",
            "dist/valideval_v5_reviewer_packet.zip",
            "reports/v5/VALID_EVAL_V5_REVIEWER_PACKET_AUDIT.md",
        ),
    }
    root = Path(args.root).resolve()
    allowlist, default_output, report = profiles[args.profile]
    plan = plan_release(root, root / allowlist, excluded_paths={report})
    write_release_audit(plan, root / report)
    build = None
    if args.build:
        build = build_deterministic_zip(root, plan, Path(args.output or root / default_output))
    _print(
        json.dumps(
            {
                "profile": args.profile,
                "status": plan["status"],
                "included_count": plan["included_count"],
                "excluded_count": plan["excluded_count"],
                "build": build,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def command_stats_check(args: argparse.Namespace) -> int:
    payload = run_stats_check(args.results, args.output)
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_validate_benchmark_file(args: argparse.Namespace) -> int:
    if args.benchmark != "gpqa_diamond":
        raise ValueError("validate-benchmark-file currently supports --benchmark gpqa_diamond.")
    payload = validate_gpqa_item_file(
        args.items,
        output_dir=validation_dir(args.results_root, args.benchmark),
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 1


def command_score_outputs(args: argparse.Namespace) -> int:
    if args.benchmark != "gpqa_diamond":
        raise ValueError("score-outputs currently supports --benchmark gpqa_diamond.")
    payload = score_raw_outputs(
        items_path=args.items,
        input_path=args.input,
        output_path=args.output,
        prompt_variant=args.prompt_variant,
        benchmark_id=args.benchmark,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_validate_alignment(args: argparse.Namespace) -> int:
    if args.benchmark != "gpqa_diamond":
        raise ValueError("validate-alignment currently supports --benchmark gpqa_diamond.")
    payload = validate_alignment(
        items_path=args.items,
        predictions_path=args.predictions,
        output_dir=validation_dir(args.results_root, args.benchmark),
        benchmark_id=args.benchmark,
        required_variants=args.required_variants or ["full"],
        min_models=args.min_models,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["go_no_go_status"] == "pass" else 1


def command_extraction_audit(args: argparse.Namespace) -> int:
    if args.benchmark != "gpqa_diamond":
        raise ValueError("extraction-audit currently supports --benchmark gpqa_diamond.")
    payload = extraction_audit(
        items_path=args.items,
        outputs_path=args.outputs,
        output_dir=validation_dir(args.results_root, args.benchmark),
        prompt_variant=args.prompt_variant,
        benchmark_id=args.benchmark,
        success_threshold=args.success_threshold,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passes_threshold"] else 1


def command_validate_prompt_variants(args: argparse.Namespace) -> int:
    payload = validate_prompt_variant_cache(
        benchmark_id=args.benchmark,
        panel_id=args.panel,
        cache_root=args.cache_root,
        output_dir=validation_dir(args.results_root, args.benchmark),
        required_variants=args.required_variants,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


def command_run_v6(args: argparse.Namespace) -> int:
    payload = run_from_config(
        args.config,
        mode_override=args.mode,
        output_root=args.output_root,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return (
        0
        if payload["status"]
        in {
            "RUN_COMPLETE",
            "RUN_COMPLETE_WITH_RECORDED_FAILURES",
        }
        else 2
    )


def command_accept_s1_v6(args: argparse.Namespace) -> int:
    payload = accept_s1_smoke_v6(
        args.input_dir,
        output_root=args.output_root,
        minimum_extraction_reliability=args.minimum_extraction_reliability,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return (
        0
        if payload["status"]
        in {
            "S1_SMOKE_ACCEPTED",
            "S1_SMOKE_ACCEPTED_WITH_RECORDED_MODEL_FAILURES",
        }
        else 2
    )


def command_accept_s1_v7_2(args: argparse.Namespace) -> int:
    payload = accept_s1_v7_2(
        args.input_dir,
        output_root=args.output_root,
        minimum_extraction_reliability=args.minimum_extraction_reliability,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return (
        0
        if payload["status"]
        in {
            "S1_V7_2_ACCEPTED",
            "S1_V7_2_ACCEPTED_WITH_RECORDED_MODEL_FAILURES",
        }
        else 2
    )


def command_replay_cpu_evidence(args: argparse.Namespace) -> int:
    payload = replay_cpu_evidence(args.repository_root, output=args.output)
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "CPU_REPLAY_PASS" else 2


def command_validate_release_v7_2_1(args: argparse.Namespace) -> int:
    payload = validate_cpu_maxout_release(args.repository_root)
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "RELEASE_VALIDATION_PASS" else 2


def command_recalibrate_runtime_v6(args: argparse.Namespace) -> int:
    payload = recalibrate_runtime_from_s1(args.input_root, args.output)
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_recalibrate_study_c_after_s1(args: argparse.Namespace) -> int:
    payload = recalibrate_study_c_after_s1(args.input_root, args.output)
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_gpqa_go_no_go(args: argparse.Namespace) -> int:
    if args.benchmark != "gpqa_diamond":
        raise ValueError("gpqa-go-no-go currently supports --benchmark gpqa_diamond.")
    payload = go_no_go_report(
        items_path=args.items,
        panel_id=args.panel,
        cache_root=args.cache_root,
        results_root=args.results_root,
        benchmark_id=args.benchmark,
        required_variants=args.required_variants,
        min_models=args.min_models,
        extraction_success_threshold=args.extraction_success_threshold,
        config_path=args.config,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "go" else 1


def command_audit_manifest(args: argparse.Namespace) -> int:
    if args.benchmark != "gpqa_diamond":
        raise ValueError("audit-manifest currently supports --benchmark gpqa_diamond.")
    payload = write_audit_manifest(
        items_path=args.items,
        panel_id=args.panel,
        cache_root=args.cache_root,
        results_root=args.results_root,
        benchmark_id=args.benchmark,
        config_path=args.config,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_export_gpqa_diamond(args: argparse.Namespace) -> int:
    payload = export_gpqa_diamond(
        output_path=args.output,
        source=args.source,
        source_file=args.source_file,
        seed=args.seed,
        results_root=args.results_root,
        hf_path=args.hf_path,
        hf_name=args.hf_name,
        hf_split=args.hf_split,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["validation_status"] == "pass" else 1


def command_check_panel(args: argparse.Namespace) -> int:
    payload = check_panel_readiness(
        panel_id=args.panel,
        cache_root=args.cache_root,
        results_root=args.results_root,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_generate_outputs(args: argparse.Namespace) -> int:
    if args.benchmark != "gpqa_diamond":
        raise ValueError("generate-outputs currently supports --benchmark gpqa_diamond.")
    payload = generate_gpqa_outputs(
        items_path=args.items,
        panel_id=args.panel,
        prompt_variant=args.prompt_variant,
        output_dir=args.output_dir,
        limit_items=args.limit_items,
        seed=args.seed,
        temperature=args.temperature,
        overwrite=args.overwrite,
        dry_run_mock=args.dry_run_mock,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_audit(args: argparse.Namespace) -> int:
    if getattr(args, "dry_run_real", False):
        panel = load_panel(args.panel)
        items_path = args.local_path or "data/gpqa/gpqa_diamond.jsonl"
        payload = real_audit_dry_run(
            items_path=items_path,
            panel_id=panel.panel_id,
            cache_root=args.cache_root,
            results_root=args.results_root,
            benchmark_id=args.benchmark,
            required_variants=args.required_variants,
            min_models=args.min_models,
            config_path=args.config,
        )
        _print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "ready" else 1
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    config = load_default_config(args.config)
    diagnostics = _audit_diagnostics(args)
    if getattr(args, "input_validated_only", False):
        path = validation_dir(args.results_root, benchmark.benchmark_id) / "go_no_go.json"
        if not path.exists():
            raise ValueError(
                "Input validation is required. Run gpqa-go-no-go before --input-validated-only."
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("status") != "go":
            raise ValueError("Input validation go/no-go status is not go.")
    diagnostic_config = dict(config.get("diagnostics", config))
    if getattr(args, "dry_run", False):
        diagnostic_config["_audit_metadata"] = {
            "audit_mode": "dry_run",
            "artifact_scope": benchmark.construct_spec.metadata.get("artifact_scope", "dry_run"),
        }
    results = runner.run_diagnostics(
        benchmark,
        panel,
        diagnostics=diagnostics,
        config=diagnostic_config,
        from_cache_only=getattr(args, "from_cache", False),
    )
    _print(f"Wrote {len(results)} diagnostic result files.")
    for result in results:
        _print(f"- results/{benchmark.benchmark_id}/{panel.panel_id}/{result.diagnostic_name}.json")
    _print(f"- results/{benchmark.benchmark_id}/manifest.json")
    if getattr(args, "dry_run", False):
        report_path = runner.render_report(benchmark, panel)
        output_dir = Path(args.results_root) / benchmark.benchmark_id / panel.panel_id
        manifest = _load_manifest(Path(args.results_root), benchmark.benchmark_id)
        card_paths = render_validity_card(
            benchmark,
            panel.panel_id,
            results,
            output_dir=output_dir,
            manifest=manifest,
        )
        certificate_paths = issue_certificate(
            benchmark,
            panel.panel_id,
            results,
            output_dir=output_dir,
            manifest=manifest,
        )
        evidence_paths = render_evidence_matrix(
            benchmark,
            panel.panel_id,
            results,
            output_dir=output_dir,
        )
        _print(f"- {report_path}")
        for rendered_path in [
            *card_paths.values(),
            *certificate_paths.values(),
            *evidence_paths.values(),
        ]:
            _print(f"- {rendered_path}")
    return 0


def command_domain_list(args: argparse.Namespace) -> int:
    payload = {
        "domains": [
            {
                "domain_id": pack.domain_id,
                "description": pack.description,
                "supported_item_types": pack.supported_item_types,
                "diagnostics": pack.diagnostic_names,
                "threat_count": len(pack.threat_library),
            }
            for pack in list_domain_packs()
        ]
    }
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_domain_describe(args: argparse.Namespace) -> int:
    _print(json.dumps(describe_domain_pack(args.domain_id), indent=2, sort_keys=True))
    return 0


def command_schema_export(args: argparse.Namespace) -> int:
    output = export_schema(args.schema_name, args.output)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_schema_validate(args: argparse.Namespace) -> int:
    output = validate_payload(args.schema_name, args.path)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["valid"] else 1


def command_import_outputs(args: argparse.Namespace) -> int:
    output = import_outputs(
        args.input,
        adapter=args.adapter,
        output_path=args.output,
        benchmark_id=args.benchmark_id,
        prompt_variant=args.prompt_variant,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_quickstart_audit(args: argparse.Namespace) -> int:
    output = run_quickstart_audit(
        items_path=args.items,
        outputs_path=args.outputs,
        benchmark_card=args.benchmark_card,
        output_dir=args.output_dir,
        adapter=args.adapter,
        seed=args.seed,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_init_benchmark(args: argparse.Namespace) -> int:
    output = init_benchmark(args.path, overwrite=args.overwrite)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_validate_benchmark(args: argparse.Namespace) -> int:
    output = validate_benchmark(args.path)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["valid"] else 1


def command_generate_card(args: argparse.Namespace) -> int:
    output = generate_card(args.path, overwrite=not args.no_overwrite)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output.get("generated") or output.get("valid", True) else 1


def command_design_assistant(args: argparse.Namespace) -> int:
    construct = args.construct
    if not construct and not args.noninteractive:
        construct = input("Claimed construct: ").strip()
    if not construct:
        raise ValueError("--construct is required in noninteractive mode.")
    output = run_design_assistant(
        output_dir=args.output_dir,
        benchmark_id=args.benchmark_id,
        construct=construct,
        intended_decisions=args.intended_decisions,
        item_format=args.item_format,
        scoring_method=args.scoring_method,
        domain=args.domain,
        shortcuts=args.shortcuts,
        critical_fields=args.critical_fields,
        human_validation=args.human_validation,
        metrics=args.metrics,
        invalidating_conditions=args.invalidating_conditions,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_preregister(args: argparse.Namespace) -> int:
    output = generate_preregistration(
        benchmark=args.benchmark,
        goal=args.goal,
        domain=args.domain,
        panel=args.panel,
        artifact_scope=args.artifact_scope,
        diagnostics=args.diagnostics,
        output_dir=args.output_dir,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_advisor(args: argparse.Namespace) -> int:
    output = advise_benchmark_selection(args.goal)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    if args.cpu_maxout:
        output = run_cpu_maxout_doctor(
            args.repository_root,
            output_root=args.output_root,
            require_gpu=args.require_gpu,
        )
        _print(json.dumps(output, indent=2, sort_keys=True))
        return (
            0
            if output["status"] in {"PASS", "WARN"} and not args.strict
            else int(output["status"] != "PASS")
        )
    output = run_doctor(
        benchmark_id=args.benchmark,
        panel_id=args.panel,
        local_path=args.local_path,
        cache_root=args.cache_root,
        results_root=args.results_root,
        reportcards_root=args.reportcards_root,
        config_path=args.config,
        required_variants=args.required_variants,
        required_diagnostics=args.required_diagnostics,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not args.strict or output["status"] == "pass" else 1


def command_plugins_list(args: argparse.Namespace) -> int:
    output = list_plugins(args.kind)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_paper_assets(args: argparse.Namespace) -> int:
    output = generate_paper_assets(
        benchmark=args.benchmark,
        panel=args.panel,
        results_root=args.results_root,
        paper_dir=args.paper_dir,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_bundle(args: argparse.Namespace) -> int:
    output = build_reproducibility_bundle(
        benchmark=args.benchmark,
        panel=args.panel,
        output_dir=args.output_dir,
        results_root=args.results_root,
        reportcards_root=args.reportcards_root,
        configs=args.configs,
        seed=args.seed,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_verify_bundle(args: argparse.Namespace) -> int:
    output = verify_bundle(args.bundle_path)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["valid"] else 1


def command_reviewer_risk(args: argparse.Namespace) -> int:
    output = reviewer_risk_report(report=args.report, output_path=args.output)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_environment(args: argparse.Namespace) -> int:
    output = write_environment(
        args.output,
        command=args.command_text,
        config_paths=args.configs,
        seed=args.seed,
    )
    _print(json.dumps({"environment_json": output["environment_json"]}, indent=2, sort_keys=True))
    return 0


def command_neurips_readiness(args: argparse.Namespace) -> int:
    output = neurips_readiness_report(
        benchmark=args.benchmark,
        panel=args.panel,
        paper_dir=args.paper_dir,
        output_dir=args.output_dir,
        report_path=args.report,
        bundle_path=args.bundle_path,
        validation_summary_path=args.validation_summary,
        real_benchmark=args.real_benchmark,
        real_panel=args.real_panel,
        go_no_go_path=args.go_no_go_path,
        evidence_lock_path=args.evidence_lock,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not args.strict or output["status"] == "pass" else 1


def command_baselines(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    config = load_default_config(args.config)
    results = runner.run_diagnostics(
        benchmark,
        panel,
        diagnostics=["baselines"],
        config=config.get("diagnostics", config),
        from_cache_only=getattr(args, "from_cache", False),
    )
    result = results[0]
    _print(json.dumps(result.summary_metrics, indent=2, sort_keys=True))
    _print(
        f"Wrote baseline diagnostic: results/{benchmark.benchmark_id}/{panel.panel_id}/baselines.json"
    )
    return 0


def command_core_diagnostic(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    config = load_default_config(args.config)
    diagnostic_name = DIAGNOSTIC_ALIASES.get(args.diagnostic, args.diagnostic)
    diagnostic_config = config.get("diagnostics", config)
    if getattr(args, "sanitized", False):
        diagnostic_config = dict(diagnostic_config)
        diagnostic_config.setdefault("distractor_quality", {})
        diagnostic_config["distractor_quality"] = {
            **diagnostic_config.get("distractor_quality", {}),
            "sanitized": True,
        }
    results = runner.run_diagnostics(
        benchmark,
        panel,
        diagnostics=[diagnostic_name],
        config=diagnostic_config,
        from_cache_only=getattr(args, "from_cache", False),
    )
    result = results[0]
    _print(json.dumps(result.summary_metrics, indent=2, sort_keys=True))
    _print(
        f"Wrote diagnostic: results/{benchmark.benchmark_id}/{panel.panel_id}/{result.diagnostic_name}.json"
    )
    return 0


def command_psychometrics(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    config = load_default_config(args.config)
    diagnostic_name = PSYCHOMETRIC_ALIASES[args.diagnostic]
    results = runner.run_diagnostics(
        benchmark,
        panel,
        diagnostics=[diagnostic_name],
        config=config.get("diagnostics", config),
        from_cache_only=getattr(args, "from_cache", False),
    )
    payload = {result.diagnostic_name: result.summary_metrics for result in results}
    _print(json.dumps(payload, indent=2, sort_keys=True))
    for result in results:
        _print(
            f"Wrote psychometric diagnostic: results/{benchmark.benchmark_id}/{panel.panel_id}/{result.diagnostic_name}.json"
        )
    return 0


def command_report(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    path = runner.render_report(benchmark, panel)
    _print(f"Wrote report card: {path}")
    return 0


def command_ranking(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    matrix = load_matrix(runner.cache_root, benchmark.benchmark_id, panel.panel_id, "full")
    naive = naive_accuracy_ranking(matrix)
    payload: dict[str, Any] = {"naive_accuracy_ranking": naive}
    for result in runner.load_diagnostic_results(benchmark.benchmark_id, panel.panel_id):
        if result.diagnostic_name == "irt":
            ability = ability_ranking(result.per_model_metrics)
            payload["latent_ability_proxy_ranking"] = ability
            payload["ranking_comparison"] = compare_rankings(naive, ability)
            break
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_forensics_overlap(args: argparse.Namespace) -> int:
    benchmark = get_benchmark(args.benchmark, local_path=args.local_path)
    payload = scan_corpus_overlap(benchmark, args.corpus, ngram_n=args.ngram_n)
    output_dir = Path(args.results_root) / benchmark.benchmark_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "forensics_overlap.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    metrics = payload.get("metrics", {})
    summary = {
        "status": payload.get("status"),
        "risk_level": payload.get("risk_level"),
        "corpus_path": metrics.get("corpus_path", str(args.corpus)),
        "documents_searched": metrics.get("documents_searched", 0),
        "exact_match_rate": metrics.get("exact_match_rate"),
        "question_match_rate": metrics.get("question_match_rate"),
        "suspicious_item_rate": metrics.get("suspicious_item_rate"),
        "suspicious_items": metrics.get("suspicious_items", []),
        "artifact": str(output_path),
    }
    _print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def command_repair(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = _load_required_results(runner, benchmark.benchmark_id, panel.panel_id)
    matrix = runner.ensure_matrices(benchmark, panel, variants=["full"])["full"]
    output = run_repair(
        benchmark,
        panel.panel_id,
        results,
        matrix,
        output_dir=Path(args.results_root) / benchmark.benchmark_id / panel.panel_id,
        policy=args.policy,
        target_size=args.target_size,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_card_render(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = _load_required_results(runner, benchmark.benchmark_id, panel.panel_id)
    output = render_validity_card(
        benchmark,
        panel.panel_id,
        results,
        output_dir=Path(args.results_root) / benchmark.benchmark_id / panel.panel_id,
        manifest=_load_manifest(Path(args.results_root), benchmark.benchmark_id),
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_certificate_issue(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = _load_required_results(runner, benchmark.benchmark_id, panel.panel_id)
    output = issue_certificate(
        benchmark,
        panel.panel_id,
        results,
        output_dir=Path(args.results_root) / benchmark.benchmark_id / panel.panel_id,
        manifest=_load_manifest(Path(args.results_root), benchmark.benchmark_id),
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_checklist(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = runner.load_diagnostic_results(benchmark.benchmark_id, panel.panel_id)
    output = render_checklist(
        benchmark,
        results,
        output_dir=Path(args.results_root) / benchmark.benchmark_id / panel.panel_id,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_evidence_matrix(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = _load_required_results(runner, benchmark.benchmark_id, panel.panel_id)
    output = render_evidence_matrix(
        benchmark,
        panel.panel_id,
        results,
        output_dir=Path(args.results_root) / benchmark.benchmark_id / panel.panel_id,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_leaderboard(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = _load_required_results(runner, benchmark.benchmark_id, panel.panel_id)
    matrix = runner.ensure_matrices(benchmark, panel, variants=["full"])["full"]
    output = build_platform_exports(
        benchmark=benchmark,
        panel_id=panel.panel_id,
        results=results,
        matrix=matrix,
        results_root=args.results_root,
        reportcards_root=args.reportcards_root,
        registry_root=args.registry_root,
        leaderboard_root=args.leaderboard_root,
        dashboard_root=args.dashboard_root,
        n_boot=args.bootstrap_samples,
        seed=args.seed,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_registry_validate(args: argparse.Namespace) -> int:
    payload = validate_registry(args.registry_root)
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 1


def command_registry_list(args: argparse.Namespace) -> int:
    _print(json.dumps(list_audits(args.registry_root), indent=2, sort_keys=True))
    return 0


def command_registry_add(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = _load_required_results(runner, benchmark.benchmark_id, panel.panel_id)
    record = add_audit_to_registry(
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel.panel_id,
        results=results,
        results_root=args.results_root,
        reportcards_root=args.reportcards_root,
        registry_root=args.registry_root,
        status=args.status,
    )
    _print(json.dumps(record, indent=2, sort_keys=True))
    return 0


def command_atlas(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = _load_required_results(runner, benchmark.benchmark_id, panel.panel_id)
    output = build_benchmark_atlas(
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel.panel_id,
        results=results,
        results_root=args.results_root,
        output_dir=args.leaderboard_root,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_dashboard_export(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = _load_required_results(runner, benchmark.benchmark_id, panel.panel_id)
    output = export_dashboard_data(
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel.panel_id,
        results=results,
        results_root=args.results_root,
        registry_root=args.registry_root,
        output_dir=args.dashboard_root,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_site_build(args: argparse.Namespace) -> int:
    output = build_static_site(
        site_dir=args.site_root,
        registry_root=args.registry_root,
        leaderboard_root=args.leaderboard_root,
        results_root=args.results_root,
        reportcards_root=args.reportcards_root,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_audit_diff(args: argparse.Namespace) -> int:
    output_path = Path(args.output) if args.output else None
    payload = diff_audits(args.old, args.new, output_path=output_path)
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_badges(args: argparse.Namespace) -> int:
    runner = _runner(args)
    benchmark, panel = _load_benchmark_and_panel(args)
    results = _load_required_results(runner, benchmark.benchmark_id, panel.panel_id)
    payload = health_badges(
        results,
        output_dir=Path(args.results_root) / benchmark.benchmark_id / panel.panel_id,
    )
    _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_human_packet(args: argparse.Namespace) -> int:
    benchmark, panel = _load_benchmark_and_panel(args)
    output = generate_annotation_packet(
        benchmark,
        panel.panel_id,
        cache_root=args.cache_root,
        output_dir=_human_output_dir(args, benchmark.benchmark_id, panel.panel_id),
        sample_size=args.sample_size,
        strategy=args.strategy,
        seed=args.seed,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_human_import(args: argparse.Namespace) -> int:
    benchmark, panel = _load_benchmark_and_panel(args)
    output = import_annotations(
        args.path,
        output_dir=_human_output_dir(args, benchmark.benchmark_id, panel.panel_id),
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel.panel_id,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["valid"] else 1


def command_human_agreement(args: argparse.Namespace) -> int:
    benchmark, panel = _load_benchmark_and_panel(args)
    output = write_agreement_report(
        output_dir=_human_output_dir(args, benchmark.benchmark_id, panel.panel_id),
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel.panel_id,
        n_boot=args.bootstrap_samples,
        seed=args.seed,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_human_judge(args: argparse.Namespace) -> int:
    benchmark, panel = _load_benchmark_and_panel(args)
    output_dir = _human_output_dir(args, benchmark.benchmark_id, panel.panel_id)
    _ensure_annotation_tasks(args, benchmark, panel.panel_id, output_dir)
    variants = tuple(args.variants) if args.variants else None
    output = write_judge_reliability_report(
        benchmark,
        output_dir=output_dir,
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel.panel_id,
        variants=variants or ("strict", "lenient", "regex", "mock"),
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_human_ambiguity(args: argparse.Namespace) -> int:
    benchmark, panel = _load_benchmark_and_panel(args)
    output_dir = _human_output_dir(args, benchmark.benchmark_id, panel.panel_id)
    tasks = _ensure_annotation_tasks(args, benchmark, panel.panel_id, output_dir)
    if not load_judge_predictions(output_dir):
        write_judge_reliability_report(
            benchmark,
            output_dir=output_dir,
            benchmark_id=benchmark.benchmark_id,
            panel_id=panel.panel_id,
        )
    output = detect_scoring_ambiguity(
        benchmark,
        tasks=tasks,
        output_dir=output_dir,
    )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_human_adjudication(args: argparse.Namespace) -> int:
    benchmark, panel = _load_benchmark_and_panel(args)
    output_dir = _human_output_dir(args, benchmark.benchmark_id, panel.panel_id)
    if not (output_dir / "scoring_ambiguity.csv").exists():
        tasks = _ensure_annotation_tasks(args, benchmark, panel.panel_id, output_dir)
        if not load_judge_predictions(output_dir):
            write_judge_reliability_report(
                benchmark,
                output_dir=output_dir,
                benchmark_id=benchmark.benchmark_id,
                panel_id=panel.panel_id,
            )
        detect_scoring_ambiguity(benchmark, tasks=tasks, output_dir=output_dir)
    output = create_adjudication_queue(output_dir=output_dir)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_human_ui(args: argparse.Namespace) -> int:
    benchmark, panel = _load_benchmark_and_panel(args)
    output_dir = _human_output_dir(args, benchmark.benchmark_id, panel.panel_id)
    _ensure_annotation_tasks(args, benchmark, panel.panel_id, output_dir)
    output = render_annotation_viewer(output_dir=output_dir)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_validate_diagnostics(args: argparse.Namespace) -> int:
    if args.config:
        output = run_validation_config(args.config, output_dir=args.output_dir)
    else:
        if not args.diagnostic or not args.flaw:
            raise ValueError("--diagnostic and --flaw are required when --config is not provided.")
        output = run_single_validation(
            args.diagnostic,
            args.flaw,
            strength_grid=args.strength_grid,
            seeds=args.seeds,
            n_items=args.n_items,
            output_dir=args.output_dir,
        )
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_validate_diagnostics_cross_flaw(args: argparse.Namespace) -> int:
    output = run_cross_flaw_validation(args.config, args.output)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_validate_diagnostics_heldout(args: argparse.Namespace) -> int:
    output = run_heldout_validation(args.config, args.output)
    _print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def command_validation_report(args: argparse.Namespace) -> int:
    summary = summarize_report_directory(args.report_dir)
    paths = write_summary_report(summary.get("experiments", []), args.report_dir)
    _print(json.dumps(paths, indent=2, sort_keys=True))
    return 0


def command_validation_summary(args: argparse.Namespace) -> int:
    summary = summarize_report_directory(args.report_dir)
    _print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def command_generate_synthetic(args: argparse.Namespace) -> int:
    benchmark = generate_synthetic_benchmark(
        flaw_type=args.flaw,
        flaw_strength=args.strength,
        seed=args.seed,
        n_items=args.n_items,
    )
    payload = [item.to_json_dict() for item in benchmark.load_items()]
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for item in payload:
                handle.write(json.dumps(item, sort_keys=True) + "\n")
        _print(json.dumps({"synthetic_items_jsonl": str(path)}, indent=2, sort_keys=True))
    else:
        _print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_validate_config(args: argparse.Namespace) -> int:
    data = load_yaml(args.path)
    _print(f"Loaded config: {args.path}")
    _print(f"Top-level keys: {', '.join(sorted(data)) if data else '(empty)'}")
    return 0


def _load_required_results(
    runner: AuditRunner,
    benchmark_id: str,
    panel_id: str,
):
    results = runner.load_diagnostic_results(benchmark_id, panel_id)
    if not results:
        raise ValueError("No diagnostic results found. Run `python3 -m valideval audit ...` first.")
    return results


def _load_manifest(results_root: Path, benchmark_id: str) -> dict[str, Any]:
    path = results_root / benchmark_id / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _audit_diagnostics(args: argparse.Namespace) -> list[str]:
    requested = list(args.diagnostics or [])
    domain_id = getattr(args, "domain", None)
    if domain_id:
        requested.extend(domain_diagnostic_names(domain_id))
    if not requested:
        if getattr(args, "benchmark_path", None):
            requested = ["baselines", "answer_distribution", "data_forensics"]
        else:
            requested = ["shortcut", "irt", "reliability"]
    return list(dict.fromkeys(requested))


def _human_output_dir(args: argparse.Namespace, benchmark_id: str, panel_id: str) -> Path:
    return Path(args.results_root) / benchmark_id / panel_id / "human"


def _ensure_annotation_tasks(
    args: argparse.Namespace,
    benchmark,
    panel_id: str,
    output_dir: Path,
):
    tasks = load_annotation_tasks(output_dir)
    if tasks:
        return tasks
    generate_annotation_packet(
        benchmark,
        panel_id,
        cache_root=args.cache_root,
        output_dir=output_dir,
        sample_size=getattr(args, "sample_size", 100),
        strategy=getattr(args, "strategy", "random"),
        seed=args.seed,
    )
    return load_annotation_tasks(output_dir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="valideval",
        description="Psychometric validity diagnostics for AI benchmark audits.",
    )
    parser.add_argument("--version", action="version", version=f"valideval {__version__}")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--benchmark", default="toy_mcq")
    common.add_argument("--panel", default="mock")
    common.add_argument("--local-path", default=None)
    common.add_argument("--cache-root", default="cache")
    common.add_argument("--results-root", default="results")
    common.add_argument("--reportcards-root", default="reportcards")
    common.add_argument("--registry-root", default="registry")
    common.add_argument("--leaderboard-root", default="leaderboard")
    common.add_argument("--dashboard-root", default="dashboard_data")
    common.add_argument("--seed", type=int, default=0)

    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_v7 = subparsers.add_parser(
        "ingest-and-analyze",
        help="Fail-closed V7 GPU artifact ingestion and downstream analysis routing.",
    )
    ingest_v7.add_argument("--input", required=True)
    ingest_v7.add_argument("--output-root", default="imported/v7")
    ingest_v7.set_defaults(func=command_ingest_and_analyze)

    info = subparsers.add_parser("info", help="Show package and demo information.")
    info.set_defaults(func=command_info)

    toy = subparsers.add_parser("toy", help="Preview the offline toy benchmark.")
    toy.set_defaults(func=command_toy)

    matrices = subparsers.add_parser(
        "matrices",
        parents=[common],
        help="Generate cached predictions and response matrices.",
    )
    matrices.add_argument("--variants", nargs="*", default=None)
    matrices.add_argument("--no-overwrite", action="store_true")
    matrices.set_defaults(func=command_matrices)

    matrix_from_predictions = subparsers.add_parser(
        "matrix-from-predictions",
        parents=[common],
        help="Build a response matrix from cached prediction JSONL records.",
    )
    matrix_from_predictions.add_argument("--variant", default="full")
    matrix_from_predictions.add_argument("--predictions", default=None)
    matrix_from_predictions.add_argument("--output", default=None)
    matrix_from_predictions.add_argument("--scoring-method", default="mcq")
    matrix_from_predictions.set_defaults(func=command_matrix_from_predictions)

    import_wide = subparsers.add_parser(
        "import-wide-predictions",
        help="Normalize local per-instance predictions into wide-prediction JSONL.",
    )
    import_wide.add_argument("--input", required=True)
    import_wide.add_argument("--output", required=True)
    import_wide.add_argument("--benchmark", required=True)
    import_wide.add_argument(
        "--format",
        default="auto",
        choices=[
            "auto",
            "generic_jsonl",
            "generic_csv",
            "model_major_jsonl",
            "json",
            "jsonl",
            "csv",
        ],
    )
    import_wide.add_argument("--source", default="local")
    import_wide.add_argument("--report", default=None)
    import_wide.add_argument("--include-text", action="store_true")
    import_wide.set_defaults(func=command_import_wide_predictions)

    matrix_from_wide = subparsers.add_parser(
        "matrix-from-wide-predictions",
        help="Build a model-by-item correctness matrix from normalized wide predictions.",
    )
    matrix_from_wide.add_argument("--predictions", required=True)
    matrix_from_wide.add_argument("--output", required=True)
    matrix_from_wide.add_argument("--report", default=None)
    matrix_from_wide.add_argument("--disallow-missing", action="store_true")
    matrix_from_wide.set_defaults(func=command_matrix_from_wide_predictions)

    published_details = subparsers.add_parser(
        "import-published-details",
        help="Normalize local leaderboard/HELM-style per-instance detail files.",
    )
    published_details.add_argument("--input", required=True)
    published_details.add_argument("--benchmark", required=True)
    published_details.add_argument("--output", required=True)
    published_details.add_argument(
        "--format", default="auto", choices=sorted(SUPPORTED_DETAIL_FORMATS)
    )
    published_details.add_argument("--mapping-report", default=None)
    published_details.add_argument("--include-text", action="store_true")
    published_details.set_defaults(func=command_import_published_details)

    import_gt = subparsers.add_parser(
        "import-ground-truth",
        help="Normalize external issue labels such as MMLU-Redux annotations.",
    )
    import_gt.add_argument("--input", required=True)
    import_gt.add_argument("--output", required=True)
    import_gt.add_argument("--benchmark", required=True)
    import_gt.add_argument(
        "--format",
        default="auto",
        choices=["auto", "json", "jsonl", "csv", "mmlu_redux_jsonl", "mmlu_redux_csv"],
    )
    import_gt.add_argument("--report", default=None)
    import_gt.set_defaults(func=command_import_ground_truth)

    export_flags = subparsers.add_parser(
        "export-flags",
        help="Export per-item diagnostic flags from existing result JSON files.",
    )
    export_flags.add_argument("--benchmark", required=True)
    export_flags.add_argument("--results", default=None)
    export_flags.add_argument("--matrix", default=None)
    export_flags.add_argument("--irt", default=None)
    export_flags.add_argument("--output", required=True)
    export_flags.set_defaults(func=command_export_flags)

    validate_flags = subparsers.add_parser(
        "validate-flags-against-ground-truth",
        help="Validate diagnostic flags against external issue labels.",
    )
    validate_flags.add_argument("--benchmark", required=True)
    validate_flags.add_argument("--flags", required=True)
    validate_flags.add_argument("--ground-truth", required=True)
    validate_flags.add_argument("--output", required=True)
    validate_flags.add_argument("--top-k", type=int, default=None)
    validate_flags.add_argument("--bootstrap-samples", type=int, default=200)
    validate_flags.add_argument("--seed", type=int, default=0)
    validate_flags.add_argument("--group-by", choices=["diagnostic"], default="diagnostic")
    validate_flags.add_argument("--restrict-to-ground-truth-subjects", action="store_true")
    validate_flags.add_argument("--issue-type", action="append", default=None)
    validate_flags.add_argument("--severity", action="append", default=None)
    validate_flags.set_defaults(func=command_validate_flags_against_ground_truth)

    panel_validity = subparsers.add_parser(
        "panel-validity",
        help="Check whether a wide response matrix supports item-level psychometrics.",
    )
    panel_validity.add_argument("--matrix", required=True)
    panel_validity.add_argument("--output", required=True)
    panel_validity.add_argument("--chance", type=float, default=0.25)
    panel_validity.add_argument("--min-models", type=int, default=30)
    panel_validity.add_argument("--min-items", type=int, default=20)
    panel_validity.add_argument("--strict", action="store_true")
    panel_validity.set_defaults(func=command_panel_validity)

    fit_irt = subparsers.add_parser(
        "fit-irt",
        help="Fit wide-matrix IRT proxy/Rasch/2PL-proxy reports without LLM generation.",
    )
    fit_irt.add_argument("--matrix", required=True)
    fit_irt.add_argument("--model", choices=["1pl", "rasch", "2pl", "proxy"], default="2pl")
    fit_irt.add_argument("--output", required=True)
    fit_irt.add_argument("--chance", type=float, default=0.25)
    fit_irt.add_argument("--min-models", type=int, default=30)
    fit_irt.add_argument("--min-items", type=int, default=20)
    fit_irt.add_argument("--strict", action="store_true")
    fit_irt.set_defaults(func=command_fit_irt)

    gpqa_wide = subparsers.add_parser(
        "gpqa-wide-readiness",
        help="Check whether GPQA has a wide, non-chance panel suitable for item claims.",
    )
    gpqa_wide.add_argument("--predictions", required=True)
    gpqa_wide.add_argument("--matrix", required=True)
    gpqa_wide.add_argument("--output", default="GPQA_WIDE_PANEL_READINESS.md")
    gpqa_wide.add_argument("--min-models", type=int, default=50)
    gpqa_wide.add_argument("--min-items", type=int, default=198)
    gpqa_wide.add_argument("--chance", type=float, default=0.25)
    gpqa_wide.add_argument("--strict", action="store_true")
    gpqa_wide.set_defaults(func=command_gpqa_wide_readiness)

    mmlu_redux = subparsers.add_parser(
        "mmlu-redux-validation",
        help="Run or block the MMLU-Redux external-validation pipeline from local inputs.",
    )
    mmlu_redux.add_argument("--predictions", required=True)
    mmlu_redux.add_argument("--matrix", required=True)
    mmlu_redux.add_argument("--ground-truth", required=True)
    mmlu_redux.add_argument("--output", required=True)
    mmlu_redux.add_argument("--strict", action="store_true")
    mmlu_redux.set_defaults(func=command_mmlu_redux_validation)

    mmlu_redux_issue = subparsers.add_parser(
        "mmlu-redux-issue-validation",
        help="Run issue-type-specific MMLU-Redux validation from local matrix/predictions.",
    )
    mmlu_redux_issue.add_argument("--predictions", required=True)
    mmlu_redux_issue.add_argument("--matrix", required=True)
    mmlu_redux_issue.add_argument("--ground-truth", required=True)
    mmlu_redux_issue.add_argument("--mapping", required=True)
    mmlu_redux_issue.add_argument("--output", required=True)
    mmlu_redux_issue.add_argument("--restrict-to-ground-truth-subjects", action="store_true")
    mmlu_redux_issue.add_argument("--severity", action="append", default=None)
    mmlu_redux_issue.add_argument("--issue-type", action="append", default=None)
    mmlu_redux_issue.add_argument("--diagnostics", default=None)
    mmlu_redux_issue.add_argument("--subject-normalize", action="store_true")
    mmlu_redux_issue.add_argument("--subject-matched-null", type=int, default=0)
    mmlu_redux_issue.add_argument("--min-positive-count", type=int, default=20)
    mmlu_redux_issue.add_argument("--bootstrap-samples", type=int, default=200)
    mmlu_redux_issue.add_argument("--seed", type=int, default=0)
    mmlu_redux_issue.set_defaults(func=command_mmlu_redux_issue_validation)

    align_mmlu_redux_cmd = subparsers.add_parser(
        "align-mmlu-redux",
        help="Align normalized MMLU-Redux issue labels to HELM MMLU item ids.",
    )
    align_mmlu_redux_cmd.add_argument("--predictions", required=True)
    align_mmlu_redux_cmd.add_argument("--redux", required=True)
    align_mmlu_redux_cmd.add_argument("--output", required=True)
    align_mmlu_redux_cmd.add_argument("--report", required=True)
    align_mmlu_redux_cmd.set_defaults(func=command_align_mmlu_redux)

    mmlu_redux_alignment_preflight = subparsers.add_parser(
        "mmlu-redux-alignment-preflight",
        help="Dry-run only check for direct/hash MMLU-Redux alignment fields.",
    )
    mmlu_redux_alignment_preflight.add_argument("--predictions", required=True)
    mmlu_redux_alignment_preflight.add_argument("--redux", required=True)
    mmlu_redux_alignment_preflight.add_argument(
        "--output",
        default="results/preflight/mmlu_redux_alignment_preflight.json",
    )
    mmlu_redux_alignment_preflight.add_argument("--dry-run", action="store_true")
    mmlu_redux_alignment_preflight.add_argument("--execute-alignment", action="store_true")
    mmlu_redux_alignment_preflight.set_defaults(func=command_mmlu_redux_alignment_preflight)

    real_panel_ranking = subparsers.add_parser(
        "real-panel-ranking-audit",
        help="Dry-run only manifest for future real-panel ranking finding analysis.",
    )
    real_panel_ranking.add_argument("--matrix", required=True)
    real_panel_ranking.add_argument("--predictions", required=True)
    real_panel_ranking.add_argument("--results-dir", default=None)
    real_panel_ranking.add_argument("--mmlu-redux", default=None)
    real_panel_ranking.add_argument(
        "--output",
        default="results/preflight/real_panel_ranking_audit_dryrun.json",
    )
    real_panel_ranking.add_argument("--dry-run", action="store_true")
    real_panel_ranking.add_argument("--execute-confirmatory-real-panel", action="store_true")
    real_panel_ranking.add_argument("--execute", action="store_true")
    real_panel_ranking.set_defaults(func=command_real_panel_ranking_audit)

    diagnostic_disagreement = subparsers.add_parser(
        "diagnostic-disagreement-audit",
        help="Dry-run only manifest for future diagnostic-disagreement analysis.",
    )
    diagnostic_disagreement.add_argument("--matrix", required=True)
    diagnostic_disagreement.add_argument("--predictions", required=True)
    diagnostic_disagreement.add_argument("--irt", default=None)
    diagnostic_disagreement.add_argument("--results-dir", default=None)
    diagnostic_disagreement.add_argument("--mmlu-redux", default=None)
    diagnostic_disagreement.add_argument(
        "--output",
        default="results/preflight/diagnostic_disagreement_audit_dryrun.json",
    )
    diagnostic_disagreement.add_argument("--dry-run", action="store_true")
    diagnostic_disagreement.add_argument("--execute-confirmatory-real-panel", action="store_true")
    diagnostic_disagreement.add_argument("--execute", action="store_true")
    diagnostic_disagreement.set_defaults(func=command_diagnostic_disagreement_audit)

    subject_instability = subparsers.add_parser(
        "subject-instability-audit",
        help="Dry-run only manifest for future subject-instability analysis.",
    )
    subject_instability.add_argument("--matrix", required=True)
    subject_instability.add_argument("--predictions", required=True)
    subject_instability.add_argument("--results-dir", default=None)
    subject_instability.add_argument("--mmlu-redux", default=None)
    subject_instability.add_argument(
        "--output",
        default="results/preflight/subject_instability_audit_dryrun.json",
    )
    subject_instability.add_argument("--dry-run", action="store_true")
    subject_instability.add_argument("--execute-confirmatory-real-panel", action="store_true")
    subject_instability.add_argument("--execute", action="store_true")
    subject_instability.set_defaults(func=command_subject_instability_audit)

    ranking_disagreement = subparsers.add_parser(
        "ranking-disagreement",
        help="Compute artifact-backed real-panel ranking sensitivity and baselines.",
    )
    ranking_disagreement.add_argument("--matrix", required=True)
    ranking_disagreement.add_argument("--irt", default=None)
    ranking_disagreement.add_argument("--output", required=True)
    ranking_disagreement.add_argument("--bootstrap", type=int, default=1000)
    ranking_disagreement.add_argument("--execute", action="store_true")
    ranking_disagreement.set_defaults(func=command_ranking_disagreement)

    real_panel_baselines_run = subparsers.add_parser(
        "real-panel-baselines",
        help="Compute random and subject-stratified real-panel baseline artifacts.",
    )
    real_panel_baselines_run.add_argument("--matrix", required=True)
    real_panel_baselines_run.add_argument("--predictions", default=None)
    real_panel_baselines_run.add_argument("--output", required=True)
    real_panel_baselines_run.add_argument("--bootstrap", type=int, default=1000)
    real_panel_baselines_run.add_argument("--execute", action="store_true")
    real_panel_baselines_run.set_defaults(func=command_real_panel_baselines)

    real_panel_baselines = subparsers.add_parser(
        "real-panel-baselines-preflight",
        help="Dry-run only manifest for future real-panel baseline and ablation analysis.",
    )
    real_panel_baselines.add_argument(
        "--config",
        default="configs/real_panel/baselines_mmlu.yaml",
    )
    real_panel_baselines.add_argument(
        "--output",
        default="results/preflight/real_panel_baselines_dryrun.json",
    )
    real_panel_baselines.add_argument("--dry-run", action="store_true")
    real_panel_baselines.add_argument("--execute-confirmatory-real-panel", action="store_true")
    real_panel_baselines.set_defaults(func=command_real_panel_baselines_preflight)

    panel_preflight = subparsers.add_parser(
        "panel-preflight",
        help="Dry-run only panel config preflight; does not contact local model services.",
    )
    panel_preflight.add_argument(
        "--config",
        default="configs/panels/ollama_local_small.yaml",
    )
    panel_preflight.add_argument("--output", default="results/preflight/panel_preflight.json")
    panel_preflight.add_argument("--dry-run", action="store_true")
    panel_preflight.add_argument("--execute-inference", action="store_true")
    panel_preflight.set_defaults(func=command_panel_preflight)

    benchmark_preflight = subparsers.add_parser(
        "benchmark-preflight",
        help="Dry-run only benchmark config and fixture-schema preflight.",
    )
    benchmark_preflight.add_argument(
        "--config",
        default="configs/benchmarks/gsm8k_audit.yaml",
    )
    benchmark_preflight.add_argument(
        "--output",
        default="results/preflight/benchmark_preflight.json",
    )
    benchmark_preflight.add_argument("--dry-run", action="store_true")
    benchmark_preflight.add_argument("--execute-evaluation", action="store_true")
    benchmark_preflight.set_defaults(func=command_benchmark_preflight)

    calibration_preflight = subparsers.add_parser(
        "calibration-preflight",
        help="Dry-run only logprob schema and calibration-plan preflight.",
    )
    calibration_preflight.add_argument(
        "--config",
        default="configs/calibration/mmlu_logprob_calibration.yaml",
    )
    calibration_preflight.add_argument(
        "--output",
        default="results/preflight/calibration_preflight.json",
    )
    calibration_preflight.add_argument("--dry-run", action="store_true")
    calibration_preflight.add_argument("--execute-analysis", action="store_true")
    calibration_preflight.set_defaults(func=command_calibration_preflight)

    power_materiality = subparsers.add_parser(
        "power-materiality-preflight",
        help="Dry-run only power/materiality analysis planning preflight.",
    )
    power_materiality.add_argument(
        "--config",
        default="configs/statistics/power_materiality_mmlu.yaml",
    )
    power_materiality.add_argument(
        "--output",
        default="results/preflight/power_materiality_preflight.json",
    )
    power_materiality.add_argument("--dry-run", action="store_true")
    power_materiality.add_argument("--execute-analysis", action="store_true")
    power_materiality.set_defaults(func=command_power_materiality_preflight)

    decoupled_synthetic = subparsers.add_parser(
        "decoupled-synthetic-preflight",
        help="Dry-run only API and claim-state preflight for the decoupled synthetic scaffold.",
    )
    decoupled_synthetic.add_argument(
        "--output",
        default="results/preflight/decoupled_synthetic_preflight.json",
    )
    decoupled_synthetic.add_argument("--dry-run", action="store_true")
    decoupled_synthetic.add_argument("--execute-decoupled-synthetic", action="store_true")
    decoupled_synthetic.set_defaults(func=command_decoupled_synthetic_preflight)

    import_kaggle_outputs_cmd = subparsers.add_parser(
        "import-kaggle-outputs",
        help="Import returned Kaggle benchmark ZIPs into versioned folders and wide caches.",
    )
    import_kaggle_outputs_cmd.add_argument("--input-dir", default="kaggle_outputs")
    import_kaggle_outputs_cmd.add_argument(
        "--output-root",
        default="data/external/kaggle_imported",
    )
    import_kaggle_outputs_cmd.add_argument("--cache-root", default="cache")
    import_kaggle_outputs_cmd.add_argument("--results-root", default="results")
    import_kaggle_outputs_cmd.add_argument("--strict", action="store_true")
    import_kaggle_outputs_cmd.set_defaults(func=command_import_kaggle_outputs_v4)

    post_import = subparsers.add_parser(
        "post-import-analysis",
        help="Run the V4 analysis router on one imported benchmark matrix.",
    )
    post_import.add_argument("--benchmark", required=True)
    post_import.add_argument("--matrix", required=True)
    post_import.add_argument("--predictions", default=None)
    post_import.add_argument("--output", required=True)
    post_import.add_argument("--cache-root", default="cache")
    post_import.add_argument("--results-root", default="results")
    post_import.add_argument("--bootstrap", type=int, default=100)
    post_import.add_argument("--execute", action="store_true")
    post_import.set_defaults(func=command_post_import_analysis_v4)

    cross_benchmark_analysis_cmd = subparsers.add_parser(
        "cross-benchmark-analysis",
        help="Compute V4 cross-benchmark stability and transfer artifacts from cached matrices.",
    )
    cross_benchmark_analysis_cmd.add_argument("--benchmarks", required=True)
    cross_benchmark_analysis_cmd.add_argument("--cache-root", default="cache")
    cross_benchmark_analysis_cmd.add_argument("--results-root", default="results")
    cross_benchmark_analysis_cmd.add_argument("--output", default="results/cross_benchmark")
    cross_benchmark_analysis_cmd.add_argument("--execute", action="store_true")
    cross_benchmark_analysis_cmd.set_defaults(func=command_cross_benchmark_analysis_v4)

    validate_run_v5 = subparsers.add_parser(
        "validate-run",
        help="Validate one V5 Kaggle result ZIP, or every ZIP under a directory, without extraction.",
    )
    validate_run_v5.add_argument("path", nargs="?", default="kaggle_outputs_v5")
    validate_run_v5.add_argument("--expected-study", default=None)
    validate_run_v5.add_argument("--expected-run", default=None)
    validate_run_v5.add_argument("--expected-benchmark", default=None)
    validate_run_v5.add_argument("--expected-config-hash", default=None)
    validate_run_v5.add_argument("--expected-zip-sha256", default=None)
    validate_run_v5.add_argument("--allow-nested-archives", action="store_true")
    validate_run_v5.add_argument("--strict", action="store_true")
    validate_run_v5.set_defaults(func=command_validate_run_v5)

    run_v6 = subparsers.add_parser(
        "run",
        help="Run, resume, validate, or package an exact V6 controlled execution config.",
    )
    run_v6.add_argument("--config", required=True, help="Frozen V6 run YAML.")
    run_v6.add_argument(
        "--mode",
        choices=RUN_MODES,
        help="Operational override; resume/validate_only/package_only preserve the frozen run hash.",
    )
    run_v6.add_argument(
        "--output-root",
        help="Override the output root without changing the frozen experimental condition.",
    )
    run_v6.set_defaults(func=command_run_v6)

    accept_s1_v6 = subparsers.add_parser(
        "accept-s1",
        help="Validate and optionally import the exact three V6 S1 engineering ZIPs.",
    )
    accept_s1_v6.add_argument("--input-dir", default="kaggle_outputs/v6")
    accept_s1_v6.add_argument("--output-root", default=None)
    accept_s1_v6.add_argument(
        "--minimum-extraction-reliability",
        type=float,
        default=0.95,
    )
    accept_s1_v6.set_defaults(func=command_accept_s1_v6)

    accept_s1_v7_2 = subparsers.add_parser(
        "accept-s1-v7-2",
        help="Fail-closed acceptance of the exact three native V7.2 S1 ZIPs.",
    )
    accept_s1_v7_2.add_argument("--input-dir", default="kaggle_icml2027_outputs/packages")
    accept_s1_v7_2.add_argument("--output-root", default="imported/v7_2/s1")
    accept_s1_v7_2.add_argument(
        "--minimum-extraction-reliability",
        type=float,
        default=0.95,
    )
    accept_s1_v7_2.set_defaults(func=command_accept_s1_v7_2)

    accept_s1_v7_2_1 = subparsers.add_parser(
        "accept-s1-v7-2-1",
        help="Fail-closed acceptance of the exact V7.2.1-tagged native S1 ZIPs.",
    )
    accept_s1_v7_2_1.add_argument("--input-dir", default="kaggle_icml2027_outputs/packages")
    accept_s1_v7_2_1.add_argument("--output-root", default="imported/v7_2_1/s1")
    accept_s1_v7_2_1.add_argument(
        "--minimum-extraction-reliability",
        type=float,
        default=0.95,
    )
    accept_s1_v7_2_1.set_defaults(func=command_accept_s1_v7_2)

    replay_cpu = subparsers.add_parser(
        "replay-cpu-evidence",
        help="Recompute and verify the registered CPU evidence summaries.",
    )
    replay_cpu.add_argument("--repository-root", default=".")
    replay_cpu.add_argument("--output", default="results/final_cpu_maxout/replay/cpu_replay.json")
    replay_cpu.set_defaults(func=command_replay_cpu_evidence)

    validate_release = subparsers.add_parser(
        "validate-release",
        help="Validate V7.2.1 source coherence and final CPU maxout release artifacts.",
    )
    validate_release.add_argument("--repository-root", default=".")
    validate_release.set_defaults(func=command_validate_release_v7_2_1)

    recalibrate_v6 = subparsers.add_parser(
        "recalibrate-runtime",
        help="Recalibrate S2-S4 planning ranges from accepted V6 S1 runtime fields.",
    )
    recalibrate_v6.add_argument("--input-root", default="imported/v6")
    recalibrate_v6.add_argument(
        "--output",
        default="results/planning/runtime_recalibration_v6.json",
    )
    recalibrate_v6.set_defaults(func=command_recalibrate_runtime_v6)

    recalibrate_v7_2 = subparsers.add_parser(
        "recalibrate-study-c-after-s1",
        help="Recalibrate S2-S4 distributions from accepted real V7.2.1 S1 outputs.",
    )
    recalibrate_v7_2.add_argument("--input-root", default="imported/v7_2_1/s1")
    recalibrate_v7_2.add_argument(
        "--output",
        default="results/final_cpu_maxout/planning/study_c_recalibration_after_s1.json",
    )
    recalibrate_v7_2.set_defaults(func=command_recalibrate_study_c_after_s1)

    import_kaggle_v5 = subparsers.add_parser(
        "import-kaggle",
        help="Fail-closed import of validated V5 Kaggle result ZIPs.",
    )
    import_kaggle_v5.add_argument("--input-dir", default="kaggle_outputs_v5")
    import_kaggle_v5.add_argument("--output-root", default="data/external/kaggle_imported_v5")
    import_kaggle_v5.add_argument("--cache-root", default="cache")
    import_kaggle_v5.add_argument("--results-root", default="results")
    import_kaggle_v5.add_argument("--expected-study", default=None)
    import_kaggle_v5.add_argument("--expected-benchmark", default=None)
    import_kaggle_v5.add_argument("--strict", action="store_true")
    import_kaggle_v5.set_defaults(func=command_import_kaggle_v5)

    post_import_v5 = subparsers.add_parser(
        "post-import",
        help="Build a fail-closed V5 analysis route from validated import receipts.",
    )
    post_import_v5.add_argument("--receipt", action="append", default=[])
    post_import_v5.add_argument("--import-root", default="data/external/kaggle_imported_v5")
    post_import_v5.add_argument(
        "--output",
        default="results/post_import_v5",
    )
    post_import_v5.add_argument("--minimum-extraction-reliability", type=float, default=0.95)
    post_import_v5.add_argument("--minimum-coverage", type=float, default=1.0)
    post_import_v5.add_argument("--strict", action="store_true")
    post_import_v5.set_defaults(func=command_post_import_v5)

    cross_benchmark_v5 = subparsers.add_parser(
        "cross-benchmark",
        help="Run the fail-closed V5 exact-checkpoint overlap gate and analysis.",
    )
    cross_benchmark_v5.add_argument(
        "--config",
        default="configs/analysis/cross_benchmark_confirmatory_v5.yaml",
    )
    cross_benchmark_v5.add_argument(
        "--matrix",
        action="append",
        default=[],
        metavar="BENCHMARK=PATH",
    )
    cross_benchmark_v5.add_argument(
        "--metadata",
        action="append",
        default=[],
        metavar="BENCHMARK=JSON",
    )
    cross_benchmark_v5.add_argument("--output", default="results/cross_benchmark_v5")
    cross_benchmark_v5.add_argument("--execute", action="store_true")
    cross_benchmark_v5.set_defaults(func=command_cross_benchmark_v5)

    build_evidence_ledger_v5 = subparsers.add_parser(
        "build-evidence-ledger",
        help="Rebuild the V5 claim-to-evidence ledger from primary local artifacts.",
    )
    build_evidence_ledger_v5.add_argument("--root", default=".")
    build_evidence_ledger_v5.add_argument(
        "--csv",
        default="results/evidence/claim_evidence_ledger_v5.csv",
    )
    build_evidence_ledger_v5.add_argument(
        "--report",
        default="reports/v5/VALID_EVAL_V5_CLAIM_EVIDENCE_LEDGER.md",
    )
    build_evidence_ledger_v5.set_defaults(func=command_build_evidence_ledger_v5)

    build_paper_assets_v5 = subparsers.add_parser(
        "build-paper-assets",
        help="Build V5 paper tables from the reproduced evidence and claim ledger.",
    )
    build_paper_assets_v5.add_argument("--root", default=".")
    build_paper_assets_v5.set_defaults(func=command_build_paper_assets_v5)

    build_release_v5 = subparsers.add_parser(
        "build-release",
        help="Audit or build one allowlist-only deterministic V5 release profile.",
    )
    build_release_v5.add_argument(
        "--profile", choices=["evidence", "reviewer", "source"], default="source"
    )
    build_release_v5.add_argument("--root", default=".")
    build_release_v5.add_argument("--build", action="store_true")
    build_release_v5.add_argument("--output", default=None)
    build_release_v5.set_defaults(func=command_build_release_v5)

    stats_check = subparsers.add_parser(
        "stats-check",
        help="Write a statistical grounding report over existing result artifacts.",
    )
    stats_check.add_argument("--results", required=True)
    stats_check.add_argument("--output", required=True)
    stats_check.set_defaults(func=command_stats_check)

    validate_benchmark_file = subparsers.add_parser(
        "validate-benchmark-file",
        parents=[common],
        help="Validate a local benchmark item file before a real audit.",
    )
    validate_benchmark_file.add_argument("--items", required=True)
    validate_benchmark_file.set_defaults(func=command_validate_benchmark_file)

    score_outputs = subparsers.add_parser(
        "score-outputs",
        parents=[common],
        help="Score raw cached outputs with the frozen benchmark scorer.",
    )
    score_outputs.add_argument("--items", required=True)
    score_outputs.add_argument("--input", required=True)
    score_outputs.add_argument("--output", required=True)
    score_outputs.add_argument("--prompt-variant", default="full")
    score_outputs.set_defaults(func=command_score_outputs)

    validate_alignment_cmd = subparsers.add_parser(
        "validate-alignment",
        parents=[common],
        help="Validate alignment between benchmark items and cached predictions.",
    )
    validate_alignment_cmd.add_argument("--items", required=True)
    validate_alignment_cmd.add_argument("--predictions", required=True)
    validate_alignment_cmd.add_argument("--required-variants", nargs="*", default=None)
    validate_alignment_cmd.add_argument("--min-models", type=int, default=8)
    validate_alignment_cmd.set_defaults(func=command_validate_alignment)

    extraction_audit_cmd = subparsers.add_parser(
        "extraction-audit",
        parents=[common],
        help="Run extraction-only validation on raw cached outputs.",
    )
    extraction_audit_cmd.add_argument("--items", required=True)
    extraction_audit_cmd.add_argument("--outputs", required=True)
    extraction_audit_cmd.add_argument("--prompt-variant", default="full")
    extraction_audit_cmd.add_argument("--success-threshold", type=float, default=0.95)
    extraction_audit_cmd.set_defaults(func=command_extraction_audit)

    validate_prompt_variants_cmd = subparsers.add_parser(
        "validate-prompt-variants",
        parents=[common],
        help="Check cached outputs and matrices for preregistered prompt variants.",
    )
    validate_prompt_variants_cmd.add_argument("--items", default=None)
    validate_prompt_variants_cmd.add_argument(
        "--required-variants",
        nargs="+",
        default=GPQA_VARIANTS,
    )
    validate_prompt_variants_cmd.set_defaults(func=command_validate_prompt_variants)

    gpqa_go_no_go = subparsers.add_parser(
        "gpqa-go-no-go",
        parents=[common],
        help="Write the GPQA Diamond real-audit go/no-go checklist.",
    )
    gpqa_go_no_go.add_argument("--items", required=True)
    gpqa_go_no_go.add_argument("--required-variants", nargs="*", default=None)
    gpqa_go_no_go.add_argument("--min-models", type=int, default=8)
    gpqa_go_no_go.add_argument("--extraction-success-threshold", type=float, default=0.95)
    gpqa_go_no_go.add_argument("--config", default=None)
    gpqa_go_no_go.set_defaults(func=command_gpqa_go_no_go)

    audit_manifest = subparsers.add_parser(
        "audit-manifest",
        parents=[common],
        help="Hash GPQA real-audit configs, prompt templates, inputs, and cached outputs.",
    )
    audit_manifest.add_argument("--items", required=True)
    audit_manifest.add_argument("--config", default=None)
    audit_manifest.set_defaults(func=command_audit_manifest)

    export_gpqa = subparsers.add_parser(
        "export-gpqa-diamond",
        help="Export a local GPQA Diamond source into ValidEval's local JSONL schema.",
    )
    export_gpqa.add_argument("--source", choices=["hf"], default=None)
    export_gpqa.add_argument("--source-file", default=None)
    export_gpqa.add_argument("--output", required=True)
    export_gpqa.add_argument("--seed", type=int, default=0)
    export_gpqa.add_argument("--results-root", default="results")
    export_gpqa.add_argument("--hf-path", default="Idavidrein/gpqa")
    export_gpqa.add_argument("--hf-name", default="gpqa_diamond")
    export_gpqa.add_argument("--hf-split", default="train")
    export_gpqa.set_defaults(func=command_export_gpqa_diamond)

    check_panel_cmd = subparsers.add_parser(
        "check-panel",
        parents=[common],
        help="Check local/cached readiness for a model panel.",
    )
    check_panel_cmd.set_defaults(func=command_check_panel)

    generate_outputs = subparsers.add_parser(
        "generate-outputs",
        parents=[common],
        help="Generate cached raw outputs for GPQA using local/open runners.",
    )
    generate_outputs.add_argument("--items", required=True)
    generate_outputs.add_argument(
        "--prompt-variant",
        default="full",
    )
    generate_outputs.add_argument("--output-dir", required=True)
    generate_outputs.add_argument("--limit-items", type=int, default=None)
    generate_outputs.add_argument("--temperature", type=float, default=0.0)
    generate_outputs.add_argument("--overwrite", action="store_true")
    generate_outputs.add_argument("--dry-run-mock", action="store_true")
    generate_outputs.set_defaults(func=command_generate_outputs)

    audit = subparsers.add_parser("audit", parents=[common], help="Run validity diagnostics.")
    audit.add_argument(
        "benchmark_path",
        nargs="?",
        help="Optional benchmark scaffold directory or BenchmarkItem JSONL file.",
    )
    audit.add_argument("--diagnostics", nargs="+", default=None)
    audit.add_argument(
        "--dry-run",
        action="store_true",
        help="Label artifacts as dry-run outputs and render report/evidence files after diagnostics.",
    )
    audit.add_argument("--from-cache", action="store_true")
    audit.add_argument("--input-validated-only", action="store_true")
    audit.add_argument("--dry-run-real", action="store_true")
    audit.add_argument("--required-variants", nargs="*", default=None)
    audit.add_argument("--min-models", type=int, default=8)
    audit.add_argument(
        "--domain",
        choices=[pack.domain_id for pack in list_domain_packs()],
        default=None,
        help="Add diagnostics from a domain-specific validity pack.",
    )
    audit.add_argument("--config", default="configs/default.yaml")
    audit.set_defaults(func=command_audit)

    domain = subparsers.add_parser("domain", help="List and describe domain validity packs.")
    domain_subparsers = domain.add_subparsers(dest="domain_command", required=True)
    domain_list = domain_subparsers.add_parser("list", help="List available domain packs.")
    domain_list.set_defaults(func=command_domain_list)
    domain_describe = domain_subparsers.add_parser(
        "describe",
        help="Describe one domain pack, its threats, diagnostics, and repair policies.",
    )
    domain_describe.add_argument(
        "domain_id", choices=[pack.domain_id for pack in list_domain_packs()]
    )
    domain_describe.set_defaults(func=command_domain_describe)

    schema = subparsers.add_parser("schema", help="Export and validate standard JSON schemas.")
    schema_subparsers = schema.add_subparsers(dest="schema_command", required=True)
    schema_export = schema_subparsers.add_parser("export", help="Export JSON Schema files.")
    schema_export.add_argument("schema_name", choices=[*schema_names(), "all"])
    schema_export.add_argument("--output", default="docs/schemas")
    schema_export.set_defaults(func=command_schema_export)
    schema_validate = schema_subparsers.add_parser("validate", help="Validate JSON/JSONL payloads.")
    schema_validate.add_argument("schema_name", choices=schema_names())
    schema_validate.add_argument("--path", required=True)
    schema_validate.set_defaults(func=command_schema_validate)

    plugins = subparsers.add_parser("plugins", help="List registered extension plugins.")
    plugins_subparsers = plugins.add_subparsers(dest="plugins_command", required=True)
    plugins_list = plugins_subparsers.add_parser("list", help="List registered plugins.")
    plugins_list.add_argument("--kind", choices=list(PLUGIN_KINDS), default=None)
    plugins_list.set_defaults(func=command_plugins_list)

    import_cmd = subparsers.add_parser(
        "import-outputs",
        help="Normalize local outputs from external evaluation frameworks.",
    )
    import_cmd.add_argument("--input", required=True)
    import_cmd.add_argument("--output", required=True)
    import_cmd.add_argument("--adapter", choices=SUPPORTED_IMPORTERS, default="generic-jsonl")
    import_cmd.add_argument("--benchmark-id", default="imported")
    import_cmd.add_argument("--prompt-variant", default="full")
    import_cmd.set_defaults(func=command_import_outputs)

    quickstart = subparsers.add_parser(
        "quickstart-audit",
        help="Run an offline one-hour audit scaffold from items and optional model outputs.",
    )
    quickstart.add_argument("--items", required=True)
    quickstart.add_argument("--outputs", default=None)
    quickstart.add_argument("--benchmark-card", default=None)
    quickstart.add_argument("--output-dir", default="quickstart_audit")
    quickstart.add_argument("--adapter", choices=SUPPORTED_IMPORTERS, default="generic-jsonl")
    quickstart.add_argument("--seed", type=int, default=0)
    quickstart.set_defaults(func=command_quickstart_audit)

    init_cmd = subparsers.add_parser(
        "init-benchmark",
        help="Create a benchmark-author scaffold.",
    )
    init_cmd.add_argument("path")
    init_cmd.add_argument("--overwrite", action="store_true")
    init_cmd.set_defaults(func=command_init_benchmark)

    validate_benchmark_cmd = subparsers.add_parser(
        "validate-benchmark",
        help="Validate a benchmark-author scaffold.",
    )
    validate_benchmark_cmd.add_argument("path")
    validate_benchmark_cmd.set_defaults(func=command_validate_benchmark)

    generate_card_cmd = subparsers.add_parser(
        "generate-card",
        help="Generate a benchmark card from a scaffold.",
    )
    generate_card_cmd.add_argument("path")
    generate_card_cmd.add_argument("--no-overwrite", action="store_true")
    generate_card_cmd.set_defaults(func=command_generate_card)

    design = subparsers.add_parser(
        "design-assistant",
        help="Generate construct, audit, card, human-validation, and threat-model scaffolds.",
    )
    design.add_argument("--noninteractive", action="store_true")
    design.add_argument("--benchmark-id", required=True)
    design.add_argument("--construct", default="")
    design.add_argument("--intended-decisions", default="")
    design.add_argument("--item-format", default="mcq")
    design.add_argument("--scoring-method", default="exact_or_mcq")
    design.add_argument("--domain", default="general")
    design.add_argument("--shortcuts", default="")
    design.add_argument("--critical-fields", default="")
    design.add_argument("--human-validation", default="recommended")
    design.add_argument("--metrics", default="")
    design.add_argument("--invalidating-conditions", default="")
    design.add_argument("--output-dir", default="design_assistant")
    design.set_defaults(func=command_design_assistant)

    preregister = subparsers.add_parser(
        "preregister",
        help="Generate a preregistration scaffold for a benchmark audit.",
    )
    preregister.add_argument("--benchmark", required=True)
    preregister.add_argument("--goal", default="")
    preregister.add_argument("--domain", default="general")
    preregister.add_argument("--panel", default="TBD")
    preregister.add_argument("--artifact-scope", default="TBD")
    preregister.add_argument("--diagnostics", nargs="*", default=None)
    preregister.add_argument("--output-dir", default="docs/protocols")
    preregister.set_defaults(func=command_preregister)

    advisor = subparsers.add_parser(
        "advisor",
        help="Recommend benchmark types, threats, diagnostics, and safe claims for an eval goal.",
    )
    advisor.add_argument("--goal", required=True)
    advisor.set_defaults(func=command_advisor)

    doctor = subparsers.add_parser(
        "doctor",
        parents=[common],
        help="Run a metadata-only local readiness and artifact-hygiene check.",
    )
    doctor.add_argument("--config", default="configs/default.yaml")
    doctor.add_argument("--required-variants", nargs="*", default=None)
    doctor.add_argument("--required-diagnostics", nargs="*", default=None)
    doctor.add_argument("--cpu-maxout", action="store_true")
    doctor.add_argument("--require-gpu", action="store_true")
    doctor.add_argument("--repository-root", default=".")
    doctor.add_argument("--output-root", default="kaggle_icml2027_outputs")
    doctor.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero unless every readiness check passes.",
    )
    doctor.set_defaults(func=command_doctor)

    paper_assets = subparsers.add_parser(
        "paper-assets",
        parents=[common],
        help="Generate paper figures and LaTeX tables from local results artifacts.",
    )
    paper_assets.add_argument("--paper-dir", default="paper")
    paper_assets.set_defaults(func=command_paper_assets)

    bundle = subparsers.add_parser(
        "bundle",
        parents=[common],
        help="Build a reproducibility bundle for an audit.",
    )
    bundle.add_argument("--output-dir", default="bundles")
    bundle.add_argument("--configs", nargs="*", default=["configs/default.yaml"])
    bundle.set_defaults(func=command_bundle)

    verify_bundle_cmd = subparsers.add_parser(
        "verify-bundle",
        help="Verify bundle manifest hashes and required reproduction files.",
    )
    verify_bundle_cmd.add_argument("bundle_path")
    verify_bundle_cmd.set_defaults(func=command_verify_bundle)

    reviewer_risk = subparsers.add_parser(
        "reviewer-risk",
        help="Audit a report for overclaiming and missing reviewer-facing disclosures.",
    )
    reviewer_risk.add_argument("--report", required=True)
    reviewer_risk.add_argument("--output", default=None)
    reviewer_risk.set_defaults(func=command_reviewer_risk)

    environment = subparsers.add_parser(
        "environment",
        help="Capture Python, OS, package, git, command, config, and seed metadata.",
    )
    environment.add_argument("--output", default="environment.json")
    environment.add_argument("--command-text", default=None)
    environment.add_argument("--configs", nargs="*", default=["configs/default.yaml"])
    environment.add_argument("--seed", type=int, default=0)
    environment.set_defaults(func=command_environment)

    neurips_readiness = subparsers.add_parser(
        "neurips-readiness",
        parents=[common],
        help="Write a NeurIPS-oriented publication readiness report from local artifacts.",
    )
    neurips_readiness.add_argument("--paper-dir", default="paper")
    neurips_readiness.add_argument("--output-dir", default="paper")
    neurips_readiness.add_argument("--report", default=None)
    neurips_readiness.add_argument("--bundle-path", default=None)
    neurips_readiness.add_argument(
        "--validation-summary",
        default="validation_reports/diagnostic_validation_summary.json",
    )
    neurips_readiness.add_argument("--real-benchmark", default="gpqa_diamond")
    neurips_readiness.add_argument(
        "--real-panel",
        default="gpqa_minimal_open_local_amended_v2_compliant",
    )
    neurips_readiness.add_argument("--go-no-go-path", default=None)
    neurips_readiness.add_argument(
        "--evidence-lock",
        default="NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md",
        help="No-run evidence-state lock that must preserve blocked/weak claim markers.",
    )
    neurips_readiness.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero unless every required publication-readiness gate passes.",
    )
    neurips_readiness.set_defaults(func=command_neurips_readiness)

    baselines = subparsers.add_parser(
        "baselines",
        parents=[common],
        help="Run shallow heuristic baselines and report the dumb baseline gap.",
    )
    baselines.add_argument("--config", default="configs/default.yaml")
    baselines.set_defaults(func=command_baselines)

    diagnostics = subparsers.add_parser(
        "diagnostics",
        parents=[common],
        help="Run one core validity diagnostic.",
    )
    diagnostics.add_argument(
        "diagnostic",
        choices=[
            "answer-distribution",
            "contamination",
            "data-forensics",
            "distractor-quality",
            "distractors",
            "prompt-sensitivity",
            "extraction-robustness",
        ],
    )
    diagnostics.add_argument("--config", default="configs/default.yaml")
    diagnostics.add_argument("--from-cache", action="store_true")
    diagnostics.add_argument("--sanitized", action="store_true")
    diagnostics.set_defaults(func=command_core_diagnostic)

    psychometrics = subparsers.add_parser(
        "psychometrics",
        parents=[common],
        help="Run one advanced psychometric diagnostic.",
    )
    psychometrics.add_argument(
        "diagnostic",
        choices=["irt", "saturation", "power", "dif", "calibration", "all"],
    )
    psychometrics.add_argument("--config", default="configs/default.yaml")
    psychometrics.set_defaults(func=command_psychometrics)

    report = subparsers.add_parser(
        "report", parents=[common], help="Render a Markdown report card."
    )
    report.set_defaults(func=command_report)

    audit_summary = subparsers.add_parser(
        "audit-summary",
        parents=[common],
        help="Print a compact terminal summary of diagnostic results.",
    )
    audit_summary.set_defaults(func=command_audit_summary)

    ranking = subparsers.add_parser("ranking", parents=[common], help="Compare model rankings.")
    ranking.set_defaults(func=command_ranking)

    repair = subparsers.add_parser(
        "repair",
        parents=[common],
        help="Generate item forensics and an advisory repaired subset.",
    )
    repair.add_argument(
        "benchmark_path",
        nargs="?",
        help="Optional benchmark scaffold directory or BenchmarkItem JSONL file.",
    )
    repair.add_argument("--policy", choices=policy_names(), default="conservative")
    repair.add_argument("--target-size", type=int, default=None)
    repair.set_defaults(func=command_repair)

    card = subparsers.add_parser(
        "card",
        help="Render validity cards from existing audit artifacts.",
    )
    card_subparsers = card.add_subparsers(dest="card_command", required=True)
    card_render = card_subparsers.add_parser(
        "render",
        parents=[common],
        help="Render Validity Card JSON and Markdown.",
    )
    card_render.set_defaults(func=command_card_render)

    certificate = subparsers.add_parser(
        "certificate",
        help="Issue audit-completeness evidence profiles.",
    )
    certificate_subparsers = certificate.add_subparsers(
        dest="certificate_command",
        required=True,
    )
    certificate_issue = certificate_subparsers.add_parser(
        "issue",
        parents=[common],
        help="Issue an audit-completeness evidence profile.",
    )
    certificate_issue.add_argument(
        "benchmark_path",
        nargs="?",
        help="Optional benchmark scaffold directory or BenchmarkItem JSONL file.",
    )
    certificate_issue.set_defaults(func=command_certificate_issue)

    checklist = subparsers.add_parser(
        "checklist",
        parents=[common],
        help="Generate a benchmark-author checklist.",
    )
    checklist.set_defaults(func=command_checklist)

    evidence_matrix = subparsers.add_parser(
        "evidence-matrix",
        parents=[common],
        help="Generate a claim-to-evidence matrix.",
    )
    evidence_matrix.set_defaults(func=command_evidence_matrix)

    leaderboard = subparsers.add_parser(
        "leaderboard",
        parents=[common],
        help="Build ranking views, flips, badges, registry, atlas, and dashboard exports.",
    )
    leaderboard.add_argument("--bootstrap-samples", type=int, default=500)
    leaderboard.set_defaults(func=command_leaderboard)

    badges = subparsers.add_parser(
        "badges",
        parents=[common],
        help="Generate per-dimension benchmark-health badges.",
    )
    badges.set_defaults(func=command_badges)

    registry = subparsers.add_parser("registry", help="Manage the audit registry.")
    registry_subparsers = registry.add_subparsers(dest="registry_command", required=True)
    registry_validate = registry_subparsers.add_parser(
        "validate",
        help="Validate registry JSON files.",
    )
    registry_validate.add_argument("--registry-root", default="registry")
    registry_validate.set_defaults(func=command_registry_validate)
    registry_list = registry_subparsers.add_parser("list", help="List registered audits.")
    registry_list.add_argument("--registry-root", default="registry")
    registry_list.set_defaults(func=command_registry_list)
    registry_add = registry_subparsers.add_parser(
        "add",
        parents=[common],
        help="Add the current audit to the registry.",
    )
    registry_add.add_argument("--status", default="complete")
    registry_add.set_defaults(func=command_registry_add)

    atlas = subparsers.add_parser(
        "atlas",
        parents=[common],
        help="Build benchmark atlas JSON and Markdown.",
    )
    atlas.set_defaults(func=command_atlas)

    dashboard = subparsers.add_parser("dashboard", help="Build dashboard data exports.")
    dashboard_subparsers = dashboard.add_subparsers(dest="dashboard_command", required=True)
    dashboard_export = dashboard_subparsers.add_parser(
        "export",
        parents=[common],
        help="Export dashboard JSON and CSV data.",
    )
    dashboard_export.set_defaults(func=command_dashboard_export)

    site = subparsers.add_parser("site", help="Build static dashboard site.")
    site_subparsers = site.add_subparsers(dest="site_command", required=True)
    site_build = site_subparsers.add_parser(
        "build",
        help="Build static HTML/CSS/JSON pages.",
    )
    site_build.add_argument("--site-root", default="site")
    site_build.add_argument("--registry-root", default="registry")
    site_build.add_argument("--leaderboard-root", default="leaderboard")
    site_build.add_argument("--results-root", default="results")
    site_build.add_argument("--reportcards-root", default="reportcards")
    site_build.set_defaults(func=command_site_build)

    audit_diff = subparsers.add_parser("audit-diff", help="Compare two audit artifact directories.")
    audit_diff.add_argument("old")
    audit_diff.add_argument("new")
    audit_diff.add_argument("--output", default=None)
    audit_diff.set_defaults(func=command_audit_diff)

    forensics = subparsers.add_parser(
        "forensics",
        help="Run local data-forensics utilities without remote web or paid APIs.",
    )
    forensics_subparsers = forensics.add_subparsers(dest="forensics_command", required=True)
    overlap = forensics_subparsers.add_parser(
        "overlap",
        parents=[common],
        help="Scan a local corpus for exact, question, answer, and n-gram overlap.",
    )
    overlap.add_argument("--corpus", required=True)
    overlap.add_argument("--ngram-n", type=int, default=5)
    overlap.set_defaults(func=command_forensics_overlap)

    human = subparsers.add_parser(
        "human",
        help="Generate annotation packets and audit human/judge scoring reliability.",
    )
    human_subparsers = human.add_subparsers(dest="human_command", required=True)
    human_packet = human_subparsers.add_parser(
        "packet",
        parents=[common],
        help="Generate an offline annotation packet.",
    )
    human_packet.add_argument("--sample-size", type=int, default=100)
    human_packet.add_argument(
        "--strategy",
        choices=[
            "random",
            "high-disagreement",
            "low-discrimination",
            "shortcut-suspicious",
            "scorer-sensitive",
            "coverage-balanced",
            "ranking-critical",
        ],
        default="random",
    )
    human_packet.set_defaults(func=command_human_packet)

    human_import = human_subparsers.add_parser(
        "import",
        parents=[common],
        help="Import and validate human annotation CSV/JSONL files.",
    )
    human_import.add_argument("--path", required=True)
    human_import.set_defaults(func=command_human_import)

    human_agreement = human_subparsers.add_parser(
        "agreement",
        parents=[common],
        help="Compute human annotation agreement statistics.",
    )
    human_agreement.add_argument("--bootstrap-samples", type=int, default=200)
    human_agreement.set_defaults(func=command_human_agreement)

    human_judge = human_subparsers.add_parser(
        "judge",
        parents=[common],
        help="Run deterministic judge variants and compare against human labels when available.",
    )
    human_judge.add_argument("--sample-size", type=int, default=100)
    human_judge.add_argument("--strategy", default="random")
    human_judge.add_argument(
        "--variants",
        nargs="*",
        choices=["strict", "lenient", "regex", "mock"],
        default=None,
    )
    human_judge.set_defaults(func=command_human_judge)

    human_ambiguity = human_subparsers.add_parser(
        "ambiguity",
        parents=[common],
        help="Export scoring ambiguity triage rows.",
    )
    human_ambiguity.add_argument("--sample-size", type=int, default=100)
    human_ambiguity.add_argument("--strategy", default="random")
    human_ambiguity.set_defaults(func=command_human_ambiguity)

    human_adjudication = human_subparsers.add_parser(
        "adjudication",
        parents=[common],
        help="Create adjudication queues from ambiguity artifacts.",
    )
    human_adjudication.add_argument("--sample-size", type=int, default=100)
    human_adjudication.add_argument("--strategy", default="random")
    human_adjudication.set_defaults(func=command_human_adjudication)

    human_ui = human_subparsers.add_parser(
        "ui",
        parents=[common],
        help="Render a dependency-free static annotation viewer.",
    )
    human_ui.add_argument("--sample-size", type=int, default=100)
    human_ui.add_argument("--strategy", default="random")
    human_ui.set_defaults(func=command_human_ui)

    validate_diagnostics = subparsers.add_parser(
        "validate-diagnostics",
        help="Run synthetic detector-validation sweeps for ValidEval diagnostics.",
    )
    validate_diagnostics.add_argument("--config", default=None)
    validate_diagnostics.add_argument("--diagnostic", default=None)
    validate_diagnostics.add_argument("--flaw", default=None)
    validate_diagnostics.add_argument("--output-dir", default="validation_reports")
    validate_diagnostics.add_argument("--n-items", type=int, default=64)
    validate_diagnostics.add_argument("--strength-grid", nargs="*", type=float, default=None)
    validate_diagnostics.add_argument("--seeds", nargs="*", type=int, default=None)
    validate_diagnostics.set_defaults(func=command_validate_diagnostics)

    cross_flaw = subparsers.add_parser(
        "validate-diagnostics-cross-flaw",
        help="Run detector-by-flaw synthetic specificity validation.",
    )
    cross_flaw.add_argument("--config", default="configs/validation/synthetic_default.yaml")
    cross_flaw.add_argument("--output", default="validation_reports/cross_flaw_confusion")
    cross_flaw.set_defaults(func=command_validate_diagnostics_cross_flaw)

    heldout = subparsers.add_parser(
        "validate-diagnostics-heldout",
        help="Run held-out synthetic generator transfer validation.",
    )
    heldout.add_argument("--config", default="configs/validation/heldout_default.yaml")
    heldout.add_argument("--output", default="validation_reports/heldout_generators")
    heldout.set_defaults(func=command_validate_diagnostics_heldout)

    validation_report = subparsers.add_parser(
        "validation-report",
        help="Render or refresh the synthetic diagnostic-validation summary report.",
    )
    validation_report.add_argument("--report-dir", default="validation_reports")
    validation_report.set_defaults(func=command_validation_report)

    validation_summary = subparsers.add_parser(
        "validation-summary",
        help="Print the synthetic diagnostic-validation summary JSON.",
    )
    validation_summary.add_argument("--report-dir", default="validation_reports")
    validation_summary.set_defaults(func=command_validation_summary)

    generate_synthetic = subparsers.add_parser(
        "generate-synthetic",
        help="Generate a controlled synthetic benchmark JSONL for inspection.",
    )
    generate_synthetic.add_argument("--flaw", default="clean")
    generate_synthetic.add_argument("--strength", type=float, default=0.0)
    generate_synthetic.add_argument("--seed", type=int, default=0)
    generate_synthetic.add_argument("--n-items", type=int, default=64)
    generate_synthetic.add_argument("--output", default=None)
    generate_synthetic.set_defaults(func=command_generate_synthetic)

    validate = subparsers.add_parser("validate-config", help="Validate that a YAML config loads.")
    validate.add_argument("path")
    validate.set_defaults(func=command_validate_config)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        _print(f"[red]Error:[/red] {exc}" if console is not None else f"Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
