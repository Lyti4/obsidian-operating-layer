#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any

from _bootstrap import SRC  # noqa: F401

from obslayer import (
    GuardrailError,
    build_indexing_mcp_process_spec,
    build_indexing_wrapper_policy,
    write_indexing_mcp_report_bundle,
)
from obslayer.indexing_wrapper import DEFAULT_INDEXING_REPORT_ROOT

DEFAULT_QUERIES = (
    "Obsidian Operating Layer safety boundary",
    "approval manifest backup apply verify",
    "wikilinks tags frontmatter knowledge graph",
)


class JsonLineMcpClient:
    def __init__(self, spec, *, timeout_seconds: float = 30.0) -> None:
        env = {**os.environ, **spec.env}
        self.process = subprocess.Popen(
            list(spec.command),
            cwd=spec.cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.timeout_seconds = timeout_seconds
        self._next_id = 1

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.process.stdin is None or self.process.stdout is None:
            raise GuardrailError("MCP process pipes are unavailable")
        request_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            line = self.process.stdout.readline()
            if line:
                try:
                    response = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if response.get("id") == request_id:
                    return response
                continue
            if self.process.poll() is not None:
                stderr = self.process.stderr.read() if self.process.stderr else ""
                raise GuardrailError(f"MCP process exited before response to {method}: {stderr[-1000:]}")
            time.sleep(0.05)
        raise GuardrailError(f"Timed out waiting for MCP response to {method}")


def _tool_call(client: JsonLineMcpClient, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    return client.request("tools/call", {"name": tool, "arguments": arguments or {}})


def _first_result_path(message: dict[str, Any]) -> str | None:
    content = message.get("result", {}).get("content")
    if not isinstance(content, list) or not content:
        return None
    text = content[0].get("text") if isinstance(content[0], dict) else None
    if not isinstance(text, str):
        return None
    try:
        payload = json.loads(text.strip())
    except json.JSONDecodeError:
        return None
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return None
    for item in results:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            return item["path"]
    return None


def run_probe(*, spec, queries: list[str], index_mode: str, dry_run: bool, timeout_seconds: float) -> list[dict[str, Any]]:
    client = JsonLineMcpClient(spec, timeout_seconds=timeout_seconds)
    calls: list[dict[str, Any]] = []
    try:
        client.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "obslayer-indexing-stdio-probe", "version": "0"},
            },
        )
        tools = client.request("tools/list")
        calls.append({"kind": "list_tools", "message": tools})
        calls.append({"tool": "index_status", "message": _tool_call(client, "index_status")})
        calls.append({"tool": "index_vault", "message": _tool_call(client, "index_vault", {"mode": index_mode, "dry_run": dry_run})})
        first_path: str | None = None
        for query in queries:
            search = _tool_call(client, "search_notes", {"query": query, "limit": 5, "mode": "keyword"})
            calls.append({"tool": "search_notes", "message": search})
            first_path = first_path or _first_result_path(search)
        if first_path:
            read = _tool_call(
                client,
                "read_note",
                {"path": first_path, "start_line": 1, "end_line": 5},
            )
            calls.append({"tool": "read_note", "message": read})
        calls.append({"tool": "index_status", "message": _tool_call(client, "index_status")})
        return calls
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a guarded JSON-lines MCP stdio probe and sanitize its transcript.")
    parser.add_argument("--sandbox-vault", required=True)
    parser.add_argument("--derived-root", required=True)
    parser.add_argument("--raw-report", required=True)
    parser.add_argument("--sanitized-report", required=True)
    parser.add_argument("--report-root", default=str(DEFAULT_INDEXING_REPORT_ROOT))
    parser.add_argument("--command", action="append", required=True, help="MCP server command part; repeat for argv")
    parser.add_argument("--query", action="append", default=[])
    parser.add_argument("--index-mode", default="incremental", choices=("incremental", "full"))
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    policy = build_indexing_wrapper_policy(
        vault_root=args.sandbox_vault,
        derived_root=args.derived_root,
        discover_nested_excludes=True,
    )
    spec = build_indexing_mcp_process_spec(command=args.command, policy=policy)
    calls = run_probe(
        spec=spec,
        queries=args.query or list(DEFAULT_QUERIES),
        index_mode=args.index_mode,
        dry_run=args.dry_run,
        timeout_seconds=args.timeout_seconds,
    )
    bundle = write_indexing_mcp_report_bundle(
        calls=calls,
        policy=policy,
        raw_report=args.raw_report,
        sanitized_report=args.sanitized_report,
        report_root=args.report_root,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "calls": len(calls),
                "raw_report": bundle.raw_report,
                "sanitized_report": bundle.sanitized_report,
                "redactions": len(bundle.sanitized_transcript.redactions),
                "process_spec": spec.to_dict(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cli() -> int:
    try:
        return main()
    except (GuardrailError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
