# Real Empirical Spine Reframe

## 1. Current Best Non-Circular Evidence

The strongest current non-circular spine is the active 39-model public HELM MMLU panel plus the MMLU-Redux external-validation stress test. The key result is cautionary: matrix-derived diagnostics on the active panel do not robustly recover structurally aligned MMLU-Redux issue labels.

## 2. HELM 39-Model MMLU Panel

The active MMLU panel contains 39 public HELM model outputs over 14,042 items with no missing cells in the wide matrix. The panel clears the project panel-validity gate for item-level proxy diagnostics. The older 3-model files are historical/provenance only and should not be described as the active panel. This supports using the panel as a real empirical substrate, not as proof that the diagnostics detect item flaws.

## 3. MMLU-Redux Weak/Negative Result

The MMLU-Redux stress test remains weak/negative. Broad grouped validation is near random for combined proxy flags, subject-normalized issue-specific validation weakens the earlier raw label-error signal, and top-k hints remain review-queue scoped. The alignment is structural, not direct-id/hash confirmed.

## 4. Why This Is Publishable

The publishable contribution is methodological discipline: benchmark-validity diagnostics should themselves be validated before their outputs are used as benchmark-quality claims. A weak or negative external-validation result is scientifically useful because it prevents overclaiming and shows the need for evidence gates.

## 5. What Is Still Missing

- Decoupled flaw-agnostic synthetic validation (`RESULT_REQUIRED`).
- Direct/hash-confirmed MMLU-Redux alignment.
- Real-panel diagnostic disagreement analysis (`RESULT_REQUIRED`).
- Real-panel ranking sensitivity analysis (`RESULT_REQUIRED`).
- Human-reviewed threshold calibration.
- Confidence/logprob-backed calibration where needed.
- Second-benchmark transfer evidence.
- Final paper/reviewer packet and venue gate.

## 6. Required Future Analyses

- Run the decoupled synthetic harness only after an approved evidence protocol exists.
- Complete dry-run-to-run conversion for real-panel disagreement and ranking sensitivity.
- Add direct/hash-confirmed external labels where licensing permits.
- Report thresholds as preregistered or sensitivity-reported.
- Preserve weak/blocked states when evidence remains weak.

## 7. Claims Allowed Now

- ValidEval treats validity as a multidimensional evidence profile rather than a scalar score.
- ValidEval can run offline-safe audits and dry-run evidence gates.
- The HELM MMLU panel provides a real public response-matrix substrate.
- The active MMLU panel-size blocker is cleared for the reconciled 39-model matrix.
- Proxy IRT artifacts exist for the active panel.
- MMLU-Redux validation is weak/negative under the current protocol.
- Current evidence is consistent with the need to externally validate benchmark-validity diagnostics before relying on them.

## 8. Claims Blocked

- Generic MMLU-Redux issue detection.
- MMLU is globally valid or invalid.
- Proxy IRT is full psychometric 2PL.
- Current synthetic AUCs are independent diagnostic-validation evidence.
- Real-panel ranking sensitivity or disagreement has been established.
- Decoupled synthetic validation has been run.
- Second-benchmark evidence exists.
- The project is NeurIPS-ready.

## 9. Suggested Paper Thesis

Benchmark-validity diagnostics are often treated as if they license benchmark-quality claims, but their own validity is rarely tested. In our current strongest real stress test, matrix-derived diagnostics on a 39-model HELM MMLU panel do not robustly recover independently documented MMLU-Redux issue labels, showing that diagnostic claims must be gated and externally validated before use.
