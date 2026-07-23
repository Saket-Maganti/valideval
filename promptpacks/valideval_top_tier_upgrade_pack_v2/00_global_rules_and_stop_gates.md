# Prompt 00 — Global Rules and Stop Gates for Top-Tier Upgrade V2

You are working inside:

```text
/Users/saketmaganti/Projects/Valideval
```

## Goal

Upgrade ValidEval from `WORKSHOP_READY_ONLY` toward a serious top-tier candidate by adding real empirical evidence, stronger validation, better psychometrics, multi-benchmark coverage, and paper-quality artifacts.

## Current known state

- Active MMLU panel: 39-model HELM MMLU wide matrix.
- Panel validity: pass.
- Proxy IRT artifacts: exist.
- Ranking/disagreement: artifact-backed for MMLU.
- MMLU-Redux: weak/negative; direct/hash alignment blocked.
- Legacy synthetic AUCs: demoted to wiring/sanity-check only.
- Decoupled synthetic validation: blocked / result-required.
- Second benchmark: missing.
- Final venue gate: workshop-ready only.

## Hard rules

Do not fabricate results.
Do not hide failures.
Do not treat failed or blocked runs as success.
Do not upgrade evidence states without artifacts.
Do not claim MMLU error detection unless direct validation supports it.
Do not claim MMLU is valid or invalid.
Do not claim full 2PL unless actually run.
Do not treat proxy IRT as full IRT.
Do not treat legacy synthetic validation as diagnostic evidence.
Do not claim second-benchmark evidence unless the run actually completes.
Do not claim NeurIPS or D&B readiness unless final gate passes.

## Allowed

- Real MMLU analyses.
- Real public-artifact analyses.
- Kaggle notebook generation.
- Kaggle output import and validation.
- lm-eval-harness runner setup.
- multi-benchmark matrices.
- bootstrap/materiality/uncertainty.
- ranking sensitivity and cross-benchmark stability.
- direct/hash alignment attempts.
- human-review queue construction.
- paper/PDF/reviewer packet rebuild.

## Stop gates

Stop or mark blocked if:

- active matrix has fewer than 30 models,
- missing raw artifacts prevent direct/hash alignment,
- Kaggle outputs are absent for import prompt,
- command fails and no minimal honest implementation is possible,
- results contradict the desired thesis,
- paper still has unresolved citations or placeholders at final gate.

## Required final response for every prompt

```markdown
## Summary
## Commands run
## Artifacts created/modified
## Evidence changes
## Claims allowed
## Claims still blocked
## Failures/blockers
## Verification
## Next prompt
```
