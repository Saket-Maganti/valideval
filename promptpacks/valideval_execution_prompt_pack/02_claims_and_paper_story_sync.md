# Prompt 02 — Claims and Paper Story Sync

Run after `VALID_EVAL_EVIDENCE_RECONCILIATION_AUDIT.md`.

## Objective

Sync paper, claims ledgers, README, and reviewer-facing docs with the true evidence state.

## Read

```text
VALID_EVAL_EVIDENCE_RECONCILIATION_AUDIT.md
SYNTHETIC_HARNESS_CIRCULARITY_AUDIT.md
DECOUPLED_SYNTHETIC_PROTOCOL_AUDIT.md
DECOUPLED_SYNTHETIC_PREREGISTERED_EXECUTION_MANIFEST.md
REAL_EMPIRICAL_SPINE_REFRAME.md
MMLU_REDUX_WEAK_SIGNAL_DIAGNOSIS.md
CLAIMS_LEDGER_NEURIPS.md
paper/CLAIMS_LEDGER.md
paper/claims.md
paper/experiments.md
paper/diagnostic_validation.md
paper/results.md
paper/limitations.md
paper/reframed_abstract_negative_result.md
paper/reframed_intro_negative_result.md
README.md
NEURIPS_SUBMISSION_GO_NO_GO.md
```

## Required story

The paper should be a measurement-science/cautionary paper, not a giant toolkit pitch:

```text
Benchmark-validity diagnostics are often treated as if they license benchmark-quality claims, but their own validity is rarely tested. ValidEval provides a disciplined audit framework and, in its current strongest real stress test, matrix-derived diagnostics on a wide HELM MMLU panel do not robustly recover independently documented MMLU-Redux issue labels. Diagnostic claims must be gated, externally validated, and separated from software sanity checks.
```

## Required demotions

Ensure docs say:

- legacy synthetic AUCs are wiring/sanity-check artifacts only,
- decoupled synthetic validation is pending or artifact-backed only if run,
- MMLU-Redux is weak/negative unless future validation changes it,
- real-panel ranking/disagreement is pending unless run,
- no detection-success claim is allowed,
- no broad GPQA validity claim is allowed if panel signal is chance-level.

## Create/update

```text
paper/current_thesis.md
paper/current_evidence_state.md
paper/current_claims_allowed_blocked.md
CLAIMS_AND_STORY_SYNC_AUDIT.md
```

Audit structure:

```markdown
# Claims and Paper Story Sync Audit

## 1. Executive Summary
## 2. Evidence State Used
## 3. Claims Allowed
## 4. Claims Blocked
## 5. Paper Story After Sync
## 6. Files Updated
## 7. Stale Claims Removed
## 8. Remaining Result Required Placeholders
## 9. Final Verdict
```

Final verdict:

```text
CLAIMS_SYNC_READY
CLAIMS_SYNC_NEEDS_FIXES
CLAIMS_SYNC_BLOCKED
```

## Verification

```bash
rg "primary positive evidence|10/12 credible|detects MMLU errors|synthetic validation proves|MMLU is invalid" paper *.md src tests || true
ruff check .
```
