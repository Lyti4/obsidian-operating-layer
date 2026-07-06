#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from _bootstrap import SRC  # noqa: F401

from obslayer.remaining_link_target_discovery import write_target_discovery_packet


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover target candidates for remaining broken/ambiguous links without apply authority."
    )
    parser.add_argument("--triage-json", required=True)
    parser.add_argument("--notes-index-jsonl", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--min-confidence", type=float, default=0.92)
    args = parser.parse_args()

    result = write_target_discovery_packet(
        triage_json=args.triage_json,
        notes_index_jsonl=args.notes_index_jsonl,
        out_dir=args.out_dir,
        min_confidence=args.min_confidence,
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
