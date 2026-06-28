#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError, build_mcp_adapter_evaluation, evaluation_to_markdown, write_mcp_adapter_evaluation


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an Obsidian MCP adapter record under read-only sandbox policy.")
    parser.add_argument("--adapter-record", required=True, help="Adapter metadata JSON record")
    parser.add_argument("--sandbox-vault", required=True, help="Copied sandbox vault, never the first-run live vault")
    parser.add_argument("--out-dir", default="out/reports", help="Directory for JSON/Markdown evaluation reports")
    parser.add_argument(
        "--probe-tool",
        action="append",
        dest="probe_tools",
        help="MCP tool name to classify; may be passed multiple times. Defaults include safe and dangerous probes.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    evaluation = build_mcp_adapter_evaluation(
        adapter_record=args.adapter_record,
        sandbox_vault=args.sandbox_vault,
        probe_tools=args.probe_tools,
        artifact_root=out_dir,
    )
    json_out = Path(evaluation.artifacts["json_report"])
    md_out = json_out.with_suffix(".md")
    write_mcp_adapter_evaluation(evaluation, json_out)
    md_out.write_text(evaluation_to_markdown(evaluation), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "adapter": evaluation.adapter,
                "json_report": str(json_out),
                "markdown_report": str(md_out),
                "direct_write_disabled": evaluation.direct_write_disabled,
                "dangerous_tools_refused": evaluation.verification["dangerous_tools_refused"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
