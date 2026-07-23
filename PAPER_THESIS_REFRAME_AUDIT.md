# Paper Thesis Reframe Audit

## Executive summary

The paper-facing thesis is: ValidEval validates validity diagnostics before they license
benchmark-validity claims. This is a claim-gating and diagnostic-validation paper, not a broad
leaderboard/product paper.

## Old risky framing

Risky framing would imply generic MMLU error-detection success, that MMLU-Redux validation succeeded,
that cross-flaw or held-out validation is solved, or that synthetic validation establishes real
benchmark validity.

## New thesis

Benchmark-validity diagnostics are measurement instruments. They require evidence about sensitivity,
specificity, false-positive behavior, uncertainty, materiality, and transfer before they support
benchmark-validity claims.

## Files reviewed

`paper/abstract.md`, `paper/introduction.md`, `paper/experiments.md`,
`paper/diagnostic_validation.md`, `paper/limitations.md`, `paper/claims.md`,
`paper/related_work.md`, `paper/main.tex`, `paper/sections/`, `CLAIMS_LEDGER_NEURIPS.md`,
`MMLU_EVIDENCE_GATE_REPORT.md`, and `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`.

## Edits made

This pass added durable no-run state locking, real-panel dry-run scaffolds, and README/claim pointers
that preserve the existing thesis without upgrading evidence states.

## Claims allowed

- Controlled synthetic validation is generator-scoped.
- Cross-flaw and held-out artifacts expose mixed/weak behavior.
- MMLU-Redux is a weak/negative external stress test.
- The 39-model HELM MMLU panel is a real-panel substrate.
- Real-panel ranking/finding remains `[RESULT REQUIRED]`.

## Claims blocked

- Generic MMLU error-detection success.
- MMLU-Redux validation succeeded.
- Cross-flaw or held-out transfer is solved.
- Synthetic validation establishes real validity.
- Certificates, badges, domain packs, predictive diagnostics, or Goodhart diagnostics are validated
  NeurIPS contributions.

## Remaining `[RESULT REQUIRED]`

Real-panel findings, confirmatory cross-flaw, confirmatory held-out transfer, calibration/logprob
analysis, power/materiality analysis, and a second benchmark remain result-required.

## Reviewer risks

The main risk is overreading scaffolds and dry-run manifests as evidence. Every new preflight added
in this pass records `mode: dry_run_only`.

## Next build step

Run the targeted no-run tests and keep reviewer-packet scope slim before any future approved run.
