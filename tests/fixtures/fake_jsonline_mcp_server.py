#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time

TOOLS = [
    {"name": "search_notes", "description": "search", "inputSchema": {"type": "object"}},
    {"name": "read_note", "description": "read", "inputSchema": {"type": "object"}},
    {"name": "index_vault", "description": "index", "inputSchema": {"type": "object"}},
    {"name": "index_status", "description": "status", "inputSchema": {"type": "object"}},
]


def _tools_for_mode(mode: str) -> list[dict]:
    if mode == "missing-tool":
        return [tool for tool in TOOLS if tool["name"] != "read_note"]
    if mode == "extra-tool":
        return [*TOOLS, {"name": "write_note", "description": "write", "inputSchema": {"type": "object"}}]
    return TOOLS


def respond(request: dict, *, mode: str) -> dict | str | None:
    method = request.get("method")
    request_id = request.get("id")
    if mode == "timeout" and method == "initialize":
        time.sleep(60)
    if mode == "malformed-json" and method == "initialize":
        return "{not-json"
    if method == "initialize":
        if mode == "failed-initialize":
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": "init failed"}}
        if mode == "bad-initialize":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"capabilities": {"tools": {}}}}
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fake", "version": "0"},
            },
        }
    if method == "tools/list":
        if mode == "failed-tools-list":
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32001, "message": "tools failed"}}
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": _tools_for_mode(mode)}}
    if method == "tools/call":
        if mode == "failed-tools-call":
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32002, "message": "call failed"}}
        params = request.get("params") or {}
        name = params.get("name")
        if name == "index_status":
            payload = {"vault_root": "SANDBOX", "notes": 1, "chunks": 1, "read_only": True}
        elif name == "index_vault":
            payload = {"indexed": 1, "failed": 0, "dryRun": bool((params.get("arguments") or {}).get("dry_run", True))}
        elif name == "search_notes":
            payload = {"results": [{"path": "Notes/Safety.md", "span": "L1-L2", "snippet": "safety boundary"}]}
        elif name == "read_note":
            payload = {"path": "Notes/Safety.md", "content": "# Safety\nNo live mutation", "start_line": 1, "end_line": 2}
        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "missing tool"}}
        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": json.dumps(payload)}]}}
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "missing method"}}


mode = os.environ.get("FAKE_MCP_MODE", "ok")
for line in sys.stdin:
    if not line.strip():
        continue
    output = respond(json.loads(line), mode=mode)
    if output is None:
        continue
    if isinstance(output, str):
        print(output, flush=True)
    else:
        print(json.dumps(output), flush=True)
