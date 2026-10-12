# Architecture Over Model Size: Control-Plane Dampening for Odysseus & Ajax

**Proving how modular systems engineering solves agent reliability, syntax collapse, and memory bloat on sub-14B models—without modifying the LLM or touching Odysseus source code.**

---

## 1. The Core Philosophy: Systems Engineering vs. Parameter Scaling

The modern AI industry reflex to agentic fragility is to throw more parameters at the problem—scaling to massive 200B+ frontier models or attempting costly fine-tuning. In physical systems engineering, however, you do not fix a vibrating chassis by carving a new shape of tire; you install shock absorbers.

When running local agents (sub-14B) on consumer hardware:
* **The LLM is the wheel:** A probabilistic rotational engine that works as designed.
* **The Breakdown is Mechanical Vibration (Entropy):** Probabilistic drift compounds across multi-turn trajectories until tool schemas crash, context rots, and VRAM balloons.
* **The Solution:** By decoupling the architecture into modular external nodes (T0 Invariant Kernel, T1 Memory Bus, Delimited Delimiters, and RRS compression), we regulate the linear event pipeline. We absorb entropy before it can shatter the runtime.

---

## 2. The Solution: Three Drop-In Middleware Dampeners
We engineered a lightweight, zero-dependency Python middleware harness that acts as a shock absorber between Odysseus and Ajax without requiring modifications to Felix's core workspace:

```
[ Odysseus Workspace ] <--- Standard OpenAI JSON ---> [ Semantic Interceptor Hook ] <--- RRS / Clean XML ---> [ Ajax (9B GGUF) ]
```

1. **The Semantic Interceptor Hook (`harness/semantic_hook.py`):**
   * **Downstream:** Strips verbose JSON schemas and passes compact **Rykr Reduced Semantics (RRS)** definitions to Ajax.
   * **Upstream:** Catches clean delimited tags (`<invoke tool="name">raw_script</invoke>`) and programmatically synthesizes 100% valid, escaped OpenAI JSON objects for Odysseus.
2. **The 3-Tier Memory Bus (`harness/memory_bus.py`):**
   * Pins system invariants in **T0 (The Kernel)**, caps working context under 4,000 tokens in **T1 (Working RAM)**, and serializes milestones to **T2 (Plain-Text Disk Logs)**, keeping VRAM flat.
3. **The Air-Gapped Sandbox (`sandbox/`):**
   * Docker-isolated workspace with network firewall rules blocking private LAN access and hardware cgroup caps (4 CPU cores, 16GB RAM) to eliminate host damage risks.

---

## 3. Empirical Benchmark Results (Tested on GTX 1080 Ti 11GB)

| Metric | Stock OpenAI JSON Schema | Dampened (RRS + Interceptor) | Empirical Gain |
| :--- | :--- | :--- | :--- |
| **Tool Prompt Overhead** | ~408 tokens (1,635 bytes) | **~111 tokens (447 bytes)** | **72.8% Token Reduction** |
| **Complex Pipe Escaping** | Syntax Errors / Escaping Drift | **0% Error Rate (100% Valid JSON)** | **Rock-Solid Reliability** |
| **Synthesis Latency** | N/A (Model generation) | **0.069 ms** | **Zero Latency Penalty** |
| **Active VRAM Footprint** | Escalates with turns (OOM risk) | **Flat (<4k Token Budget)** | **Ice-Cold Hardware** |

---

## 4. Live Field Evaluation & Operator Assessment

The middleware was validated in a live end-to-end sandbox deployment on native Pascal silicon (NecroBeast: GTX 1080 Ti 11GB + Ryzen 5 5600X) driving Felix's Odysseus Web UI:

* **Hardware & Runtime Metrics:**
  * **Sustained Inference Speed:** **30.05 tokens/s** on NVIDIA GeForce GTX 1080 Ti (sm_61).
  * **VRAM Allocation:** 10,160 MiB / 11,264 MiB (safe 1.1 GB headroom; secondary GPU completely free).
  * **Thermal Load:** 52°C–53°C under sustained multi-turn generation.
* **Systems Architecture Findings:**
  * **Multi-Threaded SSE Streaming:** Upgrading the interceptor to `ThreadingHTTPServer` with line-by-line SSE streaming delivered real-time token delivery while simultaneously serving Odysseus's background `/slots` and `/v1/models` health probes without TCP queue contention.
  * **Genesis Macro Governance:** Pinned T0 Kernel instructions successfully governed the sub-14B model via `~plan`, `~redteam`, and `~execute` macros, enforcing strict behavioral phases (e.g., zero code generation during planning) natively.
  * **Delimited Syntax Resilience:** 100% elimination of JSON escaping syntax crashes during tool execution.

> **Operator Qualitative Field Impression (Bill Fullen):**
> *"Testing was significantly better than I expected. Everything performed flawlessly: syntax, cadence, terms, honesty, macro commands, etc. I see no issues."*

---

## 5. Reproducing the Benchmark

Clone this repository and run the standalone benchmark suite:

```bash
# Run the benchmark test suite (zero external dependencies)
python3 tests/benchmark_json_vs_xml.py
```

---

## 6. Documentation & Engineering Audit Trail

* **Theoretical Paper:** [`docs/local_agent_architecture_rfc.md`](docs/local_agent_architecture_rfc.md) — *Detailed systems engineering white paper on control-plane dampening for autonomous daemons.*
* **Live Planning Transcript:** [`docs/portfolio_session_transcript.md`](docs/portfolio_session_transcript.md) — *1:1 unedited session record between systems engineer and orchestrator demonstrating the disciplined planning workflow.*

---

## Author & Contact
* **Engineer:** Bill Fullen (`tethtibis`) — Systems & Network Engineer
* **Ethos:** Sovereign, self-hosted, independent AI engineered to run reliably on affordable hardware.

