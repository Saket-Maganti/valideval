# MMLU IRT Psychometric Run Report

## Executive Summary

Psychometric proxy diagnostics completed on the active 39-model MMLU wide panel. Proxy item parameters, flags, model ability proxies, and 2PL-proxy slopes exist. The local Rasch/1PL optimizer was blocked as too large for the 14,080-free-parameter wide matrix, and full parametric 2PL was not run.

Final verdict: `IRT_RUN_PARTIAL_PROXY_ONLY`

## Inputs

- Matrix: `cache/mmlu/wide/matrix.csv`
- Panel: 39 models x 14,042 items
- Panel-validity status: `pass`

## Runs

| Run | Output | Status |
|---|---|---|
| Proxy | `results/mmlu/irt_proxy/` | `ok` |
| Rasch/1PL | `results/mmlu/irt_rasch/` | artifact written, Rasch unavailable for matrix size |
| 2PL proxy | `results/mmlu/irt_2pl/` | proxy slopes only |

## Proxy Item Diagnostics

- Negative discrimination flags: 1,037
- Near-zero discrimination flags: 1,342
- Extreme difficulty flags: 2,676
- Discrimination proxy mean: 0.30600378093101704
- Discrimination proxy median: 0.3305239600898195

## Model Ability Proxies

- Model ability proxy mean: 0.8527060716117385
- Model ability proxy minimum: -0.9079308105746507
- Model ability proxy maximum: 1.8800028286329638

## Rasch / 1PL Status

The Rasch/1PL fit was skipped by a guard because the local BFGS implementation would require 14,080 free parameters on this matrix. Full Rasch evidence remains `RESULT_REQUIRED`.

## 2PL Status

The `2pl` run exported proxy slopes from item-total discrimination. It is not a full parametric 2PL fit. Full 2PL remains blocked/not claimed.

## Artifacts

- `results/mmlu/irt_proxy/item_parameters.csv`
- `results/mmlu/irt_proxy/model_abilities.csv`
- `results/mmlu/irt_proxy/flags.jsonl`
- `results/mmlu/irt_proxy/fit_summary.json`
- `results/mmlu/irt_rasch/fit_summary.json`
- `results/mmlu/irt_2pl/item_parameters.csv`
- `results/mmlu/irt_2pl/fit_summary.json`

## Claims Allowed

- Item-level proxy psychometric diagnostics were computed on the active MMLU panel.
- The panel is eligible for item-level proxy diagnostics under the implemented panel-validity gate.
- Item flags are diagnostic signals under this observed panel.

## Claims Blocked

- MMLU error detection.
- MMLU validity or invalidity.
- Externally validated item-error labels.
- Full Rasch/1PL evidence.
- Full parametric 2PL evidence.

## Final Verdict

`IRT_RUN_PARTIAL_PROXY_ONLY`
