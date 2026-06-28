from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import GuardrailError, normalize_findings_to_proposal, write_normalized_proposal


def make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "Obsidian"
    (vault / "Notes").mkdir(parents=True)
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "Notes" / "alpha.md").write_text("# Alpha\nold body\n", encoding="utf-8")
    (vault / ".obsidian" / "app.json").write_text("{}\n", encoding="utf-8")
    return vault


def test_normalize_findings_to_proposal_preserves_evidence_risk_and_dry_run_defaults(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    findings = [
        {
            "id": "finding-1",
            "type": "metadata-suggestion",
            "severity": "low",
            "evidence": "alpha note is missing a status field",
            "risk": "low",
            "targets": [
                {
                    "path": "Notes/alpha.md",
                    "old_text": "# Alpha\n",
                    "new_text": "---\nstatus: proposed\n---\n# Alpha\n",
                }
            ],
        }
    ]

    proposal = normalize_findings_to_proposal(vault_root=vault, findings=findings, source_id="unit-test")

    assert proposal["mode"] == "dry-run"
    assert proposal["dry_run_default"] is True
    assert proposal["approval_required"] is True
    assert proposal["risk_class"] == "low"
    assert proposal["source_id"] == "unit-test"
    assert proposal["targets"] == [
        {
            "path": "Notes/alpha.md",
            "old_text": "# Alpha\n",
            "new_text": "---\nstatus: proposed\n---\n# Alpha\n",
            "finding_id": "finding-1",
            "finding_type": "metadata-suggestion",
            "risk": "low",
            "evidence": "alpha note is missing a status field",
        }
    ]
    assert proposal["evidence"] == [
        {
            "finding_id": "finding-1",
            "finding_type": "metadata-suggestion",
            "target_paths": ["Notes/alpha.md"],
            "evidence": "alpha note is missing a status field",
            "risk": "low",
        }
    ]
    assert "approval manifest" in proposal["next_safe_step"]


def test_normalize_findings_to_proposal_refuses_protected_targets(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    findings = [
        {
            "type": "metadata-suggestion",
            "evidence": "plugin setting should never be changed by worker",
            "targets": [{"path": ".obsidian/app.json", "old_text": "{}", "new_text": '{"unsafe": true}'}],
        }
    ]

    with pytest.raises(GuardrailError, match="protected path"):
        normalize_findings_to_proposal(vault_root=vault, findings=findings, source_id="unsafe")


def test_write_normalized_proposal_refuses_out_dir_inside_vault_root_without_writing(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    proposal = normalize_findings_to_proposal(
        vault_root=vault,
        findings=[
            {
                "id": "finding-inside-vault",
                "type": "metadata-suggestion",
                "evidence": "alpha note is missing a status field",
                "targets": [
                    {
                        "path": "Notes/alpha.md",
                        "old_text": "# Alpha\n",
                        "new_text": "---\nstatus: proposed\n---\n# Alpha\n",
                    }
                ],
            }
        ],
        source_id="inside-vault-test",
    )
    out_dir = vault / "proposal-output"

    with pytest.raises(GuardrailError, match="inside vault root"):
        write_normalized_proposal(proposal, out_dir)

    assert not (out_dir / "proposal.json").exists()
    assert not (out_dir / "proposal.md").exists()


def test_proposal_worker_cli_writes_proposal_and_apply_dry_run_accepts_it(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    vault = make_vault(tmp_path)
    findings_path = tmp_path / "findings.json"
    out_dir = tmp_path / "proposal"
    findings_path.write_text(
        json.dumps(
            {
                "source_id": "cli-test",
                "findings": [
                    {
                        "id": "finding-cli",
                        "type": "candidate-backlink",
                        "severity": "medium",
                        "evidence": "alpha should link to beta",
                        "targets": [
                            {
                                "path": "Notes/alpha.md",
                                "old_text": "old body",
                                "new_text": "old body\nRelated: [[Beta]]",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_proposal_worker.py"),
            "--findings",
            str(findings_path),
            "--vault-root",
            str(vault),
            "--out-dir",
            str(out_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    proposal_path = Path(payload["proposal_json"])
    assert proposal_path.is_file()
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    assert proposal["source_id"] == "cli-test"
    assert proposal["targets"][0]["path"] == "Notes/alpha.md"

    dry_run = subprocess.run(
        [sys.executable, str(repo / "tools" / "obsidian_apply.py"), "--proposal", str(proposal_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert dry_run.returncode == 0, dry_run.stderr + dry_run.stdout
    assert json.loads(dry_run.stdout)["status"] == "dry-run"


def test_verify_accepts_normalized_proposal_targets_after_safety_validation(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    vault = make_vault(tmp_path)
    observation = tmp_path / "observe.json"
    proposal_path = tmp_path / "proposal.json"
    observation.write_text(json.dumps({"vault_root": str(vault), "observed_at": "unit-test"}), encoding="utf-8")
    proposal = normalize_findings_to_proposal(
        vault_root=vault,
        findings=[
            {
                "id": "finding-verify",
                "type": "metadata-suggestion",
                "evidence": "alpha needs status",
                "targets": [{"path": "Notes/alpha.md", "old_text": "# Alpha", "new_text": "# Alpha\nstatus: proposed"}],
            }
        ],
        source_id="verify-test",
    )
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_verify.py"),
            "--observe",
            str(observation),
            "--proposal",
            str(proposal_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert "verification ok" in completed.stdout
