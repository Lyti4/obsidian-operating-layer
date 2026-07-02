#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from _bootstrap import SRC  # noqa: F401

from obslayer import (
    GuardrailError,
    build_indexing_mcp_process_spec,
    build_indexing_wrapper_policy,
    is_protected_relative,
    verify_indexing_runtime_tools,
    write_indexing_mcp_report_bundle,
)
from obslayer.indexing_wrapper import (
    DEFAULT_INDEXING_REPORT_ROOT,
    redact_derived_root_paths,
    redact_live_vault_paths,
    redact_sandbox_vault_paths,
)

DEFAULT_QUERIES = (
    "Obsidian Operating Layer safety boundary",
    "approval manifest backup apply verify",
    "wikilinks tags frontmatter knowledge graph",
)
MAX_STDERR_CAPTURE_CHARS = 16_000
SAFE_CHILD_PATH = "/home/hermesadmin/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
PARENT_ENV_ALLOWLIST = (
    "FAKE_MCP_MODE",
    "FAKE_MCP_LIVE_MUTATION_TARGET",
    "FAKE_MCP_CHILD_PID_FILE",
    "FAKE_MCP_CHILD_TERM_FILE",
)
SECRET_DIAGNOSTIC_REDACTIONS = (
    ("OPENAI_API_KEY", "<REDACTED_SECRET>"),
    ("GH_TOKEN", "<REDACTED_SECRET>"),
    ("GITHUB_TOKEN", "<REDACTED_SECRET>"),
)
SECRET_DIAGNOSTIC_PATTERN = re.compile(
    r"(?i)\b[A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASS|KEY|CREDENTIAL|COOKIE|AUTH|PROXY)[A-Z0-9_]*\s*[:=]\s*[^\s,;'}\"]+"
)


def _minimal_child_env(spec) -> dict[str, str]:
    env = dict(spec.env)
    env.setdefault("PATH", SAFE_CHILD_PATH)
    env.setdefault("npm_config_cache", str(Path(spec.policy.derived_root) / "npm-cache"))
    env.setdefault("npm_config_prefix", str(Path(spec.policy.derived_root) / "npm-prefix"))
    for key in PARENT_ENV_ALLOWLIST:
        value = os.environ.get(key)
        if value:
            env.setdefault(key, value)
    return env


def _live_vault_fingerprint(root: str) -> dict[str, tuple[int, int, str]]:
    live_root = Path(root).expanduser().resolve()
    if not live_root.exists():
        return {}
    fingerprint: dict[str, tuple[int, int, str]] = {}
    for path in live_root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(live_root).as_posix()
        stat = path.stat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        fingerprint[rel] = (stat.st_size, stat.st_mtime_ns, digest)
    return fingerprint


def _assert_live_vault_unchanged(before: dict[str, tuple[int, int, str]], spec) -> None:
    after = _live_vault_fingerprint(spec.policy.live_vault_root)
    if after != before:
        raise GuardrailError("MCP probe detected live vault mutation while indexing sandbox vault")


def _sanitize_diagnostic_text(text: str, spec) -> str:
    redacted = text[-MAX_STDERR_CAPTURE_CHARS:]
    redacted, _ = redact_live_vault_paths(redacted, live_vault_root=spec.policy.live_vault_root)
    redacted, _ = redact_sandbox_vault_paths(redacted, vault_root=spec.policy.vault_root)
    redacted, _ = redact_derived_root_paths(redacted, derived_root=spec.policy.derived_root)
    for key, replacement in SECRET_DIAGNOSTIC_REDACTIONS:
        secret_value = os.environ.get(key)
        if secret_value:
            redacted = redacted.replace(secret_value, replacement)
    redacted = SECRET_DIAGNOSTIC_PATTERN.sub("<REDACTED_SECRET>", redacted)
    return redacted


class JsonLineMcpClient:
    def __init__(self, spec, *, timeout_seconds: float = 30.0) -> None:
        self.spec = spec
        env = _minimal_child_env(spec)
        self.process = subprocess.Popen(
            list(spec.command),
            cwd=spec.cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        self._process_group_id: int | None = None
        try:
            self._process_group_id = os.getpgid(self.process.pid)
        except ProcessLookupError:
            self._process_group_id = None
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
        for chunk in stream:
            self._stderr_chunks.append(chunk)
            captured = "".join(self._stderr_chunks)
            if len(captured) > MAX_STDERR_CAPTURE_CHARS:
                self._stderr_chunks = [captured[-MAX_STDERR_CAPTURE_CHARS:]]

    def stderr_tail(self) -> str:
        return _sanitize_diagnostic_text("".join(self._stderr_chunks)[-1000:], self.spec)

    def close(self) -> None:
        if self.process.poll() is None:
            self._terminate_process_group(signal.SIGTERM)
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._terminate_process_group(signal.SIGKILL)
                self.process.wait(timeout=3)
        else:
            self._terminate_process_group(signal.SIGTERM)
        self._stdout_thread.join(timeout=1)
        self._stderr_thread.join(timeout=1)

    def _terminate_process_group(self, sig: signal.Signals) -> None:
        if self._process_group_id is not None:
            try:
                os.killpg(self._process_group_id, sig)
                return
            except ProcessLookupError:
                return
            except PermissionError:
                pass
        if self.process.poll() is None:
            if sig == signal.SIGTERM:
                self.process.terminate()
            else:
                self.process.kill()

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
                error_text = _sanitize_diagnostic_text(json.dumps(response["error"], sort_keys=True), self.spec)
                raise GuardrailError(f"MCP response to {method} returned error: {error_text}")
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


def _index_vault_failed_count(sanitized_calls: list[dict[str, Any]]) -> int:
    failed_total = 0
    for call in sanitized_calls:
        if call.get("tool") != "index_vault":
            continue
        payload = call.get("payload")
        if not isinstance(payload, dict):
            continue
        failed = payload.get("failed")
        if isinstance(failed, int) and failed > 0:
            failed_total += failed
    return failed_total


def _normalize_requested_markdown_path(raw: str) -> str:
    text = str(raw).strip().replace("\\", "/")
    if not text:
        raise GuardrailError("paths file contains an empty path")
    rel = Path(text)
    if rel.is_absolute() or ".." in rel.parts:
        raise GuardrailError("paths file entry must be vault-relative")
    clean = rel.as_posix()
    if clean.startswith("./"):
        clean = clean[2:]
    if not clean.endswith(".md"):
        raise GuardrailError("paths file entry must point to markdown")
    return clean


def _load_paths_file(path: str | None, *, derived_root: str | Path) -> list[str] | None:
    if not path:
        return None
    payload_path = Path(path).expanduser().resolve()
    derived = Path(derived_root).expanduser().resolve()
    try:
        payload_path.relative_to(derived)
    except ValueError as exc:
        raise GuardrailError("paths file must live under derived root") from exc
    raw = payload_path.read_text(encoding="utf-8")
    if payload_path.suffix == ".json":
        payload = json.loads(raw)
        entries = payload.get("paths") if isinstance(payload, dict) else payload
        if not isinstance(entries, list) or not all(isinstance(item, str) for item in entries):
            raise GuardrailError("JSON paths file must be a string list or an object with a string paths list")
        raw_paths = entries
    else:
        raw_paths = [line.strip() for line in raw.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    normalized: list[str] = []
    for raw_path in raw_paths:
        clean = _normalize_requested_markdown_path(raw_path)
        if clean not in normalized:
            normalized.append(clean)
    return normalized


def _discover_markdown_paths(vault_root: str) -> list[str]:
    root = Path(vault_root).expanduser().resolve()
    paths: list[str] = []
    for candidate in sorted(root.rglob("*.md")):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        paths.append(candidate.relative_to(root).as_posix())
    return paths


def _path_is_excluded(rel_path: str, spec) -> bool:
    rel = rel_path.replace("\\", "/")
    return is_protected_relative(rel) or any(rel.startswith(prefix) for prefix in spec.policy.exclude_paths)


def _filter_index_paths(paths: list[str], spec) -> tuple[list[str], list[str]]:
    allowed: list[str] = []
    skipped: list[str] = []
    for rel_path in paths:
        clean = _normalize_requested_markdown_path(rel_path)
        if _path_is_excluded(clean, spec):
            skipped.append(clean)
            continue
        if clean not in allowed:
            allowed.append(clean)
    return allowed, skipped


def _batches(items: list[str], size: int) -> list[list[str]]:
    if size < 1:
        raise GuardrailError("--batch-size must be >= 1")
    return [items[index : index + size] for index in range(0, len(items), size)]


def _batch_checkpoint_target(spec, checkpoint_path: str | None) -> Path:
    target = Path(checkpoint_path).expanduser().resolve() if checkpoint_path else Path(spec.policy.derived_root) / "batch-checkpoint.json"
    derived = Path(spec.policy.derived_root).expanduser().resolve()
    try:
        target.relative_to(derived)
    except ValueError as exc:
        raise GuardrailError(f"batch checkpoint must live under derived root: {target}") from exc
    return target


def _read_batch_checkpoint(spec, checkpoint_path: str | None) -> dict[str, Any] | None:
    target = _batch_checkpoint_target(spec, checkpoint_path)
    if not target.exists():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardrailError("batch checkpoint must be a JSON object")
    return payload


def _write_batch_checkpoint(spec, checkpoint_path: str | None, payload: dict[str, Any]) -> None:
    target = _batch_checkpoint_target(spec, checkpoint_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _completed_checkpoint_paths(checkpoint: dict[str, Any] | None, *, allowed_paths: list[str], spec) -> list[str]:
    if not checkpoint:
        return []
    completed = checkpoint.get("completed_batches", [])
    if not isinstance(completed, list):
        raise GuardrailError("batch checkpoint completed_batches must be a list")
    paths: list[str] = []
    for batch in completed:
        if not isinstance(batch, dict):
            raise GuardrailError("batch checkpoint completed batch must be an object")
        batch_paths = batch.get("paths", [])
        if not isinstance(batch_paths, list) or not all(isinstance(item, str) for item in batch_paths):
            raise GuardrailError("batch checkpoint completed batch paths must be a string list")
        for raw in batch_paths:
            clean = _normalize_requested_markdown_path(raw)
            if clean not in allowed_paths or _path_is_excluded(clean, spec):
                continue
            if clean not in paths:
                paths.append(clean)
    return paths


def _validate_resume_checkpoint(
    checkpoint: dict[str, Any] | None,
    *,
    allowed_paths: list[str],
    batch_size: int,
    index_mode: str,
    dry_run: bool,
) -> None:
    if checkpoint is None:
        return
    expected = {"allowed_paths": allowed_paths, "batch_size": batch_size, "mode": index_mode, "dry_run": dry_run}
    for key, value in expected.items():
        if key in checkpoint and checkpoint[key] != value:
            raise GuardrailError(f"batch checkpoint does not match current request: {key}")


def _index_vault_failed_from_message(message: dict[str, Any]) -> int:
    content = message.get("result", {}).get("content")
    if not isinstance(content, list) or not content:
        return 0
    text = content[0].get("text") if isinstance(content[0], dict) else None
    if not isinstance(text, str):
        return 0
    try:
        payload = json.loads(text.strip())
    except json.JSONDecodeError:
        return 0
    failed = payload.get("failed") if isinstance(payload, dict) else None
    return failed if isinstance(failed, int) and failed > 0 else 0


def run_probe(
    *,
    spec,
    queries: list[str],
    index_mode: str,
    dry_run: bool,
    allow_derived_index_write: bool,
    timeout_seconds: float,
    paths: list[str] | None = None,
    batch_size: int = 25,
    checkpoint_path: str | None = None,
    resume: bool = False,
) -> list[dict[str, Any]]:
    if not dry_run and not allow_derived_index_write:
        raise GuardrailError("stdio probe refuses non-dry-run index_vault calls without --allow-derived-index-write")
    if not dry_run and not spec.policy.require_sandbox_vault:
        raise GuardrailError("stdio probe derived index writes require a sandbox vault policy")
    live_vault_before = _live_vault_fingerprint(spec.policy.live_vault_root)
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
        requested_paths = paths if paths is not None else None
        if requested_paths is None:
            calls.append({"tool": "index_vault", "message": _tool_call(client, "index_vault", {"mode": index_mode, "dry_run": dry_run})})
        else:
            allowed_paths, skipped_paths = _filter_index_paths(requested_paths, spec)
            prior_checkpoint = _read_batch_checkpoint(spec, checkpoint_path) if resume else None
            _validate_resume_checkpoint(
                prior_checkpoint,
                allowed_paths=allowed_paths,
                batch_size=batch_size,
                index_mode=index_mode,
                dry_run=dry_run,
            )
            completed_paths = _completed_checkpoint_paths(prior_checkpoint, allowed_paths=allowed_paths, spec=spec)
            pending_paths = [path for path in allowed_paths if path not in completed_paths]
            batch_items = _batches(pending_paths, batch_size)
            checkpoint: dict[str, Any] = dict(prior_checkpoint or {})
            checkpoint.update(
                {
                    "mode": index_mode,
                    "dry_run": dry_run,
                    "batch_size": batch_size,
                    "requested": len(requested_paths),
                    "allowed": len(allowed_paths),
                    "allowed_paths": allowed_paths,
                    "skipped": skipped_paths,
                    "resume": resume,
                    "pending": len(pending_paths),
                }
            )
            checkpoint.setdefault("completed_batches", [])
            _write_batch_checkpoint(spec, checkpoint_path, checkpoint)
            start_index = len(checkpoint["completed_batches"]) + 1
            for batch_index, batch_paths in enumerate(batch_items, start=start_index):
                message = _tool_call(
                    client,
                    "index_vault",
                    {"mode": index_mode, "dry_run": dry_run, "paths": batch_paths},
                )
                calls.append({"tool": "index_vault", "message": message, "batch": {"index": batch_index, "paths": batch_paths}})
                batch_record = {
                    "index": batch_index,
                    "paths": batch_paths,
                    "stderr_tail": client.stderr_tail(),
                }
                failed = _index_vault_failed_from_message(message)
                if failed:
                    batch_record["failed"] = failed
                    checkpoint.setdefault("failed_batches", []).append(batch_record)
                else:
                    checkpoint["completed_batches"].append(batch_record)
                _write_batch_checkpoint(spec, checkpoint_path, checkpoint)
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
        _assert_live_vault_unchanged(live_vault_before, spec)


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
        "--allow-derived-index-write",
        action="store_true",
        help="Allow non-dry-run index_vault only for a sandbox vault and derived index storage; never writes to the source/live vault.",
    )
    parser.add_argument(
        "--non-dry-run",
        action="store_false",
        dest="dry_run",
        help="Run index_vault with dry_run=false; requires --allow-derived-index-write and still requires a sandbox vault.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument(
        "--paths-file",
        help="Optional newline or JSON list of vault-relative markdown paths to index in batches",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help=(
            "Batch size for --paths-file, or for discovered paths "
            "when --discover-paths is used"
        ),
    )
    parser.add_argument("--batch-checkpoint", help="Optional checkpoint JSON path under --derived-root")
    parser.add_argument(
        "--discover-paths",
        action="store_true",
        help=(
            "Discover markdown files under the sandbox vault and index them "
            "via batched paths"
        ),
    )
    parser.add_argument("--resume", action="store_true", help="Resume batched paths from an existing checkpoint under --derived-root")
    parser.add_argument("--live-vault-root", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()

    policy = build_indexing_wrapper_policy(
        vault_root=args.sandbox_vault,
        derived_root=args.derived_root,
        live_vault_root=args.live_vault_root or "/home/hermesadmin/Obsidian",
        discover_nested_excludes=True,
    )
    spec = build_indexing_mcp_process_spec(command=args.command, policy=policy)
    calls = run_probe(
        spec=spec,
        queries=args.query or list(DEFAULT_QUERIES),
        index_mode=args.index_mode,
        dry_run=args.dry_run,
        allow_derived_index_write=args.allow_derived_index_write,
        timeout_seconds=args.timeout_seconds,
        paths=(
            _discover_markdown_paths(policy.vault_root)
            if args.discover_paths
            else _load_paths_file(
                args.paths_file,
                derived_root=policy.derived_root,
            )
        ),
        batch_size=args.batch_size,
        checkpoint_path=args.batch_checkpoint,
        resume=args.resume,
    )
    bundle = write_indexing_mcp_report_bundle(
        calls=calls,
        policy=policy,
        raw_report=args.raw_report,
        sanitized_report=args.sanitized_report,
        report_root=args.report_root,
    )
    index_vault_failed = _index_vault_failed_count(bundle.sanitized_transcript.calls)
    status = "failed" if index_vault_failed > 0 else "ok"
    print(
        json.dumps(
            {
                "status": status,
                "calls": len(calls),
                "index_vault_failed": index_vault_failed,
                "raw_report": bundle.raw_report,
                "sanitized_report": bundle.sanitized_report,
                "redactions": len(bundle.sanitized_transcript.redactions),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if index_vault_failed > 0 else 0


def cli() -> int:
    try:
        return main()
    except (GuardrailError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
