#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.graphify_embedding_handoff import write_graphify_embedding_handoff


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a bounded embedding manifest from Graphify graph.json without running embeddings."
    )
    parser.add_argument("--graph-json", required=True, help="Generated Graphify graph.json")
    parser.add_argument("--sandbox-vault", required=True, help="Sandbox vault/corpus that Graphify analyzed")
    parser.add_argument("--out-dir", required=True, help="Report directory under out/reports/graphify-embedding-handoff")
    parser.add_argument(
        "--derived-root",
        default="out/external-indexing-spike/graphify-derived",
        help="Derived embedding cache root under out/external-indexing-spike/graphify-derived",
    )
    parser.add_argument("--max-candidates", type=int, default=50)
    args = parser.parse_args()

    result = write_graphify_embedding_handoff(
        graph_json=Path(args.graph_json),
        sandbox_vault=Path(args.sandbox_vault),
        out_dir=Path(args.out_dir),
        derived_root=Path(args.derived_root),
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
