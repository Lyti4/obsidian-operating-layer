#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import (
    GuardrailError,
    build_rag_graph_adapter_evaluation,
    rag_graph_evaluation_to_markdown,
    write_rag_graph_adapter_evaluation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an Obsidian RAG/graph adapter record under sandbox-only policy.")
    parser.add_argument("--adapter-record", required=True, help="RAG/graph adapter metadata JSON record")
    parser.add_argument("--sandbox-vault", required=True, help="Copied sandbox vault; live vault paths are refused")
    parser.add_argument("--out-dir", default="out/reports", help="Directory for JSON/Markdown evaluation reports")
    parser.add_argument(
        "--query",
        action="append",
        dest="fixed_queries",
        help="Fixed evaluation query to record; may be passed multiple times. Defaults to Phase 04 queries.",
    )
    parser.add_argument(
        "--exclude-source-prefix",
        action="append",
        dest="source_exclude_prefixes",
        default=[],
        help="Proposal-only hygiene filter: exclude findings whose source/cluster/name equals or is under this relative prefix.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    evaluation = build_rag_graph_adapter_evaluation(
        adapter_record=args.adapter_record,
        sandbox_vault=args.sandbox_vault,
        fixed_queries=args.fixed_queries,
        artifact_root=out_dir,
        source_exclude_prefixes=args.source_exclude_prefixes,
    )
    json_out = Path(evaluation.artifacts["json_report"])
    md_out = json_out.with_suffix(".md")
    write_rag_graph_adapter_evaluation(evaluation, json_out)
    md_out.write_text(rag_graph_evaluation_to_markdown(evaluation), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "adapter": evaluation.adapter,
                "json_report": str(json_out),
                "markdown_report": str(md_out),
                "direct_write_disabled": evaluation.direct_write_disabled,
                "normalized_findings_only": evaluation.verification["normalized_findings_only"],
                "notes_scanned": evaluation.verification["notes_scanned"],
                "raw_finding_count": evaluation.verification["raw_finding_count"],
                "finding_count": evaluation.verification["finding_count"],
                "excluded_finding_count": evaluation.verification["excluded_finding_count"],
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
