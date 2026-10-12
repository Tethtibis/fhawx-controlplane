#!/usr/bin/env bash
# ==============================================================================
# ODYSSEUS SANDBOX: SECURE LAUNCHER
# Enforces firewall containment rules and launches the isolated Odysseus container.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${SCRIPT_DIR}/workspace"

echo "[*] Initializing Odysseus Sandbox Launch Sequence..."

# 1. Ensure scratch workspace exists
mkdir -p "${WORKSPACE_DIR}"
chmod 777 "${WORKSPACE_DIR}"

# 2. Enforce Network Wall
if [ -f "${SCRIPT_DIR}/sandbox_firewall.sh" ]; then
    bash "${SCRIPT_DIR}/sandbox_firewall.sh"
fi

# 3. Spin up isolated Docker Compose service
cd "${SCRIPT_DIR}"
echo "[*] Starting odysseus_sandbox container..."
docker compose -f docker-compose.sandbox.yml up -d

echo "[+] Odysseus Sandbox is running in strict isolation."
echo "    - UI accessible at: http://127.0.0.1:8000"
echo "    - Workspace: ${WORKSPACE_DIR}"
echo "    - LAN Access: BLOCKED"
echo "    - To reset/nuke: ./destroy_sandbox.sh"
