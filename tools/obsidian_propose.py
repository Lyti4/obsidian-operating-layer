#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import DEFAULT_APPROVAL_PHRASE, GuardrailError, canonical_run_commands, planned_backup_dir


def build_proposal(observation: dict, out_dir: Path) -> dict:
    vault_root = Path(observation["vault_root"]).expanduser().resolve()
    backup_dir = planned_backup_dir(vault_root)
    run_commands = canonical_run_commands().to_dict()
    proposal = {
        "vault_root": str(vault_root),
        "based_on": observation.get("observed_at", ""),
        "summary": "Guardrail-first proposal skeleton",
        "mode": "dry-run",
        "dry_run_default": True,
        "approval_required": True,
        "approval_phrase": DEFAULT_APPROVAL_PHRASE,
        "backup_plan": {
            "backup_root": str(backup_dir.parent),
            "backup_dir": str(backup_dir),
        },
        "targets": [],
        "risk_class": "read_only_only",
        "run_commands": run_commands,
        "next_safe_step": "Prepare approval manifest and author exact targets before any live apply.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "proposal.json").write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "proposal.md").write_text(
        "# Obsidian Operating Layer Proposal\n\n"
        f"- vault: `{proposal['vault_root']}`\n"
        f"- dry-run default: `{proposal['dry_run_default']}`\n"
        f"- approval phrase: `{proposal['approval_phrase']}`\n"
        f"- backup dir: `{proposal['backup_plan']['backup_dir']}`\n"
        "- targets: none in this safety-rails slice\n\n"
        "## Safe commands\n\n"
        f"- observe: `{run_commands['observe']}`\n"
        f"- propose: `{run_commands['propose']}`\n"
        f"- apply: `{run_commands['apply']}`\n"
        f"- verify: `{run_commands['verify']}`\n"
        f"- backfill report: `{run_commands['backfill_report']}`\n",
        encoding="utf-8",
    )
    return proposal


def main() -> int:
    parser = argparse.ArgumentParser(description="Turn observation JSON into a dry-run-first proposal bundle.")
    parser.add_argument("--observe", required=True, help="Observation JSON path")
    parser.add_argument("--out-dir", required=True, help="Output directory for proposal bundle")
    args = parser.parse_args()

    observe_path = Path(args.observe).expanduser().resolve()
    try:
        observation = json.loads(observe_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GuardrailError(f"Observation file missing: {observe_path}") from exc
    if not isinstance(observation, dict):
        raise GuardrailError("Observation JSON must be an object")

    proposal = build_proposal(observation, Path(args.out_dir).expanduser().resolve())
    print(json.dumps({"status": "ok", "proposal": proposal}, indent=2, sort_keys=True))
    return 0


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
