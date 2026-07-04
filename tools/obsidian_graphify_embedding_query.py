#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.graphify_embedding_query import write_graphify_embedding_query_smoke_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run semantic query smoke against a Graphify embedding-run derived cache.")
    parser.add_argument("--run-json", required=True, help="embedding-run.json under out/reports/graphify-embedding-runs")
    parser.add_argument("--out-dir", required=True, help="Report dir under out/reports/graphify-embedding-query-smoke")
    parser.add_argument("--query", action="append", required=True, help="Query text; repeat for multiple queries")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--provider", choices=["ollama", "local-hashing-v1"], default=None)
    parser.add_argument("--dimensions", type=int, default=None)
    parser.add_argument("--ollama-base-url", default="http://localhost:11434")
    parser.add_argument("--ollama-model", default="bge-m3")
    parser.add_argument("--ollama-timeout-seconds", type=int, default=360)
    parser.add_argument(
        "--keep-ollama-loaded-after-query",
        action="store_true",
        help="Do not request Ollama model unload after query smoke",
    )
    args = parser.parse_args()
    result = write_graphify_embedding_query_smoke_report(
        run_json=Path(args.run_json),
        out_dir=Path(args.out_dir),
        queries=args.query,
        top_k=args.top_k,
        provider=args.provider,
        dimensions=args.dimensions,
        ollama_base_url=args.ollama_base_url,
        ollama_model=args.ollama_model,
        ollama_timeout_seconds=args.ollama_timeout_seconds,
        unload_ollama_after_query=not args.keep_ollama_loaded_after_query,
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
