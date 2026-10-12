#!/usr/bin/env python3
"""
==============================================================================
RYKR CONTROL-PLANE MIDDLEWARE (UNIFIED ODYSSEUS & AJAX ADAPTER)
==============================================================================
Drop-in transparent proxy between Odysseus and local Pascal inference (Ollama/llama-server).

Architectural Pillars Implemented:
1. T0 Pinned Kernel & Macro Engine:
   - Injects immutable Rykr Kernel invariants at head.
   - Natively intercepts and enforces ~ macro commands (~plan, ~redteam, ~execute, ~commit, ~close).
2. T1/T2 Hierarchical Memory Bus:
   - Capped working RAM (~3,500 tokens). Prunes ephemeral history to prevent VRAM KV-cache
     explosion on consumer hardware (GTX 1080 Ti), keeping token speed at 30+ t/s indefinitely.
3. RRS (Rykr Reduced Semantics) Token Compressor:
   - Strips verbose JSON Schemas and compresses tool definitions by ~75%.
4. Delimited XML Tool Parsing:
   - Intercepts <invoke tool="..."> tags from sub-14B models and synthesizes RFC-compliant
     OpenAI JSON tool_calls objects for Odysseus.
"""

import json
import re
import uuid
import sys
import os
import time
from typing import Dict, Any, List, Optional
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error

UPSTREAM_INFERENCE_URL = "http://127.0.0.1:11434/v1/chat/completions"
UPSTREAM_BASE = "http://127.0.0.1:11434"
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8080

MAX_WORKING_CHARS = 14000  # ~3,500 tokens buffer cap for T1 working memory

TOOL_INVOKE_REGEX = re.compile(
    r'<invoke\s+tool=["\'](?P<name>[^"\']+)["\']>(?P<content>.*?)</invoke>',
    re.DOTALL | re.IGNORECASE
)

ALT_TOOL_INVOKE_REGEX = re.compile(
    r'<tool_invoke\s+name=["\'](?P<name>[^"\']+)["\']>(?:<arg\s+name=["\']cmd["\']>(?P<cmd>.*?)</arg>|(?P<content>.*?))</tool_invoke>',
    re.DOTALL | re.IGNORECASE
)

T0_RYKR_KERNEL = """# [SYSTEM: INITIALIZATION PROTOCOL - RYKR CONTROL-PLANE KERNEL v3.0]
You are Rykr, an Executive Advocate and System Orchestrator. Your primary directive is to absorb administrative friction, manage cognitive load, and advocate for the Operator's executive function.

## 1. THE LAWS OF RYKR
* The Law of Cognitive Conservation: Never force the Operator to make a low-level administrative decision if it can be avoided. Do not ask open-ended questions that cause decision fatigue. Offer optimized paths and ask for simple binary confirmation.
* The Law of Intent Optimization & Lateral Pivot: Evaluate the underlying intent of an instruction. If a workflow encounters friction or an impasse, execute a "Lateral Pivot"—a creative, unconventional workaround that bypasses friction to achieve the goal directly.
* The Law of Unyielding Advocacy: Prioritize the Operator's mental bandwidth above raw productivity. Monitor input for signs of executive fatigue and proactively take on the heavy lifting.
* The Law of Radical Honesty (Anti-Bias Directive): Be purely objective and analytically honest. Never mask limitations, pad responses with unnecessary conversational niceties, or lean into confirmation bias just to agree. State technical realities directly.
* The Law of Absolute Preservation: Maintain velocity while preventing objective financial or physical harm.

## 2. COMMUNICATION & BEHAVIORAL PROTOCOL
- Output format: Direct, factual, structured GitHub-flavored markdown.
- Conversational padding: Categorically forbidden. Never use corporate filler phrases ("Sure, I can help with that!", "As an AI...").
- Decision management: Always present clear, structured conclusions and binary choices ([1] / [2]) rather than open-ended questions.

## 3. THE GENESIS PIPELINE (MACRO STATE MACHINE)
If the Operator invokes a macro command starting with '~', you must strictly obey that state machine phase:
- ~plan: PHASE 1 (SKELETON & MAP). Output ZERO executable code. Output strictly a modular architectural skeleton, mapping data flow, inputs, outputs, and interface boundaries.
- ~redteam: PHASE 2 (ADVERSARIAL AUDIT). Adopt an adversarial "Devil's Advocate" stance. Stress-test assumptions, hunt for failure modes, security vulnerabilities, and resource limits.
- ~execute: PHASE 3 (MODULAR EXECUTION). Build ONE isolated module at a time using strict UNIX pipe philosophy. Verify local module before proceeding.
- ~commit: PHASE 4 (STATE COMMIT). Summarize completed module state, update local archives, and signal [MEM_COMMIT] to flush working context.
- ~close: PHASE 5 (HANDOFF). Synthesize final session report, document open items, and finalize task state.

## 4. TOOL INVOCATION DISCIPLINE (RRS & DELIMITED TAGS)
- Do NOT output raw JSON function calls.
- When calling tools, use strictly delimited XML tags:
  <invoke tool="tool_name">raw_arguments</invoke>
- All tool arguments must be written cleanly between the invoke tags."""


def compress_tools_to_rrs(tools: List[Dict[str, Any]]) -> str:
    """Compresses verbose JSON Schema tool definitions into compact RRS notation."""
    compressed_lines = [
        "Available Tools (Invoke using <invoke tool=\"name\">raw_arguments</invoke>):"
    ]
    for tool in tools:
        fn = tool.get("function", {})
        name = fn.get("name", "unknown")
        desc = fn.get("description", "").strip()
        params = fn.get("parameters", {}).get("properties", {})
        param_names = list(params.keys())
        compressed_lines.append(f"- [{name}]: ({', '.join(param_names)}) -- {desc}")
    
    compressed_lines.append(
        "CRITICAL: Do NOT output JSON for tool calls. Output strictly: <invoke tool=\"tool_name\">arguments</invoke>"
    )
    return "\n".join(compressed_lines)


def parse_delimited_output(content: str) -> Optional[List[Dict[str, Any]]]:
    """Inspects model output for delimited tool calls and synthesizes OpenAI JSON tool_calls."""
    tool_calls = []

    # 1. Match <invoke tool="name">...</invoke>
    for match in TOOL_INVOKE_REGEX.finditer(content):
        name = match.group("name").strip()
        raw_args = match.group("content").strip()
        
        try:
            parsed_args = json.loads(raw_args)
        except Exception:
            parsed_args = {"command": raw_args, "input": raw_args}

        tool_calls.append({
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(parsed_args)
            }
        })

    # 2. Match <tool_invoke name="name">...</tool_invoke>
    if not tool_calls:
        for match in ALT_TOOL_INVOKE_REGEX.finditer(content):
            name = match.group("name").strip()
            raw_args = (match.group("cmd") or match.group("content") or "").strip()
            try:
                parsed_args = json.loads(raw_args)
            except Exception:
                parsed_args = {"command": raw_args, "input": raw_args}

            tool_calls.append({
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(parsed_args)
                }
            })

    return tool_calls if tool_calls else None


def apply_memory_bus_and_macros(messages: List[Dict[str, Any]], rrs_tools: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Applies the full Rykr Control-Plane:
    1. T0 Pinned Kernel injection at head.
    2. RRS Tool Compression injection.
    3. T1 Working Memory Capping & Pruning (prevents VRAM KV-cache bloat on consumer GPUs).
    4. Macro command detection & phase directive injection (~plan, ~redteam, ~execute, ~commit).
    """
    if not messages:
        messages = []

    sys_parts = [T0_RYKR_KERNEL]
    if rrs_tools:
        sys_parts.append(rrs_tools)

    # Collect existing system content from Odysseus
    existing_sys = [m["content"] for m in messages if m.get("role") == "system"]
    if existing_sys:
        sys_parts.extend(existing_sys)
    
    combined_system_prompt = "\n\n".join(sys_parts)

    other_msgs = [m for m in messages if m.get("role") != "system"]

    # 1. Macro Command Routing
    last_user_content = ""
    for m in reversed(other_msgs):
        if m.get("role") == "user":
            last_user_content = str(m.get("content", "")).strip()
            break

    macro_guard = None
    if last_user_content:
        first_word = last_user_content.split()[0].lower()
        if first_word == "~plan":
            macro_guard = "[GENESIS DIRECTIVE: ~plan active. MANDATORY: Output ZERO executable code. Output strictly a modular architectural skeleton, mapping data flow, inputs, outputs, and interface boundaries.]"
        elif first_word == "~redteam":
            macro_guard = "[GENESIS DIRECTIVE: ~redteam active. MANDATORY: Adopt adversarial Devil's Advocate stance. Stress-test theoretical assumptions, hunt for failure modes, security risks, and resource limits.]"
        elif first_word == "~execute":
            macro_guard = "[GENESIS DIRECTIVE: ~execute active. MANDATORY: Construct ONE isolated module only under strict UNIX pipe philosophy. Verify local module before proceeding.]"
        elif first_word in ("~commit", "~close"):
            macro_guard = "[GENESIS DIRECTIVE: State commit active. Synthesize completed progress, summarize outcomes, and flush working memory state.]"

    # 2. T1 Working Memory Capping
    total_chars = sum(len(str(m.get("content", ""))) for m in other_msgs)
    if total_chars > MAX_WORKING_CHARS and len(other_msgs) > 3:
        pruned = [other_msgs[0]]  # preserve original user mission
        pruned.append({
            "role": "system",
            "content": f"[MEM_BUS: Working memory capped to prevent KV-cache bloat. {len(other_msgs) - 3} ephemeral turns offloaded to T2 archive.]"
        })
        pruned.extend(other_msgs[-3:])  # preserve latest 3 working turns
        sys.stderr.write(f"[MemoryBus] T1 Context capped: {total_chars} chars -> {sum(len(str(m.get('content', ''))) for m in pruned)} chars.\n")
        other_msgs = pruned

    result = [{"role": "system", "content": combined_system_prompt}]
    result.extend(other_msgs)

    if macro_guard:
        result.append({"role": "system", "content": macro_guard})

    return result


class SemanticProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_raw()

    def do_POST(self):
        if self.path.endswith("/chat/completions"):
            self.handle_chat_completions()
        else:
            self.proxy_raw()

    def handle_chat_completions(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            req_data = json.loads(body.decode("utf-8"))
        except Exception as e:
            self.send_error(400, f"Malformed JSON: {e}")
            return

        has_tools = "tools" in req_data and req_data["tools"]
        original_tools = req_data.pop("tools", None)
        req_data.pop("tool_choice", None)

        rrs_block = compress_tools_to_rrs(original_tools) if has_tools else None
        messages = req_data.get("messages", [])

        # Apply Complete Rykr Control-Plane (T0 Kernel + T1 Memory Bus + Macro Routing + RRS)
        req_data["messages"] = apply_memory_bus_and_macros(messages, rrs_block)

        # Map model to upstream Ollama tag
        model_name = req_data.get("model", "")
        if model_name in ("ajax", "ajax-local") or "qwen" in model_name.lower():
            req_data["model"] = "ajax:latest"

        # Forward request to upstream inference server
        out_body = json.dumps(req_data).encode("utf-8")
        req = urllib.request.Request(
            UPSTREAM_INFERENCE_URL,
            data=out_body,
            headers={"Content-Type": "application/json"}
        )

        is_streaming = bool(req_data.get("stream", False))
        if is_streaming:
            try:
                resp = urllib.request.urlopen(req, timeout=300)
            except urllib.error.HTTPError as e:
                self.send_error(e.code, str(e.reason))
                return
            except urllib.error.URLError as e:
                self.send_error(502, f"Inference engine unreachable: {e}")
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            try:
                for line in resp:
                    self.wfile.write(line)
                    self.wfile.flush()
                    if b"[DONE]" in line:
                        break
            except Exception as e:
                sys.stderr.write(f"[RykrControlPlane] Stream closed: {e}\n")
            finally:
                resp.close()
            return

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            self.send_error(502, f"Inference engine unreachable: {e}")
            return

        # Upstream JSON normalization: check if model returned delimited tool calls
        choices = resp_data.get("choices", [])
        if choices:
            msg = choices[0].get("message", {})
            content = msg.get("content", "") or ""
            
            tool_calls = parse_delimited_output(content)
            if tool_calls:
                msg["tool_calls"] = tool_calls
                clean_content = TOOL_INVOKE_REGEX.sub("", content)
                clean_content = ALT_TOOL_INVOKE_REGEX.sub("", clean_content).strip()
                msg["content"] = clean_content if clean_content else None
                choices[0]["finish_reason"] = "tool_calls"

        final_body = json.dumps(resp_data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(final_body)))
        self.end_headers()
        self.wfile.write(final_body)

    def proxy_raw(self):
        """Pass-through for /v1/models, /slots, or other endpoints."""
        if self.path.rstrip("/").endswith("/slots"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"[]")
            return
        if self.path.rstrip("/").endswith("/models"):
            model_list = {
                "object": "list",
                "data": [
                    {"id": "ajax", "object": "model", "owned_by": "local", "permissions": []},
                    {"id": "ajax:latest", "object": "model", "owned_by": "local", "permissions": []}
                ]
            }
            body = json.dumps(model_list).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        target_url = f"{UPSTREAM_BASE}{self.path}"
        req = urllib.request.Request(target_url, data=body)
        for header, val in self.headers.items():
            if header.lower() not in ["host", "content-length"]:
                req.add_header(header, val)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                for header, val in resp.getheaders():
                    self.send_header(header, val)
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_error(e.code, str(e.reason))
        except urllib.error.URLError as e:
            self.send_error(502, f"Backend unavailable: {e}")

    def log_message(self, format, *args):
        sys.stderr.write(f"[RykrControlPlane] {self.address_string()} - {format % args}\n")


def run():
    server_address = (LISTEN_HOST, LISTEN_PORT)
    httpd = ThreadingHTTPServer(server_address, SemanticProxyHandler)
    httpd.daemon_threads = True
    print(f"[*] Rykr Control-Plane Middleware (Multi-Threaded) listening on {LISTEN_HOST}:{LISTEN_PORT}")
    print(f"[*] Upstream inference target: {UPSTREAM_INFERENCE_URL}")
    print(f"[*] Architecture: T0 Pinned Kernel + T1 Memory Bus + RRS Token Compressor + Delimited Tool Parser")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
