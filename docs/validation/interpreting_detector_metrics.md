# Interpreting Detector Metrics

The validation harness treats each diagnostic as a detector. Ground truth comes from synthetic item metadata; diagnostic scores come from normal ValidEval diagnostic outputs.

Core metrics:

- ROC AUC: how well higher diagnostic scores separate flawed from clean items.
- PR AUC: precision-recall area, useful when flawed items are sparse.
- Sensitivity: fraction of flawed items flagged at a threshold.
- Specificity: fraction of clean items not flagged.
- False-positive rate: clean items incorrectly flagged.
- Monotonicity: whether diagnostic scores rise as injected flaw strength rises.
- Score-strength Spearman correlation: rank correlation between injected strength and diagnostic score.
- Null distribution: diagnostic scores under strength `0.0`.

Interpretation should be cautious. High AUC under a synthetic generator means evidence that the diagnostic detects that controlled synthetic flaw. It does not prove that the same diagnostic will detect every real version of the flaw.

Thresholds are estimated from null synthetic scores. They are starting points for the same synthetic protocol, not universal real-benchmark cutoffs.
