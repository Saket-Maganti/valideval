# ValidEval V6 S1 Model Panel Freeze

Gate: `S1_EXACT_PANEL_FROZEN`

Panel hash: `84a65d684fb839a1929d00b04961fd99f9f6883dfa89651de0235c8fda2f394a`

| Checkpoint | Immutable model/tokenizer revision | License | Expected bytes |
|---|---|---|---:|
| `Qwen/Qwen2.5-0.5B-Instruct` | `7ae557604adf67be50417f59c2c2f167def9a775` | Apache-2.0 | 999,604,126 |
| `Qwen/Qwen2.5-1.5B-Instruct` | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` | Apache-2.0 | 3,098,973,447 |
| `Qwen/Qwen2.5-3B-Instruct` | `aa8e72537993ba99e69dfaafa59ed015b17504d1` | Qwen Research | 6,183,464,935 |
| `microsoft/Phi-3-mini-4k-instruct` | `f39ac1d28e925b323eae81227eaba4464caced4e` | MIT | 7,644,766,216 |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | `fe8a4ea1ffedaf415f4da2f062534de366a451e6` | Apache-2.0 | 2,202,470,207 |

The public repositories and immutable refs were verified against their official Hugging Face
repositories on 2026-07-23. The total declared download size is 20,129,278,931 bytes
(18.75 GiB). All use `float16`, no quantization, `trust_remote_code: false`, pinned chat-template
policies, and architecture allowlisting. The fail-closed disk threshold is approximately 25.75 GiB
free (declared model bytes plus the 7 GiB configured reserve).

T4 fit is `EXPECTED_FIT_UNVERIFIED_UNTIL_S1`; remote T4×2 loading has not been represented as a
local empirical result. This three-family, five-checkpoint panel is `ENGINEERING_ONLY`,
`scientific_panel_adequacy: false`, and cannot support scientific common-panel comparisons.
