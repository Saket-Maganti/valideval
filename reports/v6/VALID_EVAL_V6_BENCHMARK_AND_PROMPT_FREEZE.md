# ValidEval V6 Benchmark and Prompt Freeze

Gate: `S1_BENCHMARK_CONTRACTS_FROZEN`

| Benchmark | Repository and immutable revision | Split | S1 items | Contract SHA-256 | Subset SHA-256 |
|---|---|---|---:|---|---|
| MMLU | `cais/mmlu@c30699e8356da336a370243923dbaf21066bb9fe` | test | 50 | `76cb036759dba37a804595d4905ced6873abc2028ee461e1bf349df99637fe8e` | `2a41fbe2bede32acd1bfb1860c714324a67141161115e271ce36cae956feb19a` |
| GSM8K | `openai/gsm8k@740312add88f781978c0658806c59bc2815b9866` | test | 50 | `14bde26f615f3268ebe7414438f60568ec95d52f16074feec995fae12e508128` | `ae1b46a8330ef26b67c708d02596ae100ab2687be6c7330c17d64dea0a2520f6` |
| BBH | `lukaemon/bbh@982bb89fd79532a8ac676a61fc42eb1aeec63f99` | test | 50 | `de70e0cc3152104a1bf2b1842e9cddefac79ec9298c897c283560c97920879ec` | `d25ed8f57db8e5b71981773f8daa83c9f6d7565495bba64cd95ceb05cef85829` |

MMLU uses controlled greedy answer generation and a gold-blind A/B/C/D parser. GSM8K uses greedy
generation and a gold-blind numeric parser covering signs, commas, decimals, fractions, currency,
percent markers, and ambiguous/invalid formats. BBH covers all 27 declared tasks with reviewed
task-specific normalizers and scorers.

The BBH few-shot decision is `zero_shot_s1_v6`. No prompt examples are silently reconstructed from
an unverified mirror. All three contracts use the empty few-shot hash
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
This is a deliberate, versioned condition, not an assertion that zero-shot is universally optimal.

The deterministic seed is `20260723`. Subsets store public identities, row locators, and hashes, not
gold text. Prompt and public-subset hashes are in
`results/freeze/s1_prompt_and_dataset_hashes_v6.json`.
