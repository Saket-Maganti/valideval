# Prompt 12 — Paper Rewrite, Appendix, and PDF Compilation

## Objective

Produce a polished paper draft centered on real evidence and honest gates.

## Recommended title direction

```text
Who Validates the Validators? A Measurement-Science Audit of Benchmark-Validity Diagnostics
```

## Core thesis

- benchmark validity diagnostics are measurement instruments,
- their outputs require validation before licensing claims,
- legacy synthetic wiring checks are not evidence,
- HELM/MMLU + MMLU-Redux is the real empirical spine,
- decoupled synthetic validation is included only if executed,
- ValidEval contributes claim-gated infrastructure plus a cautionary empirical finding.

## Read

```text
paper/current_thesis.md
paper/current_evidence_state.md
paper/current_claims_allowed_blocked.md
ARTIFACT_MANIFEST_FOR_PAPER.md
FIGURE_TABLE_COMPLETENESS_AUDIT.md
CLAIMS_LEDGER_NEURIPS.md
paper/CLAIMS_LEDGER.md
REAL_EMPIRICAL_SPINE_REFRAME.md
MMLU_REAL_PANEL_CORE_RUN_REPORT.md
MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md
MMLU_IRT_PSYCHOMETRIC_RUN_REPORT.md
MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md
DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md
```

## Rewrite/update

```text
paper/abstract.md
paper/introduction.md
paper/related_work.md
paper/method.md
paper/experiments.md
paper/results.md
paper/discussion.md
paper/limitations.md
paper/ethics.md
paper/claims.md
paper/main.tex
```

If LaTeX section files exist, update those instead.

## Appendices

Create/update:

```text
paper/appendices/evidence_state_appendix.md
paper/appendices/mmlu_panel_appendix.md
paper/appendices/mmlu_redux_appendix.md
paper/appendices/synthetic_demotion_appendix.md
paper/appendices/decoupled_synthetic_protocol_appendix.md
paper/appendices/reproducibility_appendix.md
```

## Compile

Try:

```bash
cd paper && latexmk -pdf main.tex
```

Fallback:

```bash
cd paper && pdflatex -interaction=nonstopmode main.tex
cd paper && bibtex main || true
cd paper && pdflatex -interaction=nonstopmode main.tex
cd paper && pdflatex -interaction=nonstopmode main.tex
```

## Report

```text
PAPER_REWRITE_AND_COMPILE_REPORT.md
```

Final verdict:

```text
PAPER_COMPILED_READY_FOR_REVIEW
PAPER_COMPILED_BUT_PLACEHOLDERS_REMAIN
PAPER_COMPILE_BLOCKED
```

## Verification

```bash
ruff check .
python3 -m pytest -q
```
