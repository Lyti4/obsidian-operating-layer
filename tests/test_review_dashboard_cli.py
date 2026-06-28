from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_proposal(root: Path, name: str, *, status: str = "needs-review", risk: str = "low") -> Path:
    proposal_dir = root / name
    proposal_dir.mkdir(parents=True)
    proposal = {
        "source_id": name,
        "summary": f"Proposal {name}",
        "status": status,
        "risk_class": risk,
        "dry_run_default": True,
        "approval_required": True,
        "approval_phrase": "APPROVE_OBSIDIAN_OPERATING_LAYER_APPLY",
        "backup_plan": {"backup_root": "_Backups/obsidian-operating-layer"},
        "next_safe_step": "Review, then create an approval manifest before any live apply.",
        "targets": [
            {
                "path": "Notes/alpha.md",
                "old_text": "old",
                "new_text": "new",
                "evidence": "unit test",
            }
        ],
        "evidence": [{"finding_id": "f1", "risk": risk}],
    }
    path = proposal_dir / "proposal.json"
    path.write_text(json.dumps(proposal), encoding="utf-8")
    (proposal_dir / "proposal.md").write_text("# Proposal\n", encoding="utf-8")
    return path


def test_review_dashboard_list_outputs_pending_proposals_as_json_and_markdown(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    root = tmp_path / "proposals"
    write_proposal(root, "pending-one", status="needs-review", risk="medium")
    write_proposal(root, "already-applied", status="applied", risk="low")

    json_run = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_review_dashboard.py"),
            "list",
            "--proposal-root",
            str(root),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert json_run.returncode == 0, json_run.stderr + json_run.stdout
    payload = json.loads(json_run.stdout)
    assert payload["count"] == 1
    row = payload["proposals"][0]
    assert row["proposal_id"] == "pending-one"
    assert row["risk"] == "medium"
    assert row["target_count"] == 1
    assert row["status"] == "needs-review"
    assert row["dry_run_default"] is True
    assert row["approval_required"] is True

    md_run = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_review_dashboard.py"),
            "list",
            "--proposal-root",
            str(root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert md_run.returncode == 0, md_run.stderr + md_run.stdout
    assert "Pending Obsidian Operating Layer Proposals" in md_run.stdout
    assert "pending-one" in md_run.stdout
    assert "already-applied" not in md_run.stdout


def test_review_dashboard_explain_refuses_unsafe_non_dry_run_proposal(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    proposal_path = write_proposal(tmp_path / "proposals", "unsafe")
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    proposal["dry_run_default"] = False
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_review_dashboard.py"),
            "explain",
            "--proposal",
            str(proposal_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "must require approval and default to dry-run" in completed.stderr


def test_review_dashboard_explain_outputs_human_summary(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    proposal_path = write_proposal(tmp_path / "proposals", "explain-me", risk="high")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_review_dashboard.py"),
            "explain",
            "--proposal",
            str(proposal_path),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    explanation = payload["explanation"]
    assert explanation["proposal_id"] == "explain-me"
    assert explanation["risk"] == "high"
    assert explanation["what_will_change"] == ["Notes/alpha.md"]
    assert explanation["target_diffs"][0]["path"] == "Notes/alpha.md"
    assert "--- a/Notes/alpha.md" in explanation["target_diffs"][0]["diff"]
    assert "+new" in explanation["target_diffs"][0]["diff"]
    assert explanation["approval_phrase"] == "APPROVE_OBSIDIAN_OPERATING_LAYER_APPLY"


def test_review_dashboard_explain_markdown_includes_proposed_diff(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    proposal_path = write_proposal(tmp_path / "proposals", "diff-me")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_review_dashboard.py"),
            "explain",
            "--proposal",
            str(proposal_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert "## Proposed diff" in completed.stdout
    assert "```diff" in completed.stdout
    assert "--- a/Notes/alpha.md" in completed.stdout
    assert "+new" in completed.stdout
