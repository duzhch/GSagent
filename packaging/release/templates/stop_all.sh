#!/usr/bin/env bash
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${BUNDLE_ROOT}/state"

stop_pid_file() {
  local name="$1"
  local pid_file="$2"
  if [[ ! -f "${pid_file}" ]]; then
    echo "[stop_all] ${name}: no pid file"
    return
  fi
  local pid
  pid="$(cat "${pid_file}")"
  if kill -0 "${pid}" 2>/dev/null; then
    kill "${pid}" || true
    sleep 1
    if kill -0 "${pid}" 2>/dev/null; then
      kill -9 "${pid}" || true
    fi
    echo "[stop_all] ${name}: stopped pid ${pid}"
  else
    echo "[stop_all] ${name}: process already exited"
  fi
  rm -f "${pid_file}"
}

stop_pid_file "worker" "${PID_DIR}/worker.pid"
stop_pid_file "api" "${PID_DIR}/api.pid"
