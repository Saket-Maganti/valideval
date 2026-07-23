# NeurIPS Submission Go/No-Go

Decision values:

- `SUBMIT_NEURIPS_READY`
- `BORDERLINE_NEEDS_REVISION`
- `WORKSHOP_FIRST`
- `TMLR_FIRST`
- `NOT_READY`

Current default decision after final venue gate: `WORKSHOP_FIRST`.

Rationale: the active MMLU panel-size blocker is cleared for the reconciled
39-model HELM MMLU wide matrix, proxy IRT artifacts exist, real-panel
ranking/disagreement artifacts now exist, the paper compiles, and a
reviewer-safe packet was rebuilt. The strongest current real-panel finding is
subject-level rank sensitivity under the active MMLU panel.

The project is still not NeurIPS-ready: MMLU-Redux remains weak/negative under
structural alignment, direct/hash MMLU-Redux alignment is not confirmed,
decoupled synthetic validation remains blocked/`RESULT_REQUIRED`,
second-benchmark evidence remains `RESULT_REQUIRED`, full 2PL remains
`RESULT_REQUIRED`, and related work/bibliography polish remains incomplete.

Final venue gate: `WORKSHOP_READY_ONLY` in
`FINAL_SUBMISSION_GATE_AND_VENUE_STRATEGY.md`.
