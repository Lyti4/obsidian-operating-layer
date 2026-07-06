#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from obslayer.guardrails import GuardrailError  # noqa: E402
from obslayer.manifest_candidate_selector import (  # noqa: E402
    build_manifest_candidate_selector,
    manifest_candidate_selector_to_markdown,
    write_manifest_candidate_selector,
)


def cli() -> int:
    parser = argparse.ArgumentParser(description="Build repo-only manifest candidate selector evidence.")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument(
        "--candidate-packet",
        default=(
            "out/reports/candidate-volume-operator-packet/"
            "full-vault-proposal-only-20260706T182612Z/candidate-volume-operator-packet.json"
        ),
        help="Repo-local candidate-volume packet JSON",
    )
    parser.add_argument(
        "--unified-index",
        default=(
            "out/reports/unified-operator-review-index/"
            "full-vault-proposal-only-20260706T182612Z/unified-operator-review-index.json"
        ),
        help="Repo-local unified operator review index JSON",
    )
    parser.add_argument(
        "--operator-review-packet",
        default="out/reports/operator-review-packet/grouped-next5-smoke/operator-review-packet.json",
        help="Repo-local operator review packet JSON",
    )
    parser.add_argument(
        "--out-dir",
        default="out/reports/manifest-candidate-selector/grouped-next5-smoke",
        help="Repo-local output directory for JSON and REPORT.md",
    )
    parser.add_argument("--max-candidates", type=int, default=5, help="Maximum candidates to select")
    parser.add_argument("--json-only", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    try:
        selector = build_manifest_candidate_selector(
            repo=Path(args.repo),
            candidate_packet=args.candidate_packet,
            unified_index=args.unified_index,
            operator_review_packet=args.operator_review_packet,
            max_candidates=args.max_candidates,
        )
        json_path, _ = write_manifest_candidate_selector(selector, args.out_dir)
        if args.json_only:
            print(json.dumps(selector.to_dict(), indent=2, sort_keys=True))
        else:
            print(manifest_candidate_selector_to_markdown(selector))
            print(json_path)
        return 0 if selector.status != "blocked" else 1
    except (OSError, ValueError, json.JSONDecodeError, GuardrailError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
