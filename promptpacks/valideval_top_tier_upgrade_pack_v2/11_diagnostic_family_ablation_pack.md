# Prompt 11 — Diagnostic Family Ablation Pack

## Objective

Avoid “one magic diagnostic” claims by showing how conclusions change across diagnostic families.

## Analyses

Run ranking/disagreement/materiality with:

1. accuracy only,
2. proxy IRT only,
3. difficulty flags only,
4. low-discrimination flags only,
5. negative-discrimination flags only,
6. subject instability only,
7. combined diagnostics,
8. random diagnostic baseline.

## Outputs

```text
results/mmlu/diagnostic_family_ablation/
paper/figures/diagnostic_family_ablation.pdf
paper/tables/diagnostic_family_ablation.csv
```

## Report

```text
DIAGNOSTIC_FAMILY_ABLATION_REPORT.md
```

Final verdict:

```text
DIAGNOSTIC_ABLATION_COMPLETE
DIAGNOSTIC_ABLATION_WEAK_EFFECTS
DIAGNOSTIC_ABLATION_BLOCKED
```
