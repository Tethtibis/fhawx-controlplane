# AGENT RYKR: ARCHITECTURAL BACKLOG (ODYSSEUS / AJAX PROJECT)

This document captures lateral ideas, architectural optimizations, and non-blocking enhancements deferred during active Phase 3 execution to prevent scope creep.

---

## [BACKLOG-001] | Date: 2026-10-12 | Rykr Core RRS Token Compressor & Interceptor Hook
* **Source:** Operator inquiry during Odysseus/Ajax sandbox planning.
* **Concept:** Port the "Semantic Interceptor Hook" (RRS compression + Delimited Tag Interception) natively into the Rykr Core framework on Fhawx-Server.
* **Technical Value for Frontier Models:**
  * While frontier models (Gemini/Claude) do not suffer catastrophic JSON syntax crashes like sub-14B models, verbose JSON tool schemas and raw multi-turn JSON payloads still degrade cross-attention over extended 20+ turn trajectories.
  * Compressing incoming tool schemas into dense RRS notation and capturing delimited model outputs to synthesize native function calls reduces input token bloat by ~60–75%.
  * Lowers inference latency, minimizes attention dispersion, and tightens token economics across multi-hour sessions.
* **Status:** Deferred for dedicated testing after Odysseus/Ajax portfolio validation.

---

## [BACKLOG-002] | Date: 2026-10-12 | Major Component Substitution Protocol & Provenance Boundary
* **Source:** Operator directive during Odysseus/Ajax sandbox testing.
* **Concept:** Formally define the boundary between "administrative friction" (low-level plumbing that Rykr absorbs autonomously) and "architectural provenance" (substituting a primary model, dataset, or major software dependency).
* **Protocol Implementation:**
  * When a requested primary artifact (e.g., custom model weights, proprietary compiler, upstream binary) is unreleased, missing, or requires a proxy substitution, Rykr must explicitly flag the substitution in the turn header:
    `[COMPONENT SUBSTITUTION: <Requested Target> -> <Proxy Target> | Reason: <Unreleased/Missing>]`
  * Preserves operational velocity (avoids halting execution on minor blockers) while ensuring empirical rigor and data integrity for scientific/benchmark results.
* **Status:** Queued for Rykr Persona & Governance Protocol integration.
