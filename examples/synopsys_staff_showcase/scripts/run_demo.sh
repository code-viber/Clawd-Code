#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHOWCASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PYTHONPATH="${SHOWCASE_DIR}/python${PYTHONPATH:+:${PYTHONPATH}}"

python -m eda_hpc_triage.cli triage \
  "${SHOWCASE_DIR}/sample_data/regression.log" \
  --workers "${SHOWCASE_DIR}/sample_data/workers.json"
