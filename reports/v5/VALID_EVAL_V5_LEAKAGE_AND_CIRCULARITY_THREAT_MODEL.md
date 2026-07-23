# ValidEval V5 Leakage and Circularity Threat Model

## Gate verdict

**Status: `LEAKAGE_GUARDS_PARTIAL`; the P0 execution gate is `BLOCKED`.** The local fail-closed
guards and their adversarial tests are `REPRODUCED`, and the controlled MMLU, GSM8K, and BBH
contracts pin repository revisions, splits, and expected counts. Their full canonical item
records and content manifests are not materialized locally, and the BBH few-shot manifest is
not frozen. Consequently, the required three-benchmark overlap scan has not run and the V5 P0
leakage gate cannot pass.

Machine-readable state: `results/leakage/leakage_checks_v5.json`.

## Threat register

| Threat | Failure mode | V5 control | Current state | Gate consequence |
|---|---|---|---|---|
| Benchmark split leakage | Train, validation, test, source, rationale, template, subtask, or semantic overlap inflates apparent transfer | Exact normalized hashes, ordered-option hashes, option-set hashes, token n-gram candidates, bounded manual-review queue | `BLOCKED`: revisions are pinned, but full controlled rows are not local and the BBH few-shot hash is not frozen | P0; must close before S1 or higher |
| Gold-answer leakage | Gold, correctness, reward, or retry feedback reaches generation or extraction | `build_generation_payload`, recursive forbidden-key checks, target/few-shot overlap rejection, explicit extraction failures | `REPRODUCED` in adversarial tests | Closed at tested code boundary; runners must use that boundary |
| Diagnostic-label leakage | External, human, flaw, repair, or synthetic labels influence diagnostic scores or thresholds | Recursive label-field rejection and neutral artifact-path checks | `REPRODUCED` in adversarial tests | Closed at tested input boundary; future feature paths remain auditable |
| Synthetic circularity | Generator branch, schema, metadata, filename, seed, order, or severity encodes the injected flaw | Private-label boundary, negative/no-flaw controls, held-out-family protocol, preregistered endpoints | Guard fixtures `REPRODUCED`; confirmatory study `PLANNED` | Fixtures are `NON_EVIDENCE_FIXTURE`, never detector validation |
| Cross-benchmark identity leakage | Family names or aliases are treated as the same checkpoint | Full checkpoint/revision/execution-identity comparison | Five Study C checkpoint revisions frozen; run identity remains `PLANNED` | Family-only transfer is blocked |
| Post-selection leakage | Thresholds, subsets, nulls, diagnostics, or figures are chosen after outcomes | Frozen V5 hypotheses, endpoints, multiplicity, exclusions, seeds, and threshold policy | Config `VERIFIED_FROM_PRIMARY_ARTIFACT`; future results `PLANNED` | Any deviation requires a labeled amendment |
| Human-review leakage | Raters see diagnostic rank, correctness pattern, risk selection, external labels, or hypothesis | Blinded randomized packets and controls | Protocol built elsewhere; real labels `BLOCKED` | Human-validation claims remain blocked |
| Model pretraining contamination | Benchmark content was present in model training | No repository-only test can prove absence | `BLOCKED` as an unresolved limitation | Must not be described as solved or conflated with pipeline leakage |

## Cross-benchmark overlap protocol

For each frozen benchmark split, the scan must compare canonical item records in this order:

1. exact normalized question hash;
2. question plus ordered-options hash;
3. question plus option-set hash to detect permutations;
4. exact rationale and repeated-template hashes where applicable;
5. token 3-gram candidate retrieval;
6. locally feasible MinHash or embedding retrieval;
7. blinded manual adjudication of high-confidence candidates.

The locally available GPQA Diamond (198 rows) and MMLU high-school biology subset (310 rows)
were scanned as a partial code-path exercise, producing zero candidates. The input hashes and
scope are recorded in `results/leakage/leakage_checks_v5.json`. The corresponding CSV contains
only its header. That zero applies only to the two local subsets and is not evidence of zero
overlap among full controlled MMLU, GSM8K, and BBH.

## Gold and diagnostic isolation boundary

Only public item fields may cross into model generation. The scorer may access the answer
only after the generation artifact is frozen. Extraction cannot use the expected answer to
select or repair a candidate, and a failed extraction must preserve `prediction=null` plus a
separate failure type. Diagnostics reject nested gold, human, external, synthetic, and repair
labels as well as filenames that reveal class membership.

These controls were exercised in the focused 41-test scientific validation; all 41 passed.
Passing those tests establishes behavior of the tested code paths, not absence of leakage in
an unexecuted notebook or future third-party runner.

## Contamination taxonomy

- **Model pretraining contamination:** unresolved and generally not provable here.
- **Project-pipeline leakage:** guarded locally, but must be rechecked against imported run
  manifests.
- **Benchmark split leakage:** contracts are pinned, but the gate is `BLOCKED` until their
  datasets and few-shot records are materialized, content-verified, and scanned.
- **Label leakage:** guarded locally; any label-informed threshold requires a development split
  or nested validation and a frozen confirmatory evaluation.

## Allowed and blocked statements

Allowed: “The tested V5 generation, extraction, diagnostic-input, and synthetic-fixture
boundaries fail closed under the current adversarial tests.”

Blocked: “The controlled study is leakage-free,” “the benchmarks do not overlap,” and “the
models were not contaminated during pretraining.”

## Exact next action

Materialize the pinned MMLU, GSM8K, and BBH revisions without running inference; verify their
content manifests; freeze the BBH few-shot manifest; execute the exact, option-aware,
permutation, and token-ngram overlap scan; then adjudicate every high-confidence candidate
before S1 execution.
