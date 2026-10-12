#!/usr/bin/env python3
"""
==============================================================================
3-TIER HIERARCHICAL MEMORY BUS (CONTROL-PLANE DAMPENER)
==============================================================================
Implements Pattern 1 from the Architectural RFC for local agent harnesses:
- T0 (The Kernel): Immutable system invariants pinned statically at head.
- T1 (Working RAM): Ephemeral context buffer capped at 4,000 tokens. Flushed via [MEM_COMMIT].
- T2 (The Archive): Sequential, high-density disk logs ([REF-###]) stored in plain-text markdown.
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional

DEFAULT_MAX_WORKING_TOKENS = 4000
CHARS_PER_TOKEN_ESTIMATE = 4


class MemoryBus:
    def __init__(self, kernel_prompt: str, archive_path: str, max_tokens: int = DEFAULT_MAX_WORKING_TOKENS):
        self.kernel_prompt = kernel_prompt.strip()
        self.archive_path = os.path.abspath(archive_path)
        self.max_tokens = max_tokens
        self.max_chars = max_tokens * CHARS_PER_TOKEN_ESTIMATE
        
        self.t1_working_turns: List[Dict[str, str]] = []
        os.makedirs(os.path.dirname(self.archive_path), exist_ok=True)
        if not os.path.exists(self.archive_path):
            with open(self.archive_path, "w", encoding="utf-8") as f:
                f.write("# AGENT ARCHIVE LOG (TIER 2 STORAGE)\n\n")

    def append_turn(self, role: str, content: str):
        """Appends an interaction turn to T1 working memory."""
        self.t1_working_turns.append({"role": role, "content": content})
        self._check_context_pressure()

    def _check_context_pressure(self):
        """Monitors working token usage and warns if approaching limits."""
        total_chars = sum(len(t["content"]) for t in self.t1_working_turns)
        est_tokens = total_chars // CHARS_PER_TOKEN_ESTIMATE
        if est_tokens > self.max_tokens:
            sys.stderr.write(
                f"[MemoryBus:WARNING] T1 Working context ({est_tokens} tokens) exceeds "
                f"safe budget ({self.max_tokens} tokens). Recommend [MEM_COMMIT].\n"
            )

    def commit(self, ref_id: str, summary: str):
        """
        Executes a [MEM_COMMIT]:
        1. Appends dense outcome to T2 disk archive.
        2. Flushes ephemeral T1 working turns.
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"### [{ref_id}] | {timestamp}\n- **Summary:** {summary.strip()}\n\n"
        
        with open(self.archive_path, "a", encoding="utf-8") as f:
            f.write(entry)

        # Flush working context
        flushed_count = len(self.t1_working_turns)
        self.t1_working_turns.clear()
        sys.stderr.write(f"[MemoryBus] Committed {ref_id} to disk. Flushed {flushed_count} T1 turns.\n")

    def get_injected_payload(self) -> List[Dict[str, str]]:
        """
        Synthesizes the pristine context payload:
        [T0 Kernel (Pinned)] + [T1 Working Context]
        Guarantees system invariants are NEVER dropped or degraded by FIFO truncation.
        """
        messages = [{"role": "system", "content": self.kernel_prompt}]
        messages.extend(self.t1_working_turns)
        return messages


if __name__ == "__main__":
    # Deterministic self-test
    bus = MemoryBus(
        kernel_prompt="SYSTEM LAW: Operate within sandbox. Never exceed boundaries.",
        archive_path="/tmp/test_archive.md",
        max_tokens=100
    )
    bus.append_turn("user", "Build module 1.")
    bus.append_turn("assistant", "Module 1 built successfully.")
    
    payload = bus.get_injected_payload()
    assert len(payload) == 3
    assert payload[0]["role"] == "system"
    assert "SYSTEM LAW" in payload[0]["content"]

    bus.commit("REF-001", "Module 1 validated with zero syntax errors.")
    payload_after = bus.get_injected_payload()
    assert len(payload_after) == 1  # T1 was flushed; T0 remained pinned!
    
    print("[+] 3-Tier Memory Bus unit test: PASSED")
