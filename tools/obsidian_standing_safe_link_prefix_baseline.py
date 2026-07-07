#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from _bootstrap import SRC  # noqa: F401

from obslayer.standing_safe_link_prefix_baseline import write_standing_safe_link_prefix_baseline


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only standing safe link-prefix classifier baseline.")
    parser.add_argument("--vault", required=True, help="Vault root to scan read-only.")
    parser.add_argument("--scan-root", help="Optional scan root inside vault. Defaults to vault root.")
    parser.add_argument("--out-dir", required=True, help="Directory for JSON/Markdown evidence.")
    args = parser.parse_args()
    result = write_standing_safe_link_prefix_baseline(vault_root=args.vault, scan_root=args.scan_root, out_dir=args.out_dir)
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
