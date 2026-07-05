#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.operator_review_queue import build_operator_review_queue, write_operator_review_queue


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a read-only operator review queue index from known evidence artifacts.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    queue = build_operator_review_queue(args.repo_root)
    write_operator_review_queue(queue, args.out_dir)
    print(json.dumps(queue.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
