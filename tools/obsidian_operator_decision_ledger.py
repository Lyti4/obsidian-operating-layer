#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _bootstrap import SRC  # noqa: F401

from obslayer.operator_decision_ledger_v1 import (
    normalize_decision_record,
    read_operator_decision_records,
    write_operator_decision_ledger_bundle,
)


def _record_from_args(args: argparse.Namespace) -> dict[str, Any] | None:
    fields = {
        "created_at": args.created_at,
        "decision_id": args.decision_id,
        "decision_type": args.decision_type,
        "actor": args.actor,
        "reason": args.reason,
        "source_pattern": args.source_pattern,
        "proposed_target": args.proposed_target,
        "scorer_version": args.scorer_version,
        "verification_outcome": args.verification_outcome,
        "evidence_refs": args.evidence_ref or [],
        "proposal_refs": args.proposal_ref or [],
        "target_refs": args.target_ref or [],
        "approval_manifest_refs": args.approval_manifest_ref or [],
        "safety_flags": args.safety_flag or [],
    }
    if not any(value for key, value in fields.items() if key not in {"actor", "verification_outcome"}):
        return None
    return normalize_decision_record({key: value for key, value in fields.items() if value is not None and value != []})


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an evidence-only operator-decision-ledger-v1 bundle.")
    parser.add_argument("--records", action="append", default=[], help="Existing decision records JSON/JSONL; may repeat")
    parser.add_argument("--out-dir", required=True, help="Output directory under out/")
    parser.add_argument("--ledger-id", default=None)
    parser.add_argument("--created-at", default=None, help="Ledger timestamp; also used for a single appended record if set")
    parser.add_argument("--decision-id", default=None)
    parser.add_argument("--decision-type", default=None)
    parser.add_argument("--actor", default="operator")
    parser.add_argument("--reason", default=None)
    parser.add_argument("--source-pattern", default=None)
    parser.add_argument("--proposed-target", default=None)
    parser.add_argument("--scorer-version", default=None)
    parser.add_argument("--verification-outcome", default="not-verified")
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--proposal-ref", action="append", default=[])
    parser.add_argument("--target-ref", action="append", default=[])
    parser.add_argument("--approval-manifest-ref", action="append", default=[])
    parser.add_argument("--safety-flag", action="append", default=[])
    args = parser.parse_args()

    records: list[dict[str, Any]] = []
    for records_path in args.records:
        records.extend(read_operator_decision_records(Path(records_path)))
    appended = _record_from_args(args)
    if appended is not None:
        records.append(appended)
    result = write_operator_decision_ledger_bundle(records, out_dir=Path(args.out_dir), ledger_id=args.ledger_id)
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
