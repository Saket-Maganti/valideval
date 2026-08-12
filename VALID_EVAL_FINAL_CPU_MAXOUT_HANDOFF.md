# ValidEval Final CPU Max-Out Handoff

## 1. Executive verdict

`ALL_USEFUL_PRE_GPU_CPU_WORK_EXHAUSTED` and `NO_KNOWN_P0_OR_P1_CPU_FIX_REMAINS`. S1 engineering smoke is authorized; no real GPU or human evidence was created.

## 2. Baseline

Baseline commit: `49bdc529a482596bb4bcb308b3d96df34e8dcd80`. Canonical S1 source ref: `valideval-v7.2.1-icml2027-kaggle-s1-ready`.

## 3. All repairs

Canonical provenance, rare-event intervals, archive security, typed retry semantics, evidence invalidation, scorer boundaries, and odd-panel rank stress were repaired and tested.

## 4. CPU analyses

Registered runs: 14; recorded analysis runtime: 35.519971 seconds; Monte Carlo/bootstrap replicates: 81500.

## 5. Claim policy

`CLAIM_POLICY_CONFIRMATION_SUPPORTING_ONLY`. Aggregate family safety passes, but 21 of 60 critical cells fail the simultaneous safety bound.

## 6. Rank inference

`RANK_SCOPE_RESTRICTION_REQUIRED` with minimum registered joint coverage 0.920.

## 7. Dependence

Family and benchmark dependence are explicit sensitivity dimensions. Effective benchmark count is labeled an approximation.

## 8. Nulls

Frozen null results remain unchanged. No favorable null was selected.

## 9. Historical MMLU

Weighting, jackknife, and bootstrap sensitivity cover 39 models and 14042 items. They do not create new benchmark evidence.

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

- S1: `S1_ENGINEERING_SMOKE_AUTHORIZED`
- S2: `DRAFT_PENDING_ACCEPTED_S1`
- S3: `BLOCKED_PENDING_S2`
- S4: `TEMPLATE_ONLY_BLOCKED_PENDING_S3`

## 18. Remaining GPU work

- Run and accept the three real Kaggle T4x2 S1 engineering packages.
- Measure S1 runtime, extraction reliability, failures, and package health.
- Do not authorize S2 until S1 acceptance and recalibration pass.
- V8 independent confirmation remains unrun and unauthorized.
- Execute future held-out transport and repair studies before those claims.

## 19. Remaining human work

- Collect independent item labels under the frozen annotation protocol.
- Complete adjudication and reliability acceptance before human validation.

## 20. Exact next action

Check out valideval-v7.2.1-icml2027-kaggle-s1-ready and run kaggle_icml2027/00_v7_2_t4x2_preflight.ipynb on Kaggle with two T4 GPUs.
