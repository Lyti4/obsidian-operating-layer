#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import (
    INDEXING_WRAPPER_TOOL_ALLOWLIST,
    GuardrailError,
    build_indexing_mcp_process_spec,
    build_indexing_wrapper_policy,
    is_protected_relative,
    write_indexing_mcp_report_bundle,
)
from obslayer.indexing_wrapper import DEFAULT_INDEXING_REPORT_ROOT


def _load_calls(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    calls = payload.get("calls") if isinstance(payload, dict) else payload
    if not isinstance(calls, list):
        raise GuardrailError("Raw indexing transcript must be a list or an object with a calls list")
    return calls


def _mcp_text(payload: object) -> dict:
    return {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": json.dumps(payload)}]}}


def _first_probe_markdown(vault: Path) -> tuple[str, str]:
    for candidate in sorted(vault.rglob("*.md")):
        if not candidate.is_file():
            continue
        rel = candidate.relative_to(vault).as_posix()
        if is_protected_relative(rel):
            continue
        text = candidate.read_text(encoding="utf-8", errors="replace")
        return rel, text
    raise GuardrailError(f"Auto-probe sample requires at least one non-protected markdown note under {vault}")


def _build_auto_probe_sample_calls(vault_root: str, *, query: str) -> list[dict]:
    vault = Path(vault_root).expanduser().resolve()
    rel_path, text = _first_probe_markdown(vault)
    lines = text.splitlines()
    first_line = lines[0] if lines else ""
    snippet = first_line[:240]
    return [
        {"kind": "list_tools", "message": _mcp_text({"tools": [{"name": name} for name in INDEXING_WRAPPER_TOOL_ALLOWLIST]})},
        {"tool": "index_status", "message": _mcp_text({"read_only": True, "startup_index": False, "notes": 1})},
        {"tool": "index_vault", "message": _mcp_text({"indexed": 1, "failed": 0, "dryRun": True})},
        {
            "tool": "search_notes",
            "message": _mcp_text(
                {
                    "query": query,
                    "results": [
                        {
                            "path": rel_path,
                            "matched_sections": [{"line": 1, "snippet": snippet}],
                        }
                    ],
                }
            ),
        },
        {
            "tool": "read_note",
            "message": _mcp_text(
                {
                    "path": rel_path,
                    "start_line": 1,
                    "end_line": min(max(len(lines), 1), 5),
                    "content": "\n".join(lines[:5]),
                }
            ),
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize and gate an indexing MCP runtime transcript.")
    parser.add_argument("--sandbox-vault", required=True, help="Sandbox vault root; live vault paths are refused")
    parser.add_argument("--derived-root", required=True, help="Derived MCP/index storage root under out/external-indexing-spike")
    parser.add_argument("--raw-transcript", help="Input raw transcript JSON with a calls list")
    parser.add_argument(
        "--auto-probe-sample",
        action="store_true",
        help="Build a local sample transcript from the sandbox vault and route it through the same guardrails",
    )
    parser.add_argument(
        "--sample-query",
        default="Obsidian Operating Layer safety boundary",
        help="Query label recorded in --auto-probe-sample transcripts",
    )
    parser.add_argument("--raw-report", required=True, help="Output raw report path under the report root")
    parser.add_argument("--sanitized-report", required=True, help="Output sanitized report path under the report root")
    parser.add_argument(
        "--report-root",
        default=str(DEFAULT_INDEXING_REPORT_ROOT),
        help="Allowed report root for both raw and sanitized outputs",
    )
    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help="Optional MCP server command part; repeat to record a safe process spec without executing it",
    )
    args = parser.parse_args()

    policy = build_indexing_wrapper_policy(
        vault_root=args.sandbox_vault,
        derived_root=args.derived_root,
        discover_nested_excludes=True,
    )
    if args.auto_probe_sample == bool(args.raw_transcript):
        raise GuardrailError("Provide exactly one of --raw-transcript or --auto-probe-sample")
    calls = (
        _build_auto_probe_sample_calls(policy.vault_root, query=args.sample_query)
        if args.auto_probe_sample
        else _load_calls(Path(args.raw_transcript).expanduser().resolve())
    )
    bundle = write_indexing_mcp_report_bundle(
        calls=calls,
        policy=policy,
        raw_report=args.raw_report,
        sanitized_report=args.sanitized_report,
        report_root=args.report_root,
    )
    if args.command:
        build_indexing_mcp_process_spec(command=args.command, policy=policy)

    print(
        json.dumps(
            {
                "status": "ok",
                "raw_report": bundle.raw_report,
                "sanitized_report": bundle.sanitized_report,
                "calls": len(bundle.sanitized_transcript.calls),
                "redactions": len(bundle.sanitized_transcript.redactions),
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
