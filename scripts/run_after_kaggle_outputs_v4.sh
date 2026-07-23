#!/usr/bin/env bash
set -euo pipefail

python3 -m valideval import-kaggle-outputs \
  --input-dir kaggle_outputs \
  --output-root data/external/kaggle_imported \
  --cache-root cache \
  --results-root results \
  --strict

for benchmark in gsm8k bbh truthfulqa third_benchmark; do
  matrix="cache/${benchmark}/wide/matrix.csv"
  predictions="cache/${benchmark}/wide/predictions.jsonl"
  output="results/${benchmark}"
  if [[ -f "${matrix}" && -f "${predictions}" ]]; then
    python3 -m valideval post-import-analysis \
      --benchmark "${benchmark}" \
      --matrix "${matrix}" \
      --predictions "${predictions}" \
      --output "${output}" \
      --execute
  fi
done

python3 -m valideval cross-benchmark-analysis \
  --benchmarks mmlu,gsm8k,bbh \
  --cache-root cache \
  --results-root results \
  --output results/cross_benchmark \
  --execute

python3 scripts/update_paper_from_artifacts_v4.py
python3 scripts/make_reviewer_packet.py --output dist/valideval_reviewer_packet_v4_pre_execution.zip
ruff check .
python3 -m pytest -q
python3 scripts/write_final_v4_gate_from_artifacts.py
