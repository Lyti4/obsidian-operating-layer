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
