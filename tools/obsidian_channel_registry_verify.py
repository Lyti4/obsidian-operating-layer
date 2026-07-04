#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.channel_registry import channel_registry_validation_to_markdown, validate_channel_registry


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the Obsidian Layer channel registry.")
    parser.add_argument("--registry", default="docs/spec-kit/channel-registry.json")
    parser.add_argument("--out-dir", default="out/reports/channel-registry-verify/manual")
    args = parser.parse_args()

    report = validate_channel_registry(args.registry)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "channel-registry-validation.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "REPORT.md").write_text(channel_registry_validation_to_markdown(report), encoding="utf-8")
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
