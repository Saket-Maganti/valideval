# Codex Prompt — 05 Real-Panel Figures and Tables Templates

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Create publication-ready templates with no fake values.

Create:
- `paper/tables/real_panel_ranking_audit_template.tex`
- `paper/tables/diagnostic_disagreement_template.tex`
- `paper/tables/subject_instability_template.tex`
- `paper/tables/baseline_comparison_template.tex`
- `paper/figures/README_REAL_PANEL_FIGURES.md`
- `templates/reports/REAL_PANEL_FINDING_SUMMARY_TEMPLATE.md`
- `templates/reports/REAL_PANEL_RANKING_AUDIT_TEMPLATE.md`
- `templates/reports/DIAGNOSTIC_DISAGREEMENT_AUDIT_TEMPLATE.md`
- `templates/reports/SUBJECT_INSTABILITY_AUDIT_TEMPLATE.md`
- `REAL_PANEL_FIGURE_TABLE_TEMPLATE_AUDIT.md`

Every template must use `[RESULT REQUIRED]`.

Document future figures:
1. accuracy-only vs validity-adjusted ranking scatter,
2. rank shift bar plot,
3. diagnostic disagreement heatmap,
4. subject instability heatmap,
5. suspicious-item subset effect plot,
6. MMLU-Redux weak/negative summary,
7. synthetic cross-flaw/held-out evidence-state figure.

Do not compile unless placeholders are known safe.

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```
