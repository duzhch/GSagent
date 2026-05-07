#!/usr/bin/env bash
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${BUNDLE_ROOT}/logs"
PID_DIR="${BUNDLE_ROOT}/state"
RUNTIME_DIR="${BUNDLE_ROOT}/runtime_env"
RUNTIME_ARCHIVE="${BUNDLE_ROOT}/runtime_env.tar.gz"
API_PORT="${ANIMAL_GS_AGENT_PORT:-8000}"
API_URL="${ANIMAL_GS_AGENT_API_URL:-http://127.0.0.1:${API_PORT}}"
RUNTIME_PY="${RUNTIME_DIR}/bin/python"
mkdir -p "${LOG_DIR}" "${PID_DIR}"

verify_pid_running() {
  local name="$1"
  local pid_file="$2"
  if [[ ! -f "${pid_file}" ]]; then
    echo "[start_all] ${name} pid file missing: ${pid_file}"
    return 1
  fi
  local pid
  pid="$(cat "${pid_file}")"
  if ! kill -0 "${pid}" 2>/dev/null; then
    echo "[start_all] ${name} failed to stay alive (pid ${pid})"
    return 1
  fi
  return 0
}

if [[ ! -d "${RUNTIME_DIR}" ]]; then
  echo "[start_all] unpacking runtime environment..."
  mkdir -p "${RUNTIME_DIR}"
  tar -xzf "${RUNTIME_ARCHIVE}" -C "${RUNTIME_DIR}"
fi
if [[ ! -f "${RUNTIME_DIR}/.unpacked_ok" ]]; then
  "${RUNTIME_DIR}/bin/python" "${RUNTIME_DIR}/bin/conda-unpack" >/dev/null 2>&1
  touch "${RUNTIME_DIR}/.unpacked_ok"
fi

if [[ -f "${PID_DIR}/api.pid" ]] && kill -0 "$(cat "${PID_DIR}/api.pid")" 2>/dev/null; then
  echo "[start_all] API already running with pid $(cat "${PID_DIR}/api.pid")"
else
  nohup bash "${BUNDLE_ROOT}/start_api.sh" >"${LOG_DIR}/api.log" 2>&1 &
  echo $! > "${PID_DIR}/api.pid"
  echo "[start_all] started API pid $(cat "${PID_DIR}/api.pid")"
fi

if [[ -f "${PID_DIR}/worker.pid" ]] && kill -0 "$(cat "${PID_DIR}/worker.pid")" 2>/dev/null; then
  echo "[start_all] worker already running with pid $(cat "${PID_DIR}/worker.pid")"
else
  nohup bash "${BUNDLE_ROOT}/start_worker.sh" >"${LOG_DIR}/worker.log" 2>&1 &
  echo $! > "${PID_DIR}/worker.pid"
  echo "[start_all] started worker pid $(cat "${PID_DIR}/worker.pid")"
fi

sleep 1
if ! verify_pid_running "api" "${PID_DIR}/api.pid"; then
  echo "[start_all] API log tail:"
  tail -n 80 "${LOG_DIR}/api.log" || true
  exit 1
fi
if ! verify_pid_running "worker" "${PID_DIR}/worker.pid"; then
  echo "[start_all] worker log tail:"
  tail -n 80 "${LOG_DIR}/worker.log" || true
  exit 1
fi

for _ in $(seq 1 60); do
  if "${RUNTIME_PY}" - "${API_URL}/health" <<'PY' >/dev/null 2>&1
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=2) as resp:
    if resp.status < 200 or resp.status >= 300:
        raise RuntimeError(f"bad status: {resp.status}")
PY
  then
    echo "[start_all] API health check passed at ${API_URL}/health"
    break
  fi
  sleep 1
done
if ! "${RUNTIME_PY}" - "${API_URL}/health" <<'PY' >/dev/null 2>&1
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=2) as resp:
    if resp.status < 200 or resp.status >= 300:
        raise RuntimeError(f"bad status: {resp.status}")
PY
then
  echo "[start_all] API health check failed at ${API_URL}/health"
  echo "[start_all] API log tail:"
  tail -n 80 "${LOG_DIR}/api.log" || true
  exit 1
fi

echo "[start_all] logs: ${LOG_DIR}/api.log , ${LOG_DIR}/worker.log"
