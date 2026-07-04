#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.semantic_candidate_decision_packet import write_candidate_decision_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify semantic proposal candidates into operator decision groups.")
    parser.add_argument("--semantic-proposal-json", required=True, help="proposal.json under out/proposals/semantic-query-reports")
    parser.add_argument("--out-dir", required=True, help="Output dir under out/proposals/semantic-candidate-decisions")
    parser.add_argument("--packet-id", default=None)
    args = parser.parse_args()
    result = write_candidate_decision_packet(
        semantic_proposal_json=Path(args.semantic_proposal_json),
        out_dir=Path(args.out_dir),
        packet_id=args.packet_id,
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
