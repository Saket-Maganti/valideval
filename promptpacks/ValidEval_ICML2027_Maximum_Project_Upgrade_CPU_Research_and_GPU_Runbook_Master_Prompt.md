# ValidEval — ICML 2027 Maximum-Ceiling Project Upgrade Master Prompt

## Mission

You are taking over the complete **ValidEval** repository for one aggressive but evidence-disciplined upgrade pass aimed at pushing the project as close as possible to its **maximum credible ICML 2027 ceiling before the remaining large GPU experiments and final paper construction**.

This is not a paper-writing task.

This is not another prompt-pack generation task.

This is not a planning-only audit.

You must directly inspect the live repository, preserve the validated V6 evidence boundary, implement the strongest remaining scientific methodology, execute every feasible CPU-only analysis and simulation, repair code/statistical weaknesses, formalize the project’s main statistical contribution, build the complete exact-model controlled Study C, maximize diagnostic validity and leakage resistance, build production-grade GPU execution configs and Kaggle T4×2 notebooks/runbooks, and leave the project in the strongest possible pre-full-execution state.

Target: **ICML 2027 main track**.

Optimize for:
1. scientific originality;
2. statistical soundness;
3. claim identifiability;
4. decision relevance;
5. generalization;
6. cross-benchmark transportability;
7. reproducibility;
8. robustness;
9. reviewer trust;
10. maximum eventual paper ceiling.

---

## Repository

Expected local repository:

```text
/Users/saketmaganti/Projects/Valideval
```

Remote:

```text
Saket-Maganti/valideval
```

Current important refs:

```text
valideval-v5-pre-execution
valideval-v6-controlled-gpu-smoke-ready
```

Current validated V6 state is approximately:

```text
CONTROLLED_GPU_SMOKE_READY
PRODUCTION_RUNNER_READY
S1_EXACT_PANEL_FROZEN
S1_BENCHMARK_CONTRACTS_FROZEN
BBH_PROTOCOL_FROZEN
S1_LEAKAGE_GUARDS_COMPLETE
T4X2_SCHEDULER_READY
KAGGLE_NOTEBOOKS_PRODUCTION_PATH_VALIDATED
S1_IMPORT_AND_ACCEPTANCE_READY
RANK_MATERIALITY_ANALYSIS_READY
MEASUREMENT_MODEL_PLAN_DEFENSIBLE
```

The exact live repository is the source of truth.

Read before modifying:

```text
VALID_EVAL_V6_FINAL_PRE_S1_HANDOFF.md
VALID_EVAL_V6_CONTROLLED_GPU_SMOKE_RUNBOOK.md
VALID_EVAL_V6_MACHINE_STATE.json
reports/v5/VALID_EVAL_V5_CONTRIBUTION_HIERARCHY.md
reports/v6/MMLU_V6_RANK_MATERIALITY_CLOSURE.md
reports/v6/VALID_EVAL_V6_MEASUREMENT_MODEL_CLOSURE.md
reports/v6/VALID_EVAL_V6_S1_LEAKAGE_SEAL.md
reports/v6/VALID_EVAL_V6_REPAIR_CHANGELOG.md
results/evidence/claim_evidence_ledger_v5.csv
```

---

# Hard boundaries

## Do not construct the final paper

Do not spend this pass on final prose polishing, venue formatting, camera-ready layout, abstract iteration, final title selection, final figure placement, submission forms, author block, or rebuttal writing.

You may build paper-ready result generators, figure/table code, LaTeX macros, evidence-to-paper automation, and artifact-backed result templates.

## Do not fabricate GPU evidence

Do not fabricate S1/S2/S3/S4 outputs, benchmark results, controlled MMLU results, human labels, external labels, or cross-benchmark findings.

## CPU execution is mandatory

Run all feasible CPU-safe analyses using the existing 39-model historical MMLU matrix, synthetic data, locally available metadata, fixture data, planning simulations, and cached artifacts.

If an analysis is computationally expensive but feasible on CPU, run it unless clearly unreasonable.

## GPU infrastructure must be complete

All remaining GPU-dependent work must have exact configs, exact model revisions, benchmark revisions, prompts, seeds, output schemas, run manifests, T4×2-safe notebooks, resume, OOM fallback, import, validation, acceptance, and downstream analysis routes.

No GPU experiment should remain only as a prose idea.

---

# Core scientific repositioning

The project must no longer be framed internally as:

```text
a toolkit with many diagnostics
```

or:

```text
IRT applied to LLM benchmarks
```

or:

```text
rankings are unstable
```

Build ValidEval toward a **claim-licensing statistical methodology**:

> Benchmark diagnostics are measurement instruments. A diagnostic should only support a benchmark-quality or model-comparison claim when its uncertainty, stability, false-positive behavior, materiality, external validity, and transportability satisfy predeclared conditions.

---

# Phase A — Formal claim-licensing framework

This is the highest-priority methodology upgrade.

Define claim classes:

```text
DESCRIPTIVE
STABLE
MATERIAL
EXTERNALLY_VALIDATED
TRANSPORTABLE
DECISION_LICENSED
BLOCKED
```

Define benchmark claim types:

```text
MODEL_A_OUTPERFORMS_MODEL_B
MODEL_IN_TOP_K
MODEL_CROSSES_THRESHOLD
MODEL_FAMILY_BEST
ITEM_IS_SUSPICIOUS
SUBJECT_IS_UNSTABLE
BENCHMARK_RANKING_IS_STABLE
DIAGNOSTIC_TRANSFERS
REPAIR_IMPROVES_DECISION
```

Implement:

```python
license_claim(claim, evidence, policy) -> ClaimLicenseResult
```

Return:

```text
LICENSED
LICENSED_WITH_SCOPE
EXPLORATORY_ONLY
UNDERPOWERED
BLOCKED_BY_UNCERTAINTY
BLOCKED_BY_MULTIPLICITY
BLOCKED_BY_EXTERNAL_VALIDATION
BLOCKED_BY_TRANSPORT
BLOCKED_BY_IDENTITY
BLOCKED_BY_LEAKAGE
```

Make policy configurable:
- confidence level;
- FDR level;
- bootstrap stability threshold;
- effect-size threshold;
- minimum exact-model overlap;
- minimum independent model families;
- external validation requirement;
- held-out validation requirement;
- minimum human precision;
- transport heterogeneity threshold;
- decision-regret bound.

Use confidence bounds, not point estimates.

Examples:
- A > B only if lower confidence bound of delta exceeds the materiality threshold.
- Top-k only if simultaneous rank set supports membership.
- Item suspicious only if q <= alpha and bootstrap stability passes threshold.
- Transfer supported only if held-out benchmark/family validation passes.

Create:

```text
src/valideval/claims/
src/valideval/claims/contracts.py
src/valideval/claims/licensing.py
src/valideval/claims/policies.py
src/valideval/claims/evidence.py
src/valideval/claims/reporting.py
tests/test_claim_licensing_v7.py
tests/test_claim_policy_v7.py
tests/test_claim_failure_states_v7.py
reports/v7/VALID_EVAL_V7_CLAIM_LICENSING_METHOD.md
```

---

# Phase B — Inferential diagnostic framework

Audit diagnostic dependencies.

For every diagnostic define:
- source data;
- formula;
- dependency on accuracy;
- dependency on rank;
- dependency on external labels;
- dependency overlap with other diagnostics.

Build:

```text
results/diagnostics/diagnostic_dependency_graph_v7.json
reports/v7/VALID_EVAL_V7_DIAGNOSTIC_DEPENDENCY_AUDIT.md
```

Recompute every retained diagnostic independently.

Retire any diagnostic that is duplicate, algebraically equivalent, label-contaminated, post-selected, or not genuinely independent.

Implement:
- item bootstrap;
- family-cluster bootstrap;
- subject-aware bootstrap;
- CIs;
- stability-selection frequency;
- null distributions;
- matched-difficulty nulls;
- permutation nulls;
- empirical-Bayes shrinkage;
- Benjamini-Hochberg FDR;
- Benjamini-Yekutieli sensitivity.

Each flagged item should expose:

```text
diagnostic_score
standard_error
confidence_interval
null_p_value
FDR_q_value
bootstrap_stability
effect_size
subject
difficulty
claim_status
```

Build diagnostic agreement/disagreement matrices and taxonomy:

```text
CONSISTENT_HIGH_RISK
DIFFICULTY_ONLY
DISCRIMINATION_ONLY
RANK_MATERIAL_ONLY
FORENSIC_ONLY
DIAGNOSTIC_CONFLICT
LOW_SIGNAL
```

Create:

```text
src/valideval/diagnostics/inference.py
src/valideval/diagnostics/stability.py
src/valideval/diagnostics/multiplicity.py
src/valideval/diagnostics/dependency.py
scripts/run_diagnostic_inference_v7.py
reports/v7/VALID_EVAL_V7_INFERENTIAL_DIAGNOSTIC_REPORT.md
```

---

# Phase C — Max out Study H with existing MMLU data

Use the historical 39-model x 14,042-item panel.

Do not restore the old “severe >=10” language.

Implement/verify:
- pairwise superiority probabilities;
- simultaneous rank confidence sets;
- top-1 probability;
- top-3 probability;
- top-5 probability;
- top-10 probability;
- rank entropy;
- normalized rank dispersion;
- top-k Jaccard;
- Kendall W CI;
- subject-to-subject Kendall tau;
- effect-size-filtered reversals.

Resampling:
- item bootstrap within subject;
- nested subject/item bootstrap;
- family-cluster bootstrap;
- one-model-per-family sensitivity;
- equal-family weighting;
- leave-one-family-out;
- leave-one-subject-out;
- leave-one-model-out.

Null suite:

```text
ADD_ABILITY_SUBJECT
EMPIRICAL_BAYES_ADDITIVE
SUBJECT_SIZE_ONLY
FIXED_MARGIN_PERMUTATION
FAMILY_CORRELATED_NULL
LATENT_FACTOR_NULL
MODEL_SUBJECT_RANDOM_EFFECT_NULL
```

Sensitivity sweeps:
- model count;
- subject count;
- item count;
- ability spread;
- family concentration;
- missingness;
- saturation;
- chance-level model fraction.

Benchmark composition:
- subject reweighting;
- item reweighting;
- leave-subject-out;
- random item removal;
- matched-difficulty removal;
- family-balanced ranking.

Create benchmark fragility curves.

Outputs:

```text
results/mmlu/study_h_v7/
reports/v7/MMLU_V7_FULL_UNCERTAINTY_AND_NULL_ANALYSIS.md
```

---

# Phase D — Generalizability theory and variance decomposition

Build a variance-decomposition framework.

Study H components:

```text
model
family
subject
item
model × subject
family × subject
residual
```

Future Study C components:

```text
benchmark
model × benchmark
family × benchmark
prompt
model × prompt
seed
model × seed
```

Compute reliability/generalizability for:
- aggregate benchmark score;
- pairwise model comparison;
- top-k selection;
- subject-conditioned score.

Estimate how many:
- items;
- subjects;
- model families;
- model checkpoints;

are needed for target reliability:

```text
0.80
0.90
0.95
```

Create benchmark-design reliability curves.

Create:

```text
src/valideval/reliability/
src/valideval/reliability/variance_components.py
src/valideval/reliability/generalizability.py
src/valideval/reliability/design_curves.py
scripts/run_generalizability_v7.py
reports/v7/VALID_EVAL_V7_GENERALIZABILITY_STUDY.md
```

---

# Phase E — Decision materiality and selective ranking

Move from “variation exists” to “does variation alter a decision?”

Support:

```text
PAIRWISE_SUPERIORITY
TOP_1
TOP_K
THRESHOLD_PASS
BEST_FAMILY
DEPLOYMENT_SELECTION
```

Define configurable practical materiality thresholds.

Build selective ranking that can output:

```text
A > B
A ~ B
INSUFFICIENT_EVIDENCE
```

Build pairwise confidence graphs.

Implement expected decision regret.

Compare:
- naive leaderboard;
- uncertainty-aware selection;
- claim-licensed selection.

Find:
- minimum subject-weight perturbation that flips decision;
- minimum item removal fraction that flips decision;
- minimum matched-difficulty removal that flips decision.

If feasible, approximate:

```text
smallest benchmark composition perturbation causing decision reversal
```

Create:

```text
src/valideval/decision/
src/valideval/decision/selective_ranking.py
src/valideval/decision/regret.py
src/valideval/decision/fragility.py
scripts/run_decision_materiality_v7.py
reports/v7/VALID_EVAL_V7_DECISION_MATERIALITY.md
```

---

# Phase F — Benchmark item influence

Build exact leave-one-item influence for tractable subsets.

Estimate influence on:
- model scores;
- pairwise differences;
- top-k;
- winner.

Implement scalable approximations and validate against exact subsets.

Compute subject influence.

For suspicious-item removal:
- discover on one fold;
- evaluate on held-out fold.

Compare against:
- random removal;
- matched-difficulty removal;
- high-difficulty removal;
- high-variance removal.

Create:

```text
src/valideval/influence/
scripts/run_benchmark_influence_v7.py
reports/v7/VALID_EVAL_V7_BENCHMARK_INFLUENCE.md
```

---

# Phase G — Measurement model regime study

Use the validated regularized subject-conditioned model as a baseline.

Compare:
- aggregate ability;
- additive model + subject difficulty;
- regularized subject-conditioned model;
- low-rank factor model;
- Rasch/1PL where feasible;
- regularized 2PL on controlled subsets;
- Bayesian hierarchical model if feasible.

Cross-validation:
- held-out items;
- held-out subjects where meaningful;
- held-out model families;
- grouped CV.

Metrics:
- log loss;
- Brier;
- calibration;
- calibration slope/intercept;
- rank prediction;
- held-out pairwise-order prediction.

Simulate regimes:

```text
model_count = [5, 10, 20, 30, 40, 80, 120]
family_count
item_count
subject_count
ability_distribution
family_correlation
latent_dimensions
missingness
saturation
```

Ability distributions:
- Gaussian;
- skewed;
- multimodal;
- family-clustered;
- heavy-tailed.

Evaluate parameter recovery where latent parameters are claimed:
- bias;
- RMSE;
- coverage;
- rank recovery;
- calibration.

Build a regime map:

```text
SUPPORTED
CAUTION
UNRELIABLE
UNIDENTIFIABLE
```

Create:

```text
src/valideval/measurement/regime_study.py
scripts/run_measurement_regime_study_v7.py
results/measurement/regime_study_v7/
reports/v7/VALID_EVAL_V7_MEASUREMENT_REGIME_STUDY.md
```

---

# Phase H — Confirmatory decoupled synthetic validation

Freeze before running:
- generators;
- flaw classes;
- diagnostics;
- primary metric;
- primary thresholds;
- seeds;
- sample sizes;
- success criteria.

Git-hash/tag the freeze.

Flaw classes:

```text
NO_FLAW
LABEL_ERROR
MULTIPLE_LABEL_ERRORS
AMBIGUITY
DISTRACTOR_FAILURE
SUBJECT_MISASSIGNMENT
DUPLICATE_ITEM
MISSINGNESS
CORRELATED_MODEL_FAILURE
```

Sweep:
- flaw severity;
- prevalence;
- number of models;
- number of families;
- item count;
- subject count;
- dependence.

Controls:
- label permutation;
- no flaw;
- unseen flaw;
- held-out generator family;
- mixed flaws;
- diagnostic ablation.

Primary metrics:
- AUPRC;
- precision@k;
- FDR;
- recall at fixed FDR;
- calibration;
- power.

Secondary:
- AUROC;
- enrichment.

Create:

```text
configs/synthetic/confirmatory_v7.yaml
results/synthetic/confirmatory_v7/
reports/v7/VALID_EVAL_V7_CONFIRMATORY_SYNTHETIC_RESULTS.md
```

These may be promoted as real CPU evidence only if the freeze truly precedes the run.

---

# Phase I — Diagnostic transportability methodology

Define transport estimands:

```text
score_transport
ranking_transport
flag_transport
calibration_transport
decision_transport
repair_transport
```

Build future analyses for:
- MMLU → GSM8K;
- MMLU → BBH;
- GSM8K → BBH;
- pooled → held-out benchmark.

Require leave-one-benchmark-out and leave-one-model-family-out.

Implement:
- benchmark-specific effects;
- pooled effect;
- heterogeneity;
- random-effects meta-analysis where appropriate.

Return:

```text
TRANSFER_SUPPORTED
TRANSFER_PARTIAL
TRANSFER_BENCHMARK_SPECIFIC
TRANSFER_DIRECTION_REVERSES
TRANSFER_NOT_SUPPORTED
UNDERPOWERED
BLOCKED
```

Create:

```text
src/valideval/transport/
scripts/run_transportability_v7.py
reports/v7/VALID_EVAL_V7_TRANSPORTABILITY_METHOD.md
```

---

# Phase J — MMLU-Redux final policy

Do one final low-cost identity attempt only if justified using:
- normalized question;
- normalized options;
- answer;
- subject;
- source index;
- canonical hash.

Detect collisions.

If identity remains unresolved, permanently preserve:

```text
REDUX_VALIDATION_RETIRED
```

Do not spend further project time on it.

---

# Phase K — Human validation maximization

Do not fabricate labels.

Complete:
- stratified sampler;
- high/medium/low diagnostic strata;
- random controls;
- subject balancing;
- benchmark balancing;
- blinding;
- final taxonomy;
- power/precision planner;
- agreement metrics;
- adjudication pipeline.

Annotators must not see:
- diagnostic score;
- issue probability;
- model identity;
- model-response pattern where avoidable;
- external labels.

Final taxonomy:

```text
INCORRECT_GOLD
AMBIGUOUS_STEM
AMBIGUOUS_OPTIONS
MULTIPLE_VALID_ANSWERS
INSUFFICIENT_CONTEXT
OUTDATED_FACT
SCORING_ERROR
EXTRACTION_ERROR
DOMAIN_DISPUTE
NO_ISSUE
UNSURE
```

Simulate annotation sizes:

```text
50
100
150
200
300
500
```

Estimate precision CI, enrichment CI, agreement precision, and issue-prevalence uncertainty.

Support:
- 2 annotators;
- 3 annotators;
- specialist adjudication.

Create:

```text
configs/human/human_validation_v7.yaml
reports/v7/VALID_EVAL_V7_HUMAN_STUDY_FINAL_PROTOCOL.md
results/planning/human_annotation_power_v7.csv
```

---

# Phase L — Benchmark contamination and forensics

Run CPU analyses for:
- exact duplicates;
- normalized duplicates;
- option permutations;
- answer-equivalent duplicates;
- cross-split overlap;
- cross-benchmark overlap;
- n-gram overlap;
- MinHash;
- optional embedding candidate retrieval.

For MCQ:
- correct-answer position distribution;
- subject-specific imbalance;
- model answer-position preference;
- position-conditioned accuracy.

Build extraction ambiguity profiles.

Create:

```text
reports/v7/VALID_EVAL_V7_BENCHMARK_FORENSICS.md
```

---

# Phase M — Study C panel optimization

Do not choose 32 models blindly.

Re-run power calculations for actual estimands.

Build a candidate registry with:
- exact repo;
- immutable revision;
- family;
- size;
- instruction/base;
- license;
- memory;
- dtype;
- quantization fallback;
- expected runtime.

Optimize for:
- family diversity;
- ability spread;
- parameter diversity;
- execution feasibility.

Minimize:
- family duplication;
- memory risk;
- cost;
- gated access;
- identity ambiguity.

Build:

```text
S1 engineering smoke
S2 execution pilot
S3 minimum scientific panel
S4 maximum-ceiling panel
S5 robustness extension
```

Freeze a fallback panel before S3.

Create:

```text
configs/panels/s2_pilot_v7.yaml
configs/panels/s3_scientific_v7.yaml
configs/panels/s4_maximum_ceiling_v7.yaml
configs/panels/s4_fallback_v7.yaml
reports/v7/VALID_EVAL_V7_STUDY_C_PANEL_DESIGN.md
```

---

# Phase N — Benchmark portfolio optimization

Primary controlled benchmarks:

```text
MMLU
GSM8K
BBH
```

Evaluate whether one additional construct-diverse benchmark materially improves the study.

Potential roles:
- hard knowledge/reasoning;
- code generation;
- truthfulness;
- instruction following.

Do not add one merely to inflate benchmark count.

If clearly valuable and T4-feasible:
- build adapter;
- freeze contract;
- build notebook;
- add importer;
- add transport analysis.

Otherwise document why the 3-benchmark portfolio is sufficient.

---

# Phase O — Prompt/scoring robustness

Build now:
- MMLU controlled generation;
- MMLU option log-likelihood if feasible;
- GSM8K alternate prompt;
- GSM8K alternate parser on saved outputs;
- BBH alternate prompt;
- optional stochastic seed subset;
- representative quantization sensitivity.

Primary deterministic condition:

```text
temperature = 0
```

All robustness configs go under:

```text
configs/robustness/
```

---

# Phase P — Build every remaining GPU Kaggle T4×2 runbook

Do not execute large studies.

Required notebook/runbook coverage:

```text
S2 pilot MMLU
S2 pilot GSM8K
S2 pilot BBH

S3 scientific MMLU
S3 scientific GSM8K
S3 scientific BBH

S4 maximum-ceiling MMLU
S4 maximum-ceiling GSM8K
S4 maximum-ceiling BBH

prompt robustness
scoring robustness
quantization robustness
optional fourth benchmark
```

Every notebook must:
- pin source commit;
- pin requirements;
- pin model revisions;
- pin dataset revisions;
- validate hashes;
- check T4×2;
- check disk;
- use dual-GPU scheduler;
- checkpoint;
- resume;
- deterministic package;
- print exact local import command.

Provide runtime ranges:

```text
optimistic
expected
conservative
```

Estimate storage and download size.

Classify each run:

```text
ENGINEERING_ONLY
EXPLORATORY
CONFIRMATORY
ROBUSTNESS
OPTIONAL_CEILING_EXTENSION
```

---

# Phase Q — Automatic future GPU import and analysis

Every future GPU output must automatically route through:
1. security validation;
2. provenance validation;
3. identity validation;
4. benchmark validation;
5. coverage;
6. extraction reliability;
7. scoring validation;
8. panel feasibility;
9. claim eligibility;
10. rank uncertainty;
11. measurement models;
12. diagnostic inference;
13. transport;
14. decision materiality;
15. evidence ledger.

If feasible, create:

```bash
python -m valideval ingest-and-analyze --input <zip-or-dir>
```

Fail closed.

---

# Phase R — Preregistration / anti-cherry-picking freeze

Before S3, freeze:

- primary hypothesis;
- primary diagnostics;
- primary panel;
- primary benchmarks;
- primary metric;
- materiality threshold;
- claim policy;
- exclusions;
- missing-data policy;
- multiple-testing method;
- human endpoint;
- transport metric;
- repair policy.

Create:

```text
configs/preregistration/icml2027_primary_v7.yaml
reports/v7/VALID_EVAL_V7_ICML_PREREGISTRATION.md
```

Hash and Git-tag it.

---

# Phase S — Benchmark repair methodology

Build repair policies:

```text
REMOVE_CONFIRMED_ISSUES
DOWNWEIGHT_UNCERTAIN_ITEMS
ABSTAIN_ON_DISPUTED_ITEMS
REWEIGHT_FOR_RELIABILITY
```

Validation must require:
- cross-fitting;
- held-out labels;
- held-out model families;
- random matched baseline.

Measure:
- rank uncertainty;
- pairwise confidence;
- decision regret;
- generalizability;
- calibration;
- reliability.

Return:

```text
REPAIR_SUPPORTED
REPAIR_PARTIAL
REPAIR_NO_BENEFIT
REPAIR_HARMS
UNDERPOWERED
BLOCKED
```

---

# Phase T — Current novelty defense

Use current primary literature and web search.

Build competitor matrix covering:
- HELM;
- BetterBench;
- BenchBench;
- tinyBenchmarks;
- Land & Bikel 2026;
- current IRT reliability work;
- current ranking uncertainty work;
- JE-IRT;
- benchmark contamination;
- benchmark repair;
- uncertainty-aware evaluation.

For each competitor record:

```text
what they do
what ValidEval overlaps
what they do better
what ValidEval uniquely tests
what ValidEval must not claim
```

Create:

```text
reports/v7/VALID_EVAL_V7_NOVELTY_DEFENSE.md
```

Do not write final related-work prose.

---

# Phase U — Reproducibility max-out

Build:
- one-command Study H reproduction;
- one-command synthetic run;
- one-command generalizability run;
- one-command rank-materiality run;
- one-command influence run;
- one-command decision analysis.

CI should fail on:
- evidence-ledger mismatch;
- stale hashes;
- unsupported claim state;
- stale configs.

Create:
- CPU constraints/lock;
- Kaggle T4×2 lock;
- `Dockerfile.cpu` if reasonable;
- source release;
- CPU reproduction release;
- derived evidence release;
- anonymous reviewer release.

Use manifests and checksums.

---

# Phase V — ICML reviewer red-team

Simulate at least:

```text
This is just engineering.
IRT already exists.
Rank uncertainty already exists.
The model panel is dependent.
The benchmarks are too similar.
The method has no theorem.
The diagnostics are post-selected.
The synthetic study is circular.
Human review estimates precision but not recall.
Repair is tuned on the same panel.
Cross-benchmark transfer is underpowered.
The benchmark flaws do not change decisions.
The software is more mature than the science.
```

For each:
- classify severity;
- implement repair if feasible;
- otherwise add exact required future experiment.

Create:

```text
reports/v7/VALID_EVAL_V7_ICML_REVIEWER_RED_TEAM.md
```

---

# CPU execution mandate

Actually execute every feasible CPU study.

At minimum:

```text
claim licensing validation
inferential diagnostics
nested bootstrap
family-balanced bootstrap
null suite
sensitivity sweeps
generalizability analysis
decision materiality
benchmark influence
measurement regime simulation
confirmatory synthetic validation
human power planning
benchmark forensics
panel power optimization
```

Record exact runtime.

Do not reduce simulation depth merely for convenience.

---

# Authoritative remaining-run execution plan

Create:

```text
VALID_EVAL_ICML2027_EXECUTION_PLAN.md
```

Classify runs:

```text
C0_CPU_EXISTING_DATA
C1_CPU_SYNTHETIC
C2_CPU_STATISTICAL
G0_GPU_SMOKE
G1_GPU_PILOT
G2_GPU_SCIENTIFIC_PRIMARY
G3_GPU_ROBUSTNESS
G4_GPU_OPTIONAL_EXTENSION
H0_HUMAN_PILOT
H1_HUMAN_CONFIRMATORY
```

For each run include:

```text
run_id
priority
mandatory
scientific_question
study
benchmark
models
families
items
subtasks
CPU_or_GPU
hardware
runtime_optimistic
runtime_expected
runtime_conservative
storage
dependencies
command_or_notebook
outputs
acceptance_gate
claims_unlocked
claims_not_unlocked
fallback
```

---

# Final gates

Issue separately:

```text
STUDY_H_REPRODUCED_AND_STABLE
STUDY_H_REPRODUCED_WITH_LIMITATIONS
STUDY_H_BLOCKED
```

```text
CLAIM_LICENSING_METHOD_READY
CLAIM_LICENSING_METHOD_PARTIAL
CLAIM_LICENSING_METHOD_BLOCKED
```

```text
INFERENTIAL_DIAGNOSTICS_READY
INFERENTIAL_DIAGNOSTICS_PARTIAL
INFERENTIAL_DIAGNOSTICS_BLOCKED
```

```text
SYNTHETIC_CONFIRMATORY_COMPLETE
SYNTHETIC_CONFIRMATORY_PARTIAL
SYNTHETIC_CONFIRMATORY_BLOCKED
```

```text
GENERALIZABILITY_ANALYSIS_READY
GENERALIZABILITY_ANALYSIS_PARTIAL
GENERALIZABILITY_ANALYSIS_BLOCKED
```

```text
DECISION_MATERIALITY_READY
DECISION_MATERIALITY_PARTIAL
DECISION_MATERIALITY_BLOCKED
```

```text
MEASUREMENT_REGIME_STUDY_COMPLETE
MEASUREMENT_REGIME_STUDY_PARTIAL
MEASUREMENT_REGIME_STUDY_BLOCKED
```

```text
STUDY_C_FULL_EXECUTION_BUILD_READY
STUDY_C_BUILD_PARTIAL
STUDY_C_BUILD_BLOCKED
```

Issue separately:

```text
S1_READY
S2_READY
S3_READY
S4_READY
ROBUSTNESS_RUNBOOKS_READY
```

Human:

```text
HUMAN_CONFIRMATORY_PROTOCOL_READY
HUMAN_PROTOCOL_PARTIAL
```

Final maximum-ceiling gate:

```text
ICML2027_MAXIMUM_PRE_EXECUTION_BUILD_READY
ICML2027_STRONG_PRE_EXECUTION_BUILD_PARTIAL
ICML2027_MAJOR_SCIENTIFIC_GAPS_REMAIN
```

---

# Required final files

At minimum:

```text
reports/v7/VALID_EVAL_V7_CLAIM_LICENSING_METHOD.md
reports/v7/VALID_EVAL_V7_DIAGNOSTIC_DEPENDENCY_AUDIT.md
reports/v7/VALID_EVAL_V7_INFERENTIAL_DIAGNOSTIC_REPORT.md
reports/v7/MMLU_V7_FULL_UNCERTAINTY_AND_NULL_ANALYSIS.md
reports/v7/VALID_EVAL_V7_GENERALIZABILITY_STUDY.md
reports/v7/VALID_EVAL_V7_DECISION_MATERIALITY.md
reports/v7/VALID_EVAL_V7_BENCHMARK_INFLUENCE.md
reports/v7/VALID_EVAL_V7_MEASUREMENT_REGIME_STUDY.md
reports/v7/VALID_EVAL_V7_CONFIRMATORY_SYNTHETIC_RESULTS.md
reports/v7/VALID_EVAL_V7_TRANSPORTABILITY_METHOD.md
reports/v7/VALID_EVAL_V7_HUMAN_STUDY_FINAL_PROTOCOL.md
reports/v7/VALID_EVAL_V7_BENCHMARK_FORENSICS.md
reports/v7/VALID_EVAL_V7_STUDY_C_PANEL_DESIGN.md
reports/v7/VALID_EVAL_V7_ICML_PREREGISTRATION.md
reports/v7/VALID_EVAL_V7_NOVELTY_DEFENSE.md
reports/v7/VALID_EVAL_V7_ICML_REVIEWER_RED_TEAM.md
reports/v7/VALID_EVAL_V7_REPAIR_CHANGELOG.md

VALID_EVAL_ICML2027_EXECUTION_PLAN.md
VALID_EVAL_V7_FINAL_MAXIMUM_PRE_EXECUTION_HANDOFF.md
VALID_EVAL_V7_MACHINE_STATE.json
```

---

# Git requirements

Start from current clean V6 state.

Create:

```text
icml2027-v7-max-upgrade
```

Commit logically.

Do not overwrite V5/V6 tags.

After validation:
- final V7 commit;
- tag:

```text
valideval-v7-icml2027-max-pre-execution
```

Push branch and tag to:

```text
Saket-Maganti/valideval
```

Do not force-push.

---

# Final validation

Run:
- clean environment install;
- full pytest;
- Ruff lint;
- Ruff format check;
- targeted mypy;
- package build;
- all CPU scientific runs;
- generated-artifact validation;
- notebook fixture execution;
- mocked production execution;
- importer adversarial tests;
- paper-asset generator smoke;
- release build;
- secret scan;
- checksum validation;
- Git clean-state verification.

Report:
- passed;
- failed;
- skipped;
- xfailed;
- warnings;
- duration.

---

# Final Codex response

Return:

```text
FINAL_VERDICT:
STARTING_STATE:
FINAL_GATE:

CLAIM_LICENSING_STATUS:
INFERENTIAL_DIAGNOSTICS_STATUS:
STUDY_H_STATUS:
GENERALIZABILITY_STATUS:
DECISION_MATERIALITY_STATUS:
BENCHMARK_INFLUENCE_STATUS:
MEASUREMENT_REGIME_STATUS:
SYNTHETIC_CONFIRMATORY_STATUS:
BENCHMARK_FORENSICS_STATUS:
TRANSPORTABILITY_BUILD_STATUS:
HUMAN_PROTOCOL_STATUS:

STUDY_C_PANEL_STATUS:
S1_STATUS:
S2_STATUS:
S3_STATUS:
S4_STATUS:
ROBUSTNESS_RUNBOOK_STATUS:

CPU_RUNS_COMPLETED:
CPU_RUNTIME_TOTAL:
GPU_RUNS_STILL_REQUIRED:
EXPECTED_GPU_RUNTIME_RANGE:
EXPECTED_STORAGE:

TESTS:
LINT:
FORMAT:
TYPE_CHECK:
PACKAGE_BUILD:
GIT_BRANCH:
FINAL_COMMIT:
FINAL_TAG:
PUSH_STATUS:

MOST_IMPORTANT_NEW_SCIENTIFIC_METHOD:
MOST_IMPORTANT_CPU_FINDING:
MOST_SERIOUS_REMAINING_LIMITATION:
CURRENT_ICML2027_CEILING:
PRIMARY_NEXT_ACTION:

EXECUTION_PLAN:
FINAL_HANDOFF:
MACHINE_STATE:
```

---

# Final philosophy

Do not try to make ValidEval look impressive.

Make it scientifically difficult to attack.

The strongest possible project should satisfy:

- descriptive results are separated from inferential results;
- diagnostic selection is separated from validation;
- model families are treated as dependent;
- ranking claims can abstain;
- diagnostic multiplicity is controlled;
- benchmark decisions have explicit materiality;
- psychometric claims are limited to regimes where estimators are reliable;
- synthetic validation is genuinely decoupled;
- external/human validation is blinded;
- cross-benchmark transport is tested rather than assumed;
- benchmark repair is validated out-of-sample;
- every empirical claim is tied to immutable evidence;
- every GPU run is exact, reproducible, resumable, and fail-closed.

Desired endpoint:

> ValidEval is no longer merely an auditing toolkit. It is a statistical methodology and execution system for determining when benchmark-derived model-comparison claims are supportable.

Complete every feasible CPU and build task now.

Leave only real model inference, real human annotation, and genuinely unavailable external evidence for later execution.
