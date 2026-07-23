#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"

"${PYTHON}" -m valideval toy
"${PYTHON}" -m valideval matrices --benchmark toy_mcq --panel mock
"${PYTHON}" -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core
"${PYTHON}" -m valideval report --benchmark toy_mcq --panel mock
