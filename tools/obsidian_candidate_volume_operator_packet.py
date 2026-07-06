#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.candidate_volume_operator_packet import (
    build_candidate_volume_operator_packet,
    candidate_volume_operator_packet_to_markdown,
    write_candidate_volume_operator_packet,
)
from obslayer.guardrails import GuardrailError


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a repo-only candidate-volume operator packet.")
    parser.add_argument("--repo", default=".", help="Repository root; defaults to current directory")
    parser.add_argument(
        "--observation",
        default="out/live-proposal-only-20260706T182612Z/observation.json",
        help="Repo-local observation.json",
    )
    parser.add_argument(
        "--proposal",
        default="out/live-proposal-only-20260706T182612Z/propose/proposal.json",
        help="Repo-local proposal.json",
    )
    parser.add_argument(
        "--verify",
        default="out/live-proposal-only-20260706T182612Z/verify.json",
        help="Repo-local verify.json",
    )
    parser.add_argument(
        "--unified-index",
        default=(
            "out/reports/unified-operator-review-index/"
            "full-vault-proposal-only-20260706T182612Z/unified-operator-review-index.json"
        ),
        help="Repo-local unified operator review index JSON",
    )
    parser.add_argument("--out-dir", required=True, help="Repo-local out/ or docs/ output directory")
    parser.add_argument("--json-only", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    packet = build_candidate_volume_operator_packet(
        repo=Path(args.repo),
        observation=args.observation,
        proposal=args.proposal,
        verify=args.verify,
        unified_index=args.unified_index,
    )
    json_path, report_path = write_candidate_volume_operator_packet(packet, args.out_dir)
    if args.json_only:
        print(json.dumps(packet.to_dict(), indent=2, sort_keys=True))
    else:
        print(candidate_volume_operator_packet_to_markdown(packet))
        print(json_path)
        print(report_path)
    return 0 if packet.status != "blocked" else 1


def cli() -> int:
    try:
        return main()
    except (OSError, ValueError, json.JSONDecodeError, GuardrailError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
