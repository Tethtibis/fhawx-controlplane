#!/usr/bin/env bash
# ==============================================================================
# ODYSSEUS SANDBOX: AIR-GAP NETWORK FIREWALL ENFORCER
# Prevents any sandboxed AI processes from discovering, scanning, or routing
# to local LAN networks (192.168.0.0/16, etc.) or host management interfaces.
# ==============================================================================

set -euo pipefail

SUBNET="172.28.0.0/24"
HOST_GW="172.28.0.1"
INFERENCE_PORT="8080"

echo "[*] Initializing Network Wall for Odysseus Sandbox (${SUBNET})..."

# Ensure iptables is available
if ! command -v iptables &>/dev/null; then
    echo "[!] Error: iptables not found on host."
    exit 1
fi

# 1. Allow established and related connections (so responses to inbound UI traffic work)
sudo iptables -I FORWARD 1 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT || true

# 2. Allow container to access host inference port strictly on the gateway
sudo iptables -I FORWARD 2 -s "${SUBNET}" -d "${HOST_GW}" -p tcp --dport "${INFERENCE_PORT}" -j ACCEPT || true

# 3. Block all NEW outbound connections initiated by the sandbox to the local home network (192.168.0.0/16)
sudo iptables -I FORWARD 3 -s "${SUBNET}" -d 192.168.0.0/16 -m conntrack --ctstate NEW -j DROP || true

# 4. Block all NEW outbound connections to standard private network ranges (RFC 1918)
sudo iptables -I FORWARD 4 -s "${SUBNET}" -d 10.0.0.0/8 -m conntrack --ctstate NEW -j DROP || true
sudo iptables -I FORWARD 5 -s "${SUBNET}" -d 172.16.0.0/12 -m conntrack --ctstate NEW -j DROP || true

# 5. Block Link-Local / Multicast discovery (mDNS / SSDP / LLMNR)
sudo iptables -I FORWARD 6 -s "${SUBNET}" -d 224.0.0.0/4 -j DROP || true
sudo iptables -I FORWARD 7 -s "${SUBNET}" -d 169.254.0.0/16 -j DROP || true

echo "[+] Network Wall enforced successfully."
echo "    - Host Inference (port ${INFERENCE_PORT}): ALLOWED"
echo "    - Private LAN (192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12): BLOCKED (DROP)"
