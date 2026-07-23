# Second Real Benchmark Decision

Default order:

1. MMLU-Redux first, because it supplies the clearest external issue-label target.
2. GSM8K/GSM1k second if local per-instance predictions and issue labels are available.
3. GPQA wide panel as a restricted-data protocol case, not as the first evidence case.
4. TruthfulQA or MMLU-Pro only after confirming local prediction details and external labels.

Do not expand into domain-specific packs for NeurIPS unless an external ground truth exists.
