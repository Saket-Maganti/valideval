# Decoupled Synthetic Harness Design

## 1. Goal

Build a future synthetic validation harness that can test diagnostic behavior without using hidden injected flaw labels as model-control inputs or readout selectors. The goal is not to upgrade current evidence. The current implementation is a scaffold and dry-run preflight only.

## 2. Non-Circularity Requirement

The future harness must separate the generator, model, diagnostic, and readout. A synthetic item may have hidden labels for later evaluation, but the synthetic model and fixed readout must not receive or branch on those labels.

## 3. Forbidden Couplings

- Model behavior must not branch on `is_flawed`.
- Model behavior must not branch on `flaw_type`.
- Model behavior must not read `ground_truth_signal`.
- Readout must not switch statistics by flaw family.
- Thresholds must not be tuned after inspecting target-flaw performance.
- Diagnostics must not receive a per-flaw custom extraction rule.
- Held-out generators must not mirror detector-specific behavior.

## 4. Flaw-Agnostic Model Requirement

The synthetic model API must accept observable item features and a public prompt variant only. Hidden generator labels may exist in evaluation artifacts, but they must be stripped before model prediction.

The scaffolded API is:

```python
class FlawAgnosticSyntheticModel:
    def predict(self, item: ObservableItemFeatures, variant: str = "original") -> str:
        ...
```

There is no `is_flawed` parameter and no `flaw_type` parameter.

## 5. Fixed Readout Requirement

The readout must be specified before observing the flaw family. It may compute a fixed score such as item instability, disagreement, invalid-output rate, or preregistered composite, but it must not select a statistic based on the target flaw.

The scaffolded API is:

```python
class FixedDiagnosticReadout:
    def score_items(self, panel_outputs: list[PanelOutput]) -> dict[str, float]:
        ...
```

## 6. Generator / Model / Diagnostic Separation

- Generator creates original and flawed items and stores hidden labels only for evaluation.
- Model receives only `ObservableItemFeatures.public_metadata()`, prompt text, choices, answer, subject, and variant.
- Diagnostic consumes response matrices or panel outputs without hidden labels.
- Readout produces one fixed item score per item.
- Evaluation compares the fixed score to hidden labels only after scoring is complete.

## 7. Allowed Item Properties

Allowed model inputs:

- `item_id`
- `prompt`
- `choices`
- `answer` when the protocol is explicitly answer-aware
- `subject`
- public metadata after hidden-label stripping
- prompt variant

Forbidden model inputs:

- `is_flawed`
- `flaw_type`
- `flaw_strength`
- `ground_truth_signal`
- any direct or renamed hidden target label

## 8. Allowed Model Behavior

The model may deterministically depend on prompt wording, answer-choice surface form, subject, public metadata, declared variant, and model configuration such as ability or format sensitivity. The model may have fixed stochasticity through a seed/config. It must not know which items are targets.

## 9. Held-Out Transfer Design

Held-out transfer must use flaw generators not mirrored by model-control branches. The model should be unchanged across generator families. The readout should remain unchanged across generator families. Transfer results should report both average performance and failure cases, including off-target activations.

## 10. Baselines

Future runs should include:

- random item ranking baseline,
- item-length or answer-position surface baseline,
- majority-class or prior-only baseline,
- fixed model-disagreement baseline,
- diagnostic-specific candidate score, if preregistered before target labels are inspected.

## 11. Future Execution Plan

1. Freeze a protocol with hidden-label stripping checks.
2. Freeze a fixed readout and baseline set.
3. Generate items only after approval for an evidence run.
4. Run flaw-agnostic models without hidden labels.
5. Score items with the fixed readout.
6. Compare to hidden labels and report confidence intervals, threshold sensitivity, and baseline comparisons.
7. Keep all evidence states `RESULT_REQUIRED` until artifacts exist.

## 12. Claims Allowed After Future Runs

Only if a future approved run exists:

- Evidence consistent with fixed-readout synthetic sensitivity under a decoupled protocol.
- Evidence consistent with generator transfer for the specific tested generator families.
- Baseline-relative performance under preregistered thresholds or sensitivity reports.

## 13. Claims Still Blocked

- ValidEval solves benchmark validity.
- Synthetic validation proves real benchmark validity.
- One diagnostic establishes global benchmark invalidity.
- Current legacy synthetic AUCs are independent validation evidence.
- Thresholds transfer to real benchmarks without real calibration.
- MMLU-Redux detection succeeds under current weak/negative results.

Current old harness remains labeled `legacy_wiring_only`.
