# Master Later Run Plan

## Do-not-run-together rule

Do not execute all evidence families in one mega batch. Each run needs a separate command, expected
runtime, inputs, preflight status, evidence state before, claim state before, stop rule, and explicit
user approval.

## Priority order

1. One focused real-panel finding run
2. Preregistered confirmatory cross-flaw
3. Preregistered confirmatory held-out
4. Calibration/logprob analysis
5. Power/materiality analysis
6. Second benchmark

## Approval requirement

Every item above remains blocked until the user explicitly authorizes that specific run.
