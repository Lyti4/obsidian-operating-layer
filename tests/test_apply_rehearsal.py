from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_live_apply_rehearsal_on_disposable_sandbox_vault_creates_backup_and_verifies(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    sandbox_vault = tmp_path / "sandbox-vault"
    notes = sandbox_vault / "Notes"
    notes.mkdir(parents=True)
    target = notes / "alpha.md"
    target.write_text("# Alpha\nold body\n", encoding="utf-8")

    proposal_path = tmp_path / "proposal.json"
    proposal = {
        "vault_root": str(sandbox_vault),
        "source_id": "sandbox-apply-rehearsal",
        "summary": "Disposable sandbox apply rehearsal.",
        "mode": "dry-run",
        "dry_run_default": True,
        "approval_required": True,
        "approval_phrase": "APPROVE OBSIDIAN APPLY",
        "targets": [
            {
                "path": "Notes/alpha.md",
                "old_text": "old body",
                "new_text": "new body\nrehearsed: true",
                "evidence": "rehearsal unit test",
            }
        ],
    }
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    manifest_path = tmp_path / "approval-manifest.json"
    manifest = {
        "approved": True,
        "approval_phrase": "APPROVE OBSIDIAN APPLY",
        "task_id": "sandbox-apply-rehearsal",
        "approver": "unit-test",
        "reason": "Disposable sandbox rehearsal only; never live vault.",
        "vault_root": str(sandbox_vault),
        "proposal": str(proposal_path),
        "targets": [str(target)],
        "backup_root": "_Backups/obsidian-operating-layer",
        "dry_run": False,
        "require_post_verify": True,
        "max_files_per_run": 1,
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    apply_out = tmp_path / "apply-result.json"
    apply_run = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_apply.py"),
            "--proposal",
            str(proposal_path),
            "--approval-manifest",
            str(manifest_path),
            "--apply",
            "--out",
            str(apply_out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert apply_run.returncode == 0, apply_run.stderr + apply_run.stdout
    result = json.loads(apply_out.read_text(encoding="utf-8"))
    assert result["status"] == "applied"
    assert result["vault_root"] == str(sandbox_vault.resolve())
    assert result["applied"] == [
        {
            "path": "Notes/alpha.md",
            "backup": str(Path(result["backup_dir"]) / "Notes" / "alpha.md"),
            "changed": True,
        }
    ]
    assert target.read_text(encoding="utf-8") == "# Alpha\nnew body\nrehearsed: true\n"
    assert (Path(result["backup_dir"]) / "Notes" / "alpha.md").read_text(encoding="utf-8") == "# Alpha\nold body\n"
    assert (Path(result["backup_dir"]) / "approval-manifest.json").is_file()
    assert (Path(result["backup_dir"]) / "backup-plan.json").is_file()

    observe_out = tmp_path / "post-observe.json"
    observe_run = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_observe.py"),
            "--vault",
            str(sandbox_vault),
            "--out",
            str(observe_out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert observe_run.returncode == 0, observe_run.stderr + observe_run.stdout
    observed = json.loads(observe_out.read_text(encoding="utf-8"))
    assert observed["vault_root"] == str(sandbox_vault.resolve())
    assert observed["file_counts"][".md"] >= 1
    assert "Notes/alpha.md" in observed["sample_notes"]
