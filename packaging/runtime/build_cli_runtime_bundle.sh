#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${1:-${ROOT_DIR}/dist/gsagent-cli-runtime-${DATE_TAG}}"

mkdir -p "${OUT_DIR}/wheels"

echo "[bundle] root: ${ROOT_DIR}"
echo "[bundle] output: ${OUT_DIR}"

cd "${ROOT_DIR}"

echo "[bundle] build wheel (no deps)"
python -m pip wheel --no-deps . -w "${OUT_DIR}/wheels"

echo "[bundle] copy runtime environment template"
cp "${ROOT_DIR}/packaging/runtime/environment.yml" "${OUT_DIR}/environment.yml"
cp "${ROOT_DIR}/packaging/runtime/install_runtime.sh" "${OUT_DIR}/install_runtime.sh"
chmod +x "${OUT_DIR}/install_runtime.sh"

cat > "${OUT_DIR}/README_RUNTIME_BUNDLE.txt" <<'EOF'
GSAgent CLI Runtime Bundle
==========================

1) Create/refresh runtime env
   bash install_runtime.sh

2) Activate env
   conda activate gsagent_runtime

3) Use CLI from any location
   gsagent preflight --workdir /path/to/project
   gsagent serve --workdir /path/to/project --host 0.0.0.0 --port 8000
   gsagent worker --workdir /path/to/project
EOF

echo "[bundle] done"
