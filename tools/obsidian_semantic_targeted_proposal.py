#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.semantic_targeted_proposal import write_targeted_semantic_proposal


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote one semantic decision group into a proposal-only targeted packet.")
    parser.add_argument(
        "--decision-packet-json",
        required=True,
        help="decision-packet.json under out/proposals/semantic-candidate-decisions",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Output dir under out/proposals/semantic-targeted-proposals",
    )
    parser.add_argument("--group", default="link_hygiene_reports")
    parser.add_argument("--proposal-id", default=None)
    args = parser.parse_args()
    result = write_targeted_semantic_proposal(
        decision_packet_json=Path(args.decision_packet_json),
        out_dir=Path(args.out_dir),
        group=args.group,
        proposal_id=args.proposal_id,
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
