from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_field_slice_cli_runs_proposal_only_flow_and_records_decision(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    vault = tmp_path / "vault-subset"
    (vault / "Notes").mkdir(parents=True)
    before = "# Alpha\nfield candidate\n"
    note = vault / "Notes" / "alpha.md"
    note.write_text(before, encoding="utf-8")
    out_root = tmp_path / "field-slice"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_field_slice.py"),
            "--vault",
            str(vault),
            "--out-root",
            str(out_root),
            "--task-id",
            "field-test",
            "--decision",
            "rejected",
            "--reason",
            "Acceptance test rejects proposal without applying it.",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["live_apply"] == "not-run"
    assert note.read_text(encoding="utf-8") == before

    proposal = json.loads(Path(payload["proposal"]).read_text(encoding="utf-8"))
    assert proposal["dry_run_default"] is True
    assert proposal["approval_required"] is True
    assert proposal["targets"][0]["path"] == "Notes/alpha.md"

    verify = json.loads(Path(payload["verify"]).read_text(encoding="utf-8"))
    assert verify["ok"] is True

    dashboard = json.loads(Path(payload["dashboard_list"]).read_text(encoding="utf-8"))
    assert dashboard["count"] == 1
    assert dashboard["proposals"][0]["proposal_id"] == "field-test"

    decision = json.loads(Path(payload["decision"]).read_text(encoding="utf-8"))
    assert decision["decision"] == "rejected"
    assert decision["mutation_boundary"] == "proposal-only"
    assert decision["live_apply"] == "not-run"
    assert (out_root / "decision.md").is_file()
