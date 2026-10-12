#!/usr/bin/env bash
# ==============================================================================
# ODYSSEUS & AJAX AUTOMATED SERVICE TEARDOWN (NECROBEAST)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUDO_PASS="~Vitamin838!"

echo "[*] Stopping Odysseus Sandbox Container..."
cd "${SCRIPT_DIR}/sandbox"
echo "${SUDO_PASS}" | sudo -S docker compose -f docker-compose.sandbox.yml down || true

echo "[*] Terminating tmux sessions (Inference & Semantic Hook)..."
tmux kill-session -t odysseus_hook 2>/dev/null || true
tmux kill-session -t odysseus_infer 2>/dev/null || true

echo "[*] Freeing ports 8080 and 8081..."
fuser -k 8080/tcp 2>/dev/null || true
fuser -k 8081/tcp 2>/dev/null || true

echo "[+] Odysseus service and inference engines stopped cleanly. GPU VRAM released."
