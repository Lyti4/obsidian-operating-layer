#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _bootstrap import SRC  # noqa: F401

from obslayer.external_tool_benchmark import write_external_tool_benchmark_report


def _read_json_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        records: list[dict[str, Any]] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"Expected JSON object per line in {path}")
            records.append(payload)
        return records

    payload = json.loads(text)
    if isinstance(payload, dict):
        for key in ("scored_packets", "scorer_packets", "scored_links", "candidate_packets"):
            if isinstance(payload.get(key), list):
                return [record for record in payload[key] if isinstance(record, dict)]
        if isinstance(payload.get("candidates"), list) and payload.get("source"):
            return [payload]
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    raise ValueError(f"Expected scorer packet object, list, JSONL, or scored_packets array in {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a repo-only read-only external-tool benchmark report.")
    parser.add_argument(
        "--scored-packets",
        default=None,
        help="Optional scored candidate packet JSON/JSONL input. Defaults to deterministic repo-local examples.",
    )
    parser.add_argument(
        "--out-dir",
        default="out/reports/external-tool-benchmark/manual",
        help="Output directory under out/reports/external-tool-benchmark/",
    )
    parser.add_argument("--benchmark-id", default=None)
    args = parser.parse_args()

    scored_packets = _read_json_records(Path(args.scored_packets)) if args.scored_packets else None
    result = write_external_tool_benchmark_report(scored_packets, out_dir=Path(args.out_dir), benchmark_id=args.benchmark_id)
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
