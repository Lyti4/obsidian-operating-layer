#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer.semantic_review_index import build_semantic_review_index, semantic_review_index_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a proposal-only semantic review index from a targeted proposal packet.")
    parser.add_argument("--targeted-proposal-json", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    index = build_semantic_review_index(args.targeted_proposal_json)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "review-index.json").write_text(json.dumps(index.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "REPORT.md").write_text(semantic_review_index_to_markdown(index), encoding="utf-8")
    print(json.dumps(index.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
