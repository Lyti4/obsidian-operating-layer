#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from _bootstrap import SRC  # noqa: F401

from obslayer import (
    DEFAULT_APPROVAL_PHRASE,
    GuardrailError,
    is_protected_relative,
    load_json,
    manifest_backup_plan,
    normalize_vault_root,
    validate_approval_manifest,
    validate_targets,
    write_json,
)


def proposal_target_relpaths(vault_root: Path, targets: list[dict]) -> list[Path]:
    relpaths: list[Path] = []
    for item in targets:
        if not isinstance(item, dict):
            raise GuardrailError("Each target must be an object")
        raw_path = item.get("path")
        if not raw_path:
            raise GuardrailError("Target missing path")
        candidate = Path(raw_path).expanduser()
        target_path = candidate.resolve() if candidate.is_absolute() else (vault_root / candidate).resolve()
        try:
            rel = target_path.relative_to(vault_root)
        except ValueError as exc:
            raise GuardrailError(f"Target escapes vault root: {target_path}") from exc
        if is_protected_relative(rel):
            raise GuardrailError(f"Refusing protected path: {rel}")
        relpaths.append(rel)
    return relpaths


def ensure_manifest_matches_proposal(vault_root: Path, proposal_targets: list[dict], manifest_targets: list[str]) -> list[Path]:
    proposal_relpaths = proposal_target_relpaths(vault_root, proposal_targets)
    approved_relpaths = validate_targets(vault_root, manifest_targets)
    proposal_list = sorted(path.as_posix() for path in proposal_relpaths)
    approved_list = sorted(path.as_posix() for path in approved_relpaths)
    if proposal_list != approved_list:
        missing = sorted(set(proposal_list) - set(approved_list))
        extra = sorted(set(approved_list) - set(proposal_list))
        raise GuardrailError(f"Proposal targets do not match approval manifest; not approved={missing}; extra_approved={extra}")
    return proposal_relpaths


def ensure_manifest_names_proposal(manifest_payload: dict, proposal_path: Path) -> None:
    raw_manifest_proposal = manifest_payload.get("proposal") or manifest_payload.get("proposal_path")
    if not raw_manifest_proposal:
        raise GuardrailError("Approval manifest must explicitly name the proposal file")
    manifest_proposal = Path(raw_manifest_proposal).expanduser().resolve()
    if manifest_proposal != proposal_path:
        raise GuardrailError(f"Approval manifest proposal does not match --proposal: {manifest_proposal} != {proposal_path}")


def apply_text_replacements(vault_root: Path, targets: list[dict], backup_dir: Path) -> list[dict]:
    results: list[dict] = []
    relpaths = proposal_target_relpaths(vault_root, targets)
    for item, rel in zip(targets, relpaths, strict=True):
        old_text = item.get("old_text", "")
        new_text = item.get("new_text", "")
        target_path = (vault_root / rel).resolve()
        if not target_path.exists():
            raise GuardrailError(f"Target missing: {target_path}")

        original = target_path.read_text(encoding="utf-8")
        base_sha256 = item.get("base_sha256")
        if base_sha256:
            current_sha256 = hashlib.sha256(original.encode("utf-8")).hexdigest()
            if current_sha256 != str(base_sha256):
                raise GuardrailError(f"base_sha256 mismatch in {rel}")
        if old_text and old_text not in original:
            raise GuardrailError(f"Old text not found in {rel}")

        backup_path = (backup_dir / rel).resolve()
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_bytes(target_path.read_bytes())

        updated = original.replace(old_text, new_text, 1) if old_text else new_text
        target_path.write_text(updated, encoding="utf-8")
        results.append({"path": rel.as_posix(), "backup": str(backup_path), "changed": original != updated})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply approved Obsidian edits with a dry-run default and backup gate.")
    parser.add_argument("--proposal", required=True, help="Proposal JSON produced by obsidian_propose.py")
    parser.add_argument("--approval-manifest", help="Approval manifest JSON required for live apply")
    parser.add_argument("--apply", action="store_true", help="Execute the live apply instead of dry-run")
    parser.add_argument("--out", help="Optional JSON output path for the apply result")
    args = parser.parse_args()

    proposal_path = Path(args.proposal).expanduser().resolve()
    proposal = load_json(proposal_path)
    vault_root = normalize_vault_root(proposal.get("vault_root", "/home/hermesadmin/Obsidian"))
    targets = proposal.get("targets", [])
    if not isinstance(targets, list):
        raise GuardrailError("Proposal targets must be a list")
    proposal_relpaths = proposal_target_relpaths(vault_root, targets)

    dry_run = not args.apply
    result = {
        "status": "dry-run" if dry_run else "pending-apply",
        "proposal": str(proposal_path),
        "vault_root": str(vault_root),
        "approval_required": True,
        "approval_phrase": DEFAULT_APPROVAL_PHRASE,
        "targets": targets,
        "target_relpaths": [path.as_posix() for path in proposal_relpaths],
        "backup_dir": None,
        "applied": [],
    }

    if dry_run:
        print(json.dumps(result, indent=2, sort_keys=True))
        if args.out:
            write_json(args.out, result)
        return 0

    if not args.approval_manifest:
        raise GuardrailError("Live apply requires --approval-manifest")

    raw_manifest = load_json(args.approval_manifest)
    ensure_manifest_names_proposal(raw_manifest, proposal_path)
    manifest = validate_approval_manifest(raw_manifest)
    manifest_vault_root = normalize_vault_root(manifest.vault_root)
    if manifest_vault_root != vault_root:
        raise GuardrailError(f"Approval manifest vault does not match proposal vault: {manifest_vault_root} != {vault_root}")
    validated_targets = ensure_manifest_matches_proposal(vault_root, targets, manifest.targets)
    if len(validated_targets) > manifest.max_files_per_run:
        raise GuardrailError("Apply exceeds max_files_per_run")

    backup_plan = manifest_backup_plan(manifest)
    backup_dir = Path(backup_plan.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Mirror the approval manifest into the backup tree for auditability.
    shutil.copy2(Path(args.approval_manifest).resolve(), backup_dir / "approval-manifest.json")
    write_json(backup_dir / "backup-plan.json", backup_plan.to_dict())

    applied = apply_text_replacements(vault_root, targets, backup_dir)
    result.update(
        {
            "status": "applied",
            "backup_dir": str(backup_dir),
            "applied": applied,
            "approval_manifest": str(Path(args.approval_manifest).resolve()),
        }
    )
    if args.out:
        write_json(args.out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def cli() -> int:
    try:
        return main()
    except GuardrailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
