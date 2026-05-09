#!/usr/bin/env bash
set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-gsagent_runtime}"

if ! command -v conda >/dev/null 2>&1; then
  echo "[install] ERROR: conda not found in PATH"
  exit 1
fi

if [[ ! -f "${BUNDLE_DIR}/environment.yml" ]]; then
  echo "[install] ERROR: environment.yml not found in bundle"
  exit 1
fi

echo "[install] create env: ${ENV_NAME}"
conda env create -n "${ENV_NAME}" -f "${BUNDLE_DIR}/environment.yml" >/dev/null 2>&1 || \
conda env update -n "${ENV_NAME}" -f "${BUNDLE_DIR}/environment.yml" >/dev/null 2>&1

echo "[install] install wheel into env: ${ENV_NAME}"
conda run -n "${ENV_NAME}" python -m pip install \
  --no-index \
  --find-links "${BUNDLE_DIR}/wheels" \
  animal-gs-agent

echo "[install] done"
echo "Activate with: conda activate ${ENV_NAME}"
echo "Verify with: gsagent --help"
