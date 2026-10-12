#!/usr/bin/env bash
# ==============================================================================
# ODYSSEUS SANDBOX: 1-SECOND NUKE & RESET SWITCH
# Immediately terminates the sandbox container and wipes all ephemeral scratch
# data, returning the environment to a pristine state.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${SCRIPT_DIR}/workspace"

echo "[!] NUKE TRIGGERED: Tearing down Odysseus Sandbox..."

# 1. Force kill and remove container
if docker ps -a --format '{{.Names}}' | grep -q "^odysseus_sandbox$"; then
    echo "[*] Killing odysseus_sandbox container..."
    docker rm -f odysseus_sandbox >/dev/null 2>&1 || true
fi

# 2. Wipe workspace scratch directory completely
if [ -d "${WORKSPACE_DIR}" ]; then
    echo "[*] Purging workspace scratch directory..."
    rm -rf "${WORKSPACE_DIR}"
fi

# 3. Re-create clean empty workspace
mkdir -p "${WORKSPACE_DIR}"
chmod 777 "${WORKSPACE_DIR}"

echo "[+] Sandbox destroyed and reset cleanly."
