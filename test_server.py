"""End-to-end smoke test for the MCP server.

Spawns the server over stdio, performs the MCP initialize handshake, and
exercises each tool. Prints a summary and exits non-zero on any failure.

    uv run test_server.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


def _rpc(proc: subprocess.Popen[str], payload: dict[str, Any]) -> dict[str, Any] | None:
    assert proc.stdin and proc.stdout
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()
    if "id" not in payload:
        return None  # notification, no response expected
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("server closed stdout before responding")
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("id") == payload["id"]:
            return msg


def _tool_call(proc, call_id, name, arguments):
    resp = _rpc(proc, {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    if resp is None or "error" in resp:
        raise AssertionError(f"{name} failed: {resp}")
    result = resp["result"]
    if result.get("isError"):
        raise AssertionError(f"{name} returned isError: {result.get('content')}")
    structured = result.get("structuredContent")
    if structured is not None:
        # MCP wraps non-object returns (e.g. list[dict]) under a "result" key.
        if isinstance(structured, dict) and set(structured.keys()) == {"result"}:
            return structured["result"]
        return structured
    content = result.get("content") or []
    text = content[0]["text"] if content and content[0].get("type") == "text" else ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def main() -> int:
    proc = subprocess.Popen(
        ["uv", "run", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    try:
        init = _rpc(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "smoke-test", "version": "0"},
            },
        })
        assert init and init["result"]["serverInfo"]["name"] == "personal-memory"
        print("[OK] initialize")

        _rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

        tools = _rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        names = {t["name"] for t in tools["result"]["tools"]}
        expected = {"remember", "recall", "list_recent", "forget"}
        assert expected <= names, f"missing tools: {expected - names}"
        print(f"[OK] tools/list -> {sorted(names)}")

        stored = _tool_call(proc, 3, "remember", {
            "content": "Smoke test: the sky is blue because of Rayleigh scattering.",
            "tags": ["smoke-test", "science"],
            "source": "test_server.py",
        })
        memory_id = stored["id"]
        assert stored["status"] == "stored"
        print(f"[OK] remember  -> id={memory_id[:8]}...")

        hits = _tool_call(proc, 4, "recall", {"query": "why is the sky blue?", "limit": 3})
        assert any(h["id"] == memory_id for h in hits), "newly stored memory did not surface in recall"
        print(f"[OK] recall    -> top score={hits[0]['score']}")

        recent = _tool_call(proc, 5, "list_recent", {"limit": 5})
        assert recent and recent[0]["id"] == memory_id
        print(f"[OK] list_recent -> {len(recent)} memories, newest first")

        forgot = _tool_call(proc, 6, "forget", {"memory_id": memory_id})
        assert forgot["deleted"] is True
        print(f"[OK] forget    -> {memory_id[:8]}... deleted")

        print("\nAll smoke tests passed.")
        return 0
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=5)


if __name__ == "__main__":
    sys.exit(main())
