#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.acceptance_bundle_doctor import (
    acceptance_bundle_doctor_to_markdown,
    load_and_doctor_acceptance_bundle,
    write_acceptance_bundle_doctor_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a repo-only acceptance/evidence bundle without granting apply authority.")
    parser.add_argument("--bundle", required=True, help="Acceptance bundle JSON path")
    parser.add_argument("--repo", default=".", help="Repository root; defaults to current directory")
    parser.add_argument("--out-dir", help="Optional output directory for JSON and REPORT.md")
    parser.add_argument("--json-only", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    report = load_and_doctor_acceptance_bundle(Path(args.bundle), repo=Path(args.repo))
    if args.out_dir:
        write_acceptance_bundle_doctor_report(report, args.out_dir)
    if args.json_only:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(acceptance_bundle_doctor_to_markdown(report))
    return 0 if report.status == "accepted" else 1


def cli() -> int:
    try:
        return main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
