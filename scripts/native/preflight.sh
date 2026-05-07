#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "[preflight] repository: ${ROOT_DIR}"

if ! command -v python >/dev/null 2>&1; then
  echo "[preflight] ERROR: python not found in PATH"
  exit 1
fi

if ! command -v nextflow >/dev/null 2>&1; then
  echo "[preflight] ERROR: nextflow not found in PATH"
  exit 1
fi

if ! command -v plink2 >/dev/null 2>&1; then
  echo "[preflight] ERROR: plink2 not found in PATH"
  exit 1
fi

if ! command -v Rscript >/dev/null 2>&1; then
  echo "[preflight] ERROR: Rscript not found in PATH"
  exit 1
fi

if [[ -z "${ANIMAL_GS_AGENT_LLM_BASE_URL:-}" ]]; then
  echo "[preflight] ERROR: ANIMAL_GS_AGENT_LLM_BASE_URL is not set"
  exit 1
fi
if [[ -z "${ANIMAL_GS_AGENT_LLM_API_KEY:-}" ]]; then
  echo "[preflight] ERROR: ANIMAL_GS_AGENT_LLM_API_KEY is not set"
  exit 1
fi
if [[ -z "${ANIMAL_GS_AGENT_LLM_MODEL:-}" ]]; then
  echo "[preflight] ERROR: ANIMAL_GS_AGENT_LLM_MODEL is not set"
  exit 1
fi

PIPELINE_DIR="${ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR:-/work/home/zyqlab/dzhichao/Agent0428/gs_prototype/pipeline}"
if [[ ! -f "${PIPELINE_DIR}/main.nf" ]]; then
  echo "[preflight] ERROR: ${PIPELINE_DIR}/main.nf not found"
  exit 1
fi

echo "[preflight] OK: environment and dependencies are ready"
