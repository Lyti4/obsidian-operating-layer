#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.lane_schema_v1 import write_lane_schema_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a safe lane-schema-v1 evidence packet.")
    parser.add_argument("--actionable-lanes-json", required=True)
    parser.add_argument("--notes-index-jsonl", required=True)
    parser.add_argument("--wikilinks-jsonl", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--packet-id", default=None)
    args = parser.parse_args()

    result = write_lane_schema_packet(
        actionable_lanes_json=Path(args.actionable_lanes_json),
        notes_index_jsonl=Path(args.notes_index_jsonl),
        wikilinks_jsonl=Path(args.wikilinks_jsonl),
        out_dir=Path(args.out_dir),
        packet_id=args.packet_id,
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
