#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHOWCASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON:-}"

if [[ -z "${PYTHON_BIN}" ]]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    PYTHON_BIN="python3"
  fi
fi

export PYTHONPATH="${SHOWCASE_DIR}/python${PYTHONPATH:+:${PYTHONPATH}}"

"${PYTHON_BIN}" -m eda_hpc_triage.cli triage \
  "${SHOWCASE_DIR}/sample_data/regression.log" \
  --workers "${SHOWCASE_DIR}/sample_data/workers.json"
