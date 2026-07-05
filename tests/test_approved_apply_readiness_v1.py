from __future__ import annotations

import hashlib
import json
from pathlib import Path

from obslayer.approved_apply_readiness_v1 import evaluate_approved_apply_readiness


def _bundle(tmp_path: Path, *, with_hash: bool = True) -> tuple[Path, Path, dict, dict]:
    vault = tmp_path / "vault"
    (vault / "Notes").mkdir(parents=True)
    original = "alpha fixture\n"
    (vault / "Notes" / "alpha.md").write_text(original, encoding="utf-8")
    proposal_path = tmp_path / "proposal.json"
    manifest_path = tmp_path / "approval-manifest.json"
    target = {
        "path": "Notes/alpha.md",
        "old_text": "alpha",
        "new_text": "changed",
        "evidence": "unit fixture",
    }
    if with_hash:
        target["base_sha256"] = hashlib.sha256(original.encode("utf-8")).hexdigest()
    proposal = {"vault_root": str(vault), "targets": [target]}
    manifest = {
        "approval_phrase": "APPROVE OBSIDIAN APPLY",
        "approved": True,
        "approver": "Dmitry",
        "backup_root": "_Backups/obsidian-operating-layer",
        "dry_run": False,
        "proposal": str(proposal_path),
        "reason": "unit fixture",
        "require_post_verify": True,
        "targets": [str(vault / "Notes" / "alpha.md")],
        "task_id": "t_unit_fixture",
        "vault_root": str(vault),
        "max_files_per_run": 5,
    }
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return proposal_path, manifest_path, proposal, manifest


def test_approved_apply_readiness_accepts_hash_bound_manifest_bundle(tmp_path: Path) -> None:
    proposal_path, manifest_path, proposal, manifest = _bundle(tmp_path)

    report = evaluate_approved_apply_readiness(
        proposal,
        manifest,
        proposal_path=proposal_path,
        approval_manifest_path=manifest_path,
    ).to_dict()

    assert report["status"] == "ready"
    assert report["ready_for_human_approved_apply"] is True
    assert report["issues"] == []
    assert report["safety"]["live_mutation_authorized"] is False
    assert report["safety"]["approval_manifest_created"] is False
    assert report["safety"]["targets"] == []
    assert report["targets"][0]["sha256_present"] is True


def test_approved_apply_readiness_fails_closed_without_hash_binding(tmp_path: Path) -> None:
    proposal_path, manifest_path, proposal, manifest = _bundle(tmp_path, with_hash=False)

    report = evaluate_approved_apply_readiness(
        proposal,
        manifest,
        proposal_path=proposal_path,
        approval_manifest_path=manifest_path,
    ).to_dict()

    assert report["status"] == "not-ready"
    assert report["ready_for_human_approved_apply"] is False
    assert any("base_sha256" in issue for issue in report["issues"])


def test_approved_apply_readiness_fails_closed_on_manifest_proposal_drift(tmp_path: Path) -> None:
    proposal_path, manifest_path, proposal, manifest = _bundle(tmp_path)
    manifest["proposal"] = str(tmp_path / "other-proposal.json")

    report = evaluate_approved_apply_readiness(
        proposal,
        manifest,
        proposal_path=proposal_path,
        approval_manifest_path=manifest_path,
    ).to_dict()

    assert report["status"] == "not-ready"
    assert any("proposal does not match" in issue for issue in report["issues"])


def test_approved_apply_readiness_fails_closed_on_protected_target(tmp_path: Path) -> None:
    proposal_path, manifest_path, proposal, manifest = _bundle(tmp_path)
    vault = Path(proposal["vault_root"])
    (vault / "_Archive").mkdir()
    (vault / "_Archive" / "alpha.md").write_text("alpha\n", encoding="utf-8")
    proposal["targets"][0]["path"] = "_Archive/alpha.md"
    manifest["targets"] = [str(vault / "_Archive" / "alpha.md")]

    report = evaluate_approved_apply_readiness(
        proposal,
        manifest,
        proposal_path=proposal_path,
        approval_manifest_path=manifest_path,
    ).to_dict()

    assert report["status"] == "not-ready"
    assert any("protected" in issue.casefold() for issue in report["issues"])
