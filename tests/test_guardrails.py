from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import (
    DEFAULT_APPROVAL_PHRASE,
    GuardrailError,
    build_approval_manifest,
    canonical_run_commands,
    canonical_workspace_layout,
    manifest_backup_plan,
    planned_backup_dir,
    validate_approval_manifest,
    validate_targets,
)


def make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "Obsidian"
    (vault / "Notes").mkdir(parents=True)
    (vault / "_Backups" / "existing").mkdir(parents=True)
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "Notes" / "alpha.md").write_text("hello world\n", encoding="utf-8")
    (vault / "Notes" / "beta.md").write_text("beta\n", encoding="utf-8")
    (vault / "_Backups" / "existing" / "ignore.md").write_text("ignore\n", encoding="utf-8")
    (vault / ".obsidian" / "ignore.json").write_text("{}\n", encoding="utf-8")
    return vault


def test_workspace_layout_and_commands_are_canonical() -> None:
    layout = canonical_workspace_layout()
    assert "src/obslayer/guardrails.py" in layout
    commands = canonical_run_commands().to_dict()
    assert commands["observe"].startswith("python tools/obsidian_observe.py")
    assert commands["apply"].endswith("--apply")


def test_validate_targets_blocks_protected_paths(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    ok = validate_targets(vault, [vault / "Notes" / "alpha.md"])
    assert ok == [Path("Notes/alpha.md")]

    with pytest.raises(GuardrailError):
        validate_targets(vault, [vault / "_Backups" / "existing" / "ignore.md"])
    with pytest.raises(GuardrailError):
        validate_targets(vault, [vault / ".obsidian" / "ignore.json"])


def test_backup_plan_stays_inside_vault_backup_tree(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    backup = planned_backup_dir(vault, timestamp="20260101-010101Z")
    assert str(backup).startswith(str(vault))
    assert "_Backups/obsidian-operating-layer/20260101-010101Z" in str(backup)


def test_approval_manifest_requires_phrase_and_target_validation(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    manifest = build_approval_manifest(
        task_id="t_123",
        approver="Dmitry",
        reason="narrow safe edit",
        vault_root=str(vault),
        targets=[str(vault / "Notes" / "alpha.md")],
        dry_run=False,
    )
    validated = validate_approval_manifest(manifest.to_dict())
    assert validated.approval_phrase == DEFAULT_APPROVAL_PHRASE
    assert validated.targets == [str(vault / "Notes" / "alpha.md")]

    bad = manifest.to_dict()
    bad["approval_phrase"] = "NOPE"
    with pytest.raises(GuardrailError):
        validate_approval_manifest(bad)


def test_manifest_backup_plan_matches_validate_approval_manifest(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    manifest = build_approval_manifest(
        task_id="t_123",
        approver="Dmitry",
        reason="narrow safe edit",
        vault_root=str(vault),
        targets=[str(vault / "Notes" / "alpha.md")],
        dry_run=False,
    )
    plan = manifest_backup_plan(manifest, timestamp="20260101-010101Z")
    assert plan.backup_dir.endswith("_Backups/obsidian-operating-layer/20260101-010101Z")
    assert plan.targets == [str(vault / "Notes" / "alpha.md")]


def test_approval_manifest_rejects_backup_root_escape(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    manifest = build_approval_manifest(
        task_id="t_123",
        approver="Dmitry",
        reason="narrow safe edit",
        vault_root=str(vault),
        targets=[str(vault / "Notes" / "alpha.md")],
        dry_run=False,
    ).to_dict()

    manifest["backup_root"] = "../outside"
    with pytest.raises(GuardrailError):
        validate_approval_manifest(manifest)

    manifest["backup_root"] = "/tmp/outside"
    with pytest.raises(GuardrailError):
        validate_approval_manifest(manifest)


def test_live_apply_refuses_manifest_without_proposal_binding(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    repo = Path(__file__).resolve().parents[1]
    proposal = tmp_path / "proposal.json"
    manifest = tmp_path / "approval.json"

    proposal.write_text(
        json.dumps(
            {
                "vault_root": str(vault),
                "targets": [
                    {"path": "Notes/alpha.md", "old_text": "hello", "new_text": "changed"},
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest.write_text(
        json.dumps(
            {
                "approved": True,
                "approval_phrase": DEFAULT_APPROVAL_PHRASE,
                "task_id": "t_guard",
                "approver": "Dmitry",
                "reason": "missing proposal binding",
                "vault_root": str(vault),
                "targets": [str(vault / "Notes" / "alpha.md")],
                "backup_root": "_Backups/obsidian-operating-layer",
                "dry_run": False,
                "require_post_verify": True,
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_apply.py"),
            "--proposal",
            str(proposal),
            "--approval-manifest",
            str(manifest),
            "--apply",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "proposal file" in completed.stderr + completed.stdout
    assert (vault / "Notes" / "alpha.md").read_text(encoding="utf-8") == "hello world\n"


def test_cli_round_trip_observe_propose_verify_and_dry_run_apply(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    repo = Path(__file__).resolve().parents[1]
    observe = tmp_path / "observe.json"
    proposal_dir = tmp_path / "proposal"
    apply_out = tmp_path / "apply.json"
    verify_cmd = [sys.executable, str(repo / "tools" / "obsidian_observe.py"), "--vault", str(vault), "--out", str(observe)]
    propose_cmd = [
        sys.executable,
        str(repo / "tools" / "obsidian_propose.py"),
        "--observe",
        str(observe),
        "--out-dir",
        str(proposal_dir),
    ]
    verify_cmd2 = [
        sys.executable,
        str(repo / "tools" / "obsidian_verify.py"),
        "--observe",
        str(observe),
        "--proposal",
        str(proposal_dir / "proposal.json"),
    ]
    dry_apply_cmd = [
        sys.executable,
        str(repo / "tools" / "obsidian_apply.py"),
        "--proposal",
        str(proposal_dir / "proposal.json"),
        "--out",
        str(apply_out),
    ]

    for cmd in (verify_cmd, propose_cmd, verify_cmd2, dry_apply_cmd):
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stderr + completed.stdout

    observe_payload = json.loads(observe.read_text(encoding="utf-8"))
    proposal_payload = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    apply_payload = json.loads(apply_out.read_text(encoding="utf-8"))
    assert observe_payload["vault_root"] == str(vault.resolve())
    assert proposal_payload["dry_run_default"] is True
    assert apply_payload["status"] == "dry-run"
    assert apply_payload["approval_required"] is True


def test_root_cli_wrappers_delegate_to_canonical_tools() -> None:
    repo = Path(__file__).resolve().parents[1]
    for script_name in ("obsidian_observe.py", "obsidian_propose.py", "obsidian_apply.py", "obsidian_verify.py"):
        root_help = subprocess.run(
            [sys.executable, str(repo / script_name), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        tool_help = subprocess.run(
            [sys.executable, str(repo / "tools" / script_name), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert root_help.returncode == 0, root_help.stderr + root_help.stdout
        assert tool_help.returncode == 0, tool_help.stderr + tool_help.stdout
        assert root_help.stdout == tool_help.stdout


def test_live_apply_refuses_proposal_target_not_approved_by_manifest(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    repo = Path(__file__).resolve().parents[1]
    proposal = tmp_path / "proposal.json"
    manifest = tmp_path / "approval.json"
    apply_out = tmp_path / "apply.json"

    proposal.write_text(
        json.dumps(
            {
                "vault_root": str(vault),
                "targets": [
                    {"path": "Notes/beta.md", "old_text": "beta", "new_text": "changed"},
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest.write_text(
        json.dumps(
            {
                "approved": True,
                "proposal": str(proposal),
                "approval_phrase": DEFAULT_APPROVAL_PHRASE,
                "task_id": "t_guard",
                "approver": "Dmitry",
                "reason": "approve only alpha",
                "vault_root": str(vault),
                "targets": [str(vault / "Notes" / "alpha.md")],
                "backup_root": "_Backups/obsidian-operating-layer",
                "dry_run": False,
                "require_post_verify": True,
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_apply.py"),
            "--proposal",
            str(proposal),
            "--approval-manifest",
            str(manifest),
            "--apply",
            "--out",
            str(apply_out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "not approved" in completed.stderr + completed.stdout or "does not match" in completed.stderr + completed.stdout
    assert (vault / "Notes" / "beta.md").read_text(encoding="utf-8") == "beta\n"


def test_live_apply_refuses_protected_proposal_target_even_with_manifest(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    repo = Path(__file__).resolve().parents[1]
    proposal = tmp_path / "proposal.json"
    manifest = tmp_path / "approval.json"

    proposal.write_text(
        json.dumps(
            {
                "vault_root": str(vault),
                "targets": [
                    {"path": ".obsidian/ignore.json", "old_text": "{}", "new_text": '{"changed": true}'},
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest.write_text(
        json.dumps(
            {
                "approved": True,
                "proposal": str(proposal),
                "approval_phrase": DEFAULT_APPROVAL_PHRASE,
                "task_id": "t_guard",
                "approver": "Dmitry",
                "reason": "approve only safe target; proposal tries protected path",
                "vault_root": str(vault),
                "targets": [str(vault / "Notes" / "alpha.md")],
                "backup_root": "_Backups/obsidian-operating-layer",
                "dry_run": False,
                "require_post_verify": True,
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_apply.py"),
            "--proposal",
            str(proposal),
            "--approval-manifest",
            str(manifest),
            "--apply",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "protected path" in completed.stderr + completed.stdout
    assert (vault / ".obsidian" / "ignore.json").read_text(encoding="utf-8") == "{}\n"


def test_live_apply_refuses_manifest_vault_mismatch(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    other_vault = tmp_path / "OtherVault"
    other_vault.mkdir()
    repo = Path(__file__).resolve().parents[1]
    proposal = tmp_path / "proposal.json"
    manifest = tmp_path / "approval.json"

    proposal.write_text(
        json.dumps(
            {
                "vault_root": str(vault),
                "targets": [
                    {"path": "Notes/alpha.md", "old_text": "hello", "new_text": "changed"},
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest.write_text(
        json.dumps(
            {
                "approved": True,
                "proposal": str(proposal),
                "approval_phrase": DEFAULT_APPROVAL_PHRASE,
                "task_id": "t_guard",
                "approver": "Dmitry",
                "reason": "wrong vault",
                "vault_root": str(other_vault),
                "targets": [str(other_vault / "Notes" / "alpha.md")],
                "backup_root": "_Backups/obsidian-operating-layer",
                "dry_run": False,
                "require_post_verify": True,
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_apply.py"),
            "--proposal",
            str(proposal),
            "--approval-manifest",
            str(manifest),
            "--apply",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "vault" in completed.stderr + completed.stdout
    assert (vault / "Notes" / "alpha.md").read_text(encoding="utf-8") == "hello world\n"
