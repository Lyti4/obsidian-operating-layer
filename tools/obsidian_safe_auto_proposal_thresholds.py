#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _bootstrap import SRC  # noqa: F401

from obslayer.safe_auto_proposal_thresholds import write_safe_auto_proposal_bundle


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
        if isinstance(payload.get("scored_packets"), list):
            return [record for record in payload["scored_packets"] if isinstance(record, dict)]
        if isinstance(payload.get("candidates"), list) and payload.get("source"):
            return [payload]
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    raise ValueError(f"Expected scored packet object, list, JSONL, or scored_packets array in {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an evidence-only safe-auto-proposal-thresholds dry-run bundle.")
    parser.add_argument("--scored-packets", required=True, help="Scored candidate packet JSON/JSONL input")
    parser.add_argument("--out-dir", required=True, help="Output directory under out/")
    parser.add_argument("--bundle-id", default=None)
    args = parser.parse_args()

    scored_packets = _read_json_records(Path(args.scored_packets))
    result = write_safe_auto_proposal_bundle(scored_packets, out_dir=Path(args.out_dir), bundle_id=args.bundle_id)
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
