#!/usr/bin/env bash
# ==============================================================================
# ODYSSEUS & AJAX AUTOMATED SERVICE LAUNCHER (NECROBEAST)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_PATH="${HOME}/fhawx-orchestrator/models/qwen2.5-coder-14b-instruct-q4_k_m.gguf"
VENV_PYTHON="${HOME}/fhawx-orchestrator/.venv/bin/python3"
SUDO_PASS="~Vitamin838!"

echo "========================================================================"
echo "STARTING ODYSSEUS & AJAX SANDBOXED SERVICE ON NECROBEAST"
echo "========================================================================"

# 1. Kill any stale processes on ports 8080 or 8081
echo "[*] Cleaning up any old listeners..."
fuser -k 8080/tcp 2>/dev/null || true
fuser -k 8081/tcp 2>/dev/null || true

# 2. Verify Pascal Inference Engine (Ollama 14B on GTX 1080 Ti Pascal)
echo "[*] Verifying Pascal Inference Engine (Ollama Ajax / Qwen 14B on port 11434)..."
if ! curl -s http://127.0.0.1:11434/api/tags | grep -q "ajax"; then
    echo "[*] Creating ajax model in Ollama from local GGUF..."
    cat << 'EOF' > /tmp/Modelfile.ajax
FROM /home/tethtibis/fhawx-orchestrator/models/qwen2.5-coder-14b-instruct-q4_k_m.gguf
PARAMETER num_ctx 8192
EOF
    ollama create ajax -f /tmp/Modelfile.ajax
fi
echo "[+] Pascal Inference Engine is UP."

# 3. Launch Semantic Interceptor Hook (RRS Adapter) on port 8080
echo "[*] Launching Semantic Interceptor Hook on 0.0.0.0:8080..."
tmux new-session -d -s odysseus_hook \
    "python3 '${SCRIPT_DIR}/harness/semantic_hook.py'"

sleep 2
if curl -s http://127.0.0.1:8080/v1/models >/dev/null 2>&1; then
    echo "[+] Semantic Interceptor Hook is UP and proxying."
else
    echo "[!] Warning: Hook health check did not return 200 immediately, continuing..."
fi

# 4. Enforce Air-Gap Network Wall
echo "[*] Enforcing Network Wall via iptables..."
echo "${SUDO_PASS}" | sudo -S bash "${SCRIPT_DIR}/sandbox/sandbox_firewall.sh"

# 5. Launch Odysseus Container
echo "[*] Launching Odysseus Sandbox Container..."
cd "${SCRIPT_DIR}/sandbox"
echo "${SUDO_PASS}" | sudo -S docker compose -f docker-compose.sandbox.yml up -d

echo "========================================================================"
echo "[+] ODYSSEUS STACK IS LIVE AND READY FOR TESTING!"
echo "    - Web Interface: http://192.168.0.200:7000"
echo "    - Model Engine: Ajax / Qwen 2.5 Coder 14B (GTX 1080 Ti Pascal)"
echo "    - Middleware: Semantic Interceptor Hook (port 8080)"
echo "    - Isolation: Air-Gapped Network Wall active (LAN access blocked)"
echo "    - Stop Command: ./stop_service.sh"
echo "========================================================================"
