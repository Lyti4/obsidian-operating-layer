#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.semantic_proposal_report import write_semantic_proposal_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a proposal-only report from a Graphify embedding query-smoke JSON.")
    parser.add_argument("--query-smoke-json", required=True, help="query-smoke.json under out/reports/graphify-embedding-query-smoke")
    parser.add_argument("--out-dir", required=True, help="Output dir under out/proposals/semantic-query-reports")
    parser.add_argument("--proposal-id", default=None)
    parser.add_argument("--max-candidates", type=int, default=25)
    args = parser.parse_args()
    result = write_semantic_proposal_report(
        query_smoke_json=Path(args.query_smoke_json),
        out_dir=Path(args.out_dir),
        proposal_id=args.proposal_id,
        max_candidates=args.max_candidates,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def cli() -> int:
    try:
        return main()
    except (GuardrailError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
