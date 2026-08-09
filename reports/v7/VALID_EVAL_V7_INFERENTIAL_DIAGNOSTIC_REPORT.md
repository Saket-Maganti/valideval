# ValidEval V7 Inferential Diagnostic Report

Gate: `INFERENTIAL_DIAGNOSTICS_READY`; substantive discovery gate: `NO_DISCOVERIES`.

The analysis used 39 historical checkpoints, 10 inferred
families, and 14042 MMLU items. Each negative-discrimination estimate uses a
leave-one-item ability score, family-clustered bootstrap uncertainty (500
draws), a permutation null (500 draws), BH control, BY sensitivity, and a
predeclared 0.80 stability threshold.

Results: BH flags = 0, BY flags = 0, and stable
FDR-controlled flags = 0. The correct conclusion is not that MMLU
contains no flawed items. Under this diagnostic, panel, and null, no item supports the narrow
anti-discrimination claim after multiplicity and stability control. Causes would in any event need
independent validation.

Runtime: 7.80 seconds. Backing table:
`results/v7/diagnostics/item_inferential_diagnostics.csv`.
