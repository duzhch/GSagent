#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_ROOT="${ROOT_DIR}/.build/offline_bundle"
DIST_DIR="${ROOT_DIR}/dist"
REUSE_ENV="${ANIMAL_GS_AGENT_RELEASE_REUSE_ENV:-0}"

PIPELINE_SOURCE_DEFAULT="${ROOT_DIR}/../gs_prototype/pipeline"
DATA_SOURCE_DEFAULT="${ROOT_DIR}/../gs_prototype/data"
PIPELINE_SOURCE="${ANIMAL_GS_AGENT_PIPELINE_SOURCE:-${PIPELINE_SOURCE_DEFAULT}}"
DATA_SOURCE="${ANIMAL_GS_AGENT_DATA_SOURCE:-${DATA_SOURCE_DEFAULT}}"

CONDA_BIN_DEFAULT="/work/home/zyqlab/dzhichao/zyqgroup01_duanzhichao/miniconda3/bin/conda"
CONDA_BIN="${CONDA_BIN:-${CONDA_BIN_DEFAULT}}"

if [[ ! -x "${CONDA_BIN}" ]]; then
  echo "[release] ERROR: conda binary not found at ${CONDA_BIN}"
  exit 1
fi

if [[ ! -f "${PIPELINE_SOURCE}/main.nf" ]]; then
  echo "[release] ERROR: pipeline source missing: ${PIPELINE_SOURCE}/main.nf"
  exit 1
fi

if [[ ! -f "${DATA_SOURCE}/phenotypes.csv" || ! -f "${DATA_SOURCE}/genotypes.vcf" ]]; then
  echo "[release] ERROR: demo data missing in ${DATA_SOURCE}"
  exit 1
fi

GIT_SHA="$(cd "${ROOT_DIR}" && git rev-parse --short HEAD)"
if (cd "${ROOT_DIR}" && git diff --quiet --ignore-submodules HEAD --); then
  TREE_TAG="${GIT_SHA}"
else
  TREE_TAG="${GIT_SHA}-dirty"
fi
DATE_TAG="$(date +%Y%m%d-%H%M%S)"
PKG_NAME="animal-gs-agent-offline-${DATE_TAG}-${TREE_TAG}"
PKG_ROOT="${BUILD_ROOT}/${PKG_NAME}"
ENV_PREFIX="${BUILD_ROOT}/runtime_env"

echo "[release] root: ${ROOT_DIR}"
echo "[release] package: ${PKG_NAME}"
echo "[release] build root: ${BUILD_ROOT}"

if [[ "${REUSE_ENV}" == "1" && -d "${ENV_PREFIX}" ]]; then
  echo "[release] reusing existing runtime environment at ${ENV_PREFIX}"
  rm -rf "${PKG_ROOT}"
  mkdir -p "${PKG_ROOT}" "${DIST_DIR}"
else
  rm -rf "${BUILD_ROOT}"
  mkdir -p "${PKG_ROOT}" "${DIST_DIR}"

  echo "[release] creating runtime environment..."
  "${CONDA_BIN}" create -y -p "${ENV_PREFIX}" \
    -c conda-forge \
    -c bioconda \
    python=3.10 \
    pip \
    fastapi \
    uvicorn \
    pydantic \
    httpx \
    langgraph \
    nextflow \
    plink2 \
    openjdk=17 \
    r-base \
    r-jsonlite \
    r-data.table \
    r-bglr \
    pytest
fi

echo "[release] installing conda-pack in runtime environment..."
"${CONDA_BIN}" run -p "${ENV_PREFIX}" python -m pip install --quiet conda-pack

echo "[release] validating runtime tools..."
"${CONDA_BIN}" run -p "${ENV_PREFIX}" bash -lc '
set -euo pipefail
python -V
nextflow -version
plink2 --version | head -n 1
Rscript -e "suppressMessages(library(BGLR)); suppressMessages(library(data.table)); suppressMessages(library(jsonlite)); cat(\"R_PKGS_OK\n\")"
'

echo "[release] packing runtime environment..."
"${CONDA_BIN}" run -p "${ENV_PREFIX}" conda-pack \
  -p "${ENV_PREFIX}" \
  -o "${PKG_ROOT}/runtime_env.tar.gz"

echo "[release] copying application source..."
mkdir -p "${PKG_ROOT}/app"
rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude ".pytest_cache" \
  --exclude ".build" \
  --exclude "dist" \
  --exclude "runs" \
  --exclude "__pycache__" \
  --exclude "*.pyc" \
  --exclude "src/*.egg-info" \
  "${ROOT_DIR}/" "${PKG_ROOT}/app/"

echo "[release] copying fixed pipeline and demo data..."
mkdir -p "${PKG_ROOT}/assets/pipeline" "${PKG_ROOT}/assets/data"
rsync -a \
  --exclude ".nextflow" \
  --exclude ".nextflow*" \
  --exclude "work" \
  "${PIPELINE_SOURCE}/" "${PKG_ROOT}/assets/pipeline/"
cp -f "${DATA_SOURCE}/phenotypes.csv" "${PKG_ROOT}/assets/data/phenotypes.csv"
cp -f "${DATA_SOURCE}/genotypes.vcf" "${PKG_ROOT}/assets/data/genotypes.vcf"
if [[ -f "${DATA_SOURCE}/metadata.yaml" ]]; then
  cp -f "${DATA_SOURCE}/metadata.yaml" "${PKG_ROOT}/assets/data/metadata.yaml"
fi

mkdir -p "${PKG_ROOT}/state" "${PKG_ROOT}/runs" "${PKG_ROOT}/logs"

echo "[release] installing runtime entry scripts..."
cp -f "${ROOT_DIR}/packaging/release/templates/"*.sh "${PKG_ROOT}/"
chmod +x "${PKG_ROOT}/"*.sh

cat > "${PKG_ROOT}/.env.example" <<EOF
# Optional LLM provider. Leave empty to use local heuristic parsing.
ANIMAL_GS_AGENT_LLM_BASE_URL=
ANIMAL_GS_AGENT_LLM_API_KEY=
ANIMAL_GS_AGENT_LLM_MODEL=

ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED=1
ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY=local
ANIMAL_GS_AGENT_WORKFLOW_PIPELINE_DIR=\${BUNDLE_ROOT}/assets/pipeline
ANIMAL_GS_AGENT_WORKFLOW_OUTPUT_ROOT=\${BUNDLE_ROOT}/runs
ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH=\${BUNDLE_ROOT}/state/jobs_store.db
ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH=\${BUNDLE_ROOT}/state/run_queue.db
ANIMAL_GS_AGENT_LLM_TIMEOUT_SECONDS=30
EOF

cp -f "${ROOT_DIR}/packaging/release/README_OFFLINE.md" "${PKG_ROOT}/README.md"

echo "[release] creating final archive..."
(
  cd "${BUILD_ROOT}"
  tar -czf "${DIST_DIR}/${PKG_NAME}.tar.gz" "${PKG_NAME}"
)

echo "[release] DONE"
echo "[release] output archive: ${DIST_DIR}/${PKG_NAME}.tar.gz"
echo "[release] unpacked package: ${PKG_ROOT}"
