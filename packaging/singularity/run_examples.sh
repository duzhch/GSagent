#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  cat <<'EOF'
Usage:
  bash packaging/singularity/run_examples.sh <sif_path> <workdir>

Examples:
  bash packaging/singularity/run_examples.sh dist/gsagent-runtime.sif /path/to/project
EOF
  exit 1
fi

SIF_PATH="$1"
WORKDIR="$2"
ENGINE="${APPTAINER_ENGINE:-}"

if [[ -z "${ENGINE}" ]]; then
  if command -v apptainer >/dev/null 2>&1; then
    ENGINE="apptainer"
  elif command -v singularity >/dev/null 2>&1; then
    ENGINE="singularity"
  else
    echo "[run] ERROR: neither apptainer nor singularity is available."
    exit 1
  fi
fi

if [[ ! -f "${SIF_PATH}" ]]; then
  echo "[run] ERROR: sif not found: ${SIF_PATH}"
  exit 1
fi
if [[ ! -d "${WORKDIR}" ]]; then
  echo "[run] ERROR: workdir not found: ${WORKDIR}"
  exit 1
fi

echo "[run] engine=${ENGINE}"
echo "[run] sif=${SIF_PATH}"
echo "[run] workdir=${WORKDIR}"

"${ENGINE}" exec -B "${WORKDIR}:/workspace" "${SIF_PATH}" \
  gsagent preflight --workdir /workspace

echo "[run] starting API on 0.0.0.0:8000"
"${ENGINE}" exec -B "${WORKDIR}:/workspace" "${SIF_PATH}" \
  gsagent serve --workdir /workspace --host 0.0.0.0 --port 8000 --llm-check auto
