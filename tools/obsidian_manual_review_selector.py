#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from _bootstrap import SRC  # noqa: F401

from obslayer.manual_review_selector_v1 import write_manual_review_selector_packet


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build repo-only/evidence-only manual review shortlist from candidate-scorer-v1 or safe-auto "
            "proposal packets."
        )
    )
    parser.add_argument("--proposal-json", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-candidates", type=int, default=5)
    args = parser.parse_args()

    result = write_manual_review_selector_packet(
        proposal_packet=args.proposal_json,
        out_dir=args.out_dir,
        max_candidates=args.max_candidates,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def cli() -> int:
    try:
        return main()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", end="\n", flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
