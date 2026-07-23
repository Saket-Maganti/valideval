# ValidEval Maximum-Ceiling Pre-Execution Handoff

Authoritative V5 continuation document for
`/Users/saketmaganti/Projects/Valideval`. This handoff records the strongest honest state that can
be reached without running the controlled benchmark panel, obtaining human labels, or asserting
unconfirmed external-item identity. A passing build surface is not empirical or venue readiness.

## 1. Executive verdict

Overall gate: `PRE_EXECUTION_BUILD_PARTIAL`.

The old V4 readiness gate did not survive. V5 reproduced the underlying public MMLU response
matrix exactly, but retired the post-hoc severity threshold, contradicted the legacy pseudo-ablation,
failed closed on MMLU-Redux identity, and separated historical evidence from the future controlled
study. The local engineering substrate is substantially stronger, yet a production benchmark runner,
complete leakage inputs, and an adequate exact common panel remain blocking prerequisites to even
the S1 engineering smoke.

## 2. What ValidEval now is

ValidEval is a multidimensional validity-auditing toolkit for AI benchmarks. Its defensible thesis
is that benchmark accuracy alone does not establish construct validity; validity threats must be
audited through distinct, uncertainty-aware diagnostics without collapsing them into one universal
score. V5 is currently a reproducible historical-evidence audit plus a fail-closed controlled-study
build, not a completed cross-benchmark validation study.

## 3. Historical evidence versus controlled future evidence

| Study | Scope | Identity | Current evidence state |
|---|---|---|---|
| Study H | Public HELM-derived MMLU predictions | 39 historical model aliases; exact source/matrix hashes | `REPRODUCED` with major interpretive caveats |
| Study C | Future MMLU, GSM8K, and BBH execution | five pinned public revisions across three nominal families | `PLANNED`; no controlled output exists |

Study H may support only protocol-scoped historical statements. It may not be relabeled as a
controlled common-panel experiment. Study C may not inherit Study H findings, model identities, or
eligibility states.

## 4. Verified existing MMLU state

- Primary long-form rows: `547,638`.
- Models: `39`; items: `14,042`; subjects: `57`.
- Missing model-item cells: `0`; duplicate or conflicting model-item rows: `0`.
- Active matrix and independently reconstructed matrix are exactly equal.
- Matrix SHA-256:
  `f85a0a44f3203de2863d86bf13b2c81d8e934ae4c07b826193b5e93a3fc86e74`.
- Aggregate-accuracy spread: `0.5801880074`.
- Historical raw subject-conditioned rank-range median/maximum: `19`/`30`.
- Proxy-weighted versus aggregate ranking: Spearman `0.9979757085`, Kendall `0.9784075574`,
  maximum rank delta `2`.

These are reproduced descriptive facts under the frozen historical protocol. They do not establish
global invalidity, contamination, construct failure, or controlled-panel transfer.

Primary report: `reports/v5/VALID_EVAL_V5_CLAIM_EVIDENCE_LEDGER.md`.

## 5. Reproduced and contradicted claims

| Claim/surface | State | V5 disposition |
|---|---|---|
| Exact historical MMLU matrix and descriptive spread | `REPRODUCED` | eligible with protocol scope and hashes |
| Raw rank variation across MMLU subjects | `REPRODUCED` | descriptive only; old severity language retired |
| Severe rank instability at post-hoc range threshold 10 | `RETIRED` | null-sensitive and not preregistered |
| Eight-family diagnostic ablation | `CONTRADICTED` | seven named variants reuse accuracy-derived values rather than independent diagnostic computations |
| MMLU-Redux item-level validation | `RETIRED` | zero of 370 rows have confirmed identity |
| Controlled cross-benchmark transfer | `RESULT_REQUIRED` | no exact common-panel outputs exist |
| Human/external confirmation and repair success | `RESULT_REQUIRED` | no eligible labels or repaired benchmark execution exists |

Machine-readable ledger: `results/evidence/claim_evidence_ledger_v5.csv`.

## 6. Scientific thesis

The V5 scientific thesis is intentionally narrower and stronger: under an explicit protocol,
benchmark validity is a profile of separable threats and supporting evidence, not a synonym for
accuracy and not a single scalar certificate. Historical Study H demonstrates why diagnostic
conclusions require model, item, null, and measurement sensitivity. Controlled Study C is designed
to test whether any such conclusions transfer across exact checkpoint identities and benchmarks.

## 7. Contribution hierarchy

1. Primary: evidence-state and claim-eligibility discipline for benchmark-validity audits.
2. Primary: reproducible, uncertainty-aware multidimensional diagnostic profiles.
3. Secondary: exact-identity controlled cross-benchmark study design and fail-closed execution.
4. Secondary: secure artifact import, provenance, and post-import routing.
5. Optional ceiling extensions: blinded human validation, confirmed external labels, and a
   decoupled confirmatory synthetic study.

No optional pillar is currently empirical evidence. See
`reports/v5/VALID_EVAL_V5_CONTRIBUTION_HIERARCHY.md`.

## 8. Leakage repairs

V5 adds gold/label boundary guards, prompt and scoring contracts, provenance hashes, a controlled
overlap-candidate queue, notebook isolation checks, and release exclusions. The available local
GPQA-versus-one-MMLU-subject scan found zero candidates, but that is a partial audit and is not
evidence of no overlap or contamination.

Final leakage gate: `P0_LEAKAGE_REMAINS`. It stays closed until the full controlled item snapshots
are available, the BBH few-shot artifact is frozen and hashed, real generation/extraction boundaries
are exercised, and any overlap candidates are resolved without gold-aware repair.

## 9. Model identity and common panel

Five exact public revisions are frozen for S1:

- `Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf67be50417f59c2c2f167def9a775`
- `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- `Qwen/Qwen2.5-3B-Instruct@aa8e72537993ba99e69dfaafa59ed015b17504d1`
- `microsoft/Phi-3-mini-4k-instruct@f39ac1d28e925b323eae81227eaba4464caced4e`
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0@fe8a4ea1ffedaf415f4da2f062534de366a451e6`

The exact current panel is `5` checkpoints across `3` nominal families. The planning rule selects an
S3 target of `32` checkpoints across at least `8` families, and an S4 target of `40`/`10`. Therefore
the model gate is `COMMON_PANEL_PARTIAL`; the five-model roster is an engineering smoke panel only.

## 10. Statistical upgrades

The V5 historical analysis uses tie-aware ranks, 500 fixed-seed bootstraps, practical reversals,
top-k stability, subject/family sensitivity, and four explicit 500-simulation null protocols. The
observed tie-aware median/maximum rank range is `18.5`/`29`. Median/maximum exceedance p-values are:

| Null | Median | Maximum |
|---|---:|---:|
| Additive | 0.202 | 0.136 |
| Empirical-Bayes additive | 0.178 | 0.124 |
| Subject-size only | 0.006 | 0.044 |
| Margin permutation | 0.014 | 0.044 |

The conclusion is null-sensitive. The old severe headline is not defensible. Family-cluster
bootstrap and a justified model-bootstrap estimand remain unimplemented, so the final statistical
gate is `RANK_ANALYSIS_REQUIRES_REPAIR`.

## 11. Measurement-model plan

V5 implements a transparent regularized subject-conditioned logit decomposition and compares it
with an additive model. On the frozen historical matrix, the in-sample Brier scores are
`0.17839` versus `0.18194`, and log losses are `0.53317` versus `0.54285`. These are in-sample
descriptive comparisons, not held-out model-selection evidence. Fixture parameter recovery is
`NON_EVIDENCE_FIXTURE`. Psychometric validity, unrestricted 2PL interpretation, and construct
identification remain blocked. Gate: `MEASUREMENT_MODEL_PLAN_LIMITED`.

## 12. MMLU-Redux resolution

The V5 resolver requires content or stable shared identifiers and refuses structural or row-index
alignment. Under available artifacts, `0/370` Redux rows are confirmed and all `370` are unmatched.
The external-validation pillar is therefore `REDUX_VALIDATION_RETIRED`. It may be reconsidered only
after a lawful canonical identity source is acquired and collision/manual-review queues pass.

## 13. Benchmark contracts

Complete versioned contracts now exist for:

- MMLU at dataset revision `c30699e8356da336a370243923dbaf21066bb9fe`, 57 subjects and
  14,042 items.
- GSM8K at revision `740312add88f781978c0658806c59bc2815b9866`, 1,319 test items.
- BBH at revision `982bb89fd79532a8ac676a61fc42eb1aeec63f99`, 27 tasks and 6,511
  items.

Each contract freezes prompt, scoring, extraction, failure, and gold-isolation behavior. BBH
few-shot example content/hash and redistribution review remain blockers before S1.

## 14. Kaggle T4x2 notebooks

Six canonical notebooks under `kaggle_max_ceiling/` execute top-to-bottom in fixture mode and test
environment preflight, per-benchmark stages, deterministic validation/packaging, and optional
robustness scaffolding. Non-fixture execution deliberately returns
`CONTROLLED_GPU_EXECUTION_CONFIG_REQUIRED`; a production model/dataset/scoring runner is not wired.
No real Kaggle output exists. Gate: `KAGGLE_T4X2_FIXTURE_VALIDATED`.

## 15. Importer and router

The V5 importer fails closed on traversal, symlink, ZIP-bomb, nested archive, checksum, manifest,
schema, coverage, identity, duplicate, and conflicting-reimport failures. Fixture reimport is
idempotent. The receipt-driven router revalidates primary artifacts and only recommends analyses
whose dependencies pass; it never routes the contradicted V4 ablation. No real output ZIP has been
imported. Gate: `IMPORTER_V5_ADVERSARIAL_VALIDATED`.

## 16. Cross-benchmark build

Exact-overlap gates, matrix/metadata contracts, preregistered output tables, and descriptive
within/cross-benchmark analysis code exist. Controlled MMLU/GSM8K/BBH matrices and import receipts do
not exist, and the interaction component is descriptive rather than a fitted hierarchical model.
Gate: `CROSS_BENCHMARK_BUILD_PARTIAL`; all transfer results remain `RESULT_REQUIRED`.

## 17. Human-validation system

V5 provides blinded packet construction, a private randomization/control map, strict label import,
control checks, nominal Krippendorff alpha, bootstrap components, adjudication surfaces, and Wilson
precision planning. Fixtures pass. The sampling frame, ethics/licensing decision, reviewer
recruitment, integrated pilot, and all real labels are absent. Gate:
`HUMAN_VALIDATION_PROTOCOL_PARTIAL`.

## 18. Synthetic-validation system

Public/private generator boundaries, freeze hashes, isolation guards, and fixture execution exist.
Confirmatory mode correctly refuses to run because the generators and full frozen grid are not
implemented. No fixture result is scientific evidence. Gate: `SYNTHETIC_PROTOCOL_PREFLIGHT_ONLY`.

## 19. Runtime planner

The S1 planner records 15 `PLANNED/UNMEASURED` model-benchmark scenarios. Under explicit generic
throughput and dual-T4 utilization assumptions, the five-model, three-benchmark, 50-item smoke has
optimistic/expected/conservative total windows of `1.71/3.51/7.93` T4x2 wall-hours, including one
cached model download. The unique weight-download proxy is `22.10 GB`; the output-row proxy is
`0.0031 GB`. These are planning values, not measurements, and must be replaced after S1. S2-S5
timings remain `BLOCKED_UNTIL_S1_CALIBRATION`.

## 20. Testing and CI

The V5 validation chain covers tests, Ruff lint and format, targeted MyPy, package build, CLI
surfaces, exact MMLU reproduction, evidence ledger, leakage, Redux, panel/runtime planning,
rank/null analysis, cross preflight, human/synthetic fixtures, paper compilation, three release
profiles, and repository forensics. CI mirrors the local integrity gates. The final exact test and
command counts are recorded in section 31 and `results/v5_validation/command_ledger_v5.json`.

## 21. Paper scaffold

`paper/v5/main.tex` compiles locally. It presents only eligible historical evidence and retains
explicit placeholders for controlled, cross-benchmark, human, external, and confirmatory synthetic
results. Compilation proves document integrity only. It does not promote a blocked claim.

## 22. Release state

Source, evidence, and reviewer profiles use explicit allowlists, deterministic metadata, raw/cache
and secret exclusions, and audit manifests. Reviewer release generation is part of the final local
chain. The repository remains in unborn Git state with no immutable commit or tag, so no release may
claim code-revision reproducibility yet.

## 23. Current venue level

With existing verified MMLU evidence only, the current work is a workshop/artifact/methods-discussion
paper and is not advisable as a top-tier empirical submission. The principal fatal weaknesses are
one historical benchmark, post-hoc historical diagnostics, no controlled exact common panel, and no
external or human validation. See
`reports/v5/VALID_EVAL_V5_VENUE_CEILING_ASSESSMENT.md`.

## 24. Highest credible ceiling

The strongest plausible target after Scenario D evidence is a `STRONG_FIT` for a benchmark/data
evaluation track such as NeurIPS Evaluations & Datasets, provided the work demonstrates genuine
methodological novelty, robust uncertainty, exact common-panel execution on three benchmarks,
blinded human or confirmed external validation, current baselines, and a reproducible release. A
NeurIPS main-track paper remains `STRETCH`; the pre-execution build alone does not establish either
ceiling.

## 25. Remaining empirical blockers

1. Production model/dataset/scoring runner is not connected to notebook stages.
2. BBH few-shot examples/hash and redistribution terms are not frozen.
3. Exact common panel is 5/3, below the planned S3 32/8 target.
4. Full controlled item snapshots and cross-benchmark overlap inputs are absent.
5. Family-cluster bootstrap and a justified model-bootstrap estimand are missing.
6. No controlled MMLU, GSM8K, or BBH outputs or accepted import receipts exist.
7. Cross-benchmark interaction is not a preregistered fitted hierarchical model.
8. No integrated human pilot, real human labels, or confirmed external item identity exists.
9. Confirmatory synthetic generators/grid are not implemented.
10. Repository has no first immutable Git commit/tag.

## 26. Exact execution order

1. Preserve the current artifacts and rerun the local validation chain.
2. Implement a configuration-driven non-fixture runner behind `run_notebook_stage`.
3. Freeze/hash BBH few-shot examples, environment/package versions, and lawful-use metadata.
4. Rerun all local fixture, isolation, schema, scheduler, importer, paper, release, and forensic
   gates. Require `CONTROLLED_GPU_SMOKE_READY` before GPU use.
5. Run only S1: five pinned checkpoints, 50 items per benchmark, MMLU/GSM8K/BBH, T4x2.
6. Download ZIPs and recorded hashes; validate, import, and route locally with strict mode.
7. Recalibrate runtime/storage from accepted S1 receipts and decide S2 feasibility.
8. Run and import S2 only after a new freeze; then make the preregistered S3 roster decision.
9. Execute controlled MMLU, then GSM8K, then BBH with the exact common S3 panel.
10. Run cross-benchmark analysis only after exact-overlap and P0 leakage gates pass.
11. Run robustness and human/external/synthetic extensions only under their separate preregistrations.
12. Regenerate the evidence ledger, paper, reviewer packet, release, and final venue assessment.

## 27. Link to the single execution handbook

The only authoritative execution runbook is
`VALID_EVAL_MAXIMUM_CEILING_EXECUTION_HANDBOOK.md`. Older prompt packs, V4 execution notes, and
historical runbooks are provenance, not live operator instructions.

## 28. Allowed claims

- The frozen public Study H MMLU matrix and listed descriptive metrics were exactly reproduced.
- Under the V5 null protocols, historical subject-conditioned rank variation is null-sensitive.
- Evidence is consistent with benchmark ranking sensitivity under some diagnostics/protocols.
- The legacy pseudo-ablation is contradicted by its artifact lineage.
- MMLU-Redux validation is retired because current item identity is unconfirmed.
- V5 provides fixture-validated notebooks, an adversarially tested importer, and fail-closed evidence
  routing.
- Five exact checkpoint revisions and three benchmark dataset revisions are frozen for future Study C.
- All planning values, fixtures, and blocked states must remain visibly labeled as such.

## 29. Blocked claims

- That MMLU or any benchmark is globally invalid, worthless, contaminated, or construct-invalid.
- That rank ranges are universally or severely large under a justified null.
- That the legacy eight-family artifact is a real ablation.
- That the five-model panel is representative or meets the minimum scientific panel target.
- That controlled cross-benchmark transfer, diagnostic generalization, or benchmark repair succeeds.
- That a fixture, notebook pass, importer pass, package build, or paper compile is empirical evidence.
- That no leakage/contamination exists.
- That MMLU-Redux, human review, or synthetic validation confirms the diagnostics.
- That the paper is currently top-tier-ready or that any venue outcome is likely.

## 30. Final gates

| Gate | Verdict |
|---|---|
| Existing evidence | `EXISTING_MMLU_EVIDENCE_REPRODUCED_WITH_MAJOR_CAVEATS` |
| Leakage | `P0_LEAKAGE_REMAINS` |
| Model identity | `COMMON_PANEL_PARTIAL` |
| Statistical | `RANK_ANALYSIS_REQUIRES_REPAIR` |
| Measurement | `MEASUREMENT_MODEL_PLAN_LIMITED` |
| Redux | `REDUX_VALIDATION_RETIRED` |
| Notebook | `KAGGLE_T4X2_FIXTURE_VALIDATED` |
| Importer | `IMPORTER_V5_ADVERSARIAL_VALIDATED` |
| Cross-benchmark build | `CROSS_BENCHMARK_BUILD_PARTIAL` |
| Human protocol | `HUMAN_VALIDATION_PROTOCOL_PARTIAL` |
| Synthetic protocol | `SYNTHETIC_PROTOCOL_PREFLIGHT_ONLY` |
| Overall | `PRE_EXECUTION_BUILD_PARTIAL` |

Machine-readable source: `reports/v5/final_gates_v5.json`.

## 31. Full command ledger with exit codes

Final ledger status: `PASS`; `30/30` commands exited `0`.

| Command ID | Exit | Exact command |
|---|---:|---|
| `clean_venv_create` | 0 | `python3 -m venv --clear .venv-v5` |
| `clean_venv_pip_upgrade` | 0 | `.venv-v5/bin/python -m pip install --upgrade pip` |
| `clean_editable_install` | 0 | `.venv-v5/bin/python -m pip install -e '.[dev]'` |
| `clean_environment_tests` | 0 | `.venv-v5/bin/python -m pytest -q` |
| `full_tests` | 0 | `python3 -m pytest -q` |
| `lint` | 0 | `python3 -m ruff check .` |
| `format_check` | 0 | `python3 -m ruff format --check .` |
| `type_check` | 0 | `python3 -m mypy src/valideval/evidence src/valideval/execution src/valideval/importers/kaggle_v5.py src/valideval/importers/post_import_v5.py src/valideval/cross_benchmark src/valideval/planning src/valideval/statistics/rank_materiality.py src/valideval/statistics/rank_nulls.py src/valideval/measurement src/valideval/leakage src/valideval/synthetic src/valideval/external_labels src/valideval/human` |
| `package_build` | 0 | `python3 -m build` |
| `cli_help` | 0 | `python3 -m valideval --help` |
| `cli_doctor` | 0 | `python3 -m valideval doctor --help` |
| `mmlu_reproduction` | 0 | `python3 scripts/reproduce_mmlu_evidence_v5.py` |
| `claim_ledger` | 0 | `python3 scripts/build_claim_evidence_ledger_v5.py` |
| `leakage_audit` | 0 | `python3 scripts/build_leakage_audit_v5.py` |
| `redux_identity_resolution` | 0 | `python3 scripts/resolve_mmlu_redux_v5.py` |
| `panel_power_planner` | 0 | `python3 scripts/build_common_panel_plan_v5.py` |
| `runtime_planner` | 0 | `python3 scripts/estimate_execution_runtime_v5.py` |
| `rank_materiality` | 0 | `python3 scripts/run_mmlu_rank_materiality_v5.py --matrix cache/mmlu/wide/matrix.csv --model-family-map configs/models/study_h_family_map_v5.csv --bootstrap 500 --null-simulations 500 --output results/mmlu/rank_materiality_v5` |
| `cross_benchmark_preflight` | 0 | `python3 scripts/run_cross_benchmark_v5.py` |
| `human_protocol_dry_run` | 0 | `python3 scripts/build_blinded_human_packet_v5.py --dry-run` |
| `synthetic_fixture` | 0 | `python3 scripts/run_confirmatory_synthetic_v5.py --mode fixture` |
| `paper_assets` | 0 | `python3 scripts/build_paper_v5_assets.py` |
| `paper_pdflatex_1` | 0 | `pdflatex -interaction=nonstopmode -halt-on-error main.tex` |
| `paper_bibtex` | 0 | `bibtex main` |
| `paper_pdflatex_2` | 0 | `pdflatex -interaction=nonstopmode -halt-on-error main.tex` |
| `paper_pdflatex_3` | 0 | `pdflatex -interaction=nonstopmode -halt-on-error main.tex` |
| `source_release_dry_run` | 0 | `python3 scripts/build_release_v5.py --profile source` |
| `evidence_release_dry_run` | 0 | `python3 scripts/build_release_v5.py --profile evidence` |
| `reviewer_release_build` | 0 | `python3 scripts/build_release_v5.py --profile reviewer --build` |
| `repository_forensics` | 0 | `python3 scripts/build_repository_forensics_v5.py` |

The lossless ledger, including timestamps, durations, and stdout/stderr tails, is
`results/v5_validation/command_ledger_v5.json`; its rendered companion is
`results/v5_validation/command_ledger_v5.md`. Both test lanes report `305 passed`, `0 failed`,
`0 skipped`, and two known V4 constant-input warnings.

## 32. Files added, modified, deprecated, or moved

The repository began as an unborn Git worktree with no tracked baseline, so Git cannot distinguish
added from modified files. The exact combined pass-scope count is `240` files since
`2026-07-15 18:44:00` local time. The count excludes `.git`, `.venv-v5`, caches, build/dist,
`*.egg-info`, `.DS_Store`, Python bytecode, and transient LaTeX auxiliary files. It includes source,
tests, maintained reports/results, paper PDF, release audits, handbook, handoff, and machine state.

Known new V5 surfaces include the evidence/reproduction ledger, leakage guards, exact registries and
contracts, rank/materiality and measurement analysis, power/runtime planners, execution schema and
scheduler, six notebooks, V5 importer/router, cross-benchmark scaffold, human/synthetic protocols,
paper V5, release/forensics/validation builders, reports, handbook, handoff, and machine state.
`FINAL_V4_PRE_EXECUTION_GATE.md` is deprecated as `SUPERSEDED_BY_V5`; historical files were not
deleted or moved to manufacture cleanliness.

## 33. Instructions for the next agent after outputs return

1. Do not trust ZIP names or notebook success messages. Record the original path and SHA-256, then
   run strict `validate-run`, `import-kaggle`, and `post-import` exactly as specified in the handbook.
2. Verify import receipts, checkpoint revisions, dataset/config hashes, planned row coverage,
   extraction reliability, failure taxonomy, and absence of conflicts before analysis.
3. Keep Study H and Study C separate. Never route V4 ablation or unconfirmed Redux rows.
4. Rebuild the claim/evidence ledger from primary imported artifacts; do not hand-promote statuses.
5. If any model/benchmark is missing, any hash drifts, or P0 leakage remains, stop confirmatory
   analysis and issue an exact blocker. Do not impute or silently reduce the common panel.
6. Recalibrate runtime from S1 only; do not reuse current planning assumptions as measurements.
7. After accepted S3 outputs, run the exact-overlap gate and the preregistered within/cross analysis,
   then update paper placeholders only for claims whose eligibility is `PAPER_ELIGIBLE`.
8. Rerun the complete local validation, regenerate `VALID_EVAL_V5_MACHINE_STATE.json`, rebuild the
   reviewer release, and update the venue assessment before declaring a new gate.

Exact next action: do **not** launch Kaggle. Implement and fixture-test the production runner behind
`run_notebook_stage`, freeze/hash the BBH few-shot artifact and package environment, and rerun
`python3 scripts/run_v5_local_validation.py`. Only a resulting `CONTROLLED_GPU_SMOKE_READY` gate may
authorize the five-checkpoint S1 engineering smoke.
