# ValidEval V7.2 Final Pre-Kaggle Handoff

## 1. Verdict

`VALID_EVAL_V7_2_KAGGLE_S1_AUTHORIZED`. This authorizes the exact engineering smoke, not a real
accepted S1 or any scientific claim.

## 2. V7.1 baseline

Source `f4f803a01daf89798d4b181e5610ce3f70355f32` and metadata child
`a649f664a884404afb889aedfe35f579dcf3f3fa` are preserved. The failed V7 primary grid is unchanged.

## 3. S1 bridge

Three native V7.2 configs and five canonical Kaggle notebooks use one package implementation.

## 4. Provenance

The source tag, commit, config hashes, revisions, prompt contracts, subsets, and archive checksums
are fail-closed.

## 5. Claim-policy vacuity

V7.1 full licensing remains the zero-power, 100%-abstention baseline.

## 6. Policy development

Development/validation are disjoint; `HIGH_COVERAGE` was selected.

## 7. Pareto frontier

Dominated candidates were excluded on false licenses, power, abstention, and regret.

## 8. Policy confirmation

`CLAIM_POLICY_CONFIRMATION_PASS`: false licenses 0.0255, power
0.4563, abstention 0.8304, regret
0.0185.

## 9. Effective-N

`EFFECTIVE_N_STRESS_PASS`.

## 10. Family dependence

`FAMILY_DEPENDENCE_STRESS_PASS`.

## 11. Selective decisions

`SELECTIVE_DECISION_USEFUL_FRONTIER`.

## 12. Difficulty confound

`DIFFICULTY_CONFOUND_CHARACTERIZED`; historical AUPRC 0.439069.

## 13. V8 exploratory result

`V8_EXPLORATORY_IMPROVEMENT_FOUND`; V8 confirmation was not run or authorized.

## 14. MMLU adjusted diagnostics

Zero licensed discoveries; external labels, item length, and answer position were unavailable.

## 15. Synthetic boundaries

All policy and V8 results are generator-scoped. They do not prove behavior on real benchmarks.

## 16. Authorization

S1 run authorized; S2 blocked pending accepted S1; S3 blocked pending S2; S4 blocked pending S3.

## 17. Compute

Fourteen mandatory CPU activities produced artifacts under `results/v7_2`.

## 18. Tests and CI

Validation status: `PASS`. See machine state for
individual test, lint, format, type, build, notebook, secret, release, and CI results.

## 19. Exact Kaggle instructions

Follow `VALID_EVAL_V7_2_KAGGLE_S1_RUNBOOK.md`. Start with
`kaggle_icml2027/00_v7_2_t4x2_preflight.ipynb`.

## 20. Remaining blockers

No real accepted S1, S2, S3, S4, V8 confirmation, transport validation, or human validation exists.

## 21. Exact next action

Check out `valideval-v7.2-icml2027-kaggle-s1-ready`, run notebook 00 on Kaggle T4×2, and stop if its exact-source,
CUDA, disk, model, dataset, prompt, or subset preflight fails.
