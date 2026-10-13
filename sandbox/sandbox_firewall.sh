#!/usr/bin/env bash
# ==============================================================================
# ODYSSEUS SANDBOX: AIR-GAP NETWORK FIREWALL ENFORCER
# Prevents any sandboxed AI processes from discovering, scanning, or routing
# to local LAN networks (192.168.0.0/16, etc.) or host management interfaces.
# ==============================================================================

set -euo pipefail

ACTION="${1:-enable}"
SUBNET="172.28.0.0/24"
HOST_GW="172.28.0.1"
INFERENCE_PORT="8080"
CHAIN_NAME="ODYSSEUS_WALL"

if ! command -v iptables &>/dev/null; then
    echo "[!] Error: iptables not found on host."
    exit 1
fi

case "${ACTION}" in
    enable|start|on)
        echo "[*] Enforcing Network Wall for Odysseus Sandbox (${SUBNET})..."
        # Create chain if it doesn't exist, flush it if it does
        sudo iptables -N "${CHAIN_NAME}" 2>/dev/null || sudo iptables -F "${CHAIN_NAME}"
        
        # Ensure chain is hooked into FORWARD at top
        if ! sudo iptables -C FORWARD -j "${CHAIN_NAME}" 2>/dev/null; then
            sudo iptables -I FORWARD 1 -j "${CHAIN_NAME}"
        fi

        # 1. Allow established and related connections
        sudo iptables -A "${CHAIN_NAME}" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

        # 2. Allow container to access host inference port strictly on the gateway
        sudo iptables -A "${CHAIN_NAME}" -s "${SUBNET}" -d "${HOST_GW}" -p tcp --dport "${INFERENCE_PORT}" -j ACCEPT

        # 3. Block all NEW outbound connections to local home network
        sudo iptables -A "${CHAIN_NAME}" -s "${SUBNET}" -d 192.168.0.0/16 -m conntrack --ctstate NEW -j DROP

        # 4. Block all NEW outbound connections to private network ranges
        sudo iptables -A "${CHAIN_NAME}" -s "${SUBNET}" -d 10.0.0.0/8 -m conntrack --ctstate NEW -j DROP
        sudo iptables -A "${CHAIN_NAME}" -s "${SUBNET}" -d 172.16.0.0/12 -m conntrack --ctstate NEW -j DROP

        # 5. Block Link-Local / Multicast discovery
        sudo iptables -A "${CHAIN_NAME}" -s "${SUBNET}" -d 224.0.0.0/4 -j DROP
        sudo iptables -A "${CHAIN_NAME}" -s "${SUBNET}" -d 169.254.0.0/16 -j DROP

        echo "[+] Network Wall enforced successfully in chain ${CHAIN_NAME}."
        ;;

    disable|stop|off)
        echo "[*] Tearing down Network Wall for Odysseus Sandbox..."
        # Remove jump from FORWARD
        while sudo iptables -C FORWARD -j "${CHAIN_NAME}" 2>/dev/null; do
            sudo iptables -D FORWARD -j "${CHAIN_NAME}" 2>/dev/null || break
        done
        # Flush and delete user chain
        sudo iptables -F "${CHAIN_NAME}" 2>/dev/null || true
        sudo iptables -X "${CHAIN_NAME}" 2>/dev/null || true
        echo "[+] Network Wall removed cleanly."
        ;;

    status)
        if sudo iptables -L "${CHAIN_NAME}" -n >/dev/null 2>&1; then
            echo "[+] Network Wall is ACTIVE."
            sudo iptables -L "${CHAIN_NAME}" -n -v --line-numbers
        else
            echo "[-] Network Wall is INACTIVE."
        fi
        ;;

    *)
        echo "Usage: $0 {enable|disable|status}"
        exit 1
        ;;
esac
