# ValidEval V7 Confirmatory Synthetic Results

Execution gate: `SYNTHETIC_CONFIRMATORY_COMPLETE`. Acceptance gate:
`FROZEN_ACCEPTANCE_GATES_FAILED`.

The protocol was frozen at `valideval-v7-confirmatory-freeze` / `08336a3948db69de931e7582650abbd2f6ae0a70` before
execution. It evaluated 162 combinations covering no flaw, label errors,
multiple label errors, ambiguity, distractor failure, subject misassignment, duplicates,
missingness, and correlated-family failure. The detector received only response matrices; sealed
truth was used only for metrics.

Median AUPRC was 0.113, median precision@k was
0.050, median FDR was 0.966, and median
power was 0.017. Every preregistered success criterion failed. The fixed
readout is therefore not validated for the declared heterogeneous flaw grid and cannot support
real-item quality claims. This negative result is retained, not tuned away.

Runtime: 1.90 seconds. Backing artifacts are under
`results/v7/synthetic/confirmatory/`.
