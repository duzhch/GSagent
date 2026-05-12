#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
DATE_TAG="$(date +%Y%m%d-%H%M%S)"
GIT_SHA="$(cd "${ROOT_DIR}" && git rev-parse --short HEAD)"
OUT_SIF="${1:-${DIST_DIR}/gsagent-runtime-${DATE_TAG}-${GIT_SHA}.sif}"
BUILD_TMP="$(mktemp -d /tmp/gsagent-apptainer.XXXXXX)"
BUILD_CTX="${BUILD_TMP}/context"
ENGINE="${APPTAINER_ENGINE:-}"
EXTRA_ARGS="${APPTAINER_BUILD_ARGS:-}"

cleanup() {
  rm -rf "${BUILD_TMP}"
}
trap cleanup EXIT

if [[ -z "${ENGINE}" ]]; then
  if command -v apptainer >/dev/null 2>&1; then
    ENGINE="apptainer"
  elif command -v singularity >/dev/null 2>&1; then
    ENGINE="singularity"
  else
    if command -v module >/dev/null 2>&1; then
      module load Apptainer/1.3.3 >/dev/null 2>&1 || true
      module load Singularity/4.1.0/4.1.0 >/dev/null 2>&1 || true
    fi
    if command -v apptainer >/dev/null 2>&1; then
      ENGINE="apptainer"
    elif command -v singularity >/dev/null 2>&1; then
      ENGINE="singularity"
    else
      echo "[sif-build] ERROR: neither apptainer nor singularity is available."
      echo "[sif-build] Install Apptainer, or load cluster module then retry."
      exit 1
    fi
  fi
fi

mkdir -p "${DIST_DIR}" "${BUILD_CTX}"

echo "[sif-build] engine: ${ENGINE}"
echo "[sif-build] root: ${ROOT_DIR}"
echo "[sif-build] output: ${OUT_SIF}"
echo "[sif-build] build context: ${BUILD_CTX}"

rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude ".pytest_cache" \
  --exclude ".build" \
  --exclude "dist" \
  --exclude "runs" \
  --exclude "__pycache__" \
  --exclude "*.pyc" \
  "${ROOT_DIR}/" "${BUILD_CTX}/"

DEF_FILE="${BUILD_CTX}/packaging/singularity/Apptainer.def"
if [[ ! -f "${DEF_FILE}" ]]; then
  echo "[sif-build] ERROR: def file missing: ${DEF_FILE}"
  exit 1
fi

DEFAULT_ARGS=""
if [[ "${EUID}" -ne 0 && -z "${EXTRA_ARGS}" ]]; then
  DEFAULT_ARGS="--fakeroot"
fi

if [[ -n "${EXTRA_ARGS}" ]]; then
  # shellcheck disable=SC2086
  "${ENGINE}" build ${EXTRA_ARGS} "${OUT_SIF}" "${DEF_FILE}"
elif [[ -n "${DEFAULT_ARGS}" ]]; then
  # shellcheck disable=SC2086
  "${ENGINE}" build ${DEFAULT_ARGS} "${OUT_SIF}" "${DEF_FILE}" || {
    user_name="$(id -un)"
    if [[ ! -r /etc/subuid ]] || ! grep -q "^${user_name}:" /etc/subuid; then
      echo "[sif-build] ERROR: fakeroot requires /etc/subuid mapping for ${user_name}."
      echo "[sif-build] Ask admin to add subuid/subgid mapping, or run with:"
      echo "[sif-build]   APPTAINER_BUILD_ARGS='--remote' bash packaging/singularity/build_sif.sh"
      echo "[sif-build] and login first via: singularity remote login"
    fi
    exit 1
  }
else
  "${ENGINE}" build "${OUT_SIF}" "${DEF_FILE}"
fi

echo "[sif-build] DONE: ${OUT_SIF}"
