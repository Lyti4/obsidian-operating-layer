from __future__ import annotations

import json
from pathlib import Path

import pytest

from obsidian_operating_layer.core import (
    ApplyError,
    apply_proposal,
    build_proposal,
    observe_vault,
    verify_proposal,
)


def _write_note(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_observe_vault_detects_links_broken_links_and_orphans(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _write_note(vault / "A.md", "A links to [[B]] and [[Missing Note]].")
    _write_note(vault / "B.md", "B exists.")
    _write_note(vault / "orphan.md", "lonely note")

    observation = observe_vault(vault)

    assert observation["vault_root"] == str(vault)
    assert observation["counts"]["notes"] == 3
    assert observation["counts"]["broken_links"] == 1
    assert observation["counts"]["orphans"] == 1
    assert observation["broken_links"][0]["source"] == str(vault / "A.md")
    assert observation["broken_links"][0]["target"] == "Missing Note"
    assert observation["orphans"] == [str(vault / "orphan.md")]


def test_build_proposal_is_dry_run_by_default(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    observation = {
        "vault_root": str(vault),
        "counts": {"notes": 1, "broken_links": 0, "orphans": 0},
        "broken_links": [],
        "orphans": [],
        "notes": [],
    }

    proposal = build_proposal(observation, label="initial dry-run")

    assert proposal["label"] == "initial dry-run"
    assert proposal["dry_run"] is True
    assert proposal["target_vault"] == str(vault)
    assert proposal["proposal_id"]
    assert proposal["actions"] == []
    assert proposal["source_counts"] == observation["counts"]


def test_apply_requires_manifest_for_real_edits_and_dry_run_is_noop(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    target = vault / "A.md"
    _write_note(target, "original content")

    proposal = {
        "proposal_id": "proposal-123",
        "dry_run": False,
        "target_vault": str(vault),
        "actions": [
            {
                "kind": "write_text",
                "path": str(target),
                "content": "changed content",
            }
        ],
    }

    dry_run_result = apply_proposal(proposal)
    assert dry_run_result["dry_run"] is True
    assert target.read_text(encoding="utf-8") == "original content"

    with pytest.raises(ApplyError):
        apply_proposal(proposal, dry_run=False)

    manifest = tmp_path / "approval.json"
    manifest.write_text(
        json.dumps(
            {
                "approved": True,
                "proposal_id": "proposal-123",
                "target_vault": str(vault),
            }
        ),
        encoding="utf-8",
    )

    real_result = apply_proposal(proposal, dry_run=False, approval_manifest=manifest)
    assert real_result["dry_run"] is False
    assert target.read_text(encoding="utf-8") == "changed content"


def test_verify_accepts_consistent_observation_and_proposal(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _write_note(vault / "A.md", "A links to [[B]].")
    _write_note(vault / "B.md", "B exists.")

    observation = observe_vault(vault)
    proposal = build_proposal(observation, label="verify me")

    result = verify_proposal(observation, proposal)

    assert result["passed"] is True
    assert result["issues"] == []
    assert result["checked_counts"] == observation["counts"]
