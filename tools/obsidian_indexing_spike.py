#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import (
    GuardrailError,
    build_indexing_spike_evaluation,
    indexing_spike_to_markdown,
    write_indexing_spike_evaluation,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a knowledge-indexing candidate under no-write sandbox policy."
    )
    parser.add_argument("--candidate-record", required=True, help="Knowledge indexer metadata JSON record")
    parser.add_argument("--sandbox-vault", required=True, help="Copied sandbox vault; live vault is refused")
    parser.add_argument("--out-dir", default="out/reports/indexing-spike", help="Directory for JSON/Markdown reports")
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="Fixed evaluation query; may be passed multiple times.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    evaluation = build_indexing_spike_evaluation(
        candidate_record=args.candidate_record,
        sandbox_vault=args.sandbox_vault,
        fixed_queries=args.queries,
        artifact_root=out_dir,
    )
    json_out = Path(evaluation.artifacts["json_report"])
    md_out = json_out.with_suffix(".md")
    write_indexing_spike_evaluation(evaluation, json_out)
    md_out.write_text(indexing_spike_to_markdown(evaluation), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "candidate": evaluation.candidate,
                "verification_status": evaluation.verification["status"],
                "json_report": str(json_out),
                "markdown_report": str(md_out),
                "acceptance": evaluation.acceptance,
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
