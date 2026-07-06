#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from obslayer import GuardrailError
from obslayer.semantic_manifest import doctor_semantic_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only doctor for an existing semantic indexing manifest.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    result = doctor_semantic_manifest(repo=Path(args.repo), manifest=Path(args.manifest))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


def cli() -> int:
    try:
        return main()
    except (GuardrailError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "findings": [str(exc)]}, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
