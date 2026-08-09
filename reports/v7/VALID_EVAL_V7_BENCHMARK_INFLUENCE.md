# ValidEval V7 Benchmark Influence

Gate: `BENCHMARK_INFLUENCE_READY`.

Exact leave-one-item analysis found 0 winner-changing items and
0 top-five-changing items among 14042 historical MMLU
items. Leave-one-subject analysis found 0 winner-changing
subjects. The cross-fit 5% removal comparison includes suspicious, random, matched-difficulty,
high-difficulty, and high-variance policies; none changed the held-out winner.

This is evidence that single-item deletion was not decision-material for the measured winner under
this matrix. Influence is not a flaw label, and larger coordinated subsets can still matter.

Runtime: 8.57 seconds. Backing artifacts are under
`results/v7/influence/mmlu_v7/`.
