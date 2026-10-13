#!/usr/bin/env bash
# ==============================================================================
# ODYSSEUS & AJAX SERVICE STATUS CHECKER (NECROBEAST)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUDO_PASS="~Vitamin838!"

echo "========================================================================"
echo "ODYSSEUS & AJAX STACK STATUS (NECROBEAST)"
echo "========================================================================"

# 1. Docker container status
echo -n "[1] Odysseus Container: "
if docker ps --format '{{.Names}} ({{.Status}})' | grep -q "^odysseus_sandbox"; then
    echo "RUNNING ($(docker ps --filter name=odysseus_sandbox --format '{{.Status}}'))"
else
    echo "STOPPED"
fi

# 2. Semantic Interceptor Hook (tmux & port 8080)
echo -n "[2] Semantic Interceptor Hook (port 8080): "
if curl -s http://127.0.0.1:8080/v1/models >/dev/null 2>&1; then
    echo "ACTIVE & PROXYING"
else
    echo "INACTIVE"
fi

# 3. Web UI (port 7000)
echo -n "[3] Odysseus Web Interface (port 7000): "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7000/ 2>/dev/null || echo "000")
if [ "${HTTP_CODE}" = "200" ] || [ "${HTTP_CODE}" = "302" ]; then
    echo "ONLINE (HTTP ${HTTP_CODE}) -> http://192.168.0.200:7000"
else
    echo "OFFLINE (HTTP ${HTTP_CODE})"
fi

# 4. Air-Gap Firewall Wall
echo -n "[4] Air-Gap Network Wall: "
if echo "${SUDO_PASS}" | sudo -S iptables -L ODYSSEUS_WALL -n >/dev/null 2>&1; then
    echo "ENFORCED"
else
    echo "NOT ENFORCED"
fi

# 5. Active Ollama Models in VRAM
echo "[5] Ollama Models currently loaded in VRAM:"
ACTIVE=$(ollama ps 2>/dev/null | awk 'NR>1 {print "    - " $1 " (" $3 ", " $4 " Context: " $5 ")"}' || true)
if [ -n "${ACTIVE}" ]; then
    echo "${ACTIVE}"
else
    echo "    (None - VRAM is completely clear)"
fi

# 6. GPU Memory Allocation (GTX 1080 Ti)
echo "[6] GPU Hardware State:"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader
echo "========================================================================"
