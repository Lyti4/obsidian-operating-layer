from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from obslayer import (
    GuardrailError,
    build_acceptance_report,
    cleanup_stale_running_jobs,
    create_controlled_job,
    find_controlled_job,
    move_controlled_job,
    run_controlled_job,
    write_acceptance_report,
)


def make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "Obsidian"
    (vault / "Notes").mkdir(parents=True)
    (vault / "Notes" / "alpha.md").write_text("---\ntitle: Alpha\n---\nhello [[Beta]]\n", encoding="utf-8")
    (vault / "Notes" / "beta.md").write_text("beta\n", encoding="utf-8")
    (vault / ".obsidian").mkdir()
    (vault / ".obsidian" / "workspace.json").write_text('{"secret": false}\n', encoding="utf-8")
    return vault


def test_controlled_job_runs_read_only_and_tracks_outputs(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    before = (vault / "Notes" / "alpha.md").read_text(encoding="utf-8")
    queue_root = tmp_path / "queue"

    job, job_path = create_controlled_job(queue_root=queue_root, kind="index", vault_root=vault, task_id="phase08-index")
    assert job_path == queue_root / "pending" / "phase08-index.json"
    assert job["safety"]["direct_write_enabled"] is False
    assert job["schedule"]["enabled"] is False

    done_job, done_path = run_controlled_job(queue_root, "phase08-index")

    assert done_path == queue_root / "done" / "phase08-index.json"
    assert done_job["status"] == "done"
    assert done_job["result"]["mutation_boundary"]["apply_status"] == "not-run"
    assert done_job["result"]["mutation_boundary"]["applied_targets"] == 0
    assert done_job["result"]["read_only_index"]["markdown_files"] == 2
    assert done_job["result"]["read_only_index"]["wikilink_count"] == 1
    assert Path(done_job["outputs"]["report_json"]).is_file()
    assert Path(done_job["outputs"]["report_markdown"]).is_file()
    assert (vault / "Notes" / "alpha.md").read_text(encoding="utf-8") == before
    with pytest.raises(GuardrailError, match="must be pending"):
        run_controlled_job(queue_root, "phase08-index")


def test_controlled_autonomy_refuses_apply_like_jobs(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    with pytest.raises(GuardrailError, match="read-only observe/index/report"):
        create_controlled_job(queue_root=tmp_path / "queue", kind="apply", vault_root=vault)


def test_duplicate_controlled_job_id_is_refused(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    queue_root = tmp_path / "queue"
    create_controlled_job(queue_root=queue_root, kind="observe", vault_root=vault, task_id="duplicate")

    with pytest.raises(GuardrailError, match="already exists"):
        create_controlled_job(queue_root=queue_root, kind="observe", vault_root=vault, task_id="duplicate")


def test_stale_running_job_cleanup_keeps_audit_evidence(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    queue_root = tmp_path / "queue"
    create_controlled_job(
        queue_root=queue_root,
        kind="observe",
        vault_root=vault,
        task_id="phase08-stale",
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    move_controlled_job(
        queue_root,
        "phase08-stale",
        "running",
        "claimed by test worker",
        now=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
    )

    cleaned = cleanup_stale_running_jobs(
        queue_root,
        older_than_seconds=60,
        now=datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
    )

    assert [job["task_id"] for job in cleaned] == ["phase08-stale"]
    job, path = find_controlled_job(queue_root, "phase08-stale")
    assert path == queue_root / "failed" / "phase08-stale.json"
    assert job["failure_reason"] == "stale-running-cleanup"
    assert any("cleaned up stale running job" in item["note"] for item in job["audit"])


def test_acceptance_report_distinguishes_dry_run_applied_and_rollback_evidence(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    queue_root = tmp_path / "queue"
    create_controlled_job(queue_root=queue_root, kind="report", vault_root=vault, task_id="phase08-report")
    run_controlled_job(queue_root, "phase08-report")
    dry_run = tmp_path / "apply-dry-run.json"
    dry_run.write_text(json.dumps({"status": "dry-run", "applied": []}), encoding="utf-8")
    applied = tmp_path / "apply-applied.json"
    applied.write_text(
        json.dumps(
            {
                "status": "applied",
                "backup_dir": str(vault / "_Backups" / "obsidian-operating-layer" / "20260101-000000Z"),
                "applied": [{"path": "Notes/alpha.md", "backup": "backup.md", "changed": True}],
            }
        ),
        encoding="utf-8",
    )

    report = build_acceptance_report(queue_root, apply_result_paths=[dry_run, applied])

    assert report["job_counts"] == {"done": 1}
    assert report["mutation_summary"]["dry_run_apply_results"] == 1
    assert report["mutation_summary"]["live_apply_results"] == 1
    assert report["mutation_summary"]["applied_targets"] == 1
    assert report["rollback_evidence"][0]["backup_dir"].endswith("_Backups/obsidian-operating-layer/20260101-000000Z")

    md_path, json_path, _ = write_acceptance_report(
        queue_root=queue_root,
        markdown_out=tmp_path / "acceptance.md",
        json_out=tmp_path / "acceptance.json",
        apply_result_paths=[dry_run, applied],
    )
    text = md_path.read_text(encoding="utf-8")
    assert "proposed_targets" in text
    assert "applied_targets" in text
    assert "Rollback evidence" in text
    assert json_path is not None and json_path.is_file()
