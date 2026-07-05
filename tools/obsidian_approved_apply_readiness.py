#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.approved_apply_readiness_v1 import (
    approved_apply_readiness_to_markdown,
    load_and_evaluate_approved_apply_readiness,
    write_approved_apply_readiness_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an approved-apply proposal/manifest bundle without applying it.")
    parser.add_argument("--proposal", required=True, help="Proposal JSON path")
    parser.add_argument("--approval-manifest", required=True, help="Approval manifest JSON path")
    parser.add_argument("--out-dir", help="Optional output directory for JSON and REPORT.md")
    parser.add_argument("--json-only", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    report = load_and_evaluate_approved_apply_readiness(
        proposal_path=Path(args.proposal),
        approval_manifest_path=Path(args.approval_manifest),
    )
    if args.out_dir:
        write_approved_apply_readiness_bundle(report, args.out_dir)
    if args.json_only:
        import json
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(approved_apply_readiness_to_markdown(report))
    return 0 if report.ready_for_human_approved_apply else 1


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
