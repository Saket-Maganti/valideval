# ValidEval V7.1 Benchmark Forensics

Status: `BENCHMARK_FORENSICS_V7_1_READY` within the frozen-manifest evidence boundary.

The analysis covers 14,015 MMLU, 1,319 GSM8K, and 6,507 BBH frozen items. It checks exact item
identity, normalized exact duplicates, and cross-benchmark normalized exact overlap. It observed 78
exact-duplicate class rows among the manifest-level outputs.

The frozen manifests intentionally omit prompt and option text. Consequently n-gram/MinHash near
duplicates, option permutations, semantic candidates, and cross-split overlap are marked
unavailable rather than approximated. Any future semantic candidate would require manual
confirmation before promotion.

Forensic evidence is a potential validity-threat signal. It does not establish that an item
appeared in model pretraining, so `contamination_claim_permitted` is false.
