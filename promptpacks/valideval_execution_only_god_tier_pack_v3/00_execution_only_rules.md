# Prompt 00 — Execution-Only Rules

You are working in:

```text
/Users/saketmaganti/Projects/Valideval
```

## Objective

This pack is execution-only. Build only what directly unblocks real evidence.

## Hard rules

- Do not fabricate results.
- Do not fabricate Kaggle/Colab outputs.
- Do not create fake human labels.
- Do not treat a notebook/runbook as evidence.
- Do not treat a blocked import as a benchmark run.
- Do not claim top-tier readiness without the final gate.
- Do not claim MMLU/GSM8K/BBH validity or invalidity.
- Do not claim benchmark item errors without human/external labels.
- Do not treat approximate IRT as full 2PL.
- Preserve blocked states honestly.

## Evidence upgrade contract

### GSM8K evidence is real only if:

- a real output ZIP or predictions file exists,
- schema validation passes,
- matrix is built,
- panel validity is reported,
- diagnostics produce artifacts.

### Cross-benchmark evidence is real only if:

- MMLU + GSM8K matrices exist,
- model overlap/mapping is documented,
- rank/ability/diagnostic comparisons produce artifacts.

### Human label evidence is real only if:

- actual labels are supplied,
- schema validates,
- item IDs match the review queue,
- labels are sanitized.

## Required final response format

```markdown
## Summary
## Real execution performed
## Commands run
## Artifacts created/modified
## Evidence changed
## Claims allowed
## Claims still blocked
## Failures/blockers
## Verification
## Next action
```
