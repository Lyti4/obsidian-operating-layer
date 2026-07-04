#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError
from obslayer.resource_preflight import collect_resource_preflight


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed resource preflight for Graphify/embedding runs.")
    parser.add_argument("--min-available-mb", type=int, default=1024)
    parser.add_argument("--max-swap-used-mb", type=int, default=512)
    parser.add_argument("--max-load-per-cpu", type=float, default=1.25)
    parser.add_argument("--max-swap-io-pages-per-sec", type=int, default=20)
    parser.add_argument("--sample-seconds", type=float, default=1.0)
    args = parser.parse_args()
    report = collect_resource_preflight(
        min_available_mb=args.min_available_mb,
        max_swap_used_mb=args.max_swap_used_mb,
        max_load_per_cpu=args.max_load_per_cpu,
        max_swap_io_pages_per_sec=args.max_swap_io_pages_per_sec,
        sample_seconds=args.sample_seconds,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
