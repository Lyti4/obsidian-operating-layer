#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from obslayer.operator_review_packet import build_operator_review_packet, write_operator_review_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a repo-only operator review packet from dry-run proposal evidence.")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--proposal-packet", required=True)
    parser.add_argument("--readiness-packet")
    parser.add_argument("--max-review-items", type=int, default=5)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    packet = build_operator_review_packet(
        repo=Path(args.repo),
        proposal_packet=args.proposal_packet,
        readiness_packet=args.readiness_packet,
        max_review_items=args.max_review_items,
    )
    json_path, report_path = write_operator_review_packet(packet, args.out_dir)
    print(json_path)
    print(report_path)
    return 0 if packet.status != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
