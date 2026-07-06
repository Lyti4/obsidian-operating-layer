#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

from obslayer.indexing_manifest_doctor import (  # noqa: E402
    build_indexing_doctor_report,
    manifest_from_dict,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an indexing manifest doctor contract.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--require-artifact", action="append", default=[])
    parser.add_argument("--artifact-base", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = build_indexing_doctor_report(
        manifest_from_dict(payload),
        required_artifacts=args.require_artifact,
        artifact_base=args.artifact_base or args.manifest.parent,
    )
    output = json.dumps(report.to_dict(), indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if report.status == "ready-for-operator-review" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
