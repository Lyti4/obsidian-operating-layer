#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
from typing import Any

from _bootstrap import SRC  # noqa: F401

from obslayer import (
    GuardrailError,
    build_indexing_mcp_process_spec,
    build_indexing_wrapper_policy,
    verify_indexing_runtime_tools,
    write_indexing_mcp_report_bundle,
)
from obslayer.indexing_wrapper import DEFAULT_INDEXING_REPORT_ROOT

DEFAULT_QUERIES = (
    "Obsidian Operating Layer safety boundary",
    "approval manifest backup apply verify",
    "wikilinks tags frontmatter knowledge graph",
)
MAX_STDERR_CAPTURE_CHARS = 16_000


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
        self._stdout_queue: queue.Queue[str | None] = queue.Queue()
        self._stderr_chunks: list[str] = []
        self._stdout_thread = threading.Thread(target=self._drain_stdout, name="mcp-stdout-drain", daemon=True)
        self._stderr_thread = threading.Thread(target=self._drain_stderr, name="mcp-stderr-drain", daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()

    def _drain_stdout(self) -> None:
        if self.process.stdout is None:
            self._stdout_queue.put(None)
            return
        try:
            for line in self.process.stdout:
                self._stdout_queue.put(line)
        finally:
            self._stdout_queue.put(None)

    def _drain_stderr(self) -> None:
        stream = self.process.stderr
        if stream is None:
            return
        for chunk in iter(lambda: stream.read(4096), ""):
            self._stderr_chunks.append(chunk)
            captured = "".join(self._stderr_chunks)
            if len(captured) > MAX_STDERR_CAPTURE_CHARS:
                self._stderr_chunks = [captured[-MAX_STDERR_CAPTURE_CHARS:]]

    def stderr_tail(self) -> str:
        return "".join(self._stderr_chunks)[-1000:]

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        self._stdout_thread.join(timeout=1)
        self._stderr_thread.join(timeout=1)

    def _read_response_line(self, *, method: str) -> str:
        try:
            line = self._stdout_queue.get(timeout=self.timeout_seconds)
        except queue.Empty as exc:
            raise GuardrailError(f"Timed out waiting for MCP response to {method}; stderr={self.stderr_tail()}") from exc
        if line is None:
            raise GuardrailError(f"MCP process closed stdout before response to {method}; stderr={self.stderr_tail()}")
        return line

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.process.stdin is None:
            raise GuardrailError("MCP process stdin is unavailable")
        if self.process.poll() is not None:
            raise GuardrailError(f"MCP process exited before request {method}; stderr={self.stderr_tail()}")
        request_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        while True:
            line = self._read_response_line(method=method)
            try:
                response = json.loads(line)
            except json.JSONDecodeError as exc:
                raise GuardrailError(f"MCP process emitted malformed JSON while waiting for {method}") from exc
            if response.get("id") != request_id:
                continue
            if response.get("jsonrpc") != "2.0":
                raise GuardrailError(f"MCP response to {method} is not JSON-RPC 2.0")
            if "error" in response:
                raise GuardrailError(f"MCP response to {method} returned error: {response['error']}")
            if "result" not in response:
                raise GuardrailError(f"MCP response to {method} is missing result")
            return response


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


def _verify_initialize(message: dict[str, Any]) -> None:
    result = message.get("result")
    if not isinstance(result, dict):
        raise GuardrailError("MCP initialize response must contain an object result")
    protocol_version = result.get("protocolVersion")
    if not isinstance(protocol_version, str) or not protocol_version:
        raise GuardrailError("MCP initialize response is missing protocolVersion")
    capabilities = result.get("capabilities")
    if not isinstance(capabilities, dict):
        raise GuardrailError("MCP initialize response is missing capabilities object")


def run_probe(*, spec, queries: list[str], index_mode: str, dry_run: bool, timeout_seconds: float) -> list[dict[str, Any]]:
    if not dry_run:
        raise GuardrailError("stdio probe refuses non-dry-run index_vault calls")
    client = JsonLineMcpClient(spec, timeout_seconds=timeout_seconds)
    calls: list[dict[str, Any]] = []
    try:
        initialize = client.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "obslayer-indexing-stdio-probe", "version": "0"},
            },
        )
        _verify_initialize(initialize)
        tools = client.request("tools/list")
        verify_indexing_runtime_tools(tools, spec.policy)
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
    parser.add_argument("--dry-run", action="store_true", default=True, help="Keep index_vault in dry-run mode; this is the safe default.")
    parser.add_argument(
        "--non-dry-run",
        action="store_false",
        dest="dry_run",
        help="Rejected by guardrails; present only to make non-dry-run intent explicit and fail closed.",
    )
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
