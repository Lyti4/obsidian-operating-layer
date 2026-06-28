#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import (
    GuardrailError,
    build_indexing_mcp_process_spec,
    build_indexing_wrapper_policy,
    write_indexing_mcp_report_bundle,
)
from obslayer.indexing_wrapper import DEFAULT_INDEXING_REPORT_ROOT


def _load_calls(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    calls = payload.get("calls") if isinstance(payload, dict) else payload
    if not isinstance(calls, list):
        raise GuardrailError("Raw indexing transcript must be a list or an object with a calls list")
    return calls


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize and gate an indexing MCP runtime transcript.")
    parser.add_argument("--sandbox-vault", required=True, help="Sandbox vault root; live vault paths are refused")
    parser.add_argument("--derived-root", required=True, help="Derived MCP/index storage root under out/external-indexing-spike")
    parser.add_argument("--raw-transcript", required=True, help="Input raw transcript JSON with a calls list")
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

    policy = build_indexing_wrapper_policy(vault_root=args.sandbox_vault, derived_root=args.derived_root)
    calls = _load_calls(Path(args.raw_transcript).expanduser().resolve())
    bundle = write_indexing_mcp_report_bundle(
        calls=calls,
        policy=policy,
        raw_report=args.raw_report,
        sanitized_report=args.sanitized_report,
        report_root=args.report_root,
    )
    process_spec = None
    if args.command:
        process_spec = build_indexing_mcp_process_spec(command=args.command, policy=policy).to_dict()

    print(
        json.dumps(
            {
                "status": "ok",
                "raw_report": bundle.raw_report,
                "sanitized_report": bundle.sanitized_report,
                "calls": len(bundle.sanitized_transcript.calls),
                "redactions": len(bundle.sanitized_transcript.redactions),
                "process_spec": process_spec,
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
