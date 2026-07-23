# Reviewer Summary: MMLU-Redux Validation

All findings are preliminary and protocol-scoped. No raw MMLU question text or answer-choice text is included.

- Data: We used a public HELM MMLU panel with 39 models, 14,042 items, 0 missing response-matrix cells, and 370 MMLU-Redux labels structurally aligned by `subject_numeric_index` at confidence 0.85, without direct-id or hash confirmation.
- Methods: We evaluated broad proxy-IRT flags, issue-type-specific diagnostics, subject-normalized diagnostics, and a focused 1000-iteration subject-matched null for `label_error` using sanitized local artifacts only.
- Result: The stress test was weak/negative overall: broad combined proxy-IRT flags were near-random (AUROC 0.495, AUPRC 0.030, P@10 0.000), the raw `label_error + correct_answer_rarely_selected` signal showed limited top-k review-queue enrichment in the focused null (P@10 0.200 and P@25 0.120 versus null means 0.036 and 0.022), and subject-normalized evidence weakened the earlier raw signal.
- Blocked claims: These results do not support detection-success, global MMLU validity or invalidity, external-validation success for proxy IRT as an MMLU-error detector, or direct/hash-confirmed alignment claims.
- Why it matters: The case demonstrates that ValidEval can run sanitized external-validation surfaces while its evidence gate blocks unsupported diagnostic claims, motivating diagnostic-specific validation against the threat each diagnostic is meant to detect.
