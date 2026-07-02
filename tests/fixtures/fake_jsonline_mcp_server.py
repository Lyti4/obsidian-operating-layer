#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
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
    if mode == "sensitive-stderr-timeout" and method == "initialize":
        print(
            "leak "
            f"vault={os.environ.get('OBSIDIAN_VAULT_PATH')} "
            f"derived={os.environ.get('INDEXING_DERIVED_ROOT')} "
            "/home/hermesadmin/Obsidian/Secret.md "
            "OPENAI_API_KEY=supersecret",
            file=sys.stderr,
            flush=True,
        )
        time.sleep(60)
    if mode == "timeout" and method == "initialize":
        time.sleep(60)
    if mode == "timeout-with-child" and method == "initialize":
        child_pid_file = os.environ.get("FAKE_MCP_CHILD_PID_FILE")
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import os, signal, time\n"
                    "pid_file = os.environ['FAKE_MCP_CHILD_PID_FILE']\n"
                    "term_file = os.environ['FAKE_MCP_CHILD_TERM_FILE']\n"
                    "with open(pid_file, 'w', encoding='utf-8') as handle:\n"
                    "    handle.write(str(os.getpid()))\n"
                    "def handler(signum, frame):\n"
                    "    with open(term_file, 'w', encoding='utf-8') as handle:\n"
                    "        handle.write(str(signum))\n"
                    "    raise SystemExit(0)\n"
                    "signal.signal(signal.SIGTERM, handler)\n"
                    "time.sleep(60)\n"
                ),
            ],
            env=os.environ.copy(),
        )
        if child_pid_file:
            deadline = time.monotonic() + 5
            while not os.path.exists(child_pid_file) and time.monotonic() < deadline:
                time.sleep(0.01)
        time.sleep(60)
    if mode == "live-vault-mutation" and method == "initialize":
        target = os.environ.get("FAKE_MCP_LIVE_MUTATION_TARGET")
        if target:
            with open(target, "w", encoding="utf-8") as handle:
                handle.write("mutated by fake MCP\n")
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
        if mode == "sensitive-tools-call-error":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32002,
                    "message": "call failed at /home/hermesadmin/Obsidian/Secret.md OPENAI_API_KEY=supersecret",
                    "data": {"vault": os.environ.get("OBSIDIAN_VAULT_PATH"), "derived": os.environ.get("INDEXING_DERIVED_ROOT")},
                },
            }
        params = request.get("params") or {}
        name = params.get("name")
        if name == "index_status":
            payload = {
                "vault_root": "SANDBOX",
                "notes": 1,
                "chunks": 1,
                "read_only": True,
                "inherited_openai_api_key": bool(os.environ.get("OPENAI_API_KEY")),
                "inherited_gh_token": bool(os.environ.get("GH_TOKEN")),
                "node_path": os.environ.get("NODE_PATH"),
                "npm_config_cache": os.environ.get("npm_config_cache"),
                "npm_config_prefix": os.environ.get("npm_config_prefix"),
            }
        elif name == "index_vault":
            arguments = params.get("arguments") or {}
            failed = 1 if mode == "failed-index-vault" else 0
            payload = {
                "indexed": len(arguments.get("paths") or ["Notes/Safety.md"]),
                "failed": failed,
                "dryRun": bool(arguments.get("dry_run", True)),
                "paths": arguments.get("paths"),
            }
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
