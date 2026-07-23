# Prompt 15 — Bibliography and Citation Repair

## Objective

Fix the bibliography/citation blocker. This is mandatory before serious venue claims.

## Tasks

1. Inspect `paper/main.tex` for citation commands.
2. Populate `paper/references.bib` with real references already known in repo docs or paper notes.
3. Add citations for:
   - construct validity / measurement validity,
   - IRT / psychometrics,
   - HELM,
   - MMLU,
   - MMLU-Redux,
   - LLM evaluation,
   - benchmark contamination/reliability,
   - evaluation uncertainty/ranking instability.
4. Compile with bibtex.
5. Fix unresolved citations/references.

## Do not

Do not invent citations. If uncertain, mark a citation TODO.

## Commands

```bash
cd paper && pdflatex -interaction=nonstopmode main.tex
cd paper && bibtex main
cd paper && pdflatex -interaction=nonstopmode main.tex
cd paper && pdflatex -interaction=nonstopmode main.tex
```

## Output

```text
BIBLIOGRAPHY_AND_CITATION_REPAIR_V3_REPORT.md
```

## Final verdict

```text
BIBLIOGRAPHY_COMPILES_CLEAN
BIBLIOGRAPHY_PARTIAL_NEEDS_HUMAN_REVIEW
BIBLIOGRAPHY_BLOCKED
```
