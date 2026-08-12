# ValidEval V7 Diagnostic Dependency Audit

Gate: `DIAGNOSTIC_DEPENDENCIES_EXPLICIT`.

The audit groups diagnostics by source data, formula, and dependence on benchmark accuracy or
external labels. `legacy_accuracy_weight` is retired as a duplicate of extreme-difficulty scoring.
Negative discrimination and extreme difficulty remain separate signals but share the response
matrix, so their agreement cannot be treated as independent corroboration. External issue matches
are structurally independent only after exact identity and held-out-label checks pass.

The dependency graph is stored at
`results/v7/diagnostics/diagnostic_dependency_graph.json`. Downstream claim licensing counts a
cluster of dependent diagnostics as one evidence family and requires independent external or human
evidence for item-quality language.
