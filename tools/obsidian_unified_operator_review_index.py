#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.unified_operator_review_index import (
    build_unified_operator_review_index,
    unified_operator_review_index_to_markdown,
    write_unified_operator_review_index,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a repo-only unified operator review index.")
    parser.add_argument("--repo", default=".", help="Repository root; defaults to current directory")
    parser.add_argument("--out-dir", required=True, help="Output directory for JSON and REPORT.md")
    parser.add_argument("--artifact", action="append", default=None, help="Explicit repo-local out/ or docs/ artifact path")
    parser.add_argument("--json-only", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    index = build_unified_operator_review_index(repo=Path(args.repo), artifacts=args.artifact)
    json_path, report_path = write_unified_operator_review_index(index, args.out_dir)
    if args.json_only:
        print(json.dumps(index.to_dict(), indent=2, sort_keys=True))
    else:
        print(unified_operator_review_index_to_markdown(index))
        print(json_path)
        print(report_path)
    return 0 if index.status != "blocked" else 1


def cli() -> int:
    try:
        return main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
