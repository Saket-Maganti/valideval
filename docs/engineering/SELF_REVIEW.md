# Self Review

## 2026-06-01

1. Does this compute validity diagnostics, or only describe them?

   It computes real offline diagnostics from response matrices and benchmark metadata: shortcut retention across prompt variants, shallow baseline gaps, answer-distribution artifacts, distractor quality, prompt sensitivity, extraction robustness, IRT v2 layered estimates, subset fidelity, tag skill profiles, DIF-like model-group residuals, saturation, power, redundancy, calibration/abstention, rank uncertainty, and perturbation reliability. Contamination and coverage have modest but executable implementations; predictive and Goodhart diagnostics intentionally return helpful "required inputs missing" results.

2. Can a stranger run the toy audit?

   Yes, after `python3 -m pip install -e ".[dev]"`, `make audit` generates prediction caches, response matrices, diagnostic JSON, and `reportcards/toy_mcq_mock.md`. The Makefile defaults to `python3` because this environment does not expose `python`.

3. Are tests meaningful, or just import checks?

   The tests exercise schema serialization, toy prompt variants, MCQ scoring, extraction modes, mock model behavior, response matrix building, heuristic baselines, answer-distribution metrics, distractor CSV export, shortcut retention, prompt-sensitivity ranking flips, synthetic IRT recovery, low-discrimination flagging, saturation ceiling behavior, power formulas, DIF group bias, redundancy clusters, calibration/abstention, rank uncertainty, reliability stats, report rendering, and CLI smoke paths.

4. Did we accidentally make fake empirical claims?

   No real benchmark results are invented. The README and report card explicitly identify toy outputs as synthetic and caution against global validity claims.

5. Is IRT handled honestly with uncertainty/warnings?

   The diagnostic uses layered estimates: proxy values, a Rasch/1PL optimization path when available, 2PL slope proxies, and bootstrap uncertainty. It warns about small panels, low/negative discrimination, sparse tags, and fallback conditions rather than pretending to fit a definitive latent-trait model.

6. Are the report cards useful?

   The report card is useful as a first audit surface: it summarizes shortcut retention, reliability, IRT flags, conditional ranking comparison, warnings, limitations, and reproduction commands. It also writes a JSON manifest for provenance. It should eventually include compact tables and links to item-level CSV/JSON artifacts.

7. Is the architecture extensible?

   The package has clear modules for schemas, benchmarks, models, scoring, diagnostics, psychometrics, audit orchestration, report rendering, and ranking. Real benchmark loaders and richer diagnostics can plug into these interfaces.

8. Are real benchmark loaders honest about their status?

   Yes. MMLU, GSM8K, BBH, TruthfulQA, and CausalAgentBench are scaffolded configs/placeholders only. The placeholder adapter raises clear errors and asks for validated local exports or implemented loaders.

9. Is the README strong enough to make the project legible?

   Yes for an initial release. It states the thesis, quickstart, implemented diagnostics, architecture, roadmap, and non-claims.

10. What is the smallest next experiment that could produce a publishable number?

   Use `LocalJSONLBenchmark` on a small validated export from one real MCQ benchmark, run the mock/offline pipeline with a local open-model panel, and report shortcut retention plus IRT low-discrimination fractions with a preregistered protocol.

## Known Weak Spots

- The toy benchmark is intentionally synthetic; its numeric outputs are pipeline checks, not scientific findings.
- The eight mock models are simple heuristics and do not represent real model behavior.
- The baseline zoo and extraction modes are shallow audit probes; high scores or score shifts require item-level review.
- IRT v2 has a Rasch/1PL fallback path and bootstrap uncertainty, but full 2PL and MIRT remain proxy/scaffolded rather than definitive fits.
- DIF-like diagnostics are about model-family benchmark behavior, not human demographic fairness.
- Numeric calibration is disabled when confidence/logprob values are absent; prompt consistency is only a perturbation-stability proxy.
- Predictive and Goodhart diagnostics require external data and currently fail gracefully rather than estimate.
- Generated report cards are Markdown-only and do not yet include figures.
