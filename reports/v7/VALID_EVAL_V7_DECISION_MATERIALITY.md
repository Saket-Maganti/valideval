# ValidEval V7 Decision Materiality

Gate: `DECISION_MATERIALITY_READY` for the historical MMLU panel.

Selective ranking returns directional comparisons only when the 95% interval excludes zero and the
0.01 materiality threshold; otherwise it returns equivalence or insufficient evidence. Across the
741 pairs: A>B=292, B>A=350, A~B=1,
and insufficient evidence=98.

The aggregate winner required targeted removal of 261
items (1.86%) to flip to the nearest
challenger in the exact greedy deletion analysis. The minimum subject-weight total variation was
0.155. These are conditional
sensitivity measures, not evidence that removed items are flawed or that the observed winner is
universally preferable.

Runtime: 0.25 seconds. Backing artifacts are under
`results/v7/decision/materiality/`.
