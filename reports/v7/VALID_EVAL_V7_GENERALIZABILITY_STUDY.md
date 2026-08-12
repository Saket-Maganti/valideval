# ValidEval V7 Generalizability Study

Gate: `GENERALIZABILITY_ANALYSIS_READY` with descriptive-component limitations.

The unbalanced method-of-moments decomposition estimates family (0.0056), model
(0.0084), subject (0.0182), item (0.0814), family×subject
(0.0015), model×subject (0.0021), and residual
(0.1784) components. These quantities describe this fixed historical panel; they are
not population variance estimates.

Design curves separately cover aggregate score, pairwise comparison, top-k selection, and
subject-conditioned score. The first three reach 0.80 on the evaluated grid; subject-conditioned
score does not. This supports outcome-specific design decisions and rejects a single universal
reliability number.

Runtime: 0.34 seconds. Backing artifacts are under
`results/v7/reliability/generalizability/`.
