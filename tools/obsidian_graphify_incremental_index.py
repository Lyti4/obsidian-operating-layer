#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.graphify_incremental_index import run_graphify_incremental_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repo-only Graphify incremental indexing wrapper.")
    parser.add_argument("--graph-json", required=True)
    parser.add_argument("--sandbox-vault", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--derived-root", default="out/external-indexing-spike/graphify-derived")
    parser.add_argument("--max-candidates", type=int, default=50)
    parser.add_argument("--max-delta-candidates", type=int, default=25)
    parser.add_argument("--provider", choices=["ollama", "local-hashing-v1"], default="ollama")
    parser.add_argument("--allow-smoke-provider", action="store_true")
    parser.add_argument("--run", action="store_true", help="Actually run embeddings for the delta manifest; default is dry-run only")
    parser.add_argument("--query-smoke", action="store_true")
    parser.add_argument("--query", action="append", default=[])
    args = parser.parse_args()

    report = run_graphify_incremental_index(
        graph_json=Path(args.graph_json),
        sandbox_vault=Path(args.sandbox_vault),
        out_dir=Path(args.out_dir),
        derived_root=Path(args.derived_root),
        max_candidates=args.max_candidates,
        max_delta_candidates=args.max_delta_candidates,
        provider=args.provider,
        dry_run=not args.run,
        run_query_smoke=args.query_smoke,
        queries=args.query or None,
        allow_smoke_provider=args.allow_smoke_provider,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.status == "ready" else 1


def cli() -> int:
    try:
        return main()
    except (GuardrailError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
