from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_backfill_report_cli_writes_markdown_to_explicit_reports_dir(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    vault = tmp_path / "Obsidian"
    vault.mkdir()
    proposal_path = tmp_path / "proposal.json"
    reports_dir = tmp_path / "Reports"
    proposal_path.write_text(
        json.dumps(
            {
                "vault_root": str(vault),
                "dry_run_default": True,
                "approval_required": True,
                "backup_plan": {"backup_dir": str(vault / "_Backups" / "field")},
                "next_safe_step": "Prepare approval manifest before live apply.",
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_backfill_report.py"),
            "--proposal",
            str(proposal_path),
            "--reports-dir",
            str(reports_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    out = Path(payload["out"])
    assert payload["status"] == "ok"
    assert out == reports_dir / "obslayer-implementation-report.md"
    assert out.is_file()
    report = out.read_text(encoding="utf-8")
    assert "# Obsidian Operating Layer Implementation Report" in report
    assert "dry_run_default: `True`" in report
    assert "approval_required: `True`" in report
    assert "approval manifest" in report
    assert "python tools/obsidian_apply.py" in report
    assert not any(vault.iterdir())


def test_backfill_report_cli_refuses_output_outside_reports_dir(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    reports_dir = tmp_path / "Reports"
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text("{}\n", encoding="utf-8")
    outside = tmp_path / "outside.md"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_backfill_report.py"),
            "--proposal",
            str(proposal_path),
            "--reports-dir",
            str(reports_dir),
            "--out",
            str(outside),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "outside --reports-dir" in completed.stderr
    assert not outside.exists()


def test_backfill_report_cli_refuses_to_overwrite_existing_report(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    reports_dir = tmp_path / "Reports"
    reports_dir.mkdir()
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text("{}\n", encoding="utf-8")
    out = reports_dir / "existing.md"
    out.write_text("original\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_backfill_report.py"),
            "--proposal",
            str(proposal_path),
            "--reports-dir",
            str(reports_dir),
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "already exists" in completed.stderr
    assert out.read_text(encoding="utf-8") == "original\n"
