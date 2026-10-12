#!/usr/bin/env python3
"""
==============================================================================
PASCAL INFERENCE DAEMON RUNNER (NECROBEAST GTX 1080 Ti)
==============================================================================
Launches llama-server optimized for NVIDIA GeForce GTX 1080 Ti (Pascal sm_61)
and AMD Ryzen 5 5600X CPU constraints.

Hardware Tuning Parameters:
- GPU Offload: -ngl 99 (Full VRAM offload to 11GB GTX 1080 Ti)
- Context Limit: -c 8192 (Caps KV-cache to ~2.2GB, preventing Pascal OOM)
- CPU Thread Cap: -t 4 (Prevents 100% saturation and thermal throttling on 5600X)
- Port: 8081 (Internal upstream port; Semantic Hook fronts it on 8080)
"""

import os
import sys
import subprocess
import shutil

DEFAULT_MODEL_PATH = os.path.expanduser("~/models/ajax-qwen2.5-coder-7b-q4_k_m.gguf")
SERVER_PORT = 8081
CONTEXT_SIZE = 8192
CPU_THREADS = 4
GPU_LAYERS = 99


def find_llama_server() -> str:
    """Finds llama-server binary in PATH or common build locations."""
    path = shutil.which("llama-server")
    if path:
        return path
    
    common_paths = [
        "/usr/local/bin/llama-server",
        os.path.expanduser("~/.local/bin/llama-server"),
        os.path.expanduser("~/llama.cpp/build/bin/llama-server"),
        os.path.expanduser("~/llama.cpp/llama-server")
    ]
    for p in common_paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return "llama-server"


def start_server(model_path: str = DEFAULT_MODEL_PATH, port: int = SERVER_PORT):
    binary = find_llama_server()
    cmd = [
        binary,
        "-m", model_path,
        "-c", str(CONTEXT_SIZE),
        "-ngl", str(GPU_LAYERS),
        "-t", str(CPU_THREADS),
        "--port", str(port),
        "--host", "127.0.0.1",
        "--no-web-ui"
    ]

    print("[*] Launching Pascal Inference Daemon on NecroBeast...")
    print(f"    - Binary: {binary}")
    print(f"    - Model: {model_path}")
    print(f"    - GPU Layers: {GPU_LAYERS} (GTX 1080 Ti Pascal)")
    print(f"    - Context Window: {CONTEXT_SIZE} tokens")
    print(f"    - CPU Threads: {CPU_THREADS} (Ryzen 5600X thermal cap)")
    print(f"    - Listening: 127.0.0.1:{port}")

    try:
        proc = subprocess.Popen(cmd)
        proc.wait()
    except KeyboardInterrupt:
        print("\n[*] Shutting down inference daemon cleanly.")
        proc.terminate()
    except Exception as e:
        print(f"[!] Inference engine failed to start: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    target_model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL_PATH
    start_server(target_model)
