# ValidEval V7 Novelty Defense

This is a claim audit, not final related-work prose.

| Work | What it does | ValidEval overlap | What it does better | What V7 uniquely tests | Must not claim |
|---|---|---|---|---|---|
| [HELM](https://arxiv.org/abs/2211.09110) | Multi-scenario, multi-metric transparent evaluation | Common panels and raw artifacts | Breadth and standardized scenarios | Claim-specific licensing across uncertainty, materiality, external validity, and regret | First holistic evaluation framework |
| [BetterBench](https://arxiv.org/abs/2411.12990) | Audits benchmark-development best practices | Benchmark quality and reproducibility | Broad practice taxonomy across published benchmarks | Executable statistical gates for individual claims | First benchmark-quality checklist |
| [BenchBench](https://arxiv.org/abs/2407.13696) | Meta-evaluates benchmark agreement and robustness | Ranking/benchmark comparison | Direct benchmark meta-evaluation | Joint licensing with external, held-out, transport, and regret gates | First benchmark meta-evaluation |
| [tinyBenchmarks](https://arxiv.org/abs/2402.14992) | Efficient evaluation using IRT/item subsets | IRT and subset design | Compute-efficient score recovery | Validity threats and decision consequences, not score approximation alone | First IRT-based LLM evaluation |
| [Land & Bikel 2026](https://arxiv.org/abs/2605.30504) | Uses IRT indicators to identify mislabeled benchmark items | Direct item-diagnostic overlap | Multi-benchmark scale and human validation | Whether a diagnostic may license a claim after multiplicity, stability, materiality, and transport | Novelty for IRT flaw detection |
| [Can We Trust IRT in LLM Evaluation?](https://arxiv.org/abs/2607.15190) | Simulates IRT reliability across panel regimes | Direct regime-study overlap | Much larger simulation program | Integrates regime adequacy into fail-closed claim licensing | Novelty for showing small/non-normal panels can fail |
| [Ranking Uncertainty](https://arxiv.org/abs/2607.16259) | Quantifies rank uncertainty and subject variability | Direct rank-set overlap | Dedicated simultaneous rank inference | Couples rank uncertainty to selective decisions, regret, repair, and transport | Novelty for rank uncertainty itself |
| [JE-IRT](https://arxiv.org/abs/2509.22888) | Geometric multidimensional IRT | Measurement-model overlap | Rich latent geometry | Regime-gated choice among simpler and richer models | A new multidimensional IRT model |
| [Benchmark contamination survey](https://arxiv.org/abs/2401.06059) / [LiveBench](https://arxiv.org/abs/2406.19314) / [TRUCE](https://arxiv.org/abs/2403.00393) | Detects or mitigates contamination | Forensic/contamination threats | Purpose-built contamination evidence and fresh data | Requires contamination evidence to pass identity and decision-materiality gates before licensing a claim | Position imbalance proves contamination |

Defensible proposed contribution: a multidimensional claim-licensing methodology that treats
diagnostics as fallible measurement instruments and conditions each claim on uncertainty,
stability, false-positive behavior, decision materiality, independent validation, and transport.
Its scientific effectiveness is not yet established: the frozen synthetic readout failed and real
transport/human studies remain unexecuted.
