#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from _bootstrap import SRC  # noqa: F401

from obslayer.safe_auto_proposal_thresholds_v1 import write_safe_auto_proposal_thresholds_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit repo-only/evidence-only dry-run proposal candidates from candidate-scorer-v1 JSON.")
    parser.add_argument("--candidate-scorer-json", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--packet-id")
    args = parser.parse_args()
    result = write_safe_auto_proposal_thresholds_packet(
        candidate_scorer_json=args.candidate_scorer_json,
        out_dir=args.out_dir,
        packet_id=args.packet_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
