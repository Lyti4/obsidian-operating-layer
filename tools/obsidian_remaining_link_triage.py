#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from _bootstrap import SRC  # noqa: F401

from obslayer.remaining_link_triage import write_remaining_link_triage_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify remaining broken/ambiguous wikilinks without apply authority.")
    parser.add_argument("--wikilinks-jsonl", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    result = write_remaining_link_triage_packet(wikilinks_jsonl=args.wikilinks_jsonl, out_dir=args.out_dir)
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
