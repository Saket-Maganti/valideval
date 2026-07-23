# ValidEval — Maximum-Ceiling Pre-Execution Master Audit, Scientific Repair, Leakage Hardening, Codebase Upgrade, and Kaggle T4×2 Build Prompt

## Purpose of this prompt

You are taking over the complete **ValidEval** repository for one authoritative, repository-wide **audit + repair + maximum-ceiling pre-execution build**.

This is not another prompt-pack-writing exercise.

Do **not** merely inspect the project, generate recommendations, add superficial documentation, or produce another set of prompts for a future agent. You must directly work inside the repository, verify its current state, repair the codebase, redesign weak scientific components, harden every evidence path, build all locally possible infrastructure, create production-grade execution runbooks, and leave the project as close as it can honestly become to its highest credible publication ceiling **before real benchmark and human-label runs are executed**.

The intended ceiling is a future top-tier evaluation paper, with **NeurIPS Evaluations & Datasets** as the aspirational primary target if the eventual evidence supports it. Also assess whether the resulting work is a better fit for a NeurIPS main-track methodological contribution, TMLR, COLM, or another current venue. Do not force a venue label when the scientific contribution does not satisfy it.

The user will execute the real benchmark runs only after this build is complete. After those outputs return, the project will proceed to final empirical analysis and paper completion.

---

# 1. Repository and context

Expected repository root:

```text
/Users/saketmaganti/Projects/Valideval
```

Known project surfaces include, but are not limited to:

```text
src/valideval/
tests/
scripts/
paper/
results/
cache/
data/
dist/
kaggle/
kaggle_general/
kaggle_gsm8k/
kaggle_third_benchmark/
kaggle_v3/
```

Important existing implementation areas include:

```text
src/valideval/audit/
src/valideval/benchmarks/
src/valideval/diagnostics/
src/valideval/forensics/
src/valideval/human/
src/valideval/importers/
src/valideval/leaderboard/
src/valideval/kaggle_v4.py
```

Important existing execution and build scripts include:

```text
scripts/run_after_kaggle_outputs_v4.sh
scripts/update_paper_from_artifacts_v4.py
scripts/write_final_v4_gate_from_artifacts.py
scripts/make_reviewer_packet.py
scripts/package_kaggle_valideval.py
```

Known notebooks include:

```text
kaggle/valideval_lm_eval_panel_runner.ipynb
kaggle_general/valideval_multi_model_matrix_runner.ipynb
kaggle_gsm8k/valideval_gsm8k_panel_runner.ipynb
kaggle_third_benchmark/valideval_third_benchmark_runner.ipynb
kaggle_v3/valideval_v3_execution_kaggle_colab_runbook.ipynb
```

Read all relevant project reports and handoffs, including:

```text
Valideval_report_v2.md
V4_PRE_EXECUTION_READINESS_AUDIT.md
FINAL_V4_PRE_EXECUTION_GATE.md
MMLU_DEEP_DIAGNOSTIC_VALUE_REPORT.md
MMLU_REDUX_ALIGNMENT_RESCUE_OR_FORMAL_BLOCK_REPORT.md
CLAIMS_LEDGER_NEURIPS.md
CLAIMS_AND_STORY_SYNC_AUDIT.md
```

If a separate conversation summary such as `validevalv1.md` is available, use it only as historical context. It is not an authoritative source of evidence.

The repository, primary artifacts, reproducible commands, current source code, and verified current literature are the sources of truth.

---

# 2. Known issues that must be treated as P0 hypotheses

The following were discovered during direct inspection of the supplied project archive. Independently verify each one before relying on it, but do not ignore them:

1. The core HELM-derived MMLU matrix appears real and complete:
   - 39 models;
   - 14,042 items;
   - 57 subjects;
   - 547,638 model-item rows;
   - zero missing cells;
   - reported ability spread approximately 0.580188.

2. The reported test state appears to require an editable package installation:
   - an uninstalled clean run produced approximately `213 passed, 1 failed`;
   - after `python3 -m pip install -e .`, approximately `214 passed`.
   - Make setup and test behavior reproducible and environment-independent.

3. The existing MMLU panel and planned GSM8K/BBH panels appear to have **zero exact checkpoint-level overlap**.

4. Existing GSM8K/BBH notebook panels appear to contain only approximately 3–5 models, while a project panel gate expects around 30 models. This makes the planned small runs engineering pilots, not sufficient psychometric evidence.

5. Raw subject-level rank-range findings are real but appear under-calibrated:
   - median range reported as 19;
   - maximum reported as 30;
   - “severe ≥10” threshold appears arbitrary;
   - simple null behavior may already produce substantial rank ranges.

6. The existing “panel validity” gate appears to test minimum matrix feasibility rather than scientific psychometric validity.

7. MMLU-Redux item identity is not confirmed:
   - no direct ID match;
   - no stable metadata match;
   - no confirmed hash match;
   - structural position alignment alone cannot support item-level external validation.

8. Existing notebooks appear to need stronger:
   - dependency pinning;
   - exact checkpoint revisions;
   - configuration hashing;
   - idempotent resume logic;
   - shard completeness checks;
   - dual-GPU scheduling;
   - failure separation;
   - provenance;
   - checksum enforcement.

9. The importer and cross-benchmark runner may not fail closed when model overlap is scientifically insufficient.

10. The bundled archive may contain incomplete Git metadata, generated files, caches, `.DS_Store`, `__pycache__`, egg-info, old prompt packs, historical reports, and large artifacts that should not all be treated as a clean release.

These are P0 concerns. Resolve them before adding decorative features.

---

# 3. Master objective

Complete one integrated pass that leaves ValidEval in the strongest possible **pre-execution** state.

The final repository must contain:

1. An independently verified evidence base for all existing MMLU claims.
2. A scientifically defensible research thesis and contribution hierarchy.
3. A redesigned exact-model common-panel strategy.
4. A complete leakage and contamination threat model with enforced guards.
5. Stronger rank-materiality and measurement-model code paths.
6. Versioned benchmark, model, prompt, scoring, output, and provenance contracts.
7. Production-grade Kaggle T4×2 notebooks that are tested top-to-bottom in fixture mode.
8. A hardened importer, merger, validator, and post-import router.
9. Strict cross-benchmark readiness and overlap gates.
10. A human-validation protocol and import path, without fabricated labels.
11. A genuinely decoupled synthetic-validation protocol, without fabricated evidence.
12. Clean testing, packaging, CI, reproducibility, release, and paper-preparation surfaces.
13. A single final execution handbook describing **every real run still required**, classified by:
    - priority;
    - scientific role;
    - CPU or GPU;
    - exact hardware;
    - expected runtime range;
    - expected storage;
    - dependencies;
    - commands;
    - outputs;
    - acceptance gates;
    - claims unlocked.

The final build must maximize the likelihood that, after the user executes the required runs, the project can produce a top-tier-quality empirical paper if the results are strong.

---

# 4. Critical execution boundary

## 4.1 Do not execute the real research study

During this pass, do **not**:

- run the full GSM8K model panel;
- run the full BBH model panel;
- rerun the full controlled MMLU panel;
- run large model inference;
- start paid API calls;
- use provider APIs;
- launch Kaggle or Colab jobs;
- create fake benchmark outputs;
- create fake human annotations;
- create fake external labels;
- fabricate timings;
- fabricate statistical findings;
- promote fixture results as evidence;
- claim cross-benchmark transfer;
- claim benchmark repair success;
- claim NeurIPS readiness based on build completeness.

## 4.2 Local-safe work is required

You must execute all reasonable local-safe work, including:

- repository inspection;
- deterministic recomputation from existing artifacts;
- CPU analyses using existing data;
- unit and integration tests;
- linting;
- type checking where practical;
- clean package installation tests;
- CLI smoke tests;
- schema validation;
- notebook static validation;
- notebook fixture-mode execution;
- corrupted-input tests;
- tiny mock-model tests;
- deterministic synthetic guard tests;
- paper compilation;
- release-package inspection;
- reproducibility-manifest generation.

Tiny deterministic fixtures and tiny mock inference are allowed only to verify code paths. They must be clearly marked `NON_EVIDENCE_FIXTURE`.

If a very small public model is needed solely to validate notebook mechanics, keep this optional and off by default. Never promote its result into the scientific evidence ledger.

---

# 5. Working principles

## 5.1 Evidence statuses

Every important result, artifact, and claim must be assigned exactly one status:

```text
REPRODUCED
VERIFIED_FROM_PRIMARY_ARTIFACT
REPORTED_BUT_NOT_REPRODUCED
INFERRED
NON_EVIDENCE_FIXTURE
PLANNED
BLOCKED
CONTRADICTED
STALE
RETIRED
```

## 5.2 Evidence hierarchy

Use this hierarchy:

1. Raw or earliest defensible primary outputs.
2. Deterministically reconstructed normalized outputs.
3. Derived metrics with exact reproduction commands.
4. Figures and tables generated from those metrics.
5. Paper claims linked to the evidence ledger.

Reports are not primary evidence.

## 5.3 Fail closed

When a required condition is not satisfied:

- stop that dependent analysis;
- write an explicit blocked artifact;
- continue all independent work;
- never insert zeroes, placeholders, copied values, or simulated values into empirical result tables.

## 5.4 No prompt-pack proliferation

Do not create another collection of prompts.

Implement the work directly.

Create reports, code, tests, schemas, notebooks, and runbooks—not another plan for a future agent.

## 5.5 Preserve evidence

- Never destructively overwrite raw data.
- Never delete historical artifacts before classifying them.
- Move stale generated artifacts only when a migration map is created.
- Add immutable hashes for critical inputs.
- Record every repair.

## 5.6 Highest ceiling does not mean maximum feature count

Do not add features because they sound impressive.

Prioritize work that improves:

- correctness;
- scientific identifiability;
- causal separation of claims;
- robustness;
- uncertainty;
- validation;
- execution reliability;
- reviewer trust;
- reproducibility;
- research significance.

---

# 6. Required final architecture

Before modifying code, determine the clean target architecture.

At minimum, the final system should expose these logically separated layers:

```text
valideval.schemas
valideval.registry
valideval.benchmarks
valideval.models
valideval.execution
valideval.importers
valideval.validation
valideval.diagnostics
valideval.measurement
valideval.statistics
valideval.forensics
valideval.cross_benchmark
valideval.human
valideval.synthetic
valideval.evidence
valideval.reporting
valideval.release
```

Do not refactor mechanically if the existing layout already provides a clean equivalent. Avoid unnecessary compatibility breakage.

The key requirement is that the following concepts are versioned, explicit, and machine-readable:

- benchmark identity;
- benchmark version;
- task/subtask identity;
- dataset split;
- item identity;
- model identity;
- checkpoint revision;
- model family;
- prompt template;
- few-shot examples;
- chat template;
- generation settings;
- extraction/scoring version;
- environment;
- hardware;
- shard;
- attempt;
- failure type;
- output schema;
- source hashes;
- code revision;
- evidence status.

---

# 7. Phase A — Forensic repository audit and state freeze

## 7.1 Record initial state

Record:

- repository root;
- current timestamp;
- operating system;
- Python version;
- package manager;
- installed accelerator libraries;
- Git branch;
- Git commit;
- Git status;
- untracked files;
- ignored files;
- repository size;
- file counts;
- largest files;
- duplicate archives;
- nested archives;
- caches;
- compiled Python files;
- notebook outputs;
- stale generated artifacts;
- absolute paths;
- broken symlinks;
- embedded credentials;
- secret-like strings;
- licenses;
- data provenance notices.

If Git metadata is incomplete or invalid, state that explicitly. Do not invent a commit.

## 7.2 Create an artifact taxonomy

Classify every major file into:

```text
SOURCE
TEST
CONFIG
RAW_INPUT
NORMALIZED_INPUT
DERIVED_EVIDENCE
NON_EVIDENCE_FIXTURE
REPORT
PAPER
NOTEBOOK
RUNBOOK
RELEASE
CACHE
HISTORICAL
STALE
UNKNOWN
```

Create:

```text
reports/v5/VALID_EVAL_V5_REPOSITORY_FORENSIC_INVENTORY.md
reports/v5/VALID_EVAL_V5_ARTIFACT_CATALOG.csv
reports/v5/VALID_EVAL_V5_STALE_AND_DUPLICATE_ARTIFACTS.md
```

## 7.3 Clean release boundaries

Do not delete the working repository’s historical material without permission.

Instead:

- repair `.gitignore`;
- define clean source-release allowlists;
- define evidence-release allowlists;
- define reviewer-packet allowlists;
- exclude:
  - `__pycache__`;
  - `.pytest_cache`;
  - `.DS_Store`;
  - egg-info;
  - nested ZIPs;
  - unrelated raw benchmark files;
  - secrets;
  - model caches;
  - notebook checkpoint directories;
  - large temporary caches.

Create a dry-run release report showing exactly what would be included.

---

# 8. Phase B — Independent evidence reproduction

## 8.1 Reproduce the current MMLU matrix

Starting from the earliest defensible HELM-derived prediction artifact:

- reconstruct the normalized long table;
- reconstruct the wide response matrix;
- verify:
  - model count;
  - item count;
  - subject count;
  - row count;
  - duplicate rows;
  - contradictory duplicates;
  - invalid correctness values;
  - missingness;
  - partial model coverage;
  - partial item coverage;
  - subject indexing;
  - item identity stability;
  - model identity stability.

Compute SHA-256 hashes of primary and normalized artifacts.

## 8.2 Reproduce every headline result

Independently recompute:

- model accuracies;
- subject accuracies;
- ability spread;
- aggregate ranks;
- subject ranks;
- maximum rank range;
- median rank range;
- all threshold counts;
- diagnostic-weighted ranks;
- rank correlations;
- rank deltas;
- bootstrap outputs;
- ablation outputs;
- scalable psychometric summaries;
- MMLU-Redux alignment counts;
- external validation metrics if linkage permits.

Compare recomputed values with every report and paper table.

No tolerance should be implicit. Define numerical tolerances by metric.

## 8.3 Terminology correction

Determine whether previous wording such as:

```text
real MMLU panel execution
```

is accurate.

If the panel was imported from HELM rather than generated by this project, standardize wording to:

```text
analysis of a public HELM-derived MMLU response panel
```

or a more precise equivalent.

## 8.4 Claim-to-evidence ledger

Create:

```text
results/evidence/claim_evidence_ledger_v5.csv
reports/v5/VALID_EVAL_V5_CLAIM_EVIDENCE_LEDGER.md
```

Required columns:

```text
claim_id
claim_text
claim_category
paper_location
reported_value
verification_status
primary_inputs
reproduction_command
observed_value
tolerance
code_revision
input_hashes
output_hashes
allowed_wording
blocked_wording
notes
```

Every empirical paper sentence must eventually map to this ledger.

---

# 9. Phase C — Scientific thesis and contribution redesign

## 9.1 Do not use a generic toolkit thesis

Audit the current contribution hierarchy against current literature.

The paper must not rely primarily on:

- “we use IRT on LLM benchmarks”;
- “we compute item difficulty”;
- “we make a dashboard”;
- “we have many diagnostics”;
- “we provide a toolkit.”

Those alone are insufficient for the intended ceiling.

## 9.2 Candidate primary contribution

Test whether the project can support this contribution:

> Benchmark-validity diagnostics are measurement instruments whose own sensitivity, specificity, uncertainty, materiality, external validity, and transfer must be established before they can license benchmark-quality or model-ranking claims.

Potential empirical pillars:

1. Large HELM-derived MMLU case study.
2. Controlled exact-model cross-benchmark panel.
3. Null-calibrated and uncertainty-aware ranking materiality.
4. Diagnostic-family transfer and failure analysis.
5. Confirmed external or human validation.
6. Claim-gated evidence contracts.
7. Benchmark repair or decision-value demonstration.

## 9.3 Contribution ledger

Create:

```text
reports/v5/VALID_EVAL_V5_CONTRIBUTION_HIERARCHY.md
```

For each proposed contribution, mark:

```text
PRIMARY
SECONDARY
ENGINEERING
FUTURE
BLOCKED
RETIRED
```

For each, include:

- novelty;
- evidence required;
- evidence currently available;
- nearest competitors;
- likely reviewer objection;
- response strategy;
- claim ceiling.

---

# 10. Phase D — Complete leakage, contamination, and circularity audit

This phase is mandatory and P0.

Create a formal threat model covering every way ValidEval could appear successful because of leakage, circularity, post-selection, or identity failure.

## 10.1 Benchmark split leakage

Audit:

- train/test overlap;
- validation/test overlap;
- benchmark-source overlap;
- duplicated questions;
- near-duplicate questions;
- repeated templates;
- answer-option permutations;
- duplicated rationales;
- subtask overlap;
- cross-benchmark semantic overlap.

Use:

- exact normalized hashes;
- option-aware hashes;
- MinHash;
- token n-gram overlap;
- embedding-based candidate retrieval where locally feasible;
- manual-review queues for high-confidence matches.

## 10.2 Gold-answer leakage

Ensure:

- generation code never receives gold answers;
- extraction code does not select candidates using gold labels;
- retry logic does not use correctness feedback;
- answer-format repair does not inspect the expected answer;
- failed extraction is not silently converted into a wrong answer without a separate failure field;
- few-shot examples do not include target items or near duplicates.

Add adversarial tests.

## 10.3 Diagnostic-label leakage

Ensure diagnostics do not access:

- external issue labels;
- human labels;
- flaw-type labels;
- benchmark-repair labels;
- gold anomaly classes;
- file names revealing label status;
- output paths revealing positive/negative class;
- row order correlated with labels.

Any diagnostic weights or thresholds selected using labels must be trained and evaluated using proper splits or nested validation.

## 10.4 Synthetic circularity leakage

Audit the generator and detector for:

- flaw-specific branches;
- flaw-specific statistics;
- metadata leakage;
- schema-field leakage;
- generator seeds correlated with labels;
- output ordering;
- filename leakage;
- severity encoding;
- readout selection after observing results.

Require:

- frozen diagnostic definitions;
- hidden label mapping;
- negative controls;
- label permutation;
- no-flaw controls;
- unseen-flaw controls;
- mixed-flaw controls;
- preregistered primary metrics;
- held-out generator families.

## 10.5 Cross-benchmark identity leakage

Do not infer exact model comparability from family names.

Exact identity requires:

- same checkpoint;
- same revision or documented equivalent;
- same quantization class or controlled comparison;
- same chat/base status;
- comparable prompt regime;
- comparable decoding;
- comparable extraction.

Family-level analyses must be explicitly separate.

## 10.6 Post-selection leakage

Audit whether:

- thresholds were chosen after viewing outcomes;
- “severe” categories were defined post hoc;
- diagnostics were selected because they correlated with Redux labels;
- figures show only favorable subjects;
- bootstrap settings changed after results;
- benchmark subsets were chosen after viewing rank instability.

Create preregistration-ready config files for future confirmatory runs.

## 10.7 Human-review leakage

Design human packets so annotators are blinded to:

- diagnostic scores;
- diagnostic rank;
- model correctness pattern;
- whether an item was selected as high risk;
- external issue labels;
- intended hypothesis.

Randomize and include controls.

## 10.8 Contamination uncertainty

Distinguish:

- benchmark-data contamination in model pretraining;
- project pipeline leakage;
- benchmark split leakage;
- label leakage.

The project may not be able to prove absence of model pretraining contamination. Represent this as an uncertainty/limitation, not a solved fact.

## 10.9 Required outputs

Create:

```text
reports/v5/VALID_EVAL_V5_LEAKAGE_AND_CIRCULARITY_THREAT_MODEL.md
results/leakage/leakage_checks_v5.json
results/leakage/cross_benchmark_overlap_candidates_v5.csv
configs/preregistration/confirmatory_analysis_v5.yaml
tests/test_leakage_guards_v5.py
tests/test_gold_answer_isolation_v5.py
tests/test_synthetic_decoupling_v5.py
```

No final pre-execution gate may pass while a P0 leakage path remains open.

---

# 11. Phase E — Exact model identity registry and controlled common-panel redesign

This is the most important scientific-design repair.

## 11.1 Build a canonical model registry

Create a versioned registry containing:

```text
canonical_model_id
display_name
provider
repository
checkpoint
revision
architecture_family
parameter_count
base_or_instruction
chat_template
license
access_requirements
trust_remote_code_required
quantization_modes
minimum_gpu_memory
recommended_dtype
mmlu_historical_id
gsm8k_planned_id
bbh_planned_id
exact_identity_status
family_identity_status
runnable_on_t4
known_limitations
```

Use exact identifiers. Never collapse distinct checkpoints.

Create:

```text
configs/models/model_registry_v5.yaml
reports/v5/VALID_EVAL_V5_MODEL_IDENTITY_AUDIT.md
```

## 11.2 Separate two studies

The architecture should explicitly support:

### Study H — Historical large-panel study

- Existing public HELM-derived MMLU responses.
- Purpose:
  - large MMLU measurement audit;
  - subject heterogeneity;
  - ranking materiality;
  - diagnostic behavior.
- No claim that the same models were run on GSM8K/BBH unless exact matches exist.

### Study C — Controlled common-panel study

Run the same exact open checkpoints on:

- MMLU;
- GSM8K;
- BBH.

Purpose:

- model-level cross-benchmark transfer;
- diagnostic transfer;
- construct-specific specialization;
- controlled ranking stability;
- prompt/extraction robustness.

Do not mix results from Study H and Study C without explicit estimands.

## 11.3 Design panel tiers

Create a scientifically justified panel plan with at least:

### Tier S0 — Fixture

- 1–2 mock/tiny models;
- tiny synthetic item set;
- code-path validation only;
- never evidence.

### Tier S1 — Engineering smoke

- 2–3 real small models;
- 10–50 items per benchmark;
- validates model loading, extraction, sharding, resume, packaging;
- not paper evidence.

### Tier S2 — Execution pilot

- 4–8 exact common models;
- 100–500 items or selected subtasks;
- estimates runtime, OOM risk, failure rates, extraction reliability;
- exploratory only.

### Tier S3 — Minimum scientific common panel

Determine the minimum defensible exact model count based on:

- planned rank estimands;
- model-family diversity;
- uncertainty;
- psychometric parameterization;
- power simulations.

Do not hardcode 30 merely because the existing gate uses 30.

### Tier S4 — Full maximum-ceiling common panel

Target a diverse panel across:

- model families;
- parameter scales;
- base/instruction variants where defensible;
- dense/MoE where feasible;
- multiple capability levels.

The exact size must be justified by simulation and T4×2 feasibility.

### Tier S5 — Robustness extension

Optional models or alternative prompt/scoring conditions.

## 11.4 Panel selection criteria

The full common panel must balance:

- exact checkpoint availability;
- license;
- reproducibility;
- T4 feasibility;
- family diversity;
- scale diversity;
- non-redundancy;
- expected ability spread;
- no dominance by a single model family.

Create a family-deduplicated analysis plan.

## 11.5 Power and identifiability planner

Implement a planner that simulates whether candidate panel sizes can support:

- rank correlation;
- top-k stability;
- model-by-benchmark interaction;
- model-by-subject interaction;
- item-difficulty estimates;
- discrimination proxies;
- diagnostic transfer correlations;
- external-label AUROC/AUPRC;
- human-label precision estimates.

Create:

```text
src/valideval/planning/panel_power.py
scripts/build_common_panel_plan_v5.py
results/planning/common_panel_power_v5.csv
reports/v5/VALID_EVAL_V5_COMMON_PANEL_AND_POWER_PLAN.md
tests/test_panel_power_v5.py
```

All simulation outputs are planning aids, not empirical evidence.

---

# 12. Phase F — Rank uncertainty and materiality redesign

The current raw rank-range result must be upgraded into a reviewer-defensible analysis.

## 12.1 Replace arbitrary severity labels

Do not retain:

```text
severe rank range >= 10
```

as a headline category unless it is theoretically or decision-theoretically justified.

If retained as an exploratory threshold:

- label it exploratory;
- show threshold sensitivity;
- avoid clinical-sounding language.

## 12.2 Implement null-calibrated analyses

At minimum implement:

- additive model-ability + subject-difficulty null;
- binomial sampling null preserving subject sizes;
- empirical-Bayes or hierarchical shrinkage null;
- family-cluster bootstrap;
- subject bootstrap;
- item bootstrap within subject;
- model bootstrap only where interpretation is valid;
- permutation tests preserving marginal ability;
- tie-aware rank calculations.

## 12.3 Implement material ranking outputs

Create:

- rank confidence sets;
- pairwise outranking probabilities;
- effect-size-filtered reversals;
- top-1/top-3/top-5/top-10 membership probabilities;
- normalized rank dispersion;
- rank entropy;
- Kendall’s W;
- subject-to-subject rank correlations;
- top-k Jaccard stability;
- leave-one-subject-out sensitivity;
- leave-one-family-out sensitivity;
- family-deduplicated ranking;
- benchmark-composition perturbation;
- normalized rank range;
- probability observed dispersion exceeds null;
- practical significance thresholds.

## 12.4 Hierarchical subject model

Implement a defensible model separating:

```text
overall model ability
subject difficulty
model-by-subject interaction
model-family dependence
sampling uncertainty
```

Prefer a statistically transparent model over an unnecessarily complex one.

Possible implementations:

- mixed-effects logistic regression;
- Bayesian hierarchical binomial model;
- regularized subject-conditioned ability model.

Include:

- convergence checks;
- parameter uncertainty;
- synthetic recovery tests;
- simple baseline comparison;
- failure behavior.

## 12.5 Required outputs

Create:

```text
src/valideval/statistics/rank_materiality.py
src/valideval/statistics/rank_nulls.py
src/valideval/measurement/hierarchical_subject.py
scripts/run_mmlu_rank_materiality_v5.py
results/mmlu/rank_materiality_v5/
reports/v5/MMLU_V5_RANK_MATERIALITY_AND_NULL_AUDIT.md
tests/test_rank_materiality_v5.py
tests/test_rank_nulls_v5.py
tests/test_hierarchical_subject_v5.py
```

The paper-ready finding must be phrased based on these analyses, not on maximum rank range alone.

---

# 13. Phase G — Measurement-model audit and upgrade

## 13.1 Rename matrix gates correctly

If the current `panel_validity` diagnostic only checks:

- minimum models;
- minimum items;
- missingness;
- ability spread;
- chance-level concentration;

rename or alias it to:

```text
panel_feasibility
```

or:

```text
minimum_matrix_adequacy
```

Preserve backward compatibility where practical.

Clearly state:

> Passing this gate permits exploratory matrix analysis; it does not validate psychometric assumptions.

## 13.2 Audit IRT assumptions

Assess:

- unidimensionality;
- multidimensionality;
- local dependence;
- respondent dependence;
- family dependence;
- item-parameter uncertainty;
- model count adequacy;
- discrimination identifiability;
- prompt-method variance;
- extraction-method variance;
- subject nesting;
- saturation;
- benchmark contamination;
- invariance across model groups.

## 13.3 Compare candidate methods

Compare the scientific role and feasibility of:

- proxy IRT;
- Rasch/1PL;
- regularized 2PL;
- Bayesian IRT;
- multidimensional IRT;
- hierarchical IRT;
- explanatory IRT;
- matrix factorization;
- mixed-effects logistic models;
- generalizability theory;
- nonparametric item-response curves.

Do not build all of them.

Choose the smallest set that directly tests the paper’s central claims.

## 13.4 Required validation

For every implemented measurement model:

- synthetic recovery;
- identifiability constraints;
- uncertainty;
- convergence;
- calibration;
- sensitivity to model-family duplication;
- sensitivity to panel size;
- baseline comparison;
- explicit blocked state when conditions fail.

## 13.5 Required outputs

Create:

```text
reports/v5/VALID_EVAL_V5_MEASUREMENT_MODEL_SELECTION.md
src/valideval/measurement/
configs/measurement/
tests/test_measurement_recovery_v5.py
tests/test_measurement_assumptions_v5.py
```

Do not call a proxy a full 2PL.

---

# 14. Phase H — MMLU-Redux identity rescue or formal retirement

Treat MMLU-Redux as a data-linkage problem before treating it as validation.

## 14.1 Attempt matching in defensible order

1. Stable upstream IDs.
2. Original source row/index.
3. Exact normalized question text.
4. Exact normalized options.
5. Question + options + answer hash.
6. Canonical subject + source index.
7. Reproducible fuzzy candidate matching.
8. Manual-review queue for ambiguous matches.

## 14.2 Normalization safeguards

Document:

- Unicode normalization;
- whitespace;
- punctuation;
- option labels;
- answer ordering;
- HTML;
- LaTeX;
- case;
- quote normalization.

Detect collisions.

## 14.3 Confidence tiers

Output:

```text
CONFIRMED_EXACT
CONFIRMED_CANONICAL
HIGH_CONFIDENCE_MANUAL_REVIEW
AMBIGUOUS
UNMATCHED
```

Structural positional alignment must not be labeled confirmed item identity.

## 14.4 Two allowed outcomes

### Outcome A — Confirmed identity

Rerun external validation with:

- confirmed matches only;
- prevalence-aware baselines;
- AUROC;
- AUPRC;
- precision at preregistered k;
- confidence intervals;
- issue-type breakdown;
- sensitivity to disputed labels;
- simple heuristic baselines.

### Outcome B — Identity not confirmed

Formally retire the existing item-level validation result from the main paper.

Reframe it as:

> unsuccessful exploratory linkage attempt

Move it to limitations or appendix.

## 14.5 Required outputs

Create:

```text
src/valideval/external_labels/mmlu_redux_linkage_v5.py
results/mmlu_redux/linkage_v5.csv
reports/v5/MMLU_REDUX_V5_IDENTITY_RESOLUTION.md
tests/test_mmlu_redux_linkage_v5.py
```

---

# 15. Phase I — Benchmark contract hardening

Create a versioned benchmark contract for MMLU, GSM8K, and BBH.

Each contract must include:

```text
benchmark_id
benchmark_version
dataset_source
dataset_revision
split
subtasks
item_id_method
prompt_template_version
few_shot_policy
few_shot_examples_hash
chat_template_policy
generation_mode
generation_parameters
scoring_version
extraction_version
failure_taxonomy
license
redistribution_policy
expected_item_count
```

## 15.1 MMLU controlled-run contract

Define:

- exact subject list;
- test split;
- zero-shot or fixed few-shot protocol;
- answer format;
- multiple-choice scoring method;
- whether scoring uses generation or option log-likelihood;
- prompt sensitivity variants;
- item IDs.

## 15.2 GSM8K contract

Define:

- exact dataset version;
- test split;
- zero/few-shot;
- chain-of-thought policy;
- whether rationale is generated;
- final-answer extraction;
- numeric normalization;
- units;
- fractions;
- commas;
- negative numbers;
- scientific notation;
- multiple final numbers;
- refusal;
- timeout;
- truncation;
- invalid extraction.

Do not use gold-answer feedback during extraction.

## 15.3 BBH contract

Preserve:

- task/subtask identity;
- exact prompt format;
- task-specific scoring;
- deterministic item IDs;
- subtask-level outputs;
- no ID collisions across tasks.

## 15.4 Optional benchmark selection

Do not add benchmarks merely to increase count.

If proposing a fourth benchmark, select it for construct diversity and validation value. Evaluate:

- GPQA;
- TruthfulQA;
- MMLU-Pro;
- ARC;
- another current benchmark.

Only build a fourth runbook if it adds a clear construct or validity test.

Create:

```text
configs/benchmarks/mmlu_v5.yaml
configs/benchmarks/gsm8k_v5.yaml
configs/benchmarks/bbh_v5.yaml
reports/v5/VALID_EVAL_V5_BENCHMARK_CONTRACTS.md
```

---

# 16. Phase J — Execution schema and provenance redesign

Create a normalized long-form prediction schema.

Required fields should include:

```text
schema_version
study_id
run_id
benchmark_id
benchmark_version
task_id
subtask_id
split
item_id
item_hash
model_id
model_revision
model_family
prompt_template_id
few_shot_id
chat_template_id
generation_config_id
scoring_version
extraction_version
seed
shard_id
attempt_id
raw_output
parsed_output
gold_output
is_correct
extraction_status
generation_status
failure_type
latency_seconds
input_tokens
output_tokens
device
dtype
quantization
code_revision
environment_hash
created_at
```

Sensitive or non-redistributable fields may be stored separately, but the schema and mapping must be explicit.

## 16.1 Failure taxonomy

At minimum distinguish:

```text
SUCCESS
MODEL_LOAD_FAILURE
OOM
TIMEOUT
GENERATION_FAILURE
EMPTY_OUTPUT
TRUNCATED_OUTPUT
EXTRACTION_FAILURE
INVALID_FORMAT
SCORING_FAILURE
DATASET_FAILURE
UNKNOWN_FAILURE
```

An extraction failure must not be indistinguishable from an incorrect benchmark answer.

## 16.2 Run manifest

Every run must emit:

```text
run_manifest.json
environment.json
models.json
benchmark_contract.json
config_snapshot.yaml
file_checksums.json
shard_status.json
failure_summary.csv
```

## 16.3 Configuration hash

Resume is allowed only when the configuration hash matches.

The hash must include:

- model revision;
- benchmark revision;
- prompts;
- generation;
- scoring;
- extraction;
- shard definition;
- code version.

---

# 17. Phase K — Kaggle T4×2 notebook suite

Create or comprehensively repair a coherent notebook suite under:

```text
kaggle_max_ceiling/
```

At minimum create:

```text
00_valideval_t4x2_environment_and_preflight.ipynb
01_valideval_common_panel_mmlu_t4x2.ipynb
02_valideval_common_panel_gsm8k_t4x2.ipynb
03_valideval_common_panel_bbh_t4x2.ipynb
04_valideval_t4x2_merge_validate_package.ipynb
05_valideval_optional_robustness_runs_t4x2.ipynb
```

You may also update existing notebooks, but there must be one canonical documented suite.

## 17.1 Definition of “errorless”

You cannot guarantee that every remote model or Kaggle environment will always work.

For this project, `NOTEBOOK_PRODUCTION_READY` requires:

- valid notebook JSON;
- all cells ordered correctly;
- no hidden-state dependency;
- fixture mode executes top-to-bottom;
- imports resolve in a clean environment;
- package install cell succeeds under supported versions;
- all variables defined;
- no placeholder code paths;
- syntax checks pass;
- notebook-specific tests pass;
- expected output schema is validated;
- resume and merge are tested using fixtures;
- failure modes are explicit;
- real execution instructions are complete.

Do not call a notebook errorless merely because it opens.

## 17.2 T4×2 parallel strategy

Implement true dual-GPU support.

Preferred design:

- one worker process per GPU;
- `CUDA_VISIBLE_DEVICES=0` and `1`;
- model-level or shard-level work queue;
- no unsafe concurrent writes;
- isolated per-worker output directories;
- deterministic merge;
- worker heartbeats;
- status ledger;
- automatic retry policy;
- maximum retry count;
- clean shutdown;
- single-GPU fallback.

Avoid assuming `device_map="auto"` alone provides useful two-GPU parallelism.

## 17.3 Resource-aware scheduling

Implement:

- model memory estimates;
- per-model dtype;
- optional 8-bit or 4-bit quantization;
- OOM detection;
- batch-size reduction;
- sequence-length guard;
- model unload;
- CUDA cache cleanup;
- disk-cache checks;
- optional model-cache reuse;
- task partitioning.

Every fallback must be recorded in the manifest.

Do not silently compare differently quantized versions as if identical. Record quantization as a controlled condition.

## 17.4 Reproducibility

Each notebook must pin or record:

- Python;
- PyTorch;
- Transformers;
- Accelerate;
- Datasets;
- Tokenizers;
- BitsAndBytes if used;
- model revisions;
- dataset revisions;
- seeds;
- deterministic settings where practical.

Avoid unbounded `pip install -U`.

## 17.5 Security and access

- No embedded tokens.
- Support Kaggle secrets or environment variables.
- Make optional authentication explicit.
- Avoid `trust_remote_code=True` unless required and allowlisted.
- Record when remote code is used.
- Prefer safetensors.
- Disable external experiment tracking by default.

## 17.6 Execution modes

Every benchmark notebook must support:

```text
fixture
smoke
pilot
minimum_scientific
full_common_panel
robustness
resume
validate_only
package_only
```

These modes must be configuration-driven.

## 17.7 Progress and interruption safety

Provide:

- progress tables;
- completed/remaining work;
- per-model status;
- per-shard status;
- periodic atomic checkpoints;
- resume after notebook restart;
- no duplicate rows;
- no silent overwrite;
- configuration mismatch refusal.

## 17.8 Output packaging

The packaging notebook must:

- validate required files;
- verify checksums;
- detect incomplete shards;
- detect duplicate rows;
- detect contradictory rows;
- detect model coverage gaps;
- detect item coverage gaps;
- create deterministic ZIPs;
- include manifests;
- include failure summaries;
- exclude model caches and secrets.

## 17.9 Notebook testing

Create tests that:

- parse all notebooks;
- compile code cells where possible;
- execute fixture mode via `nbclient` or equivalent;
- verify no undefined top-level variables;
- verify output paths;
- verify schema version;
- verify dual-worker scheduler using mocks;
- verify resume idempotence;
- verify merge determinism.

Create:

```text
tests/test_kaggle_notebooks_v5.py
tests/test_t4x2_scheduler_v5.py
tests/test_notebook_fixture_execution_v5.py
reports/v5/VALID_EVAL_V5_KAGGLE_T4X2_NOTEBOOK_AUDIT.md
```

---

# 18. Phase L — Importer, merger, validator, and router hardening

Refactor or extend `src/valideval/kaggle_v4.py` into a versioned V5 import path while preserving compatible entry points where practical.

## 18.1 ZIP security

Reject:

- path traversal;
- absolute paths;
- symlink abuse;
- nested archives unless explicitly allowed;
- oversized decompression ratios;
- unexpected executable files;
- missing manifest;
- invalid schema version.

## 18.2 Manifest enforcement

Verify:

- expected benchmark;
- expected study;
- expected run ID;
- config hash;
- source ZIP hash;
- file hashes;
- shard list;
- model list;
- item counts;
- completion state;
- failure state.

## 18.3 Data integrity

Reject or explicitly quarantine:

- duplicate model-item rows;
- contradictory duplicates;
- mixed benchmark rows;
- mixed config hashes;
- mixed model revisions;
- stale shards;
- incomplete shards;
- malformed JSONL/CSV;
- unknown models;
- unknown subtasks;
- item ID collisions;
- coverage below declared mode;
- mismatched matrix and long-form predictions.

## 18.4 Idempotence

Reimporting the same ZIP must not duplicate evidence.

A different ZIP with the same run ID but different hash must trigger a conflict.

## 18.5 Post-import router

After a valid import, route based on benchmark and study:

- feasibility;
- extraction reliability;
- coverage;
- model accuracy;
- subject/subtask analysis;
- ranking materiality;
- measurement models;
- cross-benchmark eligibility;
- paper artifact generation.

No dependent analysis should run when its gate fails.

## 18.6 Cross-benchmark overlap gate

Require explicit minimums for:

- exact common models;
- independent model families;
- common configuration class;
- usable items;
- extraction reliability.

Return one of:

```text
CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL
CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY
CROSS_BENCHMARK_BLOCKED_INSUFFICIENT_MODEL_OVERLAP
CROSS_BENCHMARK_BLOCKED_CONFIGURATION_MISMATCH
CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY
```

Never return a positive generic state merely because two matrices exist.

## 18.7 Required outputs

Create:

```text
src/valideval/importers/kaggle_v5.py
src/valideval/execution/manifest.py
src/valideval/execution/shards.py
src/valideval/cross_benchmark/gates.py
tests/test_kaggle_importer_adversarial_v5.py
tests/test_cross_benchmark_gates_v5.py
reports/v5/VALID_EVAL_V5_IMPORTER_AND_ROUTER_AUDIT.md
```

---

# 19. Phase M — Cross-benchmark analysis build

Build the full analysis code now, but do not fabricate or fill missing empirical outputs.

## 19.1 Predeclare estimands

At minimum distinguish:

### Exact-model rank transfer

Same exact checkpoints across benchmarks.

### Ability transfer

Correlation or hierarchical relationship of model ability across constructs.

### Diagnostic transfer

Whether item/benchmark diagnostic families behave consistently.

### Construct specialization

Model-by-benchmark and model-by-subtask interactions.

### Ranking decision stability

Top-k and pairwise ordering consistency.

### Family-level transfer

Separate exploratory analysis when exact checkpoints do not overlap sufficiently.

## 19.2 Methods

Implement:

- overlap audit;
- rank correlation with uncertainty;
- attenuation-aware analysis where measurement error is estimated;
- pairwise order agreement;
- top-k overlap;
- hierarchical model-by-benchmark interaction;
- benchmark clustering;
- diagnostic-family transfer matrix;
- sensitivity to prompt/scoring conditions;
- family-deduplicated analysis;
- leave-one-family-out analysis;
- null and permutation baselines;
- multiple-testing correction;
- effect sizes and confidence intervals.

## 19.3 No universal transfer claim

The code and report templates must allow:

```text
TRANSFER_SUPPORTED
TRANSFER_PARTIAL
TRANSFER_BENCHMARK_SPECIFIC
TRANSFER_NOT_SUPPORTED
UNDERPOWERED
BLOCKED
```

## 19.4 Required outputs

Create:

```text
src/valideval/cross_benchmark/
scripts/run_cross_benchmark_v5.py
configs/analysis/cross_benchmark_confirmatory_v5.yaml
paper/templates/cross_benchmark_results_v5.tex
tests/test_cross_benchmark_analysis_v5.py
reports/v5/VALID_EVAL_V5_CROSS_BENCHMARK_ANALYSIS_BUILD.md
```

---

# 20. Phase N — Human-validation system

Build the study infrastructure but do not invent labels.

## 20.1 Review the current queue

Audit:

- sampling;
- diagnostic-score distribution;
- subject representation;
- benchmark representation;
- duplicates;
- selection bias;
- raw-text licensing;
- annotator blinding;
- control items.

## 20.2 Label taxonomy

At minimum support:

```text
INCORRECT_GOLD_ANSWER
AMBIGUOUS_QUESTION
AMBIGUOUS_OPTIONS
MULTIPLE_DEFENSIBLE_ANSWERS
INSUFFICIENT_CONTEXT
OUTDATED_FACT
SCORING_OR_EXTRACTION_ISSUE
DOMAIN_SPECIALIST_DISPUTE
NO_DETECTED_ISSUE
UNSURE
```

## 20.3 Study design

Create:

- blinded packet;
- randomization;
- positive and negative controls;
- pilot protocol;
- minimum annotator count;
- expertise requirements;
- agreement metrics;
- adjudication;
- exclusion criteria;
- preregistered primary endpoint;
- precision/power planner;
- import validator;
- audit trail.

## 20.4 Evaluation design

Distinguish what the selected sample can estimate:

- enrichment;
- precision;
- recall;
- calibration;
- issue-type distribution.

Do not claim recall from a high-score-only queue.

## 20.5 Required outputs

Create:

```text
configs/human/human_validation_v5.yaml
src/valideval/human/protocol_v5.py
src/valideval/human/importer_v5.py
scripts/build_blinded_human_packet_v5.py
scripts/import_human_labels_v5.py
reports/v5/VALID_EVAL_V5_HUMAN_VALIDATION_PROTOCOL.md
tests/test_human_validation_v5.py
```

---

# 21. Phase O — Decoupled synthetic validation

Build a valid confirmatory synthetic design.

## 21.1 Generator-detector separation

The generator must not reveal flaw type to the diagnostic pipeline.

## 21.2 Required experiments

Plan and implement code for:

- no flaw;
- one flaw;
- multiple flaws;
- unseen flaw;
- severity sweep;
- prevalence sweep;
- panel-size sweep;
- item-count sweep;
- model-family dependence;
- missingness;
- correlated flaws;
- label permutation;
- diagnostic ablation;
- negative controls.

## 21.3 Preregistration freeze

The following must be frozen before future evidence execution:

- generator families;
- primary diagnostics;
- metric;
- threshold policy;
- sample sizes;
- seeds;
- success criteria;
- exclusions.

## 21.4 Required outputs

Create:

```text
configs/synthetic/confirmatory_synthetic_v5.yaml
src/valideval/synthetic/
scripts/run_confirmatory_synthetic_v5.py
reports/v5/VALID_EVAL_V5_SYNTHETIC_PROTOCOL.md
tests/test_confirmatory_synthetic_v5.py
```

The build gate may pass while empirical synthetic results remain `RESULT_REQUIRED`.

---

# 22. Phase P — Baselines, ablations, and reviewer-resistant comparisons

Prepare all baseline and ablation code before real runs.

## 22.1 Baselines

Include appropriate simple baselines:

- aggregate accuracy;
- item error rate;
- subject variance;
- entropy;
- answer-position imbalance;
- random anomaly scores;
- prevalence predictor;
- simple difficulty;
- simple discrimination proxy;
- model-family heuristic;
- item-length or lexical heuristics where relevant.

## 22.2 Ablations

Build:

- one diagnostic family at a time;
- leave-one-family-out;
- score normalization variants;
- threshold variants;
- family-deduplicated panel;
- panel-size sensitivity;
- prompt variant;
- extraction variant;
- model quantization variant;
- benchmark subset;
- subject/subtask subset;
- without external labels;
- without synthetic tuning.

## 22.3 Anti-cherry-picking

Predeclare:

- primary metric;
- primary benchmark comparison;
- primary diagnostic combination;
- primary threshold;
- primary common panel;
- primary human endpoint.

Exploratory outputs must be labeled.

---

# 23. Phase Q — Runtime, cost, and feasibility estimation

The user requires realistic expected runtimes before executing.

Do not invent precise timings.

## 23.1 Build a runtime estimator

Create a planner using:

- model size;
- quantization;
- benchmark item count;
- prompt length;
- expected output tokens;
- batch size;
- T4 throughput range;
- load time;
- failure/retry overhead;
- dual-GPU utilization;
- disk bandwidth;
- model download time separately.

Produce:

- optimistic;
- expected;
- conservative;

runtime ranges.

## 23.2 Calibration strategy

The execution handbook must explain that estimates are planning ranges until updated by the S1 engineering smoke.

After smoke output is imported, the estimator should automatically revise later runtimes.

## 23.3 CPU estimates

Estimate CPU time for:

- import;
- validation;
- matrix build;
- bootstrap;
- null simulation;
- hierarchical models;
- figures;
- paper build;
- reviewer packet.

## 23.4 Required outputs

Create:

```text
src/valideval/planning/runtime_estimator.py
scripts/estimate_execution_runtime_v5.py
results/planning/runtime_estimates_v5.csv
tests/test_runtime_estimator_v5.py
```

---

# 24. Phase R — Packaging, environment, CI, and developer experience

## 24.1 Clean installation

Make these work from a clean environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest -q
```

If the project uses another environment manager, document one canonical path.

## 24.2 Dependencies

Create or repair:

- `pyproject.toml`;
- optional dependency groups;
- pinned notebook requirements;
- compatible lock or constraints file;
- minimal runtime dependencies;
- dev dependencies;
- paper-build dependencies.

Do not include local egg-info in source release.

## 24.3 Quality gates

Configure and run, where appropriate:

- `ruff check`;
- `ruff format --check`;
- `pytest`;
- type checking;
- package build;
- CLI smoke;
- notebook validation;
- paper build;
- release dry run.

Do not add a strict type checker across the entire legacy codebase if it creates low-value churn. Apply it to new critical modules at minimum.

## 24.4 CI

Create CI for:

- install;
- unit tests;
- fixture integration;
- lint;
- schema checks;
- notebook structure;
- release allowlist;
- paper build if dependencies permit.

Do not require private data or large model downloads in CI.

## 24.5 CLI

Provide discoverable commands such as:

```bash
python -m valideval doctor
python -m valideval validate-run
python -m valideval import-kaggle
python -m valideval post-import
python -m valideval cross-benchmark
python -m valideval build-evidence-ledger
python -m valideval build-paper-assets
python -m valideval build-release
```

Use the project’s existing CLI style and preserve compatible aliases.

---

# 25. Phase S — Paper and submission structure build

Do not write a final results paper before the runs.

Build a complete evidence-aware paper scaffold that can be populated automatically.

## 25.1 Venue strategy

Create separate fit analyses for:

- NeurIPS Evaluations & Datasets;
- NeurIPS main track;
- TMLR;
- future COLM;
- any more natural current venue.

Use current official scope and reviewer criteria.

## 25.2 Paper structure

Prepare:

1. Abstract template.
2. Introduction.
3. Validity and measurement framing.
4. Claim-gating framework.
5. Historical MMLU study.
6. Controlled common-panel design.
7. Rank-materiality methods.
8. Measurement models.
9. Cross-benchmark transfer.
10. External validation.
11. Human validation.
12. Synthetic validation.
13. Ablations.
14. Limitations.
15. Ethics and responsible evaluation.
16. Reproducibility.
17. Conclusion.
18. Checklist.
19. Supplement.

## 25.3 Evidence-bound writing

All empirical tables must be generated from artifacts.

Missing results must remain:

```text
[RESULT REQUIRED: exact artifact]
```

Do not write plausible numbers.

## 25.4 Figures and tables

Prepare code and templates for:

- project/evidence flow;
- claim-gating diagram;
- exact model-overlap matrix;
- rank confidence sets;
- null-versus-observed rank materiality;
- model-by-subject interaction;
- cross-benchmark rank transfer;
- diagnostic transfer heatmap;
- human precision/reliability;
- external validation PR curve;
- ablations;
- failure taxonomy;
- evidence ledger summary.

## 25.5 Related work

Perform a current primary-source literature audit covering:

- LLM benchmark auditing;
- psychometrics and IRT for model evaluation;
- leaderboard uncertainty;
- benchmark contamination;
- benchmark repair;
- external validation;
- human benchmark error audits;
- cross-benchmark evaluation;
- validity theory;
- evaluation science.

Update `paper/references.bib` with verified metadata only.

## 25.6 Reproducibility and metadata

Prepare:

- NeurIPS checklist;
- evaluation card;
- model panel card;
- benchmark contracts;
- data provenance statement;
- artifact availability statement;
- limitations;
- societal impact;
- responsible-use notes;
- machine-readable metadata if required for the eventual artifact type.

---

# 26. Phase T — Reviewer simulation and red-team audit

Simulate at least these reviewers:

1. Psychometrician.
2. Statistical-methods reviewer.
3. LLM-evaluation reviewer.
4. Benchmark/dataset curator.
5. Reproducibility reviewer.
6. Skeptical top-tier reviewer.
7. Security/leakage reviewer.
8. Artifact reviewer.

For each, identify:

- fatal flaw;
- major concern;
- minor concern;
- missing baseline;
- overclaim;
- alternative explanation;
- required experiment;
- likely score;
- repair completed;
- residual risk.

Do not invent an optimistic score.

Create:

```text
reports/v5/VALID_EVAL_V5_REVIEWER_RED_TEAM.md
reports/v5/VALID_EVAL_V5_REBUTTAL_PREPARATION.md
```

---

# 27. Phase U — Pre-execution dry validation

Run all local-safe gates.

## 27.1 Required validations

- clean editable install;
- full tests;
- lint;
- formatting;
- type checks for critical modules;
- package build;
- CLI smoke;
- MMLU evidence reproduction;
- leakage guards;
- runtime planner;
- panel power planner;
- notebook JSON validation;
- notebook fixture execution;
- dual-GPU scheduler mock test;
- importer adversarial suite;
- cross-benchmark overlap gate;
- paper compilation;
- reviewer-packet dry run;
- release allowlist audit;
- secret scan;
- path portability scan.

## 27.2 Do not count tests dishonestly

Report:

- passed;
- failed;
- skipped;
- xfailed;
- warnings;
- duration.

Do not present only the passing count.

## 27.3 Build completeness

Every required future run must have:

- config;
- code path;
- notebook;
- manifest schema;
- import path;
- analysis path;
- table/figure path;
- paper injection path;
- failure gate.

---

# 28. Single authoritative execution handbook

At the end, create exactly one comprehensive execution handbook:

```text
VALID_EVAL_MAXIMUM_CEILING_EXECUTION_HANDBOOK.md
```

This file is mandatory and must be sufficient for the user to execute all remaining work without reading old prompt packs.

## 28.1 Required handbook sections

### A. Current verified state

- existing evidence;
- existing non-evidence;
- repaired components;
- blocked components.

### B. Execution dependency graph

Show:

```text
environment preflight
→ fixture validation
→ S1 smoke
→ import smoke
→ runtime recalibration
→ S2 pilot
→ panel decision
→ controlled MMLU
→ GSM8K
→ BBH
→ cross-benchmark analysis
→ optional robustness
→ human pilot
→ human full study
→ external validation
→ final paper
```

### C. Run classification

Classify every run as:

```text
E0_LOCAL_CPU_BUILD
E1_LOCAL_CPU_ANALYSIS
E2_KAGGLE_GPU_ENGINEERING_SMOKE
E3_KAGGLE_GPU_PILOT
E4_KAGGLE_GPU_MINIMUM_SCIENTIFIC
E5_KAGGLE_GPU_FULL_COMMON_PANEL
E6_KAGGLE_GPU_ROBUSTNESS
E7_HUMAN_VALIDATION
E8_OPTIONAL_CEILING_EXTENSION
```

### D. Required run table

For every run include:

```text
run_id
priority
mandatory_or_optional
scientific_question
benchmark
study
panel_tier
exact_models
model_count
item_count
subtasks
prompt_config
scoring_config
hardware
cpu_or_gpu
expected_runtime_optimistic
expected_runtime_expected
expected_runtime_conservative
expected_storage
download_size
notebook_or_command
resume_supported
dependencies
outputs
acceptance_gate
failure_conditions
fallback
analyses_unlocked
claims_unlocked
claims_not_unlocked
```

### E. CPU runs

Include expected runtime ranges for:

- MMLU reproduction;
- leakage audit;
- duplicate scan;
- null simulations;
- bootstrap;
- hierarchical analysis;
- import;
- cross-benchmark analysis;
- paper assets;
- paper compilation;
- release build.

### F. GPU runs

Include:

- T4×2 notebook;
- mode;
- model panel;
- benchmark;
- item count;
- expected wall time;
- retry budget;
- storage;
- output ZIP.

### G. Exact Kaggle instructions

For each notebook:

- create Kaggle notebook;
- attach internet/GPU settings;
- T4×2 selection;
- secrets;
- dataset attachments;
- cells to edit;
- run mode;
- output retrieval;
- expected ZIP name;
- local destination.

### H. Exact local import commands

Include full commands for:

- validation;
- import;
- post-import analysis;
- cross-benchmark gate;
- paper update;
- reviewer packet;
- final tests.

### I. Stop/go gates

After every run state exactly when to:

- proceed;
- rerun;
- reduce panel;
- change quantization;
- repair extraction;
- abort evidence promotion.

### J. Evidence promotion rules

State exactly what makes an output:

```text
ENGINEERING_ONLY
EXPLORATORY
CONFIRMATORY
PAPER_ELIGIBLE
RETIRED
```

### K. Expected total compute

Give scenario totals:

- minimum viable scientific path;
- recommended strong path;
- maximum-ceiling path.

Separate:

- GPU hours;
- CPU hours;
- storage;
- human-label effort.

Use ranges and assumptions.

---

# 29. Required pre-execution reports and artifacts

At minimum create or update:

```text
reports/v5/VALID_EVAL_V5_REPOSITORY_FORENSIC_INVENTORY.md
reports/v5/VALID_EVAL_V5_ARTIFACT_CATALOG.csv
reports/v5/VALID_EVAL_V5_CLAIM_EVIDENCE_LEDGER.md
reports/v5/VALID_EVAL_V5_CONTRIBUTION_HIERARCHY.md
reports/v5/VALID_EVAL_V5_LEAKAGE_AND_CIRCULARITY_THREAT_MODEL.md
reports/v5/VALID_EVAL_V5_MODEL_IDENTITY_AUDIT.md
reports/v5/VALID_EVAL_V5_COMMON_PANEL_AND_POWER_PLAN.md
reports/v5/MMLU_V5_RANK_MATERIALITY_AND_NULL_AUDIT.md
reports/v5/VALID_EVAL_V5_MEASUREMENT_MODEL_SELECTION.md
reports/v5/MMLU_REDUX_V5_IDENTITY_RESOLUTION.md
reports/v5/VALID_EVAL_V5_BENCHMARK_CONTRACTS.md
reports/v5/VALID_EVAL_V5_KAGGLE_T4X2_NOTEBOOK_AUDIT.md
reports/v5/VALID_EVAL_V5_IMPORTER_AND_ROUTER_AUDIT.md
reports/v5/VALID_EVAL_V5_CROSS_BENCHMARK_ANALYSIS_BUILD.md
reports/v5/VALID_EVAL_V5_HUMAN_VALIDATION_PROTOCOL.md
reports/v5/VALID_EVAL_V5_SYNTHETIC_PROTOCOL.md
reports/v5/VALID_EVAL_V5_ENGINEERING_AND_REPRODUCIBILITY_AUDIT.md
reports/v5/VALID_EVAL_V5_REVIEWER_RED_TEAM.md
reports/v5/VALID_EVAL_V5_REPAIR_CHANGELOG.md
reports/v5/VALID_EVAL_V5_VENUE_CEILING_ASSESSMENT.md
VALID_EVAL_MAXIMUM_CEILING_EXECUTION_HANDBOOK.md
VALID_EVAL_MAXIMUM_CEILING_PRE_EXECUTION_HANDOFF.md
results/evidence/claim_evidence_ledger_v5.csv
results/planning/common_panel_power_v5.csv
results/planning/runtime_estimates_v5.csv
VALID_EVAL_V5_MACHINE_STATE.json
```

---

# 30. Machine-readable state

Create:

```text
VALID_EVAL_V5_MACHINE_STATE.json
```

Required keys:

```text
generated_at
repository_root
git_commit
git_branch
git_dirty
environment
package_install
tests
lint
format
type_check
package_build
notebook_validation
paper_build
release_build
primary_input_hashes
reproduced_mmlu_metrics
claim_status_counts
leakage_gate
model_identity_gate
panel_power_gate
notebook_gate
importer_gate
cross_benchmark_gate
human_protocol_gate
synthetic_protocol_gate
paper_scaffold_gate
remaining_blockers
exact_next_commands
```

Use `null` where a value truly cannot be known. Do not fake it.

---

# 31. Final gates

Issue each gate separately.

## 31.1 Existing evidence gate

Choose exactly one:

```text
EXISTING_MMLU_EVIDENCE_REPRODUCED
EXISTING_MMLU_EVIDENCE_REPRODUCED_WITH_MAJOR_CAVEATS
EXISTING_MMLU_EVIDENCE_NOT_REPRODUCED
EXISTING_MMLU_EVIDENCE_CONTRADICTED
```

## 31.2 Leakage gate

```text
LEAKAGE_GUARDS_COMPLETE
LEAKAGE_GUARDS_PARTIAL
P0_LEAKAGE_REMAINS
```

## 31.3 Model identity gate

```text
EXACT_COMMON_PANEL_DEFINED
COMMON_PANEL_PARTIAL
MODEL_PANEL_REDESIGN_REQUIRED
```

## 31.4 Statistical gate

```text
RANK_MATERIALITY_ANALYSIS_READY
RANK_ANALYSIS_REQUIRES_REPAIR
RANK_FINDING_NOT_DEFENSIBLE
```

## 31.5 Measurement gate

```text
MEASUREMENT_MODEL_PLAN_DEFENSIBLE
MEASUREMENT_MODEL_PLAN_LIMITED
MEASUREMENT_MODEL_REDESIGN_REQUIRED
```

## 31.6 Redux gate

```text
REDUX_ITEM_IDENTITY_CONFIRMED
REDUX_EXPLORATORY_ONLY
REDUX_VALIDATION_RETIRED
REDUX_AUDIT_BLOCKED
```

## 31.7 Notebook gate

```text
KAGGLE_T4X2_FIXTURE_VALIDATED
KAGGLE_T4X2_PARTIALLY_VALIDATED
KAGGLE_T4X2_NOT_READY
```

## 31.8 Importer gate

```text
IMPORTER_V5_ADVERSARIAL_VALIDATED
IMPORTER_V5_PARTIAL
IMPORTER_REPAIR_REQUIRED
```

## 31.9 Cross-benchmark build gate

```text
CONTROLLED_CROSS_BENCHMARK_BUILD_READY
CROSS_BENCHMARK_BUILD_PARTIAL
CROSS_BENCHMARK_DESIGN_BLOCKED
```

## 31.10 Human-validation gate

```text
HUMAN_VALIDATION_PROTOCOL_READY
HUMAN_VALIDATION_PROTOCOL_PARTIAL
HUMAN_VALIDATION_DESIGN_BLOCKED
```

## 31.11 Overall pre-execution gate

Choose exactly one:

```text
MAXIMUM_CEILING_PRE_EXECUTION_BUILD_COMPLETE
CONTROLLED_GPU_SMOKE_READY
PRE_EXECUTION_BUILD_PARTIAL
MAJOR_REDESIGN_STILL_REQUIRED
PROJECT_STATE_UNVERIFIED
```

A positive final gate means the **build** is ready. It does not mean the paper is empirically ready or venue-ready.

---

# 32. Venue-ceiling assessment

Create:

```text
reports/v5/VALID_EVAL_V5_VENUE_CEILING_ASSESSMENT.md
```

Assess these evidence scenarios:

## Scenario A — Existing verified MMLU evidence only

State:

- strongest claim;
- fatal weakness;
- current paper level;
- advisable venues;
- whether submission is advisable.

## Scenario B — Controlled MMLU + GSM8K

Assume exact common model panel and valid imported outputs.

State:

- claims unlocked;
- remaining weaknesses;
- ceiling.

## Scenario C — Controlled MMLU + GSM8K + BBH

Assume adequate exact panel and strong statistical analysis.

State:

- transfer claims possible;
- required result pattern;
- remaining validation gaps;
- ceiling.

## Scenario D — Three benchmarks + human/external validation

Assume:

- blinded human labels;
- confirmed external item identity;
- current baseline comparison;
- robust uncertainty;
- reproducible release.

State:

- maximum credible target;
- required novelty;
- major remaining reviewer risks.

Use:

```text
POOR_FIT
POSSIBLE_BUT_WEAK
CREDIBLE
STRONG_FIT
STRETCH
```

Do not invent acceptance probabilities.

---

# 33. Final handoff

Create:

```text
VALID_EVAL_MAXIMUM_CEILING_PRE_EXECUTION_HANDOFF.md
```

This must be the authoritative continuation document.

Required structure:

1. Executive verdict.
2. What ValidEval now is.
3. Historical evidence versus controlled future evidence.
4. Verified existing MMLU state.
5. Reproduced and contradicted claims.
6. Scientific thesis.
7. Contribution hierarchy.
8. Leakage repairs.
9. Model identity and common panel.
10. Statistical upgrades.
11. Measurement-model plan.
12. MMLU-Redux resolution.
13. Benchmark contracts.
14. Kaggle T4×2 notebooks.
15. Importer and router.
16. Cross-benchmark build.
17. Human-validation system.
18. Synthetic-validation system.
19. Runtime planner.
20. Testing and CI.
21. Paper scaffold.
22. Release state.
23. Current venue level.
24. Highest credible ceiling.
25. Remaining empirical blockers.
26. Exact execution order.
27. Link to the single execution handbook.
28. Allowed claims.
29. Blocked claims.
30. Final gates.
31. Full command ledger with exit codes.
32. Files added, modified, deprecated, or moved.
33. Instructions for the next agent after outputs return.

---

# 34. Final response required from Codex

Do not reply with only “completed.”

Report:

- exact overall verdict;
- whether the old V4 readiness gate survived;
- most serious scientific flaw found;
- most important repair;
- exact common-panel status;
- leakage status;
- notebook status;
- importer status;
- number of files added/modified;
- tests passed/failed/skipped;
- lint/type/build state;
- current venue level;
- highest credible ceiling;
- exact next action;
- paths to:
  - execution handbook;
  - final handoff;
  - machine state;
  - repair changelog;
  - venue assessment.

End with:

```text
FINAL_VERDICT:
OLD_V4_GATE_STATUS:
EXISTING_MMLU_STATUS:
MOST_SERIOUS_SCIENTIFIC_ISSUE:
MOST_IMPORTANT_REPAIR:
LEAKAGE_STATUS:
EXACT_COMMON_PANEL_STATUS:
RANK_MATERIALITY_STATUS:
MEASUREMENT_MODEL_STATUS:
REDUX_STATUS:
KAGGLE_T4X2_STATUS:
IMPORTER_STATUS:
CROSS_BENCHMARK_BUILD_STATUS:
HUMAN_PROTOCOL_STATUS:
SYNTHETIC_PROTOCOL_STATUS:
TESTS:
LINT_AND_BUILD:
CURRENT_VENUE_LEVEL:
HIGHEST_CREDIBLE_CEILING:
PRIMARY_REMAINING_BLOCKER:
EXECUTION_HANDBOOK:
FINAL_HANDOFF:
EXACT_NEXT_ACTION:
```

---

# 35. Final instruction

Build the project as far as it can honestly go **without performing the real benchmark, external-label, or human-label study**.

Do not optimize for the number of artifacts.

Optimize for:

- scientific validity;
- exact identity;
- leakage resistance;
- uncertainty;
- materiality;
- reproducibility;
- execution reliability;
- reviewer trust;
- a coherent top-tier contribution.

The desired endpoint is not:

```text
many notebooks and reports exist
```

The desired endpoint is:

> Every important future result has a scientifically defensible design, an exact configuration, a tested execution path, a hardened importer, a preregistered analysis, a paper destination, and a fail-closed evidence gate.

Only then may the project be declared ready for controlled GPU execution.
