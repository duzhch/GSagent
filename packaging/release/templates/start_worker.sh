#!/usr/bin/env bash
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="${BUNDLE_ROOT}/app"
RUNTIME_DIR="${BUNDLE_ROOT}/runtime_env"
RUNTIME_ARCHIVE="${BUNDLE_ROOT}/runtime_env.tar.gz"
mkdir -p "${BUNDLE_ROOT}/logs" "${BUNDLE_ROOT}/runs" "${BUNDLE_ROOT}/state"

if [[ ! -d "${RUNTIME_DIR}" ]]; then
  echo "[start_worker] unpacking runtime_env.tar.gz ..."
  mkdir -p "${RUNTIME_DIR}"
  tar -xzf "${RUNTIME_ARCHIVE}" -C "${RUNTIME_DIR}"
fi

if [[ ! -f "${RUNTIME_DIR}/.unpacked_ok" ]]; then
  "${RUNTIME_DIR}/bin/python" "${RUNTIME_DIR}/bin/conda-unpack" >/dev/null 2>&1
  touch "${RUNTIME_DIR}/.unpacked_ok"
fi

if [[ -f "${BUNDLE_ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${BUNDLE_ROOT}/.env"
  set +a
fi

export PATH="${RUNTIME_DIR}/bin:${PATH}"
export PYTHONPATH="${APP_ROOT}/src"

export ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR="${ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR:-${BUNDLE_ROOT}/assets/pipeline}"
export ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT="${ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT:-${BUNDLE_ROOT}/runs}"
export ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH="${ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH:-${BUNDLE_ROOT}/state/jobs_store.db}"
export ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH="${ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH:-${BUNDLE_ROOT}/state/run_queue.db}"
export ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY="${ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY:-local}"
export ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED="${ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED:-1}"

cd "${APP_ROOT}"
exec "${RUNTIME_DIR}/bin/python" scripts/native/worker_loop.py --interval-seconds 2
