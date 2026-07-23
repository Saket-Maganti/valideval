# Prompt 00 — Global Execution Rules

You are working inside:

```text
/Users/saketmaganti/Projects/Valideval
```

You may run analyses in this prompt pack, but every run must be evidence-safe.

## Non-negotiable rules

Do not fabricate results.  
Do not silently upgrade evidence states.  
Do not claim detection success unless a real artifact supports it.  
Do not treat legacy synthetic AUCs as diagnostic-validation evidence.  
Do not expose raw benchmark text in reviewer-facing reports.  
Do not overwrite raw/cache artifacts without backup.  
Do not commit giant raw files unless explicitly approved.

## Allowed

- evidence reconciliation,
- shape checks,
- public-artifact analysis,
- CPU analyses,
- IRT/proxy psychometric runs,
- MMLU-Redux direct/hash alignment attempts,
- real-panel ranking and disagreement analyses,
- decoupled synthetic execution only after guards pass,
- Kaggle notebook generation,
- Kaggle output import,
- paper table/figure generation,
- PDF compilation,
- reviewer ZIP rebuild.

## Forbidden claims unless proven

- “ValidEval detects MMLU errors.”
- “MMLU is invalid.”
- “synthetic validation proves diagnostic validity.”
- “legacy synthetic results validate diagnostics.”
- “ranking flips exist” unless a result artifact shows them.
- “the 39-model panel exists” unless actual files are inspected.
- “full IRT was run” unless the artifact exists.
- “NeurIPS-ready” unless the final gate says so.

## Evidence-state defaults

- Legacy synthetic AUCs: `DEMOTED_TO_WIRING_CHECK`.
- Decoupled synthetic validation: `RESULT_REQUIRED` until executed.
- MMLU-Redux detection success: blocked unless validated.
- Real-panel ranking/disagreement: `RESULT_REQUIRED` until run.
- Calibration/logprob: blocked or `RESULT_REQUIRED` until run.
- Second benchmark: `RESULT_REQUIRED` until run.

## Required final response format

```markdown
## Summary
## Commands run
## Artifacts created/modified
## Evidence changes
## Claims allowed
## Claims still blocked
## Failures or blockers
## Verification
## Next recommended prompt
```
