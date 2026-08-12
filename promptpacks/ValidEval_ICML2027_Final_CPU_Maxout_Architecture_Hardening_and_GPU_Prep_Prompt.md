# ValidEval — ICML 2027 Final CPU Max-Out, Architecture Hardening, Statistical Stress, and GPU-Prep Master Prompt

## Mission

Use the remaining Codex budget to exhaust **all useful pre-GPU work** on ValidEval.

This is the last broad CPU/architecture/testing/reproducibility pass before real Kaggle evidence collection.

Do NOT:
- fabricate GPU outputs;
- fabricate human labels;
- fabricate transport or held-out evidence;
- rewrite the final paper;
- tune frozen confirmatory failures until they pass;
- weaken gates to manufacture readiness;
- add cosmetic framework complexity with no scientific value.

The target is:

```text
ALL_USEFUL_PRE_GPU_CPU_WORK_EXHAUSTED
NO_KNOWN_P0_OR_P1_CPU_FIX_REMAINS
S1_ENGINEERING_SMOKE_AUTHORIZED
ALL_REMAINING_MATERIAL_EVIDENCE_REQUIRES_REAL_GPU_OR_HUMAN_EXECUTION
```

If any material CPU-computable issue remains, keep the corresponding gate blocked.

---

# 1. Repository and baseline

Repository:

```text
/Users/saketmaganti/Projects/Valideval
```

Remote:

```text
Saket-Maganti/valideval
```

Current recent execution lineage includes:

```text
V7
V7.1 scientific-integrity closure
V7.2 native S1 bridge + generic policy calibration
V8 exploratory difficulty-residualized detector
```

The exact live repository is source of truth.

Before editing:
- inspect branch;
- inspect tags;
- inspect Git status;
- inspect current CI;
- resolve every execution source tag;
- read all V7.1/V7.2 handoffs/machine states;
- verify existing frozen results are unchanged.

---

# 2. FIRST PRIORITY — finish unresolved V7.2.1 integrity closure

The latest deep audit found two remaining issues.

## 2.1 Canonical Kaggle runbook provenance

The V7.2 canonical runbook can contain a stale hard-coded intermediate source SHA even when the canonical tag points somewhere else.

Fix permanently.

Create/use:

```text
valideval-v7.2.1-icml2027-kaggle-s1-ready
```

Runbook source verification must resolve the tag dynamically:

```bash
git checkout valideval-v7.2.1-icml2027-kaggle-s1-ready
EXPECTED_SOURCE_COMMIT="$(git rev-parse 'valideval-v7.2.1-icml2027-kaggle-s1-ready^{commit}')"
ACTUAL_SOURCE_COMMIT="$(git rev-parse HEAD)"
test "$ACTUAL_SOURCE_COMMIT" = "$EXPECTED_SOURCE_COMMIT"
```

Never embed a pre-tag SHA in canonical execution instructions.

Add a CI test comparing:
- canonical source constant;
- S1 configs;
- future S2/S3/S4 configs if resealed;
- Kaggle notebook metadata;
- runbook;
- machine state;
- release manifest.

Gate:

```text
RUNBOOK_PROVENANCE_COHERENT
```

## 2.2 Claim-policy statistical closure

Preserve the V7.2 generic result as historical:

```text
GENERIC_KNOWN_TRUTH_POLICY_CALIBRATION_PASS
```

Do not overwrite its approximate:
- false-license rate ~0.0255;
- true-license power ~0.456;
- abstention ~0.830;
- decision regret ~0.0185.

Upgrade the policy science with:
- Wilson or Clopper-Pearson rare-event intervals;
- claim-family-native known-truth simulators;
- claim-family-level confirmation;
- prespecified critical safety strata;
- multiplicity-aware safety assessment;
- fresh dev/validation/confirmation splits;
- freeze before confirmation;
- explicit scope map.

Possible truthful final states:

```text
CLAIM_POLICY_CONFIRMATION_PUBLICATION_GRADE
CLAIM_POLICY_CONFIRMATION_PARTIAL
CLAIM_POLICY_CONFIRMATION_SUPPORTING_ONLY
CLAIM_POLICY_CONFIRMATION_FAIL
```

Do not force universal success.

---

# 3. Preserve all frozen history

Never rewrite:

```text
V7_SYNTHETIC_PRIMARY_GRID_FAILED_AND_PRESERVED
V7_1_ULTRA_CONSERVATIVE_BASELINE
V7_2_GENERIC_POLICY_CALIBRATION_RESULT
V8_EXPLORATORY_IMPROVEMENT_FOUND
V8_CONFIRMATORY_NOT_RUN
```

Do not reuse frozen V7 confirmatory data for V8 tuning.

---

# 4. Claim-family-native CPU simulators

Build actual known-truth simulators for each claim family.

## 4.1 PRIMARY_PAIRWISE

Simulate:
- item difficulty;
- model ability;
- true accuracy difference;
- paired-response correlation;
- model-family dependence;
- unequal family sizes;
- heteroskedastic items.

Run the real pairwise inference/licensing code.

Measure:
- directional error;
- false license;
- power;
- abstention;
- regret;
- coverage.

## 4.2 TOP_K

Simulate:
- latent model ordering;
- near ties;
- exact ties;
- family clusters;
- model-specific variance;
- different panel sizes.

Run the real simultaneous-rank/top-k method.

Measure:
- false inclusion;
- false exclusion;
- simultaneous coverage;
- abstention;
- set width;
- regret.

## 4.3 THRESHOLD_PASS

Simulate a scalar metric around a fixed threshold.

Stress:
- just below;
- equal;
- just above;
- large positive margin;
- large negative margin;
- huge N with tiny effect;
- small N with large effect.

Run strict LCB/UCB threshold logic.

## 4.4 ITEM_DIAGNOSTICS

Simulate:
- rare flaw labels;
- difficulty;
- subjects;
- diagnostic scores;
- family-correlated responses;
- missingness;
- duplicates;
- multiplicity;
- external validation;
- difficulty confounding.

Run actual diagnostic/FDR/stability licensing.

Measure:
- FDR;
- recall;
- AUPRC;
- precision@k;
- license rate;
- difficulty-only false positives.

## 4.5 TRANSPORT

Simulate model × benchmark outcomes with:
- shared latent ability;
- benchmark specialization;
- family effects;
- benchmark dependence;
- held-out benchmark;
- held-out family;
- heterogeneity;
- direction reversal.

Run actual transport logic.

Measure:
- false transport license;
- power;
- reversal detection;
- heterogeneity sensitivity.

## 4.6 REPAIR

Simulate:
- discovery families;
- held-out families;
- true bad items;
- no-effect items;
- harmful repair;
- beneficial repair;
- downstream decision effects.

Run actual repair licensing.

Measure:
- false repair license;
- beneficial-repair power;
- harm detection;
- held-out regret.

---

# 5. Rare-event confidence intervals

Replace Wald-style upper bounds.

Use primary:
```text
Wilson
```
or:
```text
Clopper-Pearson
```

Test against trusted values:

```text
0/1
0/5
0/10
0/100
1/10
1/100
5/100
```

Zero observed errors must not imply zero upper risk.

Create:

```text
reports/final_cpu_maxout/RARE_EVENT_INTERVAL_AUDIT.md
```

---

# 6. Critical safety strata

Preregister meaningful safety groups:

```text
LOW_EFFECTIVE_N
HIGH_FAMILY_CORRELATION
LOW_FAMILY_COUNT
HIGH_FAMILY_IMBALANCE
HIGH_MULTIPLICITY
HIGH_MEASUREMENT_NOISE
NEAR_MATERIALITY_BOUNDARY
NEAR_TIE_TOP_K
TRANSPORT_REVERSAL_RISK
DISCOVERY_VALIDATION_SHIFT
```

Each stratum needs a minimum confirmation count.

If insufficient:

```text
UNDERPOWERED_STRATUM
```

not PASS.

Account for multiple safety checks using Holm/Bonferroni/hierarchical alpha/simultaneous bootstrap.

---

# 7. Finite-sample calibration

For each claim family sweep effective N from tiny to large.

Generate:

```text
coverage vs N
false-license vs N
power vs N
abstention vs N
```

Do not use one universal minimum N unless evidence supports it.

Derive claim-family-specific minimum effective-N guidance.

---

# 8. Monte Carlo convergence

For cheap simulations evaluate:

```text
100
250
500
1000
2500
5000
```

replicates.

Report:
- Monte Carlo SE;
- CIs;
- stability of selected policy;
- stability of final gates.

Freeze adequate replicate counts.

---

# 9. Simulator misspecification stress

Confirmation must include generators not used for selection.

At minimum consider:

```text
Gaussian
actual Gaussian mixture
Student-t
skewed
heteroskedastic
contaminated Gaussian
beta-binomial
correlated Bernoulli
logistic mixed-effects
latent family mixture
nonlinear benchmark effect
```

If a config says `gaussian_mixture`, actually implement a mixture or rename it.

---

# 10. Family-dependence stress

Simulate:

```text
compound symmetry
nested family/subfamily
unequal family sizes
dominant family
family-specific variance
family-specific bias
cross-family correlation
lineage-like correlation
```

Compare:
- naive checkpoint inference;
- model bootstrap;
- family-cluster bootstrap;
- family-balanced estimand;
- one-model-per-family;
- hierarchical bootstrap.

Measure:
- CI coverage;
- false directional decisions;
- rank error;
- transport error;
- licensing error.

---

# 11. Benchmark dependence

Simulate:

```text
independent benchmarks
shared latent ability
benchmark clusters
near-redundant benchmarks
benchmark specialization
benchmark reversal
```

Estimate effective benchmark count vs raw benchmark count.

Use result in transport/effective-N semantics.

---

# 12. Model-panel composition

Vary:
- families;
- checkpoints/family;
- ability spread;
- family imbalance;
- model-size imbalance;
- architecture diversity.

Measure effects on:
- rank confidence;
- diagnostic stability;
- claim policy;
- transport;
- power.

Produce guidance for:
```text
S2 pilot
candidate S3 designs
```

Do not change frozen S1 roster.

---

# 13. Simultaneous rank CPU stress

Expand coverage beyond existing scenarios:

```text
models = 5,10,20,30,40,50
families = 2..10
ties
near ties
one clear winner
dense top cluster
high dependence
heteroskedastic uncertainty
```

Compare:
- point ranks;
- marginal intervals;
- simultaneous intervals;
- family-aware simultaneous intervals.

If coverage fails in some regime, explicitly restrict method scope.

---

# 14. Pairwise multiplicity

Stress all-pairs inference for:
```text
5,10,20,30,40,50 models
```

Compare:
- none;
- BH;
- BY;
- Holm;
- maxT/bootstrap where available.

Measure:
- FDR;
- FWER;
- power;
- directional error;
- decision density.

Separate:
```text
single prespecified pair
primary pair family
exploratory all-pairs
```

---

# 15. Materiality study

Sweep:
```text
delta = 0
small
medium
large
```

for:
- pairwise;
- top-k;
- threshold;
- repair.

Measure:
- licensing;
- power;
- abstention;
- regret;
- rank set width.

Keep statistical significance distinct from practical materiality.

---

# 16. Selective decision frontier

Compare:

```text
forced point decision
p-value-only
CI-only
multiplicity-aware CI
ValidEval selective licensing
```

Generate figure-ready data for:
```text
error vs abstention
regret vs abstention
power vs abstention
```

This is a high-value ICML method analysis.

---

# 17. Claim-specific regret

Where defensible define:

```text
pairwise: selecting worse model
top-k: wrong inclusion/exclusion
threshold: deploy below standard
repair: harmful/unnecessary repair
transport: false transfer
```

Use normalized interpretable units.

Do not claim universal economic utility.

---

# 18. Policy stability

Run:
- leave-one-generator-out;
- leave-one-dependence-regime-out;
- leave-one-effect-band-out;
- leave-one-claim-family-out;
- leave-one-critical-stratum-out.

If selected policy changes often:

```text
POLICY_SELECTION_UNSTABLE
```

Prefer robustness over tiny average utility improvements.

---

# 19. Local policy sensitivity

Perturb one parameter at a time:

```text
confidence
FDR
effective N
minimum families
minimum power
materiality
bootstrap stability
decision regret
```

Do not retune from this analysis.

Report fragility.

---

# 20. Calibration curves

Generate structured data for:

```text
nominal confidence vs empirical coverage
nominal FDR vs empirical false-license rate
effective N vs licensing probability
family correlation vs false-license rate
minimum-power threshold vs empirical power
```

Check expected monotonic behavior.

---

# 21. Adversarial falsification suite

Try to break the framework with:

```text
huge raw N + tiny effective N
tiny effect + huge raw N
large effect + few families
one dominant family
many redundant benchmarks
nearly tied top models
transport reversal
repair benefit in discovery + harm in validation
difficulty-only diagnostic
fake held-out metadata
mixed model revisions
stale source commit
```

Correct behavior should usually be:
```text
BLOCK
ABSTAIN
REJECT
```

Create a permanent falsification suite.

---

# 22. Historical MMLU: weighting sensitivity

Using the real 39 × 14,042 matrix compare:

```text
canonical item-weighted
balanced subject-weighted
trimmed subject weighting
```

Report:
- winner;
- top-k;
- simultaneous ranks;
- pairwise calls;
- materiality;
- diagnostic conclusions.

---

# 23. Historical MMLU: jackknife

Leave one out:
- subject;
- model;
- model family;
- high-influence subject group.

Measure:
- rank changes;
- pairwise changes;
- top-k;
- null conclusions;
- materiality.

---

# 24. Historical MMLU: bootstrap convergence

Increase bootstrap draws where feasible.

Verify:
- rank interval width;
- pairwise calls;
- null exceedance;
- influence conclusions

have converged.

---

# 25. Influence analysis

Compute:
- subject influence on winner/top-k;
- model-family influence on uncertainty;
- item-group influence on pairwise decisions.

Use exact leave-group-out where cheap.

Approximation only if validated against exact subsets.

---

# 26. Canonical vs deduplicated

Extend prior comparison to:
- simultaneous rank sets;
- FDR pairwise calls;
- decision regret;
- subject influence;
- materiality calls.

A robust negative result is valuable.

---

# 27. Null-model adequacy

For each Study-H null record:

```text
fixed quantities
randomized quantities
estimated parameters
hypothesis represented
known failure modes
```

Check if it reproduces:
- model totals;
- subject difficulty;
- score variance;
- dependence;
- subject sizes.

Rename/demote any null whose implementation does not match its title.

---

# 28. Null sensitivity summary

Create a structured conclusion matrix:

```text
STABLE_ACROSS_ALL_NULLS
STABLE_ACROSS_PLAUSIBLE_NULLS
NULL_SENSITIVE
```

Do not average incompatible p-values.

---

# 29. V8 exploratory difficulty work

Keep V8 exploratory.

Compare:
- raw difficulty;
- cross-fitted difficulty;
- family-balanced difficulty;
- subject-conditioned difficulty;
- matched-difficulty controls;
- residualization;
- stratified nulls.

Evaluate:
- difficulty-only negatives;
- true flaws;
- mixed flaws;
- unseen flaws;
- held-out generators.

Add leakage tests.

No V8 confirmatory promotion unless a separate untouched frozen protocol truly exists.

---

# 30. Optional measurement-regime upgrade

Current measurement-regime work is supporting-only.

Only upgrade if meaningful CPU science is feasible.

Possible estimators:
- aggregate;
- additive;
- subject-conditioned;
- low-rank;
- Rasch/1PL;
- regularized 2PL if feasible.

Evaluate:
- bias;
- RMSE;
- coverage;
- rank recovery;
- calibration;
- failure rate.

If still shallow, retain:

```text
MEASUREMENT_REGIME_SUPPORTING_ONLY
```

---

# 31. Optional generalizability upgrade

Current result is supporting-only.

If feasible, fit a stronger hierarchical model:
- binary response;
- family;
- model;
- subject;
- item;
- model×subject;
- family×subject.

Use GLMM/Bayesian/bootstrap only if dependency/tooling support is stable.

Report:
- convergence;
- variance uncertainty;
- boundary estimates;
- sensitivity.

Otherwise keep supporting-only.

---

# 32. Synthetic transport stress

Before real Study C, simulate:
- leave-one-benchmark-out;
- leave-one-family-out;
- no transport;
- partial transport;
- benchmark reversal;
- family reversal;
- interaction-dominated cases.

Measure false transport licensing and power.

---

# 33. Synthetic repair stress

Simulate:
- harmful items;
- harmless suspicious items;
- useful repair;
- no-effect repair;
- harmful repair;
- discovery-only overfit.

Require held-out-family validation.

Measure false repair licensing.

---

# 34. Human-study CPU planning

Improve human study design without fabricating labels.

Calculate required:
- unique items;
- total labels;
- adjudication labels;

for:
- diagnostic precision;
- enrichment;
- agreement;
- class-specific precision.

Support:
```text
2 annotators
3 annotators
4 strata
multiple adjudication fractions
```

---

# 35. Human annotator-noise simulation

Simulate annotator:
- sensitivity;
- specificity;
- bias;
- correlated errors;
- disagreement;
- adjudication.

Measure how label noise affects:
- diagnostic validation;
- precision estimates;
- claim licensing.

---

# 36. Human allocation optimizer

Optimize items/stratum subject to:
- target CI width;
- target power;
- minimum stratum count;
- expected prevalence.

Output:
```text
pilot
minimum confirmatory
recommended
high-precision
```

designs.

---

# 37. Study-C primary-claim hierarchy

Before S3, rank possible claims by:
- thesis centrality;
- novelty;
- identifiability;
- power feasibility;
- compute cost;
- human-validation dependence;
- reviewer significance.

Produce:

```text
PRIMARY
SECONDARY
EXPLORATORY
```

proposal.

Do not freeze based on desired outcome direction.

---

# 38. Validate the Study-C power planner

Use synthetic designs with known approximate power behavior.

Required invariants:
- power increases with N;
- power increases with effect;
- power decreases with dependence;
- family count matters for family-level claims;
- benchmark count matters for transport claims.

Add regression tests.

---

# 39. Power uncertainty

Do not output one false-precision power number.

Produce:
```text
optimistic
central
conservative
worst plausible
```

using parameter uncertainty.

After S2 replace planning assumptions with measured distributions.

---

# 40. Adaptive GPU compute planner

Prepare:

```text
S1 measurements
→ S2 design
→ S2 variance/runtime
→ S3 roster/item optimization
```

Objective:
```text
minimize GPU hours
subject to primary-claim adequacy
```

Do not authorize S3 before S2.

---

# 41. Model roster optimizer

Select candidate panels under:
- family diversity;
- ability spread;
- T4 feasibility;
- open access;
- model size;
- runtime.

Output:
- best S2 roster;
- candidate S3 rosters;
- marginal value of each added family/model.

Do not change frozen S1 roster.

---

# 42. Item-subset design

Prepare CPU-only selection methods for S2/S3:
- uniform;
- subject-stratified;
- difficulty-stratified using allowed historical/public estimates;
- balanced categories.

Do not use future target-model results to design confirmatory subsets unless frozen protocol allows it.

---

# 43. Extraction reliability simulation

Stress parser with:
- missing answer;
- multiple answers;
- prose;
- commas;
- decimals;
- fractions;
- Unicode;
- whitespace;
- malformed outputs;
- answer letters embedded in words.

Measure score impact.

---

# 44. Scorer differential testing

Build simple independent reference scorers.

MMLU:
```text
A/B/C/D
```

GSM8K:
```text
numeric normalization
```

BBH:
```text
task-specific formats
```

Production and reference implementations must agree on golden fixtures.

---

# 45. Prompt-contract mutation tests

Hash and verify:
- system text;
- prompt;
- answer format;
- few/zero-shot;
- stop behavior;
- max tokens.

Mutate one character and require identity failure.

---

# 46. Architecture — canonical schemas

Centralize active execution/package schema definitions.

Avoid future drift between:
- runner;
- package;
- importer;
- acceptance.

Preserve explicit legacy adapters.

---

# 47. Architecture — typed identifiers

Use strong dataclasses/enums where valuable for:
- benchmark;
- model;
- revision;
- family;
- run;
- study;
- source ref;
- source SHA;
- evidence state;
- claim family.

Do not overengineer.

---

# 48. Architecture — evidence state machine

Formalize allowed states:

```text
PLANNED
ENGINEERING_VALIDATED
EXPLORATORY_OBSERVED
CONFIRMATORY_OBSERVED
HELD_OUT_VALIDATED
HUMAN_VALIDATED
TRANSPORT_VALIDATED
DECISION_LICENSED
BLOCKED
INVALIDATED
```

Create transition table/tests.

No illegal jumps.

---

# 49. Architecture — invalidation propagation

If evidence is invalidated by:
- bad checksum;
- source mismatch;
- prompt bug;
- scorer bug;
- leakage;
- dataset issue;

invalidate dependent analyses/claims.

Build evidence dependency traversal.

---

# 50. Architecture — provenance DAG

Represent:

```text
claim
→ analysis
→ imported package
→ raw run
→ config
→ source tag/SHA
```

Generate machine-readable provenance graph.

---

# 51. Architecture — strict config validation

Reject unknown/invalid fields where appropriate.

Validate:
- source;
- stage;
- evidence class;
- benchmark;
- panel;
- subset;
- hashes.

Optional JSON Schema export.

---

# 52. Architecture — legacy compatibility matrix

Document/test:

```text
V5
V6
V7
V7.1
V7.2
V7.2.1
```

For each:
- executable?
- importable?
- historical only?
- canonical?

No implicit compatibility.

---

# 53. Permanent runner→ZIP→import CI

Keep a mandatory canonical roundtrip test:

```text
mock runner
→ package
→ ZIP
→ importer
→ acceptance
```

for every supported current schema.

---

# 54. Architecture — exception taxonomy

Audit:

```text
load OOM
generation OOM
timeout
CUDA failure
download failure
dataset failure
parser failure
scorer failure
checksum failure
config failure
source mismatch
```

Do not collapse critical operational failures into generic errors.

---

# 55. Retry semantics

For each failure type define:
- retryable;
- max retry;
- allowed fallback;
- state mutation.

No retry for deterministic provenance failure.

Bound all retries.

---

# 56. Resume torture tests

Interrupt:
- after model 1;
- mid-shard;
- after partial predictions;
- before package finalization;
- one worker failure.

Resume must:
- avoid duplicates;
- preserve identity;
- revalidate;
- reject changed config.

---

# 57. Atomic writes

Audit evidence files for:
- temporary write;
- flush/fsync where useful;
- atomic rename.

Never leave partial artifact looking valid.

---

# 58. Deterministic packaging

Normalize:
- archive ordering;
- timestamps;
- path separators;
- permissions.

Same logical package should get same normalized hash where feasible.

---

# 59. Filesystem portability

Test paths with:
- spaces;
- Unicode;
- long names.

No executable hard-coded `/Users/saket...` assumptions.

---

# 60. Offline/online contract

Explicitly define:
- initial online download;
- cached offline resume;
- exact revision behavior.

Never silently fetch latest revision.

---

# 61. Dependency locks

Produce canonical:
- CPU/dev lock;
- Kaggle T4 lock.

Hash both.

Record:
- Python;
- NumPy;
- SciPy;
- PyTorch;
- Transformers;
- datasets;
- tokenizers.

---

# 62. Numerical reproducibility

Classify key outputs:

```text
BITWISE_STABLE
NUMERICALLY_STABLE
CONCLUSION_STABLE
ENVIRONMENT_SENSITIVE
```

Exact hash only inside frozen environment where justified.

---

# 63. Seed registry

Centralize seeds for:
- development;
- validation;
- confirmation;
- rank simulations;
- V8 exploration;
- power studies.

Add seed-collision test.

---

# 64. Confirmation isolation

Ensure confirmation runners cannot read:
- development outputs;
- validation metrics;
- sealed labels.

Use explicit allowed inputs where feasible.

---

# 65. Package integrity

Manifest every critical file:
- path;
- size;
- hash.

Reject:
- missing;
- tampered;
- unsafe extras.

---

# 66. CLI polish

Audit:
- `--help`;
- exit codes;
- JSON output;
- dry-run/preflight;
- actionable errors.

Key commands:
```text
run
accept-s1-v7-2-1
recalibrate-study-c-after-s1
doctor
replay-cpu-evidence
validate-release
```

---

# 67. Doctor command

Verify:
- Python;
- dependencies;
- GPU visibility if requested;
- Git tag;
- configs;
- disk;
- writable output;
- package version.

Return:
```text
PASS
WARN
BLOCK
```

---

# 68. Code cleanup

Identify:
- dead active code;
- duplicate helpers;
- stale unreachable branches;
- oversized functions.

Refactor only when correctness/testability improves.

Do not remove historical compatibility casually.

---

# 69. Typing

Expand mypy over all active V7.2.1 paths where feasible.

Reduce untyped dict payloads and unsafe `Any`.

Do not waste large time typing frozen historical scripts.

---

# 70. Scientific docstrings

For scientific methods document:
- estimand;
- resampling unit;
- generalization unit;
- assumptions;
- failure behavior.

Especially:
- rank inference;
- nulls;
- effective N;
- transport;
- repair;
- claim licensing.

---

# 71. Structured logging

Record:
- run;
- benchmark;
- model;
- shard;
- event;
- duration;
- failure type.

Do not leak secrets or restricted raw data.

---

# 72. Secret/security scan

Scan for:
- HF tokens;
- API keys;
- `.env`;
- auth headers;
- private paths;
- accidental personal metadata;
- model-cache secrets.

---

# 73. Artifact size audit

Find:
- virtualenvs;
- caches;
- redundant outputs;
- giant temporary files.

Keep evidence required for reproducibility.

Ignore/remove transient artifacts.

---

# 74. Git hygiene

Check:
- line endings;
- executable bits;
- `.gitignore`;
- generated files;
- stale local-only artifacts.

Do not rewrite published history.

---

# 75. Property-based/randomized tests

Use Hypothesis if already feasible; otherwise randomized tests.

Targets:
- config parsing;
- interval invariants;
- ranking invariants;
- package roundtrip;
- scorer normalization;
- evidence transitions.

---

# 76. Importer fuzzing

Test:
- truncated JSON;
- missing fields;
- wrong types;
- duplicate rows;
- Unicode;
- bad hashes;
- mixed revisions;
- malformed archives.

Must fail safely.

---

# 77. Archive security

Test ZIP:
- `../`;
- absolute paths;
- symlinks;
- duplicate members;
- extreme compression ratio;
- too many members.

Reject unsafe extraction.

---

# 78. Mutation testing

If tooling is available, mutate critical logic:
- source comparisons;
- claim gates;
- importer acceptance;
- rank intervals.

Tests should catch mutations.

If tooling unavailable, implement manual mutation probes.

---

# 79. Test coverage

Measure active-module coverage.

Prioritize:
- error paths;
- rejection states;
- OOM;
- resume;
- provenance;
- claim licensing.

Do not chase 100% mechanically.

---

# 80. Differential statistical references

Build independent simple references for:
- BH;
- BY;
- Holm;
- Wilson/Clopper-Pearson;
- canonical accuracy;
- pairwise effect;
- deterministic archive hash.

Compare production output.

---

# 81. Reproducibility stress

Run key CPU study:
- twice same process;
- separate process;
- shuffled row order;
- shuffled model order;
- shuffled subject order.

Results should remain invariant except explicitly documented ties.

---

# 82. Tie handling audit

Audit every use of:
```text
argsort
rank
top-k
```

Define deterministic/scientific tie policy.

No row-order dependence.

---

# 83. Locale/timezone independence

Evidence identity must not depend on:
- timezone;
- locale;
- decimal formatting.

Timestamps may vary without changing normalized evidence hash.

---

# 84. Clean-clone test

From fresh checkout/tag:
- install;
- test;
- build;
- fixture notebooks;
- CPU replay.

No reliance on untracked local files.

---

# 85. Minimal dependency test

Run active code with only declared dependencies.

Catch accidental use of user's rich local environment.

---

# 86. CI structure

Maintain:
```text
QUICK_CI
```
for:
- lint;
- format;
- mypy;
- tests;
- canonical roundtrip;
- artifact validator;
- build;
- notebook fixture;
- secret scan.

Maintain:
```text
RELEASE_VALIDATION
```
for longer CPU replay/hash checks.

---

# 87. Frozen-artifact validator

Ensure CI detects accidental changes to:
- failed V7 evidence;
- V7.1 baseline;
- V7.2 generic result;
- V8 exploratory status.

Protect scientific history.

---

# 88. Kaggle S1 notebook polish

All notebooks must:
- delegate to package code;
- print source tag/SHA;
- fail fast;
- clearly mark fixture vs real;
- print ZIP paths;
- print import command;
- print next step.

---

# 89. Kaggle preflight

Notebook 00 should verify:
- 2 GPUs;
- T4 identities if required;
- CUDA;
- RAM;
- disk;
- Internet;
- dependencies;
- exact tag;
- exact configs;
- model/dataset accessibility.

No science claim from preflight.

---

# 90. Cache/download planning

Estimate:
- total model bytes;
- peak cache;
- outputs;
- ZIPs.

Define cache reuse and cleanup.

Avoid repeated downloads in same session.

---

# 91. CPU scheduler simulation

Simulate T4 scheduling with estimated durations:
- balanced tasks;
- slow model;
- failed model;
- OOM/retry;
- resume.

Check deadlock/starvation.

---

# 92. S2 draft runbook

Prepare but do not authorize.

Must say:

```text
DRAFT_PENDING_ACCEPTED_S1
```

Include:
- roster;
- subset;
- goals;
- outputs;
- acceptance;
- recalibration.

---

# 93. S3 config generator

Prepare a generator consuming S2:
- runtime;
- variance;
- failure;
- family coverage;
- extraction;
- primary claims.

It may output:
```text
S3_PROPOSED
```
or:
```text
S3_REDESIGN_REQUIRED
```

Never authorize without S2.

---

# 94. S4 optional template

Prepare only template.

Require:
- accepted S3;
- explicit scientific rationale;
- marginal-value analysis.

---

# 95. Failure recovery runbook

Document response to:
- session death;
- Internet loss;
- OOM;
- disk full;
- model failure;
- package corruption;
- extraction <0.95.

For each:
```text
resume
rerun
repair
block
```

---

# 96. CPU replay command

Create:

```bash
python -m valideval replay-cpu-evidence
```

Regenerate:
- historical MMLU summaries;
- rank coverage;
- null sensitivity;
- generic policy;
- native policy;
- V8 exploratory summary;
- power plan.

Compare hashes/tolerances.

---

# 97. Evidence ledger audit

Every evidence artifact should carry:
- source commit/tag;
- config hash;
- data hash;
- dependency lock;
- seeds;
- result hash;
- evidence class.

Detect missing provenance.

---

# 98. Claim trace report

Generate:

```text
claim
→ status
→ evidence
→ evidence class
→ assumptions
→ blockers
```

Machine-readable + Markdown.

Do not write final paper claims.

---

# 99. Internal pre-GPU release

Create bundle containing:
- source tag;
- configs;
- requirements;
- notebooks;
- CPU replay;
- machine state;
- runbooks;
- checksums.

Exclude:
- venvs;
- caches;
- model weights;
- secrets.

---

# 100. Report-generation integrity

All Markdown reports must be derived from structured JSON/CSV.

Add tests that reported numbers match source artifacts.

No hand-copied numerical truth.

---

# 101. CPU profiling

Profile:
- rank bootstrap;
- null simulations;
- policy simulations;
- power;
- packaging.

Optimize obvious hotspots.

---

# 102. Deterministic parallelism

If safe, parallelize simulations.

Seed by scenario ID, not worker order.

Results must be invariant to worker count.

Test:
```text
1,2,4,8 workers
```
where available.

---

# 103. Memory optimization

Avoid unnecessary copies of historical 547k response rows.

Use efficient arrays/categories/chunking.

Record peak memory.

---

# 104. Quick vs full modes

Add:
```text
--quick
```
for development/CI.

Label outputs:
```text
NON_EVIDENCE_FIXTURE
```

Full:
```text
--full
```
uses registered evidence settings.

Never mix them.

---

# 105. Canonical execution handbook

Create one current document answering:
- what is canonical;
- what is historical;
- what is exploratory;
- what is frozen;
- what to run next;
- what each stage proves.

Mark old V6/V7 runbooks:

```text
HISTORICAL — NOT CANONICAL FOR NEW EXECUTION
```

---

# 106. Glossary

Define:
- validity;
- diagnostic;
- license;
- materiality;
- effective N;
- independence unit;
- family;
- simultaneous rank set;
- transport;
- repair;
- engineering evidence;
- exploratory evidence;
- confirmatory evidence.

---

# 107. Architecture map

Create concise internal map:

```text
configs
→ runner
→ workers
→ package
→ importer
→ analyses
→ evidence ledger
→ claim licensing
```

No final paper figure required.

---

# 108. Public API audit

Export only stable useful interfaces.

Avoid accidental public exposure of internals.

---

# 109. Package/version/changelog

Ensure:
- package version coherent;
- changelog records V7.2.1/maxout repairs;
- release metadata agrees with machine state.

Explicitly state:
```text
no new real GPU evidence
```

---

# 110. License/citation audit

Check:
- repository LICENSE;
- CITATION.cff if useful;
- third-party notices;
- benchmark/model citations.

Do not claim unverified licenses.

---

# 111. pyproject audit

Check:
- runtime deps;
- dev deps;
- Python versions;
- entrypoints;
- package data.

Remove accidental undeclared dependency reliance.

---

# 112. Notebook generation integrity

If notebooks are generated:
- retain canonical generator;
- regenerate;
- diff;
- fail CI on manual drift.

---

# 113. Machine-state schema

Define typed/schema-validated machine state.

No missing required fields.

Include schema version.

---

# 114. Security: YAML/subprocess/path handling

Ensure:
- safe YAML loader;
- no unsafe arbitrary deserialization;
- subprocess argument arrays;
- bounded timeouts;
- path traversal rejection.

---

# 115. Policy-component ablations

CPU ablate:
- no effective-N;
- no family clustering;
- no multiplicity;
- no materiality;
- no external validation;
- no transport gate;
- no abstention.

Measure:
- false licenses;
- power;
- abstention;
- regret.

This could support necessity of each component.

---

# 116. Rank ablations

Compare:
- point rank;
- marginal CI;
- simultaneous CI;
- family-aware simultaneous.

Measure coverage/error.

---

# 117. Dependence ablations

Compare:
- item bootstrap;
- model bootstrap;
- family bootstrap;
- nested bootstrap.

Measure coverage.

---

# 118. Null ablations

Compare all plausible Study-H nulls.

Do not choose one favorable null.

---

# 119. V8 ablations

Exploratory only:
- difficulty-only;
- residual-only;
- family-balance-only;
- combined.

Keep confirmatory boundary.

---

# 120. Negative controls

Add:
- random labels;
- shuffled model IDs;
- shuffled subjects;
- difficulty-only;
- no flaw;
- fake transport;
- no repair benefit.

Expected:
```text
no scientific license
```

---

# 121. Positive controls

Add strong known-truth cases where the system should license.

This prevents “always abstain” from looking safe.

---

# 122. Boundary controls

At exact thresholds:
- materiality equality;
- top-k tie boundary;
- threshold equality.

Expected:
```text
block/abstain
```
unless contract explicitly says otherwise.

---

# 123. Statistical implementation audit

Audit interval/p-value/FDR/bootstrap names and implementations.

For every method document:
- one/two-sided;
- exact/asymptotic;
- tie behavior;
- zero-variance behavior;
- resampling unit.

No terminology overclaim.

---

# 124. Effective-N semantics

For each claim family map:

```text
observational unit
resampling unit
generalization unit
```

Do not pretend effective N is exactly known where only approximate.

Use:
```text
EFFECTIVE_N_APPROXIMATION
```
where appropriate.

---

# 125. Methods ledger

Create:

```text
results/methods/method_contracts.json
```

Fields:
- method;
- estimand;
- assumptions;
- implementation;
- status;
- evidence scope.

---

# 126. Claim registry

Create/update:

```text
results/claims/claim_registry.json
```

Fields:
- claim ID;
- family;
- status;
- evidence class;
- prerequisites;
- blockers.

---

# 127. Experiment registry

Track:
- historical CPU;
- synthetic CPU;
- future GPU;
- human.

Unique study IDs only.

---

# 128. Freeze/exploration metadata

Every result directory should expose:
```text
evidence_class
frozen
confirmatory
exploratory
```

No ambiguity.

---

# 129. Figure/table data only

Generate machine-readable future figure/table data for:
- policy Pareto;
- rank uncertainty;
- null sensitivity;
- dependence;
- power;
- V8 confound.

Do not write final paper narrative.

---

# 130. Reviewer red-team

Simulate hostile ICML review:

```text
claim licensing is just conservative thresholding
calibration is simulator-specific
families are not independent
benchmarks are dependent
rank sets are not truly simultaneous
multiplicity is incomplete
diagnostic signal is difficulty
repair is overfit
canonical benchmark was altered
synthetic evidence is circular
```

For each produce:
- current evidence;
- missing evidence;
- CPU fix if available;
- future GPU/human experiment;
- claim limitation.

---

# 131. Stop condition

Do not continue adding architecture indefinitely.

Stop when:
- known P0/P1 CPU issues are closed or honestly blocked;
- active paths pass;
- CPU science is converged enough;
- remaining material work requires real GPU/human/external evidence.

---

# 132. Required final reports

Create:

```text
reports/final_cpu_maxout/
```

with at least:

```text
CPU_MAXOUT_EXECUTIVE_VERDICT.md
CPU_MAXOUT_REPAIR_LEDGER.md
CPU_MAXOUT_CLAIM_POLICY.md
CPU_MAXOUT_FINITE_SAMPLE_CALIBRATION.md
CPU_MAXOUT_RARE_EVENT_SAFETY.md
CPU_MAXOUT_DEPENDENCE.md
CPU_MAXOUT_RANK_INFERENCE.md
CPU_MAXOUT_SELECTIVE_DECISIONS.md
CPU_MAXOUT_NULL_SENSITIVITY.md
CPU_MAXOUT_HISTORICAL_MMLU.md
CPU_MAXOUT_V8_EXPLORATORY.md
CPU_MAXOUT_HUMAN_PLANNING.md
CPU_MAXOUT_POWER_AND_COMPUTE.md
CPU_MAXOUT_ARCHITECTURE_HARDENING.md
CPU_MAXOUT_TESTING_AND_SECURITY.md
CPU_MAXOUT_REPRODUCIBILITY.md
CPU_MAXOUT_KAGGLE_PREP.md
CPU_MAXOUT_ICML_RED_TEAM.md
CPU_MAXOUT_REMAINING_BLOCKERS.md
```

---

# 133. Required machine state

Create:

```text
VALID_EVAL_FINAL_CPU_MAXOUT_MACHINE_STATE.json
```

Include:

```text
baseline_commit
final_source_commit
final_source_tag
metadata_commit
git_clean
ci

v7_2_1_closure_status
runbook_provenance
claim_policy_status
claim_family_scope
critical_strata
v8_status

cpu_runs
cpu_runtime
monte_carlo_replicates
numerical_reproducibility

architecture_status
schema_status
evidence_state_status
importer_security
resume_status
oom_status

tests
coverage
fuzz
mutation_testing
lint
format
mypy
build
notebooks
secret_scan
release

s1_status
s2_status
s3_status
s4_status

remaining_cpu_work
remaining_gpu_work
remaining_human_work
exact_next_action
```

---

# 134. Final validation

Run:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m ruff format --check src tests scripts
python -m mypy <all active modules feasible>
python -m build
```

Also run:
- clean checkout;
- fixture notebooks;
- runner→ZIP→import→accept;
- CPU replay;
- native claim-policy confirmation;
- rank coverage;
- fuzz/importer security;
- release validator;
- tag/runbook coherence;
- GitHub CI.

---

# 135. Final source tag

After all source changes pass, create a canonical final pre-GPU tag such as:

```text
valideval-icml2027-pre-gpu-cpu-maxout
```

Do not rewrite older tags.

If the canonical S1 code/config changed during this pass, update the Kaggle S1 runbook to this final tag.

Otherwise preserve the V7.2.1 S1 tag and clearly document the distinction.

---

# 136. Final handoff

Create:

```text
VALID_EVAL_FINAL_CPU_MAXOUT_HANDOFF.md
```

Sections:
1. executive verdict;
2. baseline;
3. all repairs;
4. CPU analyses;
5. claim policy;
6. rank inference;
7. dependence;
8. nulls;
9. historical MMLU;
10. V8;
11. human planning;
12. Study-C power;
13. architecture;
14. security/testing;
15. reproducibility;
16. GPU prep;
17. S1/S2/S3/S4 state;
18. remaining GPU work;
19. remaining human work;
20. exact next action.

---

# 137. Final Codex response

Return exactly:

```text
FINAL_VERDICT:

BASELINE_COMMIT:
FINAL_SOURCE_COMMIT:
FINAL_SOURCE_TAG:
METADATA_COMMIT:
CI:

V7_2_1_CLOSURE_STATUS:
RUNBOOK_PROVENANCE_STATUS:
CLAIM_POLICY_STATUS:
CLAIM_FAMILY_SCOPE:
CRITICAL_STRATUM_STATUS:
V8_STATUS:

CPU_RUNS_COMPLETED:
CPU_RUNTIME_TOTAL:
MONTE_CARLO_REPLICATES_TOTAL:

ARCHITECTURE_STATUS:
SCHEMA_STATUS:
EVIDENCE_STATE_STATUS:
IMPORTER_SECURITY_STATUS:
RESUME_STATUS:
OOM_STATUS:

TESTS:
COVERAGE:
FUZZ:
MUTATION_TESTING:
LINT:
FORMAT:
TYPE_CHECK:
PACKAGE_BUILD:
NOTEBOOKS:
SECRET_SCAN:
RELEASE:

S1_STATUS:
S2_STATUS:
S3_STATUS:
S4_STATUS:

REMAINING_CPU_BLOCKERS:
REMAINING_GPU_BLOCKERS:
REMAINING_HUMAN_BLOCKERS:

SHOULD_USER_RUN_KAGGLE_NOW:
FIRST_NOTEBOOK:
EXPECTED_ZIPS:
EXACT_IMPORT_COMMAND:
EXACT_NEXT_ACTION:

MACHINE_STATE:
FINAL_HANDOFF:
```

---

# Final rule

Use the remaining Codex budget only for:

```text
1. correctness
2. statistical validity
3. reproducibility
4. execution safety
```

Do not spend it on cosmetic architecture.

The ideal truthful endpoint is:

```text
ALL_USEFUL_PRE_GPU_CPU_WORK_EXHAUSTED
NO_KNOWN_P0_OR_P1_CPU_FIX_REMAINS
S1_ENGINEERING_SMOKE_AUTHORIZED
ALL_REMAINING_MATERIAL_EVIDENCE_REQUIRES_REAL_GPU_OR_HUMAN_EXECUTION
```
