#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

TOOLS = [
    {"name": "search_notes", "description": "search", "inputSchema": {"type": "object"}},
    {"name": "read_note", "description": "read", "inputSchema": {"type": "object"}},
    {"name": "index_vault", "description": "index", "inputSchema": {"type": "object"}},
    {"name": "index_status", "description": "status", "inputSchema": {"type": "object"}},
]


def respond(request: dict) -> dict:
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
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
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
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


for line in sys.stdin:
    if not line.strip():
        continue
    print(json.dumps(respond(json.loads(line))), flush=True)
