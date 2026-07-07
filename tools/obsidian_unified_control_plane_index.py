#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.guardrails import GuardrailError
from obslayer.unified_control_plane_index import (
    build_unified_control_plane_index,
    unified_control_plane_index_to_markdown,
    write_unified_control_plane_index,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic repo-only unified control-plane evidence index.")
    parser.add_argument("--repo", default=".", help="Repository root; defaults to current directory")
    parser.add_argument("--out-dir", required=True, help="Output directory under out/reports/unified-control-plane-index/")
    parser.add_argument(
        "--artifact",
        action="append",
        default=None,
        help="Explicit repo-local docs/, out/reports/, or out/proposals/ artifact",
    )
    parser.add_argument("--max-reports", type=int, default=50, help="Maximum auto-discovered reports to summarize")
    parser.add_argument(
        "--include-out-glob",
        action="append",
        default=None,
        help="Operator-selected bounded glob under out/reports/ or out/proposals/ to include in addition to defaults",
    )
    parser.add_argument("--json-only", action="store_true", help="Print JSON only")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on blockers")
    args = parser.parse_args()

    index = build_unified_control_plane_index(
        repo=Path(args.repo),
        artifacts=args.artifact,
        include_out_globs=args.include_out_glob,
        max_reports=args.max_reports,
    )
    json_path, report_path = write_unified_control_plane_index(index, args.out_dir)
    if args.json_only:
        print(json.dumps(index.to_dict(), indent=2, sort_keys=True))
    else:
        print(unified_control_plane_index_to_markdown(index))
        print(json_path)
        print(report_path)
    if args.strict and index.blockers:
        return 1
    return 0


def cli() -> int:
    try:
        return main()
    except (OSError, ValueError, json.JSONDecodeError, GuardrailError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
