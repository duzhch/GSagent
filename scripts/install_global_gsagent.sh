#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${HOME}/.local/bin"
TARGET_BIN="${TARGET_DIR}/gsagent"

mkdir -p "${TARGET_DIR}"

cat > "${TARGET_BIN}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="${ROOT_DIR}"

if [[ -x "\${ROOT_DIR}/.venv/bin/python" ]]; then
  export PYTHONPATH="\${ROOT_DIR}/src:\${PYTHONPATH:-}"
  exec "\${ROOT_DIR}/.venv/bin/python" -m animal_gs_agent.cli "\$@"
fi

export PYTHONPATH="\${ROOT_DIR}/src:\${PYTHONPATH:-}"
if command -v python3 >/dev/null 2>&1; then
  exec python3 -m animal_gs_agent.cli "\$@"
elif command -v python >/dev/null 2>&1; then
  exec python -m animal_gs_agent.cli "\$@"
fi

echo "[gsagent] python runtime not found (expected python3 or python)." >&2
exit 127
EOF

chmod +x "${TARGET_BIN}"

echo "[install] installed ${TARGET_BIN}"
echo "[install] verify with: gsagent --help"

if [[ ":${PATH}:" != *":${TARGET_DIR}:"* ]]; then
  echo "[install] WARNING: ${TARGET_DIR} is not in PATH."
  echo "[install] add to shell rc:"
  echo "export PATH=\"${TARGET_DIR}:\$PATH\""
fi
