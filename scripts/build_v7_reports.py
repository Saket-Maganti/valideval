from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from valideval.execution.models import load_panel_config

ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "reports/v7"


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    study_h = _json("results/v7/study_h/summary.json")
    diagnostics = _json("results/v7/diagnostics/summary.json")
    general = _json("results/v7/reliability/generalizability/summary.json")
    decision = _json("results/v7/decision/materiality/summary.json")
    influence = _json("results/v7/influence/mmlu_v7/summary.json")
    regime = _json("results/v7/measurement/regime_study/summary.json")
    synthetic = _json("results/v7/synthetic/confirmatory/summary.json")
    forensics = _json("results/v7/forensics/mmlu_v7.json")
    transport = _json("results/v7/transport/summary.json")
    power = _json("results/v7/planning/panel_power/summary.json")
    runtime = _json("results/v7/planning/gpu_runtime/summary.json")
    freeze_commit = _git("rev-parse", "valideval-v7-confirmatory-freeze^{commit}")

    _write(
        "VALID_EVAL_V7_CLAIM_LICENSING_METHOD.md",
        f"""# ValidEval V7 Claim-Licensing Method

Gate: `CLAIM_LICENSING_METHOD_READY` (method implementation only).

Validity is represented as a profile, never a scalar. The V7 contract separates model-comparison,
top-k, item-suspicion, transport, repair, and benchmark-validity claims. Each claim fails closed on
applicable identity, leakage, sample-size, power, uncertainty/materiality, multiplicity, bootstrap
stability, external/held-out validation, transport heterogeneity, and decision-regret gates.

The executable state machine returns `LICENSED`, `LICENSED_WITH_SCOPE`, or a named blocking state.
The contract tests exercise both successful and failed paths. This validates software behavior; it
does not license a real benchmark-quality claim. The V7 evidence ledger currently blocks item
suspicion, transfer, human-validation, and repair claims. The synthetic detector also failed its
frozen acceptance gates (median AUPRC {synthetic["median_AUPRC"]:.3f}, median FDR
{synthetic["median_FDR"]:.3f}).

Primary implementation: `src/valideval/claims/`. Backing artifact:
`results/v7/evidence/claim_evidence_ledger_v7.csv`.
""",
    )
    _write(
        "VALID_EVAL_V7_DIAGNOSTIC_DEPENDENCY_AUDIT.md",
        """# ValidEval V7 Diagnostic Dependency Audit

Gate: `DIAGNOSTIC_DEPENDENCIES_EXPLICIT`.

The audit groups diagnostics by source data, formula, and dependence on benchmark accuracy or
external labels. `legacy_accuracy_weight` is retired as a duplicate of extreme-difficulty scoring.
Negative discrimination and extreme difficulty remain separate signals but share the response
matrix, so their agreement cannot be treated as independent corroboration. External issue matches
are structurally independent only after exact identity and held-out-label checks pass.

The dependency graph is stored at
`results/v7/diagnostics/diagnostic_dependency_graph.json`. Downstream claim licensing counts a
cluster of dependent diagnostics as one evidence family and requires independent external or human
evidence for item-quality language.
""",
    )
    _write(
        "VALID_EVAL_V7_INFERENTIAL_DIAGNOSTIC_REPORT.md",
        f"""# ValidEval V7 Inferential Diagnostic Report

Gate: `INFERENTIAL_DIAGNOSTICS_READY`; substantive discovery gate: `NO_DISCOVERIES`.

The analysis used {diagnostics["models"]} historical checkpoints, {diagnostics["families"]} inferred
families, and {diagnostics["items"]} MMLU items. Each negative-discrimination estimate uses a
leave-one-item ability score, family-clustered bootstrap uncertainty ({diagnostics["bootstrap"]}
draws), a permutation null ({diagnostics["permutations"]} draws), BH control, BY sensitivity, and a
predeclared 0.80 stability threshold.

Results: BH flags = {diagnostics["BH_flags"]}, BY flags = {diagnostics["BY_flags"]}, and stable
FDR-controlled flags = {diagnostics["stable_FDR_flags"]}. The correct conclusion is not that MMLU
contains no flawed items. Under this diagnostic, panel, and null, no item supports the narrow
anti-discrimination claim after multiplicity and stability control. Causes would in any event need
independent validation.

Runtime: {diagnostics["runtime_seconds"]:.2f} seconds. Backing table:
`results/v7/diagnostics/item_inferential_diagnostics.csv`.
""",
    )
    nulls = pd.read_csv(ROOT / "results/v7/study_h/null_suite_comparison.csv")
    _write(
        "MMLU_V7_FULL_UNCERTAINTY_AND_NULL_ANALYSIS.md",
        f"""# MMLU V7 Full Uncertainty and Null Analysis

Gate: `{study_h["status"]}`.

Study H reproduced the 39-model, 14,042-item, 57-subject historical MMLU analysis with 500 nested
subject/item bootstraps, 500 family-cluster bootstraps, leave-one-family-out, equal-family weighting,
and seven null generators. Kendall's W was {study_h["kendalls_w"]:.3f} with bootstrap interval
[{study_h["kendalls_w_ci"][0]:.3f}, {study_h["kendalls_w_ci"][1]:.3f}]. The top four aggregate ranks
were point-stable in the nested bootstrap, while lower ranks had wider sets.

The main limitation is null sensitivity. Median-rank-range exceedance probabilities ranged from
{nulls["median_rank_range_exceedance"].min():.3f} to
{nulls["median_rank_range_exceedance"].max():.3f}. Additive and fixed-margin nulls make the observed
dispersion look unusual; family-correlated and latent-factor nulls do not. Therefore the result is
evidence consistent with subject-dependent ranking under several protocols, not a null-invariant
proof of instability.

Runtime: {study_h["runtime_seconds"]:.2f} seconds. All tables are under `results/v7/study_h/`.
""",
    )
    vc = general["variance_components"]
    _write(
        "VALID_EVAL_V7_GENERALIZABILITY_STUDY.md",
        f"""# ValidEval V7 Generalizability Study

Gate: `GENERALIZABILITY_ANALYSIS_READY` with descriptive-component limitations.

The unbalanced method-of-moments decomposition estimates family ({vc["family"]:.4f}), model
({vc["model"]:.4f}), subject ({vc["subject"]:.4f}), item ({vc["item"]:.4f}), family×subject
({vc["family_x_subject"]:.4f}), model×subject ({vc["model_x_subject"]:.4f}), and residual
({vc["residual"]:.4f}) components. These quantities describe this fixed historical panel; they are
not population variance estimates.

Design curves separately cover aggregate score, pairwise comparison, top-k selection, and
subject-conditioned score. The first three reach 0.80 on the evaluated grid; subject-conditioned
score does not. This supports outcome-specific design decisions and rejects a single universal
reliability number.

Runtime: {general["runtime_seconds"]:.2f} seconds. Backing artifacts are under
`results/v7/reliability/generalizability/`.
""",
    )
    decisions = decision["pairwise_decisions"]
    _write(
        "VALID_EVAL_V7_DECISION_MATERIALITY.md",
        f"""# ValidEval V7 Decision Materiality

Gate: `DECISION_MATERIALITY_READY` for the historical MMLU panel.

Selective ranking returns directional comparisons only when the 95% interval excludes zero and the
0.01 materiality threshold; otherwise it returns equivalence or insufficient evidence. Across the
741 pairs: A>B={decisions.get("A > B", 0)}, B>A={decisions.get("B > A", 0)}, A~B={decisions.get("A ~ B", 0)},
and insufficient evidence={decisions.get("INSUFFICIENT_EVIDENCE", 0)}.

The aggregate winner required targeted removal of {decision["item_removal_fragility"]["items_removed"]}
items ({100 * decision["item_removal_fragility"]["removal_fraction"]:.2f}%) to flip to the nearest
challenger in the exact greedy deletion analysis. The minimum subject-weight total variation was
{decision["subject_weight_fragility"]["minimum_total_variation"]:.3f}. These are conditional
sensitivity measures, not evidence that removed items are flawed or that the observed winner is
universally preferable.

Runtime: {decision["runtime_seconds"]:.2f} seconds. Backing artifacts are under
`results/v7/decision/materiality/`.
""",
    )
    _write(
        "VALID_EVAL_V7_BENCHMARK_INFLUENCE.md",
        f"""# ValidEval V7 Benchmark Influence

Gate: `BENCHMARK_INFLUENCE_READY`.

Exact leave-one-item analysis found {influence["winner_changing_items"]} winner-changing items and
{influence["top5_changing_items"]} top-five-changing items among {influence["items"]} historical MMLU
items. Leave-one-subject analysis found {influence["winner_changing_subjects"]} winner-changing
subjects. The cross-fit 5% removal comparison includes suspicious, random, matched-difficulty,
high-difficulty, and high-variance policies; none changed the held-out winner.

This is evidence that single-item deletion was not decision-material for the measured winner under
this matrix. Influence is not a flaw label, and larger coordinated subsets can still matter.

Runtime: {influence["runtime_seconds"]:.2f} seconds. Backing artifacts are under
`results/v7/influence/mmlu_v7/`.
""",
    )
    _write(
        "VALID_EVAL_V7_MEASUREMENT_REGIME_STUDY.md",
        f"""# ValidEval V7 Measurement Regime Study

Gate: `MEASUREMENT_REGIME_STUDY_COMPLETE`.

Nineteen deterministic regimes varied model count (5–120), family dependence, skew, multimodality,
heavy tails, latent dimension, missingness, and saturation. Evaluation used held-out response cells
and compared aggregate ability, additive subject difficulty, regularized subject-conditioned, and
low-rank predictions.

The corrected positive-discrimination generator produced: {regime["regime_counts"]}. This maps where
the declared estimators recover the known synthetic target. It does not establish that a real
benchmark has a scalar or multidimensional latent trait. In particular, the map must guide model
choice rather than justify fitting the most complex model everywhere.

Runtime: {regime["runtime_seconds"]:.2f} seconds. Backing table:
`results/v7/measurement/regime_study/regime_map.csv`.
""",
    )
    _write(
        "VALID_EVAL_V7_CONFIRMATORY_SYNTHETIC_RESULTS.md",
        f"""# ValidEval V7 Confirmatory Synthetic Results

Execution gate: `SYNTHETIC_CONFIRMATORY_COMPLETE`. Acceptance gate:
`{synthetic["acceptance_status"]}`.

The protocol was frozen at `{synthetic["freeze_ref"]}` / `{synthetic["freeze_commit"]}` before
execution. It evaluated {synthetic["scenario_count"]} combinations covering no flaw, label errors,
multiple label errors, ambiguity, distractor failure, subject misassignment, duplicates,
missingness, and correlated-family failure. The detector received only response matrices; sealed
truth was used only for metrics.

Median AUPRC was {synthetic["median_AUPRC"]:.3f}, median precision@k was
{synthetic["median_precision_at_k"]:.3f}, median FDR was {synthetic["median_FDR"]:.3f}, and median
power was {synthetic["median_power"]:.3f}. Every preregistered success criterion failed. The fixed
readout is therefore not validated for the declared heterogeneous flaw grid and cannot support
real-item quality claims. This negative result is retained, not tuned away.

Runtime: {synthetic["runtime_seconds"]:.2f} seconds. Backing artifacts are under
`results/v7/synthetic/confirmatory/`.
""",
    )
    _write(
        "VALID_EVAL_V7_TRANSPORTABILITY_METHOD.md",
        f"""# ValidEval V7 Transportability Method

Build gate: `{transport["build_status"]}`. Evidence gate: `{transport["overall_status"]}`.

Six estimands are defined separately: score, ranking, flag, calibration, decision, and repair
transport. Random-effects pooling reports tau-squared, I-squared, confidence intervals, direction
reversals, leave-one-benchmark-out requirements, and leave-one-family-out requirements. Exact item
and model identity, held-out evaluation, at least three benchmarks, and at least five independent
families fail closed.

Current evidence remains blocked: {transport["reason"]} The MMLU→GSM8K, MMLU→BBH, and GSM8K→BBH
directions must be populated from exact-model Study C outputs. A blank schema is at
`results/v7/transport/transport_effects_template.csv`.
""",
    )
    human = pd.read_csv(ROOT / "results/v7/planning/human_annotation_power.csv")
    row = human[human["annotations_per_stratum"] == 300].iloc[0]
    _write(
        "VALID_EVAL_V7_HUMAN_STUDY_FINAL_PROTOCOL.md",
        f"""# ValidEval V7 Human Study Final Protocol

Gate: `HUMAN_CONFIRMATORY_PROTOCOL_READY`; human evidence: `NOT_EXECUTED`.

The protocol uses disjoint high, medium, low, and probability-control strata; deterministic
benchmark/subject balancing; a physically separate randomization key; positive and negative
controls; two or three annotators; a frozen issue taxonomy; nominal agreement metrics; specialist
adjudication; and raw-versus-adjudicated reporting. Annotators do not see diagnostic scores,
selection reasons, external labels, model identities, or response patterns where avoidable.

The primary endpoint is precision in the preregistered flagged stratum. Recall is not identifiable
from the stratified design and must not be claimed. At 300 annotations per stratum, the planning
95% precision interval around an assumed 0.70 precision is [{row["precision_ci_lower"]:.3f},
{row["precision_ci_upper"]:.3f}]. These are planning assumptions, not labels.

V7 sampling is in `src/valideval/human/protocol_v7.py`; the audited V5 blinded packet, secure import,
agreement, and adjudication modules remain the execution path.
""",
    )
    gold = forensics["gold_position_distribution"]
    _write(
        "VALID_EVAL_V7_BENCHMARK_FORENSICS.md",
        f"""# ValidEval V7 Benchmark Forensics

Gate: `BENCHMARK_FORENSICS_READY` for cached MMLU position analysis.

The audit reproduced {forensics["rows"]} prediction rows over {forensics["unique_items"]} unique
items with {forensics["gold_identity_conflicts"]} gold-identity conflicts. Gold-position fractions
were A={gold["A"]["fraction"]:.3f}, B={gold["B"]["fraction"]:.3f}, C={gold["C"]["fraction"]:.3f}, and
D={gold["D"]["fraction"]:.3f}; position-conditioned accuracy ranged from
{min(forensics["position_conditioned_accuracy"].values()):.3f} to
{max(forensics["position_conditioned_accuracy"].values()):.3f}. These are forensic signals, not
contamination findings.

Freezing the full V7 splits found and retired 27 exact MMLU duplicates and 4 exact BBH duplicates;
GSM8K had none under the content-addressed identity. MMLU-Redux remains
`REDUX_VALIDATION_RETIRED`: its 370 local labels lack normalized question/options/answer or a
documented HELM mapping, and the prior fail-closed attempt confirmed 0 matches. No further fuzzy
linkage is justified.
""",
    )
    _panel_report(power, runtime)
    _write(
        "VALID_EVAL_V7_ICML_PREREGISTRATION.md",
        f"""# ValidEval V7 ICML Preregistration

Status: `FROZEN_BEFORE_S3` at tag `valideval-v7-confirmatory-freeze` (commit `{freeze_commit}`).

The frozen file is `configs/preregistration/icml2027_primary_v7.yaml` with SHA-256
`{_sha("configs/preregistration/icml2027_primary_v7.yaml")}`. It fixes the primary hypothesis,
negative-discrimination/rank/fragility diagnostics, S3 panel, MMLU/GSM8K/BBH portfolio, held-out
decision regret, 0.01 materiality threshold, claim policy, exclusions, missing-data rule, BH primary
and BY sensitivity, human precision endpoint, transport metric, and cross-fitted repair policy.

The confirmatory synthetic protocol is independently frozen with SHA-256
`{_sha("configs/synthetic/confirmatory_v7.yaml")}`. Later code may fix implementation defects, but
any change to a frozen protocol requires a new version and cannot be described as the V7 primary
analysis.
""",
    )
    _novelty_report()
    _red_team_report()
    _repair_changelog()
    _execution_plan(runtime)
    _handoff(
        study_h,
        diagnostics,
        general,
        decision,
        influence,
        regime,
        synthetic,
        transport,
        power,
        runtime,
    )
    _machine_state(
        study_h, diagnostics, general, decision, influence, regime, synthetic, transport, runtime
    )
    print(f"Wrote V7 reports to {REPORT_ROOT}")
    return 0


def _panel_report(power: dict[str, Any], runtime: dict[str, Any]) -> None:
    rows = []
    for name in ("s2_pilot_v7", "s3_scientific_v7", "s4_maximum_ceiling_v7", "s4_fallback_v7"):
        panel = load_panel_config(ROOT / f"configs/panels/{name}.yaml")
        rows.append(
            f"| {panel['panel_id']} | {len(panel['models'])} | {panel['family_count']} | "
            f"{sum(m['expected_download_size'] for m in panel['models']) / 1e9:.1f} GB |"
        )
    _write(
        "VALID_EVAL_V7_STUDY_C_PANEL_DESIGN.md",
        f"""# ValidEval V7 Study C Panel Design

Build gate: `STUDY_C_FULL_EXECUTION_BUILD_READY`; evidence gate: `GPU_NOT_EXECUTED`.

| Panel | Models | Lineage families | Declared download |
|---|---:|---:|---:|
{chr(10).join(rows)}

S2 emphasizes public checkpoint loading and extraction across seven families. S3 is the minimum
scientific panel (11 models, 9 families). S4 adds gated Llama and Gemma families; its 11-model,
9-family public fallback was frozen before S3 and has exact alternative run configs. The
DeepSeek-R1-Qwen distill is marked as a hybrid and must be merged with Qwen in dependence
sensitivity. Every checkpoint and tokenizer is pinned to a 40-character commit and remote code is
disabled.

The 0.01 paired-difference planning power is only {power["s3_materiality_power_range"][0]:.3f}–
{power["s3_materiality_power_range"][1]:.3f} under declared correlation assumptions, below 0.80.
S2 must recalibrate power before confirmatory interpretation. Full primary-route runtime is an
uncalibrated {runtime["all_run_hours_excluding_download"]["optimistic"]:.0f}–
{runtime["all_run_hours_excluding_download"]["conservative"]:.0f} T4×2 hours; reserve
{runtime["recommended_free_storage_gb"]} GB.

Benchmark portfolio decision: retain MMLU, GSM8K, and BBH. A fourth benchmark is deferred because
the current portfolio already spans knowledge, arithmetic reasoning, and diverse symbolic/logical
tasks, while the frozen maximum plan is already compute-heavy. Adding a benchmark without S2
calibration would increase cost more clearly than construct coverage.
""",
    )


def _novelty_report() -> None:
    _write(
        "VALID_EVAL_V7_NOVELTY_DEFENSE.md",
        """# ValidEval V7 Novelty Defense

This is a claim audit, not final related-work prose.

| Work | What it does | ValidEval overlap | What it does better | What V7 uniquely tests | Must not claim |
|---|---|---|---|---|---|
| [HELM](https://arxiv.org/abs/2211.09110) | Multi-scenario, multi-metric transparent evaluation | Common panels and raw artifacts | Breadth and standardized scenarios | Claim-specific licensing across uncertainty, materiality, external validity, and regret | First holistic evaluation framework |
| [BetterBench](https://arxiv.org/abs/2411.12990) | Audits benchmark-development best practices | Benchmark quality and reproducibility | Broad practice taxonomy across published benchmarks | Executable statistical gates for individual claims | First benchmark-quality checklist |
| [BenchBench](https://arxiv.org/abs/2407.13696) | Meta-evaluates benchmark agreement and robustness | Ranking/benchmark comparison | Direct benchmark meta-evaluation | Joint licensing with external, held-out, transport, and regret gates | First benchmark meta-evaluation |
| [tinyBenchmarks](https://arxiv.org/abs/2402.14992) | Efficient evaluation using IRT/item subsets | IRT and subset design | Compute-efficient score recovery | Validity threats and decision consequences, not score approximation alone | First IRT-based LLM evaluation |
| [Land & Bikel 2026](https://arxiv.org/abs/2605.30504) | Uses IRT indicators to identify mislabeled benchmark items | Direct item-diagnostic overlap | Multi-benchmark scale and human validation | Whether a diagnostic may license a claim after multiplicity, stability, materiality, and transport | Novelty for IRT flaw detection |
| [Can We Trust IRT in LLM Evaluation?](https://arxiv.org/abs/2607.15190) | Simulates IRT reliability across panel regimes | Direct regime-study overlap | Much larger simulation program | Integrates regime adequacy into fail-closed claim licensing | Novelty for showing small/non-normal panels can fail |
| [Ranking Uncertainty](https://arxiv.org/abs/2607.16259) | Quantifies rank uncertainty and subject variability | Direct rank-set overlap | Dedicated simultaneous rank inference | Couples rank uncertainty to selective decisions, regret, repair, and transport | Novelty for rank uncertainty itself |
| [JE-IRT](https://arxiv.org/abs/2509.22888) | Geometric multidimensional IRT | Measurement-model overlap | Rich latent geometry | Regime-gated choice among simpler and richer models | A new multidimensional IRT model |
| [Benchmark contamination survey](https://arxiv.org/abs/2401.06059) / [LiveBench](https://arxiv.org/abs/2406.19314) / [TRUCE](https://arxiv.org/abs/2403.00393) | Detects or mitigates contamination | Forensic/contamination threats | Purpose-built contamination evidence and fresh data | Requires contamination evidence to pass identity and decision-materiality gates before licensing a claim | Position imbalance proves contamination |

Defensible proposed contribution: a multidimensional claim-licensing methodology that treats
diagnostics as fallible measurement instruments and conditions each claim on uncertainty,
stability, false-positive behavior, decision materiality, independent validation, and transport.
Its scientific effectiveness is not yet established: the frozen synthetic readout failed and real
transport/human studies remain unexecuted.
""",
    )


def _red_team_report() -> None:
    objections = [
        (
            "This is just engineering.",
            "critical",
            "Center contribution on the statistical licensing contract; controlled GPU/human evidence still required.",
        ),
        (
            "IRT already exists.",
            "critical",
            "Concede IRT is prior work; do not claim novelty for item discrimination.",
        ),
        (
            "Rank uncertainty already exists.",
            "critical",
            "Concede prior work; contribution is its use inside scoped decision licenses.",
        ),
        (
            "The model panel is dependent.",
            "high",
            "Family bootstrap, equal-family weighting, LOFO, hybrid-family sensitivity, S3/S4 diversity.",
        ),
        (
            "The benchmarks are too similar.",
            "high",
            "Three constructs and leave-one-benchmark-out transport; fourth benchmark remains deferred.",
        ),
        (
            "The method has no theorem.",
            "high",
            "State as an auditable decision procedure; add formal error/regret guarantees before a theory claim.",
        ),
        (
            "The diagnostics are post-selected.",
            "critical",
            "Primary diagnostics and thresholds are frozen at the confirmatory tag.",
        ),
        (
            "The synthetic study is circular.",
            "critical",
            "Generator/truth are sealed from readout; nevertheless the readout failed and is not retuned.",
        ),
        (
            "Human review estimates precision but not recall.",
            "high",
            "Protocol explicitly forbids recall claims.",
        ),
        (
            "Repair is tuned on the same panel.",
            "critical",
            "Repair requires cross-fitting, held-out labels/families, and matched random controls.",
        ),
        (
            "Cross-benchmark transfer is underpowered.",
            "critical",
            "Transport is currently BLOCKED; S2 recalibration and exact overlap gates required.",
        ),
        (
            "Benchmark flaws do not change decisions.",
            "critical",
            "Observed single-item influence did not change the winner; preserve this negative result.",
        ),
        (
            "The software is more mature than the science.",
            "critical",
            "Final gate is PARTIAL, not scientifically complete.",
        ),
    ]
    lines = [
        "# ValidEval V7 ICML Reviewer Red Team",
        "",
        "| Objection | Severity | Repair / required experiment |",
        "|---|---|---|",
    ]
    lines.extend(f"| {a} | {b} | {c} |" for a, b, c in objections)
    lines.extend(
        [
            "",
            "Current verdict: the strongest objections remain synthetic validity, controlled cross-benchmark transfer, human validation, and decision materiality on exact Study C outputs. They are explicit blockers rather than prose-level fixes.",
        ]
    )
    _write("VALID_EVAL_V7_ICML_REVIEWER_RED_TEAM.md", "\n".join(lines) + "\n")


def _repair_changelog() -> None:
    _write(
        "VALID_EVAL_V7_REPAIR_CHANGELOG.md",
        """# ValidEval V7 Repair Changelog

- Added claim contracts and fail-closed licensing states instead of a scalar validity score.
- Added family-aware inferential diagnostics, BH/BY control, bootstrap stability, and a dependency audit.
- Added seven Study H nulls, nested bootstraps, equal-family weighting, and null-sensitivity reporting.
- Fixed duplicate-column bootstrapping in Kendall W and positive-direction loadings in the regime generator; regression tests cover both paths.
- Added outcome-specific generalizability, selective ranking, regret, exact deletion fragility, and cross-fit influence comparisons.
- Froze a decoupled synthetic protocol before execution and retained its failed acceptance result.
- Added six-estimand transport, exact V7 panels/runs/fallbacks, option log-likelihood, strict alternate parsing, and quantization panels.
- Retired 27 exact MMLU and 4 exact BBH duplicate items from scientific manifests.
- Preserved `REDUX_VALIDATION_RETIRED`; no unsupported fuzzy rescue was attempted.
- Added balanced blinded human sampling while reusing audited packet/import/agreement/adjudication paths.
- Repair policies are named and validated, but remain `BLOCKED` until held-out labels and exact controlled panels exist. No repaired benchmark score is reported.
""",
    )


def _execution_plan(runtime: dict[str, Any]) -> None:
    gpu = pd.read_csv(ROOT / "results/v7/planning/gpu_runtime/run_estimates.csv")
    header = "| run_id | class | priority | mandatory | question | study | benchmark | models/families/items/subtasks | hardware | runtime opt/exp/cons | storage | dependencies | command_or_notebook | outputs | acceptance_gate | claims_unlocked | claims_not_unlocked | fallback |"
    sep = "|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    rows = []
    for record in gpu.to_dict(orient="records"):
        stage = record["stage"]
        run_class = {
            "S1": "G0_GPU_SMOKE",
            "S2": "G1_GPU_PILOT",
            "S3": "G2_GPU_SCIENTIFIC_PRIMARY",
            "S4": "G4_GPU_OPTIONAL_EXTENSION",
            "S5": "G3_GPU_ROBUSTNESS",
        }[stage]
        mandatory = "yes" if stage in {"S1", "S2", "S3"} else "no"
        subtasks = {"mmlu": 57, "gsm8k": 1, "bbh": 27}[record["benchmark"]]
        fallback = (
            "frozen public S4 route" if stage == "S4" else "resume exact config or record failure"
        )
        rows.append(
            f"| {record['run_id']} | {run_class} | {1 if mandatory == 'yes' else 2} | {mandatory} | Exact controlled responses? | Study C | {record['benchmark']} | {record['models']}/{record['families']}/{record['items']}/{subtasks} | Kaggle T4×2 | {record['runtime_hours_optimistic']:.1f}/{record['runtime_hours_expected']:.1f}/{record['runtime_hours_conservative']:.1f} h | {record['download_gb'] + record['estimated_output_gb']:.1f} GB | final tag, lock, manifest | `{record['command_or_notebook']}` | deterministic ZIP | identity+coverage+extraction | stage-scoped | global validity | {fallback} |"
        )
    cpu = """| CPU-CLAIMS | C0_CPU_EXISTING_DATA | 0 | yes | Do gates fail closed? | A | fixture contracts | CPU | local CPU | <1 s | <1 MB | source | `python scripts/run_claim_licensing_v7.py` | ledger validation | all failure states tested | method readiness | substantive claims | fix tests |
| CPU-DIAGNOSTICS | C0_CPU_EXISTING_DATA | 0 | yes | Which items survive inference? | B | MMLU 39/10/14042/57 | CPU | local CPU | 7.8 s | 5 MB | cached matrix | `python scripts/run_diagnostic_inference_v7.py` | item table | BH+stability | no discoveries | causes | none |
| CPU-STUDY-H | C2_CPU_STATISTICAL | 0 | yes | Is rank dispersion protocol-stable? | H | MMLU 39/10/14042/57 | CPU | local CPU | 10.3 s | 3 MB | cached matrix | `python scripts/run_study_h_v7.py` | bootstrap/null tables | reproduce+null audit | scoped variability | global ranking | none |
| CPU-G | C2_CPU_STATISTICAL | 0 | yes | Which designs generalize? | D | MMLU | CPU | local CPU | 0.3 s | <1 MB | cached matrix | `python scripts/run_generalizability_v7.py` | variance/design curves | outcome-specific | design planning | population components | none |
| CPU-DECISION | C2_CPU_STATISTICAL | 0 | yes | Are differences material? | E | MMLU | CPU | local CPU | 0.3 s | <1 MB | Study H draws | `python scripts/run_decision_materiality_v7.py` | decisions/regret | CI+0.01 | historical decisions | deployment truth | none |
| CPU-INFLUENCE | C0_CPU_EXISTING_DATA | 0 | yes | Do deletions change decisions? | F | MMLU | CPU | local CPU | 8.6 s | 3 MB | cached matrix | `python scripts/run_benchmark_influence_v7.py` | deletion/crossfit | held-out comparison | historical sensitivity | flaw labels | none |
| CPU-REGIME | C1_CPU_SYNTHETIC | 0 | yes | When are models identifiable? | G | 19 generators | CPU | local CPU | 0.3 s | <1 MB | source | `python scripts/run_measurement_regime_study_v7.py` | regime map | recovery thresholds | generator-scoped map | real latent trait | none |
| CPU-SYNTH | C1_CPU_SYNTHETIC | 0 | yes | Does frozen readout detect flaws? | H | 162 scenarios | CPU | local CPU | 1.9 s | <1 MB | freeze tag | `python scripts/run_confirmatory_synthetic_v7.py` | metrics | preregistered criteria | negative evidence | real item validity | new version only |
| CPU-FORENSICS | C0_CPU_EXISTING_DATA | 1 | yes | Are position artifacts present? | L | MMLU 547638 rows | CPU | local CPU | 2.2 s | 1 MB | cached predictions | `python scripts/run_benchmark_forensics_v7.py` | distributions | identity consistency | forensic description | contamination | none |
| CPU-POWER | C2_CPU_STATISTICAL | 0 | yes | Is 0.01 detectable? | M | S2/S3/S4 | CPU | local CPU | <1 s | <1 MB | assumptions | `python scripts/run_panel_power_v7.py` | grid | >=0.80 | planning | empirical power | recalibrate S2 |
| H0 | H0_HUMAN_PILOT | 1 | yes | Is rubric usable? | K | 4 strata | Human | 2 annotators | TBD | private | GPU candidates | packet/import commands | blinded labels | controls+agreement | pilot precision | recall | revise rubric before H1 |
| H1 | H1_HUMAN_CONFIRMATORY | 2 | yes | What precision/enrichment holds? | K | 4 strata | Human | 2–3 annotators | TBD | private | H0 pass | packet/import commands | adjudicated+raw | frozen endpoint | scoped precision | recall/global prevalence | report blocked |"""
    content = f"""# ValidEval ICML 2027 Execution Plan

Planning ranges are not measured GPU runtimes. Primary route totals exclude download time and span
{runtime["all_run_hours_excluding_download"]["optimistic"]:.0f}–{runtime["all_run_hours_excluding_download"]["conservative"]:.0f}
T4×2 hours; recommended free storage is {runtime["recommended_free_storage_gb"]} GB.

{header}
{sep}
{cpu}
{chr(10).join(rows)}

Every GPU package routes through `python -m valideval ingest-and-analyze --input <zip-or-dir>`.
Fallback never selects a replacement after seeing benchmark scores.
"""
    (ROOT / "VALID_EVAL_ICML2027_EXECUTION_PLAN.md").write_text(content, encoding="utf-8")


def _handoff(
    study_h: dict[str, Any],
    diagnostics: dict[str, Any],
    general: dict[str, Any],
    decision: dict[str, Any],
    influence: dict[str, Any],
    regime: dict[str, Any],
    synthetic: dict[str, Any],
    transport: dict[str, Any],
    power: dict[str, Any],
    runtime: dict[str, Any],
) -> None:
    content = f"""# ValidEval V7 Final Maximum Pre-Execution Handoff

Final gate: `ICML2027_STRONG_PRE_EXECUTION_BUILD_PARTIAL`.

The repository has a complete V7 claim-licensing implementation, frozen S2/S3/S4/S5 execution
contracts, 10 T4×2 notebooks, secure ingest-and-analyze routing, deterministic release profiles,
and CPU studies. It is not scientifically complete.

## Evidence gates

- Claim licensing: `CLAIM_LICENSING_METHOD_READY` (contract behavior only).
- Inferential diagnostics: `INFERENTIAL_DIAGNOSTICS_READY`; stable flags = {diagnostics["stable_FDR_flags"]}.
- Study H: `{study_h["status"]}` because conclusions vary strongly across nulls.
- Generalizability: `{general["status"]}` with descriptive unbalanced components.
- Decision materiality: `{decision["status"]}` on historical MMLU only.
- Benchmark influence: `{influence["status"]}`; winner-changing items = {influence["winner_changing_items"]}.
- Measurement regime: `{regime["status"]}`; counts = {regime["regime_counts"]}.
- Synthetic execution: `{synthetic["status"]}`; acceptance = `{synthetic["acceptance_status"]}`.
- Transport build: `{transport["build_status"]}`; evidence = `{transport["overall_status"]}`.
- Human protocol: `HUMAN_CONFIRMATORY_PROTOCOL_READY`; labels not collected.

## Study C

S1, S2, S3, S4, and robustness infrastructure are ready to execute. S3/S4 scientific interpretation
is conditional on S1/S2 acceptance, exact family coverage, extraction reliability, and power
recalibration. Planning power for a 0.01 pairwise difference is
{power["s3_materiality_power_range"][0]:.3f}–{power["s3_materiality_power_range"][1]:.3f}; it does not
meet 0.80. GPU execution remains {runtime["all_run_hours_excluding_download"]["optimistic"]:.0f}–
{runtime["all_run_hours_excluding_download"]["conservative"]:.0f} uncalibrated T4×2 hours for the
primary route.

## Primary next action

Run the existing S1 controlled smoke, import all three ZIPs, then run S2 MMLU/GSM8K/BBH. Recalibrate
runtime, extraction, memory, and paired-difference power before authorizing S3. Do not tune the V7
synthetic readout and reuse its confirmatory label; any new detector is V8 exploratory until frozen.
"""
    (ROOT / "VALID_EVAL_V7_FINAL_MAXIMUM_PRE_EXECUTION_HANDOFF.md").write_text(
        content, encoding="utf-8"
    )


def _machine_state(
    study_h: dict[str, Any],
    diagnostics: dict[str, Any],
    general: dict[str, Any],
    decision: dict[str, Any],
    influence: dict[str, Any],
    regime: dict[str, Any],
    synthetic: dict[str, Any],
    transport: dict[str, Any],
    runtime: dict[str, Any],
) -> None:
    validation_path = ROOT / "results/v7/validation/final_validation.json"
    validation = _json_path(validation_path) if validation_path.is_file() else {"status": "PENDING"}
    runtime_total = sum(
        float(value.get("runtime_seconds", 0.0))
        for value in (study_h, diagnostics, general, decision, influence, regime, synthetic)
    ) + float(_json("results/v7/forensics/mmlu_v7.json").get("runtime_seconds", 0.0))
    payload = {
        "schema_version": "7.0",
        "generated_at": "2026-08-09",
        "branch": _git("branch", "--show-current"),
        "head_at_generation": _git("rev-parse", "HEAD"),
        "freeze_tag": "valideval-v7-confirmatory-freeze",
        "freeze_commit": _git("rev-parse", "valideval-v7-confirmatory-freeze^{commit}"),
        "final_commit": None,
        "final_commit_resolution": (
            "Resolve ci_patch_tag^{commit}; the required final tag was preserved under the "
            "no-force policy after a GitHub-only lint compatibility patch."
        ),
        "final_tag": "valideval-v7-icml2027-max-pre-execution",
        "ci_patch_tag": "valideval-v7-icml2027-max-pre-execution-ci2",
        "final_gate": "ICML2027_STRONG_PRE_EXECUTION_BUILD_PARTIAL",
        "statuses": {
            "claim_licensing": "CLAIM_LICENSING_METHOD_READY",
            "inferential_diagnostics": diagnostics["status"],
            "study_h": study_h["status"],
            "generalizability": general["status"],
            "decision_materiality": decision["status"],
            "benchmark_influence": influence["status"],
            "measurement_regime": regime["status"],
            "synthetic_execution": synthetic["status"],
            "synthetic_acceptance": synthetic["acceptance_status"],
            "transport_build": transport["build_status"],
            "transport_evidence": transport["overall_status"],
            "human_protocol": "HUMAN_CONFIRMATORY_PROTOCOL_READY",
            "s1": "S1_READY",
            "s2": "S2_READY",
            "s3": "S3_READY",
            "s4": "S4_READY",
            "robustness": "ROBUSTNESS_RUNBOOKS_READY",
        },
        "cpu_runtime_seconds_recorded": runtime_total,
        "gpu_runtime_planning": runtime,
        "validation": validation,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
        },
        "blocked": [
            "all controlled GPU evidence",
            "human labels",
            "cross-benchmark transport",
            "held-out repair validation",
            "synthetic diagnostic acceptance",
            "MMLU-Redux exact identity",
        ],
    }
    (ROOT / "VALID_EVAL_V7_MACHINE_STATE.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write(name: str, content: str) -> None:
    (REPORT_ROOT / name).write_text(content.strip() + "\n", encoding="utf-8")


def _json(relative: str) -> dict[str, Any]:
    return _json_path(ROOT / relative)


def _json_path(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
