# Advanced Psychometrics

Prompt 03 adds advanced measurement diagnostics while keeping the project's central caution: these values are evidence under a protocol, not ground truth.

## IRT v2

The IRT diagnostic now layers:

- proxy difficulty, anchor-oriented discrimination, corrected item-total correlation, and item information
- Rasch/1PL optimization when SciPy and sufficient data are available
- 2PL-style slope proxies when data are sufficient
- bootstrap uncertainty for abilities, difficulty, and discrimination
- tag-based multidimensional skill profiles as a practical scaffold before full MIRT
- subset modes for top discrimination, maximum information, tag balance, low-risk items, high-reliability items, coverage constraints, and random baselines

Warnings are emitted when estimates are unstable, optimization falls back, or construct tags have too few items.

Per-item discrimination labels distinguish `negative_discrimination`, `low_discrimination`, `positive_discrimination`, `unstable_estimate`, and `insufficient_panel`. These are proxy labels under the current model panel, not latent 2PL ground truth.

## DIF-Like Model Group Diagnostics

DIF here means model-family benchmark behavior. It is not human demographic fairness. The diagnostic compares group-conditioned item residuals and group advantages for configured model groups such as small vs large, model family, reasoning vs chat, quantized vs full precision, or custom groups.

## Saturation

Saturation reports ceiling proximity, fraction solved by all top models, fraction failed by all models, effective discriminating item count, compression, and tag-level saturation. Categories are `not saturated`, `mild`, `moderate`, `severe`, or `insufficient evidence`.

## Power

Power analysis estimates standard errors, paired bootstrap score-difference intervals, minimum detectable differences, required item counts for 1/2/5 point gaps, redundancy-adjusted effective item count, and a warning not to overinterpret small score gaps.

## Redundancy

Redundancy diagnostics detect exact or near duplicates, shared contexts, repeated templates, source reuse proxies, and answer-pattern duplicate clusters. Cluster-weighted accuracy is reported when a response matrix is available.

## Calibration and Abstention

If confidence or logprobs are present, calibration reports ECE, Brier score, NLL, confidence-correctness, and calibration by construct tag. When confidence is absent, numeric calibration output is disabled and `valideval` reports prompt consistency only as a perturbation-stability proxy. Abstention metrics include coverage, selective risk, appropriate and inappropriate refusal, risk-coverage AUC, and deferral utility.

## Ranking Uncertainty

Bootstrap rank distributions estimate rank intervals, probability model A beats model B, top-k stability, and ranking flips under item resampling.

## Limitations

Small model panels, synthetic toy data, redundant items, sparse construct tags, and missing confidence values all limit interpretation. Report cards should present these diagnostics as a multidimensional profile rather than a single validity score.
