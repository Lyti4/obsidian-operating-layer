#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.graphify_embedding_runner import write_graphify_embedding_run_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run bounded local embeddings from a Graphify-derived embedding manifest."
    )
    parser.add_argument("--manifest", required=True, help="Graphify-derived embedding-manifest.json")
    parser.add_argument("--out-dir", required=True, help="Report dir under out/reports/graphify-embedding-runs")
    parser.add_argument("--derived-root", default=None, help="Derived cache root under out/external-indexing-spike/graphify-derived")
    parser.add_argument("--max-files", type=int, default=25)
    parser.add_argument("--provider", choices=["ollama", "local-hashing-v1"], default="ollama")
    parser.add_argument("--allow-smoke-provider", action="store_true", help="Allow local-hashing-v1 smoke/test provider")
    parser.add_argument("--ollama-base-url", default="http://localhost:11434")
    parser.add_argument("--ollama-model", default="bge-m3")
    parser.add_argument("--ollama-timeout-seconds", type=int, default=180)
    parser.add_argument("--dimensions", type=int, default=128)
    parser.add_argument("--max-chars-per-file", type=int, default=80000)
    parser.add_argument("--max-chars-per-chunk", type=int, default=2000)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    parser.add_argument(
        "--skip-resource-preflight",
        action="store_true",
        help="Bypass RAM/swap/load guard; use only for tests/smoke isolation",
    )
    parser.add_argument("--min-available-mb", type=int, default=1024)
    parser.add_argument("--max-swap-used-mb", type=int, default=512)
    parser.add_argument("--max-load-per-cpu", type=float, default=1.25)
    parser.add_argument("--max-swap-io-pages-per-sec", type=int, default=20)
    parser.add_argument(
        "--keep-ollama-loaded-after-run",
        action="store_true",
        help="Do not request Ollama model unload after the bounded run",
    )
    args = parser.parse_args()

    result = write_graphify_embedding_run_report(
        manifest_path=Path(args.manifest),
        out_dir=Path(args.out_dir),
        derived_root=Path(args.derived_root) if args.derived_root else None,
        max_files=args.max_files,
        dimensions=args.dimensions,
        max_chars_per_file=args.max_chars_per_file,
        max_chars_per_chunk=args.max_chars_per_chunk,
        chunk_overlap=args.chunk_overlap,
        provider=args.provider,
        allow_smoke_provider=args.allow_smoke_provider,
        ollama_base_url=args.ollama_base_url,
        ollama_model=args.ollama_model,
        ollama_timeout_seconds=args.ollama_timeout_seconds,
        resource_preflight=not args.skip_resource_preflight,
        min_available_mb=args.min_available_mb,
        max_swap_used_mb=args.max_swap_used_mb,
        max_load_per_cpu=args.max_load_per_cpu,
        max_swap_io_pages_per_sec=args.max_swap_io_pages_per_sec,
        unload_ollama_after_run=not args.keep_ollama_loaded_after_run,
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
