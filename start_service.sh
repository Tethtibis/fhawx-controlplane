#!/usr/bin/env bash
# ==============================================================================
# ODYSSEUS & AJAX AUTOMATED SERVICE LAUNCHER (NECROBEAST)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUDO_PASS="~Vitamin838!"

echo "========================================================================"
echo "STARTING ODYSSEUS & AJAX TESTING SETUP ON NECROBEAST"
echo "========================================================================"

# 1. Clean up any stale listeners on proxy ports
echo "[*] Ensuring proxy ports 8080 and 8081 are free..."
fuser -k 8080/tcp 2>/dev/null || true
fuser -k 8081/tcp 2>/dev/null || true

# 2. Verify Pascal Inference Engine (Ollama)
echo "[*] Checking Pascal Inference Engine (Ollama)..."
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "[*] Starting Ollama service..."
    echo "${SUDO_PASS}" | sudo -S systemctl start ollama
    sleep 2
fi

# 3. Verify ajax model exists in Ollama
if ! curl -s http://127.0.0.1:11434/api/tags | grep -q '"name":"ajax'; then
    echo "[*] Creating ajax model in Ollama from local GGUF..."
    GGUF_MODEL="${HOME}/fhawx-orchestrator/models/qwen2.5-coder-14b-instruct-q4_k_m.gguf"
    if [ -f "${GGUF_MODEL}" ]; then
        cat << 'EOF' > /tmp/Modelfile.ajax
FROM /home/tethtibis/fhawx-orchestrator/models/qwen2.5-coder-14b-instruct-q4_k_m.gguf
PARAMETER num_ctx 8192
EOF
        ollama create ajax -f /tmp/Modelfile.ajax
        rm -f /tmp/Modelfile.ajax
    else
        echo "[!] ERROR: Model GGUF not found at ${GGUF_MODEL}."
        exit 1
    fi
fi
echo "[+] Ollama ajax model verified."

# 4. Launch Semantic Interceptor Hook (RRS Adapter) on port 8080
echo "[*] Launching Semantic Interceptor Hook on 0.0.0.0:8080 in tmux..."
tmux kill-session -t odysseus_hook 2>/dev/null || true
tmux new-session -d -s odysseus_hook \
    "python3 '${SCRIPT_DIR}/harness/semantic_hook.py'"

# Wait up to 5s for hook to report ready
for i in {1..5}; do
    if curl -s http://127.0.0.1:8080/v1/models >/dev/null 2>&1; then
        echo "[+] Semantic Interceptor Hook is UP and proxying."
        break
    fi
    sleep 1
done

# 5. Enforce Air-Gap Network Wall via dedicated iptables chain
echo "[*] Enforcing Air-Gap Network Wall via iptables..."
echo "${SUDO_PASS}" | sudo -S bash "${SCRIPT_DIR}/sandbox/sandbox_firewall.sh" enable

# 6. Launch Odysseus Container
echo "[*] Launching Odysseus Sandbox Container..."
cd "${SCRIPT_DIR}/sandbox"
docker compose -f docker-compose.sandbox.yml up -d

# Wait up to 10s for Odysseus web interface to respond
echo "[*] Verifying Odysseus Web UI availability..."
for i in {1..10}; do
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7000/ 2>/dev/null | grep -qE "200|302"; then
        echo "[+] Odysseus Web UI is UP and responding."
        break
    fi
    sleep 1
done

echo "========================================================================"
echo "[+] ODYSSEUS TESTING STACK IS LIVE"
echo "    - Web Interface: http://192.168.0.200:7000"
echo "    - Localhost URL: http://127.0.0.1:7000"
echo "    - Model Engine:  Ajax / Qwen 2.5 Coder 14B (GTX 1080 Ti Pascal)"
echo "    - Middleware:    Semantic Interceptor Hook (0.0.0.0:8080)"
echo "    - Isolation:     Air-Gapped Network Wall active (LAN blocked)"
echo "    - Stop Command:  odysseus-stop (or ~/odysseus_ajax/stop_service.sh)"
echo "========================================================================"
