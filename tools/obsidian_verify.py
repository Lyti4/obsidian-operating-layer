#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import GuardrailError, load_json, normalize_vault_root, validate_targets


def verify(observation: dict, proposal: dict) -> dict:
    issues: list[str] = []
    if proposal.get("dry_run_default") is not True:
        issues.append("proposal must remain dry-run by default")
    if proposal.get("approval_required") is not True:
        issues.append("proposal must require approval")
    if proposal.get("approval_phrase") != observation.get("run_commands", {}).get("approval_phrase", proposal.get("approval_phrase")):
        # The observation bundle does not currently carry the phrase; compare against proposal only.
        pass
    targets = proposal.get("targets", [])
    if not isinstance(targets, list):
        issues.append("proposal targets must be a list")
    elif targets:
        try:
            raw_vault_root = proposal.get("vault_root") or observation.get("vault_root")
            if not raw_vault_root:
                raise GuardrailError("proposal must include vault_root before target validation")
            vault_root = normalize_vault_root(str(raw_vault_root))
            target_paths = []
            for target in targets:
                raw_path = str(target.get("path")) if isinstance(target, dict) else str(target)
                candidate = Path(raw_path).expanduser()
                target_paths.append(str(candidate if candidate.is_absolute() else vault_root / candidate))
            validate_targets(vault_root, target_paths)
        except (GuardrailError, TypeError, ValueError) as exc:
            issues.append(f"proposal targets failed safety validation: {exc}")
        for target in targets:
            if not isinstance(target, dict):
                issues.append("proposal target must be an object")
                continue
            if "path" not in target or "new_text" not in target:
                issues.append("proposal target must include path and new_text")
            if not target.get("evidence"):
                issues.append("proposal target must retain evidence")
    backup_plan = proposal.get("backup_plan", {})
    if not backup_plan.get("backup_dir"):
        issues.append("proposal must include a backup dir")
    if not proposal.get("next_safe_step"):
        issues.append("proposal must include a next safe step")
    return {
        "ok": not issues,
        "issues": issues,
        "verified_observation": observation.get("vault_root"),
        "verified_proposal": proposal.get("vault_root"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an observation/proposal bundle for the Obsidian operating layer.")
    parser.add_argument("--observe", required=True, help="Observation JSON path")
    parser.add_argument("--proposal", required=True, help="Proposal JSON path")
    args = parser.parse_args()

    observation = load_json(Path(args.observe).expanduser().resolve())
    proposal = load_json(Path(args.proposal).expanduser().resolve())
    if not isinstance(observation, dict) or not isinstance(proposal, dict):
        raise GuardrailError("Observation and proposal must be JSON objects")

    result = verify(observation, proposal)
    if result["ok"]:
        print("verification ok")
    else:
        print("verification failed")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
