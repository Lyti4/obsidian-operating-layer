#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from _bootstrap import SRC  # noqa: F401

from obslayer.standing_safe_link_prefix_policy import (
    classify_link_prefix_candidate,
    load_standing_safe_link_prefix_policy,
    validate_standing_safe_link_prefix_policy,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the standing safe link-prefix policy and optionally classify an explicit fixture."
    )
    parser.add_argument("--policy-file", help="Policy JSON path. Defaults to repo root/package data.")
    parser.add_argument("--source-relpath", help="Explicit source note relpath fixture.")
    parser.add_argument("--link", help="Explicit wiki link fixture.")
    parser.add_argument(
        "--existing-target",
        action="append",
        default=[],
        help="Existing target relpath fixture. Repeatable; no vault scan is performed.",
    )
    args = parser.parse_args()

    policy = load_standing_safe_link_prefix_policy(args.policy_file)
    payload = {"policy_validation": validate_standing_safe_link_prefix_policy(policy)}

    if args.source_relpath or args.link or args.existing_target:
        if not args.source_relpath or not args.link:
            parser.error("--source-relpath and --link are required when classifying a fixture")
        payload["classification"] = classify_link_prefix_candidate(
            source_relpath=args.source_relpath,
            link=args.link,
            existing_target_relpaths=args.existing_target,
        ).to_dict()

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
