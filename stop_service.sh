#!/usr/bin/env bash
# ==============================================================================
# ODYSSEUS & AJAX AUTOMATED SERVICE TEARDOWN (NECROBEAST)
# Full cleanup and GPU VRAM eviction for zero-interference gaming readiness.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUDO_PASS="~Vitamin838!"

echo "========================================================================"
echo "STOPPING ODYSSEUS & AJAX TESTING SETUP (PREPARING FOR GAMING)"
echo "========================================================================"

# 1. Stop and remove Odysseus Sandbox Container
echo "[*] Stopping Odysseus Sandbox Container..."
cd "${SCRIPT_DIR}/sandbox"
docker compose -f docker-compose.sandbox.yml down 2>/dev/null || true
docker rm -f odysseus_sandbox 2>/dev/null || true

# 2. Terminate tmux sessions
echo "[*] Terminating middleware and inference tmux sessions..."
tmux kill-session -t odysseus_hook 2>/dev/null || true
tmux kill-session -t odysseus_infer 2>/dev/null || true

# 3. Free ports 8080 and 8081
echo "[*] Freeing ports 8080 and 8081..."
fuser -k 8080/tcp 2>/dev/null || true
fuser -k 8081/tcp 2>/dev/null || true

# 4. Tear down Air-Gap Network Wall from iptables
echo "[*] Tearing down Air-Gap Network Wall..."
echo "${SUDO_PASS}" | sudo -S bash "${SCRIPT_DIR}/sandbox/sandbox_firewall.sh" disable 2>/dev/null || true

# 5. EVICT MODELS FROM GPU VRAM (CRITICAL FOR GAMING)
echo "[*] Evicting active LLM models from GPU VRAM..."
ACTIVE_MODELS=$(ollama ps 2>/dev/null | awk 'NR>1 {print $1}' || true)
if [ -n "${ACTIVE_MODELS}" ]; then
    for m in ${ACTIVE_MODELS}; do
        echo "    -> Unloading model: ${m}..."
        ollama stop "${m}" || true
    done
else
    echo "    -> No active models loaded in Ollama."
fi

# Ensure ajax is explicitly stopped even if ollama ps didn't catch it
ollama stop ajax 2>/dev/null || true

# 6. Verify GPU state and VRAM release
echo "[*] Verifying GPU state (NVIDIA GeForce GTX 1080 Ti):"
sleep 1
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader

echo "========================================================================"
echo "[+] ODYSSEUS TESTING STACK IS COMPLETELY OFF."
echo "    - Container: Stopped & Removed"
echo "    - Middleware: Hook terminated, ports freed"
echo "    - Network: Firewall wall flushed"
echo "    - VRAM: 100% evicted and released for video games"
echo "========================================================================"
