#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError, load_findings_bundle, normalize_findings_to_proposal, write_normalized_proposal


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize component findings into a dry-run-first obslayer proposal bundle.")
    parser.add_argument("--findings", required=True, help="Component findings JSON; either a list or an object with source_id/findings")
    parser.add_argument("--vault-root", required=True, help="Vault root for target validation")
    parser.add_argument("--out-dir", required=True, help="Output directory for proposal.json and proposal.md")
    parser.add_argument("--source-id", help="Override source id recorded in the proposal")
    args = parser.parse_args()

    source_id, findings = load_findings_bundle(args.findings)
    proposal = normalize_findings_to_proposal(
        vault_root=args.vault_root,
        findings=findings,
        source_id=args.source_id or source_id,
    )
    proposal_json, proposal_md = write_normalized_proposal(proposal, Path(args.out_dir))
    print(
        json.dumps(
            {
                "status": "ok",
                "source_id": proposal["source_id"],
                "proposal_json": str(proposal_json),
                "proposal_markdown": str(proposal_md),
                "targets": len(proposal["targets"]),
                "risk_class": proposal["risk_class"],
                "dry_run_default": proposal["dry_run_default"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cli() -> int:
    try:
        return main()
    except (GuardrailError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
