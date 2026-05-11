#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${GSAGENT_ENV_NAME:-gsagent_runtime}"
TARGET_BIN_DIR="${HOME}/.local/bin"
TARGET_BIN="${TARGET_BIN_DIR}/gsagent"
MINIFORGE_DIR="${HOME}/miniforge3"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install_easy_gsagent.sh [--env-name <name>]

Features:
  1) Auto-install Miniforge when conda is missing
  2) Create/update runtime env with plink2/nextflow/Rscript dependencies
  3) Install animal-gs-agent into the runtime env
  4) Install global `gsagent` launcher to ~/.local/bin
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--env-name" ]]; then
  if [[ -z "${2:-}" ]]; then
    echo "[easy-install] ERROR: --env-name requires a value"
    exit 1
  fi
  ENV_NAME="${2}"
fi

_require_command() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "[easy-install] ERROR: required command not found: ${cmd}"
    exit 1
  fi
}

_ensure_conda() {
  if command -v conda >/dev/null 2>&1; then
    return 0
  fi

  _require_command curl
  _require_command bash

  local os arch installer url tmp
  os="$(uname -s)"
  arch="$(uname -m)"

  case "${arch}" in
    x86_64|amd64)
      arch="x86_64"
      ;;
    aarch64|arm64)
      arch="aarch64"
      ;;
    ppc64le)
      arch="ppc64le"
      ;;
    *)
      echo "[easy-install] ERROR: unsupported architecture for auto Miniforge install: ${arch}"
      exit 1
      ;;
  esac

  installer="Miniforge3-${os}-${arch}.sh"
  url="https://github.com/conda-forge/miniforge/releases/latest/download/${installer}"
  tmp="$(mktemp -d /tmp/gsagent-install.XXXXXX)"

  echo "[easy-install] conda not found, installing Miniforge to ${MINIFORGE_DIR}"
  curl --max-time 120 -fsSL "${url}" -o "${tmp}/${installer}"
  bash "${tmp}/${installer}" -b -p "${MINIFORGE_DIR}"

  # shellcheck source=/dev/null
  source "${MINIFORGE_DIR}/etc/profile.d/conda.sh"
}

_conda_bin() {
  if command -v conda >/dev/null 2>&1; then
    command -v conda
    return 0
  fi
  if [[ -x "${MINIFORGE_DIR}/bin/conda" ]]; then
    echo "${MINIFORGE_DIR}/bin/conda"
    return 0
  fi
  echo "[easy-install] ERROR: conda binary not found after installation"
  exit 1
}

echo "[easy-install] project root: ${ROOT_DIR}"
_ensure_conda
CONDA_BIN="$(_conda_bin)"
echo "[easy-install] using conda: ${CONDA_BIN}"

echo "[easy-install] create/update environment: ${ENV_NAME}"
"${CONDA_BIN}" env create -n "${ENV_NAME}" -f "${ROOT_DIR}/packaging/native/environment.yml" || \
"${CONDA_BIN}" env update -n "${ENV_NAME}" -f "${ROOT_DIR}/packaging/native/environment.yml"

echo "[easy-install] install project package into env"
"${CONDA_BIN}" run -n "${ENV_NAME}" python -m pip install -e "${ROOT_DIR}"

echo "[easy-install] verify core runtime tools"
"${CONDA_BIN}" run -n "${ENV_NAME}" bash -lc '
set -euo pipefail
python -V
nextflow -version >/dev/null
plink2 --version | head -n 1
Rscript -e "suppressMessages(library(jsonlite)); cat(\"R_OK\n\")"
'

mkdir -p "${TARGET_BIN_DIR}"
cat > "${TARGET_BIN}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
CONDA_BIN="${CONDA_BIN}"
ENV_NAME="${ENV_NAME}"
if [[ -x "\${CONDA_BIN}" ]]; then
  exec "\${CONDA_BIN}" run -n "\${ENV_NAME}" python -m animal_gs_agent.cli "\$@"
fi
if command -v conda >/dev/null 2>&1; then
  exec conda run -n "\${ENV_NAME}" python -m animal_gs_agent.cli "\$@"
fi
echo "[gsagent] conda is not available. please run install script again." >&2
exit 127
EOF
chmod +x "${TARGET_BIN}"

echo "[easy-install] installed launcher: ${TARGET_BIN}"
if [[ ":${PATH}:" != *":${TARGET_BIN_DIR}:"* ]]; then
  echo "[easy-install] add to PATH:"
  echo "  export PATH=\"${TARGET_BIN_DIR}:\$PATH\""
fi

echo "[easy-install] smoke check: gsagent preflight --workdir ${ROOT_DIR}"
echo "[easy-install] done"
