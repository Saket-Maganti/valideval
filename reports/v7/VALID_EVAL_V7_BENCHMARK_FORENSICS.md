# ValidEval V7 Benchmark Forensics

Gate: `BENCHMARK_FORENSICS_READY` for cached MMLU position analysis.

The audit reproduced 547638 prediction rows over 14042 unique
items with 0 gold-identity conflicts. Gold-position fractions
were A=0.230, B=0.247, C=0.255, and
D=0.269; position-conditioned accuracy ranged from
0.676 to
0.707. These are forensic signals, not
contamination findings.

Freezing the full V7 splits found and retired 27 exact MMLU duplicates and 4 exact BBH duplicates;
GSM8K had none under the content-addressed identity. MMLU-Redux remains
`REDUX_VALIDATION_RETIRED`: its 370 local labels lack normalized question/options/answer or a
documented HELM mapping, and the prior fail-closed attempt confirmed 0 matches. No further fuzzy
linkage is justified.
