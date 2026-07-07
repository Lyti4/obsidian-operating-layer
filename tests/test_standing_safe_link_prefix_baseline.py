from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from obslayer.standing_safe_link_prefix_baseline import (
    build_standing_safe_link_prefix_baseline,
    collect_existing_markdown_targets,
    write_standing_safe_link_prefix_baseline,
)


def make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "Obsidian"
    (vault / "Memory-Vault" / "Notes").mkdir(parents=True)
    (vault / "Memory-Vault" / "Hermes").mkdir(parents=True)
    (vault / "Memory-Vault" / "Hermes" / "Reports").mkdir(parents=True)
    (vault / "Memory-Vault" / "_Backups").mkdir(parents=True)
    (vault / "Memory-Vault" / "Notes" / "source.md").write_text(
        "ok [[Hermes/Inbox]] alias [[Hermes/Alias Target|label]] missing [[Hermes/Missing]]\n",
        encoding="utf-8",
    )
    (vault / "Memory-Vault" / "Hermes" / "Inbox.md").write_text("inbox\n", encoding="utf-8")
    (vault / "Memory-Vault" / "Hermes" / "Alias Target.md").write_text("alias\n", encoding="utf-8")
    (vault / "Memory-Vault" / "Hermes" / "Reports" / "report.md").write_text("report [[Hermes/Inbox]]\n", encoding="utf-8")
    (vault / "Memory-Vault" / "_Backups" / "backup.md").write_text("backup [[Hermes/Inbox]]\n", encoding="utf-8")
    return vault


def test_build_baseline_is_read_only_and_counts_reasons(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    packet = build_standing_safe_link_prefix_baseline(vault_root=vault).to_dict()

    assert packet["live_mutation_authorized"] is False
    assert packet["approval_manifest_created"] is False
    assert packet["apply_authority"] == "none"
    assert packet["summary"]["allowed_count"] == 2
    assert packet["summary"]["actionable_apply_items"] == 0
    assert packet["summary"]["counts_by_reason"] == {
        "allowed": 2,
        "excluded_generated_report_surface": 1,
        "excluded_protected_path": 1,
        "missing_target": 1,
    }


def test_collect_existing_targets_skips_hidden_cache_paths(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    (vault / ".obsidian").mkdir()
    (vault / ".obsidian" / "hidden.md").write_text("hidden\n", encoding="utf-8")

    targets = collect_existing_markdown_targets(vault)

    assert "Memory-Vault/Hermes/Inbox.md" in targets
    assert ".obsidian/hidden.md" not in targets


def test_write_baseline_outputs_json_and_markdown(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    out = tmp_path / "out"
    result = write_standing_safe_link_prefix_baseline(vault_root=vault, out_dir=out)

    packet = json.loads(Path(result["packet"]).read_text(encoding="utf-8"))
    report = Path(result["report"]).read_text(encoding="utf-8")
    assert packet["summary"]["total_links"] == 5
    assert "no live mutation authority" in report


def test_cli_writes_read_only_baseline(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    out = tmp_path / "cli-out"
    completed = subprocess.run(
        [
            sys.executable,
            "tools/obsidian_standing_safe_link_prefix_baseline.py",
            "--vault",
            str(vault),
            "--out-dir",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = json.loads(completed.stdout)
    packet = json.loads(Path(result["packet"]).read_text(encoding="utf-8"))
    assert packet["live_mutation_authorized"] is False
    assert packet["summary"]["allowed_count"] == 2


def test_cli_rejects_scan_root_outside_vault(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    completed = subprocess.run(
        [
            sys.executable,
            "tools/obsidian_standing_safe_link_prefix_baseline.py",
            "--vault",
            str(vault),
            "--scan-root",
            str(outside),
            "--out-dir",
            str(tmp_path / "out"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "scan_root must be inside vault_root" in completed.stderr
