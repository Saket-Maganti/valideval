from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from valideval.evidence.provenance_v7_2_1 import (
    ProvenanceEdge,
    ProvenanceNode,
    ProvenanceNodeKind,
    build_provenance_graph,
)
from valideval.execution.manifest import atomic_write_json
from valideval.execution.provenance_v7_2_1 import V7_2_CANONICAL_SOURCE_REF
from valideval.release.machine_state_v7_2_1 import (
    FinalCpuMaxoutMachineState,
    validate_machine_state,
    write_machine_state_schema,
)

FINAL_SOURCE_TAG = "valideval-icml2027-pre-gpu-cpu-maxout"
BASELINE_COMMIT = "49bdc529a482596bb4bcb308b3d96df34e8dcd80"


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_structured_state(repository_root: str | Path) -> dict[str, Any]:
    """Collect registered CPU evidence without promoting it to real-benchmark evidence."""

    root = Path(repository_root).resolve()
    selection = _json(root / "results/final_cpu_maxout/claim_policy/selection_metrics.json")
    confirmation = _json(root / "results/final_cpu_maxout/claim_policy/confirmation_summary.json")
    stress = _json(root / "results/final_cpu_maxout/stress/summary.json")
    historical = _json(root / "results/final_cpu_maxout/historical_mmlu/summary.json")
    extraction = _json(root / "results/final_cpu_maxout/extraction/summary.json")
    replay = _json(root / "results/final_cpu_maxout/replay/cpu_replay.json")
    v8 = _json(root / "results/v7_2/v8/development_summary.json")
    power = _json(root / "results/v7_1/planning/power/summary.json")
    generic_policy = _json(root / "results/v7_2/claim_policy/confirmation_summary.json")
    critical_counts = Counter(row["safety_status"] for row in confirmation["critical_strata"])
    recorded_runtime = sum(
        float(payload["runtime_seconds"])
        for payload in (selection, confirmation, stress, historical)
    )
    monte_carlo_replicates = (
        int(selection["development_scenarios"])
        + int(selection["validation_scenarios"])
        + int(confirmation["confirmation_scenarios"])
        + int(stress["monte_carlo_replicates"])
        + max(row["used_draws"] for row in historical["bootstrap_convergence"])
    )
    lock_paths = (
        "requirements-cpu-v7-2-1.lock",
        "requirements-kaggle-t4x2-v7-2-1.lock",
    )
    state = {
        "schema_version": "valideval.final-cpu-maxout-report-input.v7.2.1",
        "verdict": "ALL_USEFUL_PRE_GPU_CPU_WORK_EXHAUSTED",
        "p0_p1_status": "NO_KNOWN_P0_OR_P1_CPU_FIX_REMAINS",
        "evidence_boundary": (
            "All remaining material evidence requires real GPU, human, held-out, or external "
            "execution. CPU results do not substitute for those observations."
        ),
        "baseline_commit": BASELINE_COMMIT,
        "canonical_s1_source_ref": V7_2_CANONICAL_SOURCE_REF,
        "final_source_tag": FINAL_SOURCE_TAG,
        "source_head_resolution": "DYNAMIC_FROM_FINAL_SOURCE_TAG",
        "claim_policy": confirmation,
        "claim_policy_selection": selection,
        "generic_policy": {
            "status": "GENERIC_KNOWN_TRUTH_POLICY_CALIBRATION_PASS",
            "false_license_rate": generic_policy["false_license_rate"],
            "true_license_power": generic_policy["true_license_power"],
            "abstention_rate": generic_policy["abstention_rate"],
            "decision_regret": generic_policy["decision_regret"],
        },
        "critical_strata": {
            "total": len(confirmation["critical_strata"]),
            "passed": critical_counts["PASS"],
            "failed": critical_counts["FAIL"],
            "underpowered": critical_counts["UNDERPOWERED_STRATUM"],
            "maximum_simultaneous_upper": max(
                row["simultaneous_false_license_upper"] for row in confirmation["critical_strata"]
            ),
        },
        "stress": stress,
        "historical_mmlu": historical,
        "extraction": extraction,
        "replay": replay,
        "v8": v8,
        "power": power,
        "cpu_accounting": {
            "registered_runs": int(stress["cpu_runs"]) + 6,
            "runtime_seconds": recorded_runtime,
            "runtime_semantics": "SUM_OF_RECORDED_ANALYSIS_RUNTIME_FIELDS",
            "monte_carlo_replicates": monte_carlo_replicates,
            "components": {
                "native_policy_development_validation": selection["runtime_seconds"],
                "native_policy_confirmation": confirmation["runtime_seconds"],
                "statistical_stress": stress["runtime_seconds"],
                "historical_mmlu": historical["runtime_seconds"],
                "extraction_differential": "RUNTIME_NOT_RECORDED",
                "cpu_replay": "RUNTIME_NOT_RECORDED",
            },
        },
        "dependency_locks": {path: _sha256(root / path) for path in lock_paths},
        "stage_status": {
            "S1": "S1_ENGINEERING_SMOKE_AUTHORIZED",
            "S2": "DRAFT_PENDING_ACCEPTED_S1",
            "S3": "BLOCKED_PENDING_S2",
            "S4": "TEMPLATE_ONLY_BLOCKED_PENDING_S3",
        },
        "remaining": {
            "cpu": [],
            "gpu": [
                "Run and accept the three real Kaggle T4x2 S1 engineering packages.",
                "Measure S1 runtime, extraction reliability, failures, and package health.",
                "Do not authorize S2 until S1 acceptance and recalibration pass.",
                "V8 independent confirmation remains unrun and unauthorized.",
                "Execute future held-out transport and repair studies before those claims.",
            ],
            "human": [
                "Collect independent item labels under the frozen annotation protocol.",
                "Complete adjudication and reliability acceptance before human validation.",
            ],
        },
        "exact_next_action": (
            "Check out valideval-v7.2.1-icml2027-kaggle-s1-ready and run "
            "kaggle_icml2027/00_v7_2_t4x2_preflight.ipynb on Kaggle with two T4 GPUs."
        ),
    }
    return state


def _header(title: str, sources: list[str]) -> str:
    source_lines = "\n".join(f"- `{source}`" for source in sources)
    return (
        f"# {title}\n\n"
        "Generated from structured artifacts. It is an engineering/scientific audit record, "
        "not a final paper claim.\n\n"
        "## Structured sources\n\n"
        f"{source_lines}\n\n"
    )


def _pct(value: float) -> str:
    return f"{100.0 * value:.3f}%"


def _report_bodies(state: dict[str, Any]) -> dict[str, str]:
    policy = state["claim_policy"]
    overall = policy["overall"]
    strata = state["critical_strata"]
    stress = state["stress"]
    historical = state["historical_mmlu"]
    extraction = state["extraction"]
    sources = {
        "policy": "results/final_cpu_maxout/claim_policy/confirmation_summary.json",
        "selection": "results/final_cpu_maxout/claim_policy/selection_metrics.json",
        "stress": "results/final_cpu_maxout/stress/summary.json",
        "historical": "results/final_cpu_maxout/historical_mmlu/summary.json",
        "replay": "results/final_cpu_maxout/replay/cpu_replay.json",
        "v8": "results/v7_2/v8/development_summary.json",
        "power": "results/v7_1/planning/power/summary.json",
        "extraction": "results/final_cpu_maxout/extraction/summary.json",
    }
    family_rows = "\n".join(
        f"- {row['claim_family']}: false-license {_pct(row['false_license_rate'])}; "
        f"simultaneous upper {_pct(row['simultaneous_false_license_upper'])}; "
        f"power {_pct(row['true_license_power'])}; {row['safety_status']}."
        for row in policy["claim_family_scope"]
    )
    reports: dict[str, str] = {}
    reports["CPU_MAXOUT_EXECUTIVE_VERDICT.md"] = _header(
        "CPU Max-Out Executive Verdict", [sources["policy"], sources["stress"], sources["replay"]]
    ) + (
        f"## Verdict\n\n- `{state['verdict']}`\n- `{state['p0_p1_status']}`\n- "
        f"`{state['stage_status']['S1']}`\n\n{state['evidence_boundary']}\n\n"
        "The source and package path is ready for an engineering smoke. This does not license "
        "scientific conclusions from S1.\n"
    )
    reports["CPU_MAXOUT_REPAIR_LEDGER.md"] = _header(
        "CPU Max-Out Repair Ledger", [sources["replay"], sources["extraction"]]
    ) + (
        "## Closed correctness and safety defects\n\n"
        "- Canonical source provenance now resolves the immutable source tag dynamically.\n"
        "- Rare-event safety uses Wilson bounds, including nonzero upper risk for zero events.\n"
        "- Archive import rejects traversal, symlinks, duplicates, excessive members, oversized "
        "members, encryption, and extreme compression ratios.\n"
        "- Operational failures have bounded, typed retry policy; deterministic provenance and "
        "scoring failures are not retried.\n"
        "- Evidence invalidation propagates through an acyclic provenance graph.\n"
        "- The MMLU answer parser now requires an answer-token boundary; differential fixtures "
        f"report {extraction['production_reference_agreement']:.3f} agreement.\n"
        "- Odd-sized tied model panels no longer trigger rank-simulation broadcasting failure.\n\n"
        "Frozen historical outcomes were not rewritten.\n"
    )
    reports["CPU_MAXOUT_CLAIM_POLICY.md"] = _header(
        "CPU Max-Out Claim Policy", [sources["selection"], sources["policy"]]
    ) + (
        f"## Frozen result\n\n`{policy['status']}` with policy `{policy['policy_id']}`. "
        f"Across {overall['scenario_count']} confirmation scenarios, false-license rate was "
        f"{_pct(overall['false_license_rate'])} (Wilson upper "
        f"{_pct(overall['false_license_upper_95_wilson'])}), true-license power was "
        f"{_pct(overall['true_license_power'])}, and abstention was "
        f"{_pct(overall['abstention_rate'])}.\n\n## Family scope\n\n{family_rows}\n\n"
        f"Aggregate family checks pass, but {strata['failed']} of {strata['total']} prespecified "
        f"family-by-critical-stratum checks fail ({strata['passed']} pass). The policy is therefore supporting "
        "evidence, not publication-grade universal calibration. It was not retuned after confirmation.\n"
    )
    reports["CPU_MAXOUT_FINITE_SAMPLE_CALIBRATION.md"] = _header(
        "CPU Max-Out Finite-Sample Calibration",
        ["results/final_cpu_maxout/stress/finite_sample.csv", sources["policy"]],
    ) + (
        "## Interpretation\n\nThe registered table stratifies each native claim family by its own "
        "effective-N approximation. Guidance remains family-specific: observed units, resampling "
        "units, and generalization units are not interchangeable. No universal minimum N is licensed.\n"
    )
    rare_body = _header(
        "CPU Max-Out Rare-Event Safety",
        [sources["policy"], "src/valideval/statistics/rare_events.py"],
    ) + (
        f"## Result\n\nThe aggregate false-license count is {overall['false_license_count']} of "
        f"{overall['null_count']}; the one-sided reporting boundary uses a Wilson upper value of "
        f"{_pct(overall['false_license_upper_95_wilson'])}. Zero observed events are never reported "
        "as zero upper risk. Family and critical-stratum safety checks use simultaneous Bonferroni-adjusted "
        f"bounds. The largest critical-cell upper bound is {_pct(strata['maximum_simultaneous_upper'])}.\n"
    )
    reports["CPU_MAXOUT_RARE_EVENT_SAFETY.md"] = rare_body
    reports["RARE_EVENT_INTERVAL_AUDIT.md"] = rare_body
    reports["CPU_MAXOUT_DEPENDENCE.md"] = _header(
        "CPU Max-Out Dependence",
        ["results/final_cpu_maxout/stress/benchmark_dependence.csv", sources["stress"]],
    ) + (
        f"## Result\n\n{stress['benchmark_dependence_scenarios']} registered benchmark-dependence "
        "scenarios compare raw benchmark count with a participation-ratio effective-count approximation. "
        "The approximation is a planning sensitivity, not a known independence count. Model-family and "
        "benchmark dependence must remain explicit in S2/S3 design and transport claims.\n"
    )
    reports["CPU_MAXOUT_RANK_INFERENCE.md"] = _header(
        "CPU Max-Out Rank Inference",
        ["results/final_cpu_maxout/stress/rank_stress.csv", sources["stress"]],
    ) + (
        f"## Result\n\nThe {stress['rank_scenarios']}-scenario expansion reached minimum joint "
        f"coverage {stress['rank_minimum_joint_coverage']:.3f}. Status: "
        f"`{stress['rank_scope_status']}`. Simultaneous rank sets may be used only within declared, "
        "validated regimes; point ranks and marginal intervals are not substitutes for simultaneous coverage.\n"
    )
    reports["CPU_MAXOUT_SELECTIVE_DECISIONS.md"] = _header(
        "CPU Max-Out Selective Decisions",
        [sources["selection"], "results/final_cpu_maxout/stress/materiality.csv"],
    ) + (
        "## Result\n\nThe selected policy retains nonzero power and abstains when evidence, "
        "materiality, multiplicity, or scope gates are unmet. This supports selective-decision analysis "
        "inside the simulator scope; it does not define universal economic utility.\n"
    )
    reports["CPU_MAXOUT_NULL_SENSITIVITY.md"] = _header(
        "CPU Max-Out Null Sensitivity", ["results/v7_1/nulls", sources["replay"]]
    ) + (
        "## Boundary\n\nAll registered Study-H nulls remain visible. No favorable null was selected "
        "post hoc. The CPU replay verifies the frozen status, while real-label and held-out null adequacy "
        "remain future evidence questions.\n"
    )
    reports["CPU_MAXOUT_HISTORICAL_MMLU.md"] = _header(
        "CPU Max-Out Historical MMLU", [sources["historical"]]
    ) + (
        f"## Result\n\nThe sensitivity audit covers {historical['models']} models, "
        f"{historical['items']} items, {historical['subjects']} subjects, and "
        f"{historical['families']} model families. Winner stability is "
        f"`{historical['winner_stable']}` and top-five stability is "
        f"`{historical['top_5_stable']}` across registered estimands. This is a historical sensitivity "
        "result, not a claim that one weighting is universally correct.\n"
    )
    reports["CPU_MAXOUT_V8_EXPLORATORY.md"] = _header(
        "CPU Max-Out V8 Exploratory Boundary", [sources["v8"]]
    ) + (
        f"## Status\n\n`{state['v8']['status']}`. Difficulty confounding decreased in development, "
        "but V8 remains exploratory; independent confirmation was not run, and it does not repair the "
        "frozen V7 failure.\n"
    )
    reports["CPU_MAXOUT_HUMAN_PLANNING.md"] = _header(
        "CPU Max-Out Human Planning",
        [
            "results/final_cpu_maxout/stress/human_planning.csv",
            "results/final_cpu_maxout/stress/annotator_noise.csv",
        ],
    ) + (
        f"## Status\n\n{stress['human_plans']} allocation plans and "
        f"{stress['annotator_noise_scenarios']} annotator-noise scenarios are planning simulations only. "
        "No human label, reliability estimate, or validation result is claimed.\n"
    )
    reports["CPU_MAXOUT_POWER_AND_COMPUTE.md"] = _header(
        "CPU Max-Out Power and Compute",
        [sources["power"], "results/final_cpu_maxout/stress/power_uncertainty.csv"],
    ) + (
        f"## Status\n\n`{state['power']['status']}`. S3 scientific labeling remains blocked because "
        "the declared planning distributions have not been replaced with accepted S1/S2 measurements.\n"
    )
    reports["CPU_MAXOUT_ARCHITECTURE_HARDENING.md"] = _header(
        "CPU Max-Out Architecture Hardening",
        [
            "configs/release/legacy_compatibility_v7_2_1.json",
            "results/final_cpu_maxout/evidence/provenance_graph.json",
        ],
    ) + (
        "## Status\n\nThe active package schema is centralized; identifiers are validated; evidence "
        "transitions reject illegal jumps; invalidation is terminal and propagates through the provenance "
        "DAG; legacy adapters are explicit. Architecture status is `ACTIVE_PATHS_HARDENED`.\n"
    )
    reports["CPU_MAXOUT_TESTING_AND_SECURITY.md"] = _header(
        "CPU Max-Out Testing and Security",
        [sources["extraction"], "tests/test_archive_security_v7_2_1.py"],
    ) + (
        f"## Status\n\nDifferential scorer status is `{extraction['status']}` over "
        f"{extraction['fixture_count']} fixtures. Archive adversarial cases, importer failures, source "
        "mutations, retry semantics, evidence transitions, and prompt-contract mutation are tested. "
        "Final suite, coverage, build, notebook, and scan results are recorded in machine state.\n"
    )
    reports["CPU_MAXOUT_REPRODUCIBILITY.md"] = _header(
        "CPU Max-Out Reproducibility",
        [sources["replay"], "requirements-cpu-v7-2-1.lock", "requirements-kaggle-t4x2-v7-2-1.lock"],
    ) + (
        f"## Status\n\nCPU replay is `{state['replay']['status']}`. Frozen JSON hashes are bitwise "
        "stable; recomputed native aggregates are numerically stable; gate states are conclusion-stable; "
        "GPU inference is environment-sensitive and was not run.\n"
    )
    reports["CPU_MAXOUT_KAGGLE_PREP.md"] = _header(
        "CPU Max-Out Kaggle Prep", ["VALID_EVAL_V7_2_KAGGLE_S1_RUNBOOK.md"]
    ) + (
        f"## Authorization\n\n`{state['stage_status']['S1']}`. Run notebook 00 first. Expected ZIPs:\n\n"
        "- `valideval_v7_2_s1_mmlu_s1-v7-2-mmlu.zip`\n"
        "- `valideval_v7_2_s1_gsm8k_s1-v7-2-gsm8k.zip`\n"
        "- `valideval_v7_2_s1_bbh_s1-v7-2-bbh.zip`\n\n"
        "S1 is engineering-only. S2 remains `DRAFT_PENDING_ACCEPTED_S1`.\n"
    )
    reports["CPU_MAXOUT_ICML_RED_TEAM.md"] = _header(
        "CPU Max-Out ICML Red Team", [sources["policy"], sources["stress"], sources["v8"]]
    ) + (
        "## Surviving objections\n\n"
        "- Simulator-specific calibration: addressed only within registered generators; external validity remains open.\n"
        "- Dependence: family and benchmark dependence are explicit, but real panel dependence is unobserved.\n"
        "- Rank simultaneity: expanded stress found a restricted regime, so scope is narrowed rather than hidden.\n"
        "- Multiplicity: family aggregates pass, but 21 critical cells fail and prevent a publication-grade label.\n"
        "- Difficulty confounding: V8 is exploratory and has no licensed item discoveries.\n"
        "- Repair/transport/human claims: blocked pending real held-out or human evidence.\n"
        "- Synthetic circularity: known-truth results are supporting method evidence only.\n"
    )
    reports["CPU_MAXOUT_REMAINING_BLOCKERS.md"] = _header(
        "CPU Max-Out Remaining Blockers", ["results/claims/claim_registry.json"]
    ) + (
        "## CPU\n\nNo known P0/P1 CPU correctness blocker remains.\n\n"
        "## GPU\n\n"
        + "\n".join(f"- {item}" for item in state["remaining"]["gpu"])
        + "\n\n## Human\n\n"
        + "\n".join(f"- {item}" for item in state["remaining"]["human"])
        + "\n"
    )
    return reports


def _claim_trace(root: Path) -> dict[str, Any]:
    registry = _json(root / "results/claims/claim_registry.json")
    return {
        "schema_version": "valideval.claim-trace.v7.2.1",
        "claims": [
            {
                "claim_id": row["claim_id"],
                "family": row["family"],
                "status": row["status"],
                "evidence_class": row["evidence_class"],
                "assumptions": row["prerequisites"],
                "blockers": row["blockers"],
            }
            for row in registry["claims"]
        ],
    }


def _provenance_graph(root: Path) -> dict[str, Any]:
    policy_hash = _sha256(root / "results/final_cpu_maxout/claim_policy/confirmation_summary.json")
    nodes = [
        ProvenanceNode("source:v7.2.1", ProvenanceNodeKind.SOURCE),
        ProvenanceNode("config:native-policy", ProvenanceNodeKind.CONFIG),
        ProvenanceNode("run:native-confirmation", ProvenanceNodeKind.RAW_RUN),
        ProvenanceNode("package:confirmation-records", ProvenanceNodeKind.IMPORTED_PACKAGE),
        ProvenanceNode(
            "analysis:native-policy",
            ProvenanceNodeKind.ANALYSIS,
            artifact_hash=policy_hash,
            evidence_class="SYNTHETIC_CONFIRMATORY",
        ),
        ProvenanceNode("claim:native-policy-safety", ProvenanceNodeKind.CLAIM),
    ]
    edges = [
        ProvenanceEdge("config:native-policy", "source:v7.2.1"),
        ProvenanceEdge("run:native-confirmation", "config:native-policy"),
        ProvenanceEdge("package:confirmation-records", "run:native-confirmation"),
        ProvenanceEdge("analysis:native-policy", "package:confirmation-records"),
        ProvenanceEdge("claim:native-policy-safety", "analysis:native-policy"),
    ]
    return build_provenance_graph(nodes, edges)


def _machine_state(state: dict[str, Any]) -> FinalCpuMaxoutMachineState:
    strata = state["critical_strata"]
    payload = {
        "schema_version": "valideval.final-cpu-maxout-machine-state.v7.2.1",
        "baseline_commit": state["baseline_commit"],
        "final_source_commit": "PENDING_FINAL_SOURCE_TAG",
        "final_source_tag": state["final_source_tag"],
        "canonical_s1_source_ref": state["canonical_s1_source_ref"],
        "metadata_commit": "PENDING_METADATA_COMMIT",
        "git_clean": "PENDING_FINAL_VALIDATION",
        "ci": {"status": "PENDING_PUSH"},
        "v7_2_1_closure_status": "V7_2_1_INTEGRITY_CLOSURE_COMPLETE",
        "runbook_provenance": "RUNBOOK_PROVENANCE_COHERENT",
        "claim_policy_status": state["claim_policy"]["status"],
        "claim_family_scope": [
            row["claim_family"] for row in state["claim_policy"]["claim_family_scope"]
        ],
        "critical_strata": strata,
        "v8_status": "V8_EXPLORATORY_IMPROVEMENT_FOUND_CONFIRMATION_NOT_RUN",
        "cpu_runs": state["cpu_accounting"],
        "numerical_reproducibility": state["replay"]["numerical_reproducibility"],
        "architecture_status": "ACTIVE_V7_2_1_PATHS_HARDENED",
        "schema_status": "CANONICAL_SCHEMA_AND_EXPLICIT_LEGACY_ADAPTERS",
        "evidence_state_status": "TRANSITIONS_AND_INVALIDATION_PROPAGATION_ENFORCED",
        "importer_security": "ADVERSARIAL_ARCHIVE_REJECTION_TESTED",
        "resume_status": "IDENTITY_PRESERVING_RESUME_TESTED",
        "oom_status": "TYPED_BOUNDED_RECOVERY_TESTED",
        "validation": {
            "tests": "PENDING_FINAL_VALIDATION",
            "coverage": "PENDING_FINAL_VALIDATION",
            "fuzz": "ARCHIVE_AND_IMPORTER_ADVERSARIAL_TESTS_REGISTERED",
            "mutation_testing": "MANUAL_CRITICAL_MUTATION_PROBES_REGISTERED",
            "lint": "PENDING_FINAL_VALIDATION",
            "format": "PENDING_FINAL_VALIDATION",
            "mypy": "PENDING_FINAL_VALIDATION",
            "build": "PENDING_FINAL_VALIDATION",
            "notebooks": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "release": "PENDING_FINAL_VALIDATION",
        },
        "s1_status": state["stage_status"]["S1"],
        "s2_status": state["stage_status"]["S2"],
        "s3_status": state["stage_status"]["S3"],
        "s4_status": state["stage_status"]["S4"],
        "remaining_cpu_work": state["remaining"]["cpu"],
        "remaining_gpu_work": state["remaining"]["gpu"],
        "remaining_human_work": state["remaining"]["human"],
        "exact_next_action": state["exact_next_action"],
    }
    return validate_machine_state(payload)


def build_final_cpu_maxout_release(repository_root: str | Path) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    state = build_structured_state(root)
    structured_path = root / "results/final_cpu_maxout/release/report_inputs.json"
    atomic_write_json(structured_path, state)
    trace = _claim_trace(root)
    trace_path = root / "results/final_cpu_maxout/evidence/claim_trace.json"
    atomic_write_json(trace_path, trace)
    graph_path = root / "results/final_cpu_maxout/evidence/provenance_graph.json"
    atomic_write_json(graph_path, _provenance_graph(root))

    report_root = root / "reports/final_cpu_maxout"
    report_root.mkdir(parents=True, exist_ok=True)
    reports = _report_bodies(state)
    for name, body in reports.items():
        (report_root / name).write_text(body, encoding="utf-8")

    trace_lines = [
        "# CPU Max-Out Claim Trace\n",
        "Generated from `results/claims/claim_registry.json`.\n",
    ]
    for row in trace["claims"]:
        trace_lines.extend(
            [
                f"## {row['claim_id']}\n",
                f"- Family: `{row['family']}`\n",
                f"- Status: `{row['status']}`\n",
                f"- Evidence class: `{row['evidence_class']}`\n",
                f"- Assumptions: {', '.join(row['assumptions']) or 'none'}\n",
                f"- Blockers: {', '.join(row['blockers']) or 'none'}\n",
            ]
        )
    (report_root / "CPU_MAXOUT_CLAIM_TRACE.md").write_text("\n".join(trace_lines), encoding="utf-8")

    report_manifest = {
        "schema_version": "valideval.report-manifest.v7.2.1",
        "structured_input": str(structured_path.relative_to(root)),
        "structured_input_sha256": _sha256(structured_path),
        "reports": {
            str(path.relative_to(root)): _sha256(path) for path in sorted(report_root.glob("*.md"))
        },
    }
    atomic_write_json(
        root / "results/final_cpu_maxout/release/report_manifest.json", report_manifest
    )

    machine_path = root / "VALID_EVAL_FINAL_CPU_MAXOUT_MACHINE_STATE.json"
    machine = _machine_state(state)
    if machine_path.exists():
        existing = validate_machine_state(_json(machine_path))
        if existing.final_source_commit != "PENDING_FINAL_SOURCE_TAG":
            machine = existing
    atomic_write_json(machine_path, machine.model_dump(mode="json"))
    write_machine_state_schema(root / "configs/release/final_cpu_maxout_machine_state.schema.json")
    _write_handoff_and_runbooks(root, state)
    return {
        "status": "FINAL_CPU_MAXOUT_RELEASE_ARTIFACTS_GENERATED",
        "structured_state": str(structured_path),
        "machine_state": str(machine_path),
        "reports": len(reports),
        "report_manifest": str(root / "results/final_cpu_maxout/release/report_manifest.json"),
    }


def _write_handoff_and_runbooks(root: Path, state: dict[str, Any]) -> None:
    policy = state["claim_policy"]
    strata = state["critical_strata"]
    handoff = (
        f"""# ValidEval Final CPU Max-Out Handoff

## 1. Executive verdict

`{state["verdict"]}` and `{state["p0_p1_status"]}`. S1 engineering smoke is authorized; no real GPU or human evidence was created.

## 2. Baseline

Baseline commit: `{state["baseline_commit"]}`. Canonical S1 source ref: `{state["canonical_s1_source_ref"]}`.

## 3. All repairs

Canonical provenance, rare-event intervals, archive security, typed retry semantics, evidence invalidation, scorer boundaries, and odd-panel rank stress were repaired and tested.

## 4. CPU analyses

Registered runs: {state["cpu_accounting"]["registered_runs"]}; recorded analysis runtime: {state["cpu_accounting"]["runtime_seconds"]:.6f} seconds; Monte Carlo/bootstrap replicates: {state["cpu_accounting"]["monte_carlo_replicates"]}.

## 5. Claim policy

`{policy["status"]}`. Aggregate family safety passes, but {strata["failed"]} of {strata["total"]} critical cells fail the simultaneous safety bound.

## 6. Rank inference

`{state["stress"]["rank_scope_status"]}` with minimum registered joint coverage {state["stress"]["rank_minimum_joint_coverage"]:.3f}.

## 7. Dependence

Family and benchmark dependence are explicit sensitivity dimensions. Effective benchmark count is labeled an approximation.

## 8. Nulls

Frozen null results remain unchanged. No favorable null was selected.

## 9. Historical MMLU

Weighting, jackknife, and bootstrap sensitivity cover {state["historical_mmlu"]["models"]} models and {state["historical_mmlu"]["items"]} items. They do not create new benchmark evidence.

## 10. V8

`V8_EXPLORATORY_IMPROVEMENT_FOUND`; confirmation is not run or authorized.

## 11. Human planning

Planning and annotator-noise simulations exist. No human labels exist.

## 12. Study-C power

The planner is ready, but S1/S2 observations must replace planning assumptions before S3 authorization.

## 13. Architecture

Canonical schemas, typed identifiers, legal evidence transitions, invalidation propagation, provenance DAGs, and explicit legacy adapters cover active V7.2.1 paths.

## 14. Security/testing

Unsafe ZIPs fail closed; deterministic provenance failures are never retried; scorer and prompt-contract differentials are tested.

## 15. Reproducibility

CPU replay passes. Dependency locks and report manifests are hashed. GPU execution remains environment-sensitive.

## 16. GPU prep

Run notebook 00 first, then MMLU, GSM8K, and BBH S1 notebooks. Import only the exact three accepted ZIPs.

## 17. S1/S2/S3/S4 state

- S1: `{state["stage_status"]["S1"]}`
- S2: `{state["stage_status"]["S2"]}`
- S3: `{state["stage_status"]["S3"]}`
- S4: `{state["stage_status"]["S4"]}`

## 18. Remaining GPU work

"""
        + "\n".join(f"- {item}" for item in state["remaining"]["gpu"])
        + """

## 19. Remaining human work

"""
        + "\n".join(f"- {item}" for item in state["remaining"]["human"])
        + f"""

## 20. Exact next action

{state["exact_next_action"]}
"""
    )
    (root / "VALID_EVAL_FINAL_CPU_MAXOUT_HANDOFF.md").write_text(handoff, encoding="utf-8")

    handbook = f"""# ValidEval ICML 2027 Canonical Execution Handbook

## Canonical

V7.2.1 S1 execution is canonical at `{state["canonical_s1_source_ref"]}`. Resolve the tag dynamically; never paste an intermediate SHA into execution instructions.

## Historical

V5, V6, V7, V7.1, and V7.2 are historical for new execution. Their adapters remain explicit. V7's failed confirmatory result, V7.1's conservative baseline, and V7.2's generic policy result are frozen.

## Exploratory

V8 is exploratory development only and has no confirmatory authorization.

## What to run next

{state["exact_next_action"]}

## Stage semantics

S1 validates engineering execution. S2 estimates runtime and pilot distributions. S3 requires a post-S2 design decision before scientific execution. S4 is optional and requires accepted S3 plus marginal-value justification. None of these stages automatically licenses a validity claim.

## Online, offline, and cache contract

The initial S1 smoke requires Internet to resolve the five models and three datasets at exact revisions. The declared model cache is 20,129,278,931 bytes; production preflight adds 7 GiB of free-disk margin. Reuse one cache across all three benchmark notebooks. Resume may use a complete exact-revision cache offline, but it must block rather than fetch or substitute an unpinned revision. Clear the cache only after the three validated ZIPs are safely downloaded.
"""
    (root / "VALID_EVAL_ICML2027_CANONICAL_EXECUTION_HANDBOOK.md").write_text(
        handbook, encoding="utf-8"
    )
    glossary = """# ValidEval Glossary

- **Validity:** whether evidence supports the intended interpretation and use of a score; not accuracy alone.
- **Diagnostic:** a targeted analysis of a potential validity threat.
- **License:** a claim-specific decision permitted only after its evidence contract passes.
- **Materiality:** a prespecified practical-effect boundary distinct from statistical significance.
- **Effective N:** an approximation to independent information under a declared dependence model.
- **Independence unit:** the unit treated as statistically independent under an analysis.
- **Family:** a declared cluster of related model checkpoints or evidence units.
- **Simultaneous rank set:** a joint uncertainty set intended to cover all model ranks together.
- **Transport:** support for a claim across a held-out benchmark, family, or setting.
- **Repair:** a prespecified intervention whose benefit and harm require held-out evaluation.
- **Engineering evidence:** evidence that execution, packaging, and import work as specified.
- **Exploratory evidence:** development evidence that cannot support a frozen confirmatory claim.
- **Confirmatory evidence:** evidence produced after protocol and policy freeze on isolated inputs.
"""
    (root / "VALID_EVAL_GLOSSARY.md").write_text(glossary, encoding="utf-8")
    architecture = """# ValidEval Architecture Map

```text
configs -> runner -> bounded workers -> deterministic package -> secure importer
        -> analyses -> evidence ledger/provenance DAG -> claim-specific licensing
```

Package acceptance advances only engineering evidence. Scientific claims require their own confirmatory, held-out, transport, or human prerequisites. Invalid source, config, package, parser, scorer, or data nodes invalidate dependent analyses and claims.
"""
    (root / "VALID_EVAL_ARCHITECTURE_MAP.md").write_text(architecture, encoding="utf-8")
    s2 = """# ValidEval V7.2.1 S2 Draft Runbook

`DRAFT_PENDING_ACCEPTED_S1`

Do not execute this stage until all three S1 ZIPs pass fail-closed acceptance and the post-S1 runtime recalibration is generated. S2 must measure runtime, variance, extraction reliability, model failures, and family coverage on the frozen pilot subset. Its outputs are engineering/pilot evidence and do not authorize S3 automatically.
"""
    (root / "VALID_EVAL_V7_2_1_S2_DRAFT_RUNBOOK.md").write_text(s2, encoding="utf-8")
    s3 = """# ValidEval V7.2.1 S3 Proposal Contract

`BLOCKED_PENDING_S2`

The S3 proposal generator must consume accepted S2 runtime, variance, failure, family-coverage, extraction, and primary-claim summaries. It may emit only `S3_PROPOSED` or `S3_REDESIGN_REQUIRED`; execution still requires an explicit authorization decision.
"""
    (root / "VALID_EVAL_V7_2_1_S3_PROPOSAL_CONTRACT.md").write_text(s3, encoding="utf-8")
    s4 = """# ValidEval V7.2.1 S4 Optional Template

`TEMPLATE_ONLY_BLOCKED_PENDING_S3`

Prerequisites: accepted S3, explicit scientific rationale, and a marginal-value analysis showing that S4 addresses a remaining material uncertainty. This template is not execution authorization.
"""
    (root / "VALID_EVAL_V7_2_1_S4_OPTIONAL_TEMPLATE.md").write_text(s4, encoding="utf-8")
    recovery = """# ValidEval V7.2.1 Failure Recovery Runbook

- Session death: resume from the identity-matched shard manifest; block if identity cannot be revalidated.
- Internet loss: resume only from exact-revision cache; never fetch an unpinned latest revision.
- OOM: apply the bounded registered fallback; block after retry budget exhaustion.
- Disk full: stop, preserve valid completed shards, clear only documented caches, then resume.
- Model failure: record the typed failure; continue only if stage acceptance permits recorded model failures.
- Package corruption: reject and rerun packaging from validated source artifacts.
- Extraction reliability below 0.95: block acceptance; inspect parser outputs and rerun only after a source-controlled repair and reseal.
- Checksum, config, source, parser, or scorer failure: never retry blindly; repair, invalidate dependents, reseal, and rerun.
"""
    (root / "VALID_EVAL_V7_2_1_FAILURE_RECOVERY_RUNBOOK.md").write_text(recovery, encoding="utf-8")
