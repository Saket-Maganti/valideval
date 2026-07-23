from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.human.reporting import (
    human_validated_subset_status,
    judge_reliability_status,
    read_human_artifacts,
    validity_card_human_summary,
)
from valideval.repair.diff import compute_repair_diff, render_repair_report
from valideval.repair.recommendations import (
    build_author_checklist,
    build_claim_evidence_matrix,
    confidence_level,
    generate_misuse_warnings,
    recommend_item,
)
from valideval.repair.subset_selection import select_subset
from valideval.schemas import DiagnosticResult, ResponseMatrix, utc_now
from valideval.scoring.mcq_utils import accepted_labels

ITEM_FORENSICS_FIELDS = [
    "item_id",
    "difficulty",
    "discrimination",
    "negative_discrimination",
    "too_easy_hard",
    "shortcut_suspiciousness",
    "prompt_instability",
    "scorer_instability",
    "duplicate_cluster",
    "contamination_overlap",
    "temporal_risk",
    "provenance_missing",
    "coverage_tag",
    "coverage_critical",
    "human_ambiguity_flag",
    "recommendation",
    "confidence_level",
]

VALIDITY_CARD_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ValidEval Validity Card",
    "type": "object",
    "required": [
        "schema_version",
        "identity",
        "version_hash",
        "construct",
        "diagnostics",
        "misuse_warnings",
        "reproduction",
    ],
    "properties": {
        "schema_version": {"type": "string"},
        "identity": {"type": "object"},
        "version_hash": {"type": "object"},
        "construct": {"type": "object"},
        "intended_uses": {"type": "array", "items": {"type": "string"}},
        "non_intended_uses": {"type": "array", "items": {"type": "string"}},
        "diagnostics": {"type": "array", "items": {"type": "string"}},
        "misuse_warnings": {"type": "array", "items": {"type": "string"}},
        "reproduction": {"type": "array", "items": {"type": "string"}},
    },
}


def build_item_forensics_table(
    benchmark: Benchmark,
    results: list[DiagnosticResult],
) -> list[dict[str, Any]]:
    by_name = _by_name(results)
    items = benchmark.load_items()
    tag_counts = Counter(tag for item in items for tag in item.construct_tags)
    duplicate_map = _duplicate_clusters(by_name.get("data_forensics"))
    rows: list[dict[str, Any]] = []
    for item in items:
        item_id = item.item_id
        irt = _item_metrics(by_name, "irt", item_id)
        shortcut = _item_metrics(by_name, "shortcut", item_id)
        reliability = _item_metrics(by_name, "reliability", item_id)
        extraction = _item_metrics(by_name, "extraction_robustness", item_id)
        forensics = _item_metrics(by_name, "data_forensics", item_id)
        temporal = forensics.get("temporal_validity", {})
        provenance = forensics.get("provenance_completeness", {})
        overlap = forensics.get("corpus_overlap", {})
        row = {
            "item_id": item_id,
            "difficulty": irt.get("difficulty"),
            "discrimination": irt.get("discrimination"),
            "negative_discrimination": bool(irt.get("negative_discrimination", False)),
            "too_easy_hard": _too_easy_hard(irt),
            "shortcut_suspiciousness": shortcut.get("suspiciousness"),
            "prompt_instability": _instability_from_stability(
                reliability.get("mean_item_stability")
            ),
            "scorer_instability": extraction.get("extractor_disagreement_rate"),
            "duplicate_cluster": duplicate_map.get(item_id, ""),
            "contamination_overlap": overlap.get("risk_level", "unknown/unmeasured"),
            "temporal_risk": _temporal_risk(temporal),
            "provenance_missing": _provenance_missing_fraction(provenance),
            "coverage_tag": ";".join(item.construct_tags or ["untagged"]),
            "coverage_critical": any(tag_counts[tag] <= 1 for tag in item.construct_tags),
            "human_ambiguity_flag": bool(
                extraction.get("scoring_ambiguity_flag")
                or len(accepted_labels(item)) > 1
                or "ambiguous_scoring_risk" in item.construct_tags
            ),
        }
        row["recommendation"] = recommend_item(row)
        row["confidence_level"] = confidence_level(row)
        rows.append(row)
    return rows


def write_item_forensics_csv(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ITEM_FORENSICS_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in ITEM_FORENSICS_FIELDS})
    return output


def run_repair(
    benchmark: Benchmark,
    panel_id: str,
    results: list[DiagnosticResult],
    matrix: ResponseMatrix | None,
    *,
    output_dir: str | Path,
    policy: str = "conservative",
    target_size: int | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = build_item_forensics_table(benchmark, results)
    item_forensics_path = write_item_forensics_csv(output / "item_forensics.csv", rows)
    selection = select_subset(rows, policy_name=policy, target_size=target_size)
    diff = compute_repair_diff(
        rows,
        selection["selected_item_ids"],
        selection["removed_items"],
        matrix,
    )
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "benchmark_id": benchmark.benchmark_id,
        "panel_id": panel_id,
        "policy": policy,
        "policy_description": selection["policy_description"],
        "item_forensics_csv": str(item_forensics_path),
        "selection": selection,
        "diff": diff,
        "limitations": [
            "Repair recommendations are advisory and require benchmark-author review.",
            "Subset metrics are conditional on the audited model panel and cached diagnostics.",
        ],
    }
    diff_path = output / "repair_diff.json"
    _write_json(diff_path, payload)
    report_path = output / "repair_report.md"
    report_path.write_text(
        render_repair_report(
            diff,
            policy=policy,
            policy_description=selection["policy_description"],
        ),
        encoding="utf-8",
    )
    return {
        "item_forensics_csv": str(item_forensics_path),
        "repair_diff_json": str(diff_path),
        "repair_report_md": str(report_path),
        "selected_item_ids": selection["selected_item_ids"],
        "removed_item_count": diff["removed_item_count"],
    }


def render_validity_card(
    benchmark: Benchmark,
    panel_id: str,
    results: list[DiagnosticResult],
    *,
    output_dir: str | Path,
    manifest: dict[str, Any] | None = None,
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    warnings = generate_misuse_warnings(benchmark, results)
    human_summary = read_human_artifacts(output)
    payload = _validity_card_payload(
        benchmark,
        panel_id,
        results,
        manifest or {},
        warnings,
        human_summary=human_summary,
    )
    json_path = output / "validity_card.json"
    markdown_path = output / "validity_card.md"
    _write_json(json_path, payload)
    markdown_path.write_text(_render_validity_card_markdown(payload), encoding="utf-8")
    return {"validity_card_json": str(json_path), "validity_card_md": str(markdown_path)}


def issue_certificate(
    benchmark: Benchmark,
    panel_id: str,
    results: list[DiagnosticResult],
    *,
    output_dir: str | Path,
    manifest: dict[str, Any] | None = None,
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    payload = _certificate_payload(
        benchmark,
        panel_id,
        results,
        manifest or {},
        human_summary=read_human_artifacts(output),
    )
    json_path = output / "validity_certificate.json"
    markdown_path = output / "validity_certificate.md"
    _write_json(json_path, payload)
    markdown_path.write_text(_render_certificate_markdown(payload), encoding="utf-8")
    return {
        "validity_certificate_json": str(json_path),
        "validity_certificate_md": str(markdown_path),
    }


def render_checklist(
    benchmark: Benchmark,
    results: list[DiagnosticResult],
    *,
    output_dir: str | Path,
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "benchmark_id": benchmark.benchmark_id,
        "checklist": build_author_checklist(benchmark, results),
        "limitations": ["Checklist status is advisory and depends on available local artifacts."],
    }
    json_path = output / "author_checklist.json"
    markdown_path = output / "author_checklist.md"
    _write_json(json_path, payload)
    markdown_path.write_text(_render_checklist_markdown(payload), encoding="utf-8")
    return {"checklist_json": str(json_path), "checklist_md": str(markdown_path)}


def render_evidence_matrix(
    benchmark: Benchmark,
    panel_id: str,
    results: list[DiagnosticResult],
    *,
    output_dir: str | Path,
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = build_claim_evidence_matrix(benchmark, results)
    artifact_scope = benchmark.construct_spec.metadata.get("artifact_scope", "unspecified")
    json_path = output / "claim_evidence_matrix.json"
    md_path = output / "claim_evidence_matrix.md"
    csv_path = output / "claim_evidence_matrix.csv"
    _write_json(
        json_path,
        {
            "schema_version": "0.1",
            "created_at": utc_now(),
            "benchmark_id": benchmark.benchmark_id,
            "panel_id": panel_id,
            "artifact_scope": artifact_scope,
            "claims": rows,
        },
    )
    md_path.write_text(
        _render_evidence_matrix_markdown(rows, artifact_scope=artifact_scope),
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["claim", "evidence_needed", "diagnostic", "result", "status"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return {
        "evidence_matrix_json": str(json_path),
        "evidence_matrix_md": str(md_path),
        "evidence_matrix_csv": str(csv_path),
    }


def _validity_card_payload(
    benchmark: Benchmark,
    panel_id: str,
    results: list[DiagnosticResult],
    manifest: dict[str, Any],
    misuse_warnings: list[str],
    *,
    human_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    by_name = _by_name(results)
    items = benchmark.load_items()
    provenance = _signal(by_name.get("data_forensics"), "provenance_completeness")
    coverage = by_name.get("coverage")
    artifact_scope = benchmark.construct_spec.metadata.get("artifact_scope", "unspecified")
    if artifact_scope == "gpqa_fixture_dry_run":
        intended_uses = [
            "Use only as a GPQA fixture dry-run for schema, scoring, and report plumbing validation."
        ]
        non_intended_uses = [
            "Do not use as GPQA Diamond evidence.",
            "Do not use as a global proof of benchmark validity or invalidity.",
            "Do not use as a standalone model leaderboard without the diagnostic profile.",
        ]
    else:
        intended_uses = [
            "Use as evidence under the documented audit protocol.",
            "Use for benchmark maintenance, item review, and reproducible validity documentation.",
        ]
        non_intended_uses = [
            "Do not use as a global proof of benchmark validity or invalidity.",
            "Do not use as a standalone model leaderboard without the diagnostic profile.",
        ]
    return {
        "schema_version": "0.1",
        "artifact_scope": artifact_scope,
        "identity": {
            "benchmark_id": benchmark.benchmark_id,
            "panel_id": panel_id,
            "created_at": utc_now(),
        },
        "version_hash": {
            "dataset_id": manifest.get("dataset_id", benchmark.benchmark_id),
            "item_count": manifest.get("item_count", len(items)),
            "item_ids_hash": manifest.get("item_ids_hash"),
            "item_text_hash": manifest.get("item_text_hash"),
            "benchmark_config_hash": manifest.get("benchmark_config_hash"),
            "scorer_hash": manifest.get("scorer_hash"),
            "prompt_template_hash": manifest.get("prompt_template_hash"),
            "diagnostic_config_hash": manifest.get("diagnostic_config_hash"),
        },
        "construct": {
            "claimed_construct": benchmark.claimed_construct,
            "construct_tags": benchmark.construct_spec.construct_tags,
            "construct_critical_fields": benchmark.construct_spec.construct_critical_fields,
            "known_threats": benchmark.construct_spec.expected_threats,
        },
        "intended_uses": intended_uses,
        "non_intended_uses": non_intended_uses,
        "item_sources": _item_sources(items, provenance),
        "scoring": {
            "scoring_adapter": "benchmark.score_prediction",
            "extraction_robustness": _summary(by_name.get("extraction_robustness")),
        },
        "model_panel": {"panel_id": panel_id},
        "diagnostics": [result.diagnostic_name for result in results],
        "reliability": _summary(by_name.get("reliability")),
        "item_quality": _summary(by_name.get("irt")),
        "contamination_provenance": _summary(by_name.get("data_forensics")),
        "coverage": _summary(coverage),
        "human_validation": validity_card_human_summary(human_summary or {}),
        "known_threats": [
            *benchmark.construct_spec.expected_threats,
            *[warning for result in results for warning in result.warnings],
        ],
        "recommended_use": [
            "Use repaired subsets only after author review of removed and coverage-critical items.",
            "Report diagnostics, limitations, and reproduction commands with any score interpretation.",
        ],
        "misuse_warnings": misuse_warnings,
        "reproduction": [
            f"python3 -m valideval matrices --benchmark {benchmark.benchmark_id} --panel {panel_id}",
            (
                f"python3 -m valideval audit --benchmark {benchmark.benchmark_id} "
                f"--panel {panel_id} --diagnostics all-core"
            ),
            f"python3 -m valideval card render --benchmark {benchmark.benchmark_id} --panel {panel_id}",
        ],
    }


def _certificate_payload(
    benchmark: Benchmark,
    panel_id: str,
    results: list[DiagnosticResult],
    manifest: dict[str, Any],
    *,
    human_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    by_name = _by_name(results)
    human_summary = human_summary or {}
    dimensions = {
        "metadata_reproducibility": "strong" if manifest else "unknown",
        "provenance": _status_provenance(by_name.get("data_forensics")),
        "shortcut": _status_shortcut(by_name.get("shortcut")),
        "item_quality": _status_item_quality(by_name.get("irt")),
        "reliability": _status_reliability(by_name.get("reliability")),
        "contamination_provenance": _status_contamination(by_name.get("data_forensics")),
        "judge_reliability": judge_reliability_status(human_summary),
        "human_validated_subset": human_validated_subset_status(human_summary),
        "predictive_validity": "moderate" if by_name.get("predictive") else "unknown",
        "goodhart_consequential_validity": "moderate" if by_name.get("goodhart") else "unknown",
        "external_replication": "unknown",
    }
    profile = _audit_completeness_profile(by_name, dimensions, bool(manifest))
    return {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "benchmark_id": benchmark.benchmark_id,
        "panel_id": panel_id,
        "artifact_scope": benchmark.construct_spec.metadata.get("artifact_scope", "unspecified"),
        "profile_level": profile,
        "audit_completeness_profile": profile,
        "dimension_statuses": dimensions,
        "ordinal_levels_disabled": True,
        "profile_definitions": {
            "insufficient_evidence": "Required audit artifacts are missing or too sparse.",
            "metadata_and_provenance_recorded": "Metadata, reproducible card, and basic provenance evidence are recorded.",
            "core_diagnostics_recorded": "Core shortcut, item-quality, and reliability diagnostics are recorded.",
            "human_review_evidence_recorded": "Human/judge validation evidence is recorded in addition to core diagnostics.",
            "external_validation_evidence_recorded": "External predictive, consequential, or replication evidence is recorded.",
        },
        "interpretation": (
            "This is an evidence profile / audit completeness profile. "
            "This is not a validity score or quality grade. It records which checks were run, "
            "with available evidence and limitations, and does not prove broad benchmark validity."
        ),
    }


def _audit_completeness_profile(
    by_name: dict[str, DiagnosticResult],
    dimensions: dict[str, str],
    has_manifest: bool,
) -> str:
    profile = "insufficient_evidence"
    if has_manifest and by_name.get("data_forensics"):
        profile = "metadata_and_provenance_recorded"
    if profile == "metadata_and_provenance_recorded" and all(
        by_name.get(name) for name in ["shortcut", "irt", "reliability"]
    ):
        profile = "core_diagnostics_recorded"
    if (
        profile == "core_diagnostics_recorded"
        and dimensions["contamination_provenance"] not in {"unknown", "insufficient evidence"}
        and dimensions["judge_reliability"] not in {"unknown", "insufficient evidence"}
        and dimensions["human_validated_subset"] not in {"unknown", "insufficient evidence"}
    ):
        profile = "human_review_evidence_recorded"
    if (
        profile == "human_review_evidence_recorded"
        and by_name.get("predictive")
        and by_name.get("goodhart")
        and dimensions["external_replication"] not in {"unknown", "insufficient evidence"}
    ):
        profile = "external_validation_evidence_recorded"
    return profile


def _render_validity_card_markdown(payload: dict[str, Any]) -> str:
    construct = payload["construct"]
    reliability = payload["reliability"].get("summary", {})
    item_quality = payload["item_quality"].get("summary", {})
    forensics = payload["contamination_provenance"].get("summary", {})
    coverage = payload["coverage"].get("summary", {})
    human = payload.get("human_validation", {})
    signals = forensics.get("signals", {}) if isinstance(forensics, dict) else {}
    lines = [
        f"# Validity Card: {payload['identity']['benchmark_id']}",
        "",
        "## Identity",
        "",
        f"- Benchmark: {payload['identity']['benchmark_id']}",
        f"- Panel: {payload['identity']['panel_id']}",
        f"- Artifact scope: {payload.get('artifact_scope', 'unspecified')}",
        f"- Item count: {payload['version_hash'].get('item_count')}",
        f"- Item text hash: {payload['version_hash'].get('item_text_hash')}",
        "",
        "## Construct",
        "",
        f"- Claimed construct: {construct['claimed_construct']}",
        f"- Construct-critical fields: {', '.join(construct['construct_critical_fields']) or 'n/a'}",
        "",
        "## Intended Uses",
        "",
        *[f"- {item}" for item in payload["intended_uses"]],
        "",
        "## Non-Intended Uses",
        "",
        *[f"- {item}" for item in payload["non_intended_uses"]],
        "",
        "## Diagnostics",
        "",
        f"- Diagnostics run: {', '.join(payload['diagnostics'])}",
        (
            "- Reliability estimate: "
            f"{_fmt(reliability.get('benchmark_level_reliability_estimate'))}"
        ),
        (
            "- Item quality: "
            f"negative={_fmt(item_quality.get('negative_discrimination_items'))}, "
            f"near-zero fraction={_fmt(item_quality.get('near_zero_discrimination_fraction'))}"
        ),
        (
            "- Contamination/provenance: "
            f"overlap={_signal_label(signals.get('corpus_overlap', {}))}, "
            f"provenance={_signal_label(signals.get('provenance_completeness', {}))}"
        ),
        (
            "- Coverage: "
            f"unique tags={_fmt(coverage.get('n_unique_tags'))}, "
            f"missing expected tags={coverage.get('missing_expected_tags', [])}"
        ),
        "",
        "## Human Validation",
        "",
        f"- Status: {human.get('status', 'unknown')}",
        f"- Annotated items: {_fmt(human.get('annotated_item_count'))}",
        f"- Human raw agreement: {_fmt(human.get('raw_agreement'))}",
        f"- Judge-human agreement: {_fmt(human.get('judge_human_agreement'))}",
        "",
        "## Misuse Warnings",
        "",
        *[f"- {warning}" for warning in payload["misuse_warnings"]],
        "",
        "## Reproduction",
        "",
        "```bash",
        *payload["reproduction"],
        "```",
        "",
    ]
    return "\n".join(lines)


def _render_certificate_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Validity Evidence Profile: {payload['benchmark_id']}",
        "",
        f"- Audit completeness profile: {payload['audit_completeness_profile']}",
        "- This is not a validity score or quality grade.",
        f"- Panel: {payload['panel_id']}",
        f"- Artifact scope: {payload.get('artifact_scope', 'unspecified')}",
        "",
        "## Dimension Statuses",
        "",
    ]
    for name, status in payload["dimension_statuses"].items():
        lines.append(f"- {name}: {status}")
    lines.extend(["", "## Interpretation", "", payload["interpretation"], ""])
    return "\n".join(lines)


def _render_checklist_markdown(payload: dict[str, Any]) -> str:
    lines = [f"# Benchmark Author Checklist: {payload['benchmark_id']}", ""]
    for item in payload["checklist"]:
        lines.append(f"- {item['check']}: {item['status']} ({item['evidence']})")
    lines.append("")
    return "\n".join(lines)


def _render_evidence_matrix_markdown(
    rows: list[dict[str, str]],
    *,
    artifact_scope: str = "unspecified",
) -> str:
    lines = [
        "# Claim-to-Evidence Matrix",
        "",
        f"Artifact scope: **{artifact_scope}**.",
        "",
        "| Claim | Evidence Needed | Diagnostic | Result | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {_pipe(row['claim'])} | {_pipe(row['evidence_needed'])} | "
            f"{_pipe(row['diagnostic'])} | {_pipe(row['result'])} | {_pipe(row['status'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def _item_sources(items, provenance: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_url_count": sum(1 for item in items if item.source_url),
        "source_document_count": sum(1 for item in items if item.source_document),
        "generated_by_model_count": sum(1 for item in items if item.generated_by_model),
        "human_verified_count": sum(1 for item in items if item.human_verified),
        "provenance_completeness": provenance.get("metrics", {}).get("completeness_fraction"),
        "field_missing_counts": provenance.get("metrics", {}).get("field_missing_counts", {}),
    }


def _summary(result: DiagnosticResult | None) -> dict[str, Any]:
    if not result:
        return {"status": "not measured", "summary": {}}
    return {
        "status": "measured",
        "summary": result.summary_metrics,
        "warnings": result.warnings,
        "limitations": result.limitations,
    }


def _status_shortcut(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    return "threatened" if result.summary_metrics.get("high_retention_variants") else "moderate"


def _status_item_quality(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    negative = int(result.summary_metrics.get("negative_discrimination_items") or 0)
    near_zero = float(result.summary_metrics.get("near_zero_discrimination_fraction") or 0.0)
    if negative > 0:
        return "threatened"
    if near_zero < 0.10:
        return "strong"
    if near_zero < 0.30:
        return "moderate"
    if near_zero < 0.50:
        return "weak"
    return "threatened"


def _status_reliability(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    value = result.summary_metrics.get("benchmark_level_reliability_estimate")
    if value is None:
        return "unknown"
    value = float(value)
    if value >= 0.80:
        return "strong"
    if value >= 0.60:
        return "moderate"
    if value >= 0.40:
        return "weak"
    return "threatened"


def _status_provenance(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    provenance = _signal(result, "provenance_completeness")
    fraction = provenance.get("metrics", {}).get("completeness_fraction")
    if fraction is None:
        return "unknown"
    fraction = float(fraction)
    if fraction >= 0.90:
        return "strong"
    if fraction >= 0.50:
        return "moderate"
    if fraction > 0.0:
        return "weak"
    return "threatened"


def _status_contamination(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    overlap = _signal(result, "corpus_overlap")
    if overlap.get("status") in {"unavailable", "insufficient_corpus"}:
        return "insufficient evidence"
    risk = overlap.get("risk_level")
    if risk == "no local evidence found":
        return "strong"
    if risk == "low local evidence":
        return "moderate"
    if risk == "moderate local evidence":
        return "weak"
    if risk == "high local evidence":
        return "threatened"
    return "unknown"


def _by_name(results: list[DiagnosticResult]) -> dict[str, DiagnosticResult]:
    return {result.diagnostic_name: result for result in results}


def _item_metrics(
    by_name: dict[str, DiagnosticResult],
    diagnostic_name: str,
    item_id: str,
) -> dict[str, Any]:
    result = by_name.get(diagnostic_name)
    if not result:
        return {}
    values = result.per_item_metrics.get(item_id, {})
    return values if isinstance(values, dict) else {}


def _duplicate_clusters(result: DiagnosticResult | None) -> dict[str, str]:
    if not result:
        return {}
    duplicate_signal = _signal(result, "internal_duplicates")
    clusters = duplicate_signal.get("metrics", {}).get("duplicate_clusters", {})
    output = {}
    for cluster_name, cluster_list in clusters.items():
        for cluster in cluster_list:
            label = f"{cluster_name}:{'|'.join(cluster)}"
            for item_id in cluster:
                output.setdefault(item_id, label)
    return output


def _signal(result: DiagnosticResult | None, name: str) -> dict[str, Any]:
    if not result:
        return {}
    signals = result.summary_metrics.get("signals", {})
    value = signals.get(name, {})
    return value if isinstance(value, dict) else {}


def _too_easy_hard(irt: dict[str, Any]) -> str:
    if irt.get("too_easy"):
        return "too_easy"
    if irt.get("too_hard"):
        return "too_hard"
    return ""


def _instability_from_stability(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, 1.0 - float(value))
    except (TypeError, ValueError):
        return None


def _temporal_risk(metrics: dict[str, Any]) -> str:
    if not metrics:
        return "unknown/unmeasured"
    if metrics.get("stale_label_risk") or metrics.get("source_after_split_risk"):
        return "high local evidence"
    if metrics.get("has_relative_or_current_phrasing") or metrics.get(
        "outdated_entity_or_fact_metadata_missing"
    ):
        return "moderate local evidence"
    return "no local evidence found"


def _provenance_missing_fraction(metrics: dict[str, Any]) -> float | None:
    if not metrics:
        return None
    completeness = metrics.get("completeness_fraction")
    if completeness is None:
        return None
    return max(0.0, 1.0 - float(completeness))


def _write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    output = Path(path)
    output.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True), encoding="utf-8")
    return output


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, np.floating):
        item = float(value)
        return None if math.isnan(item) or math.isinf(item) else item
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _csv_value(value: Any) -> Any:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return ""
    if value is None:
        return ""
    return value


def _pipe(value: Any) -> str:
    return str(value).replace("|", "\\|")


def _signal_label(value: dict[str, Any]) -> str:
    if not value:
        return "not measured"
    return f"{value.get('status', 'n/a')} / {value.get('risk_level', 'n/a')}"


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if value != value:
            return "n/a"
        return f"{value:.3f}"
    return str(value)
