# Paper Rewrite and Compile Report

## Executive Summary

The paper draft was rewritten around the current artifact-backed evidence state and compiled successfully to `paper/main.pdf` using the `pdflatex` fallback. `latexmk` is not installed in this environment.

Final verdict: `PAPER_COMPILED_BUT_PLACEHOLDERS_REMAIN`

## Files Updated

- `paper/main.tex`
- `paper/abstract.md`
- `paper/introduction.md`
- `paper/experiments.md`
- `paper/results.md`
- `paper/discussion.md`
- `paper/limitations.md`
- `paper/ethics.md`
- `paper/claims.md`
- `paper/sections/01_introduction.tex`
- `paper/sections/03_validity_framework.tex`
- `paper/sections/04_toolkit.tex`
- `paper/sections/05_audit_protocol.tex`
- `paper/sections/06_results.tex`
- `paper/sections/07_analysis.tex`
- `paper/sections/08_limitations.tex`
- `paper/sections/09_ethics_broader_impact.tex`
- `paper/sections/10_conclusion.tex`

## Appendices Created

- `paper/appendices/evidence_state_appendix.md`
- `paper/appendices/mmlu_panel_appendix.md`
- `paper/appendices/mmlu_redux_appendix.md`
- `paper/appendices/synthetic_demotion_appendix.md`
- `paper/appendices/decoupled_synthetic_protocol_appendix.md`
- `paper/appendices/reproducibility_appendix.md`

## Compile Commands

- `cd paper && latexmk -pdf main.tex`: blocked, `latexmk` not installed.
- `cd paper && pdflatex -interaction=nonstopmode main.tex && bibtex main || true && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex`: completed.

## PDF

- `paper/main.pdf`
- Pages: 6
- Size: 181,764 bytes

## Warnings

- Minor overfull hbox warnings remain.
- BibTeX reports no citation commands and an empty bibliography environment.
- Direct/hash Redux validation, decoupled synthetic validation, second-benchmark evidence, and full 2PL remain unresolved gates.

## Claims Preserved

- Active MMLU panel is 39-model HELM MMLU wide matrix.
- Subject-level rank sensitivity is artifact-backed.
- Proxy IRT exists but full 2PL is not claimed.
- MMLU-Redux is weak/negative and direct/hash blocked.
- Second benchmark and decoupled synthetic validation remain `RESULT_REQUIRED`.
- NeurIPS readiness remains blocked.

## Final Verdict

`PAPER_COMPILED_BUT_PLACEHOLDERS_REMAIN`
