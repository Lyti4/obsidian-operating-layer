#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.archive_shadow_index import write_archive_shadow_index


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build archive-shadow-index v1 evidence-only artifacts."
    )
    parser.add_argument("--notes-index-jsonl", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    result = write_archive_shadow_index(
        notes_index_jsonl=Path(args.notes_index_jsonl),
        out_dir=Path(args.out_dir),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def cli() -> int:
    try:
        return main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
