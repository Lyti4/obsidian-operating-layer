from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_smoke_script_runs_safe_dry_run_pipeline(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    vault = tmp_path / "Obsidian"
    (vault / "Notes").mkdir(parents=True)
    (vault / "Notes" / "alpha.md").write_text("hello [[world]]\n", encoding="utf-8")
    out_root = tmp_path / "out"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "smoke.py"),
            "--vault",
            str(vault),
            "--out-root",
            str(out_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    summary_start = completed.stdout.rfind("{\n")
    assert summary_start != -1, completed.stdout
    summary = json.loads(completed.stdout[summary_start:])
    assert summary["status"] == "ok"
    assert summary["apply_status"] == "dry-run"
    assert summary["applied"] == []
    assert summary["approval_required"] is True
    assert Path(summary["run_dir"]).is_dir()
    assert (Path(summary["run_dir"]) / "observe.json").is_file()
    assert (Path(summary["run_dir"]) / "proposal" / "proposal.json").is_file()
    assert (Path(summary["run_dir"]) / "apply-dry-run.json").is_file()
