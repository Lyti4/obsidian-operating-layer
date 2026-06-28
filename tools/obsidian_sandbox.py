#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError, create_sandbox_vault, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or reset a protected-path-excluding sandbox copy of an Obsidian vault.")
    parser.add_argument("--source-vault", "--source", default="/home/hermesadmin/Obsidian", help="Source vault to copy read-only")
    parser.add_argument("--sandbox-root", default="out/sandbox-vaults", help="Directory that will contain sandbox vault copies")
    parser.add_argument("--name", help="Sandbox directory name under --sandbox-root")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the named sandbox if it already exists")
    parser.add_argument("--out", help="Optional JSON report path")
    args = parser.parse_args()

    report = create_sandbox_vault(
        source_vault=args.source_vault,
        sandbox_root=args.sandbox_root,
        name=args.name,
        reset=args.reset,
    ).to_dict()
    payload = {"status": "ok", **report}

    if args.out:
        write_json(Path(args.out).expanduser().resolve(), payload)
        payload["out"] = str(Path(args.out).expanduser().resolve())

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
