#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.semantic_manifest import write_semantic_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a manifest over semantic/indexing generated evidence artifacts.")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--embedding-manifest", required=True)
    parser.add_argument("--embedding-run", required=True)
    parser.add_argument("--query-smoke", required=True)
    parser.add_argument("--semantic-proposal", required=True)
    parser.add_argument("--decision-packet", required=True)
    parser.add_argument("--targeted-proposal", required=True)
    parser.add_argument("--review-index", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    result = write_semantic_manifest(
        repo=Path(args.repo),
        embedding_manifest=Path(args.embedding_manifest),
        embedding_run=Path(args.embedding_run),
        query_smoke=Path(args.query_smoke),
        semantic_proposal=Path(args.semantic_proposal),
        decision_packet=Path(args.decision_packet),
        targeted_proposal=Path(args.targeted_proposal),
        review_index=Path(args.review_index),
        out_dir=Path(args.out_dir),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] != "blocked" else 1


def cli() -> int:
    try:
        return main()
    except (GuardrailError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
