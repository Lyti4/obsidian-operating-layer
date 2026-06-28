from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import GuardrailError, create_sandbox_vault


def make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "Obsidian"
    (vault / "Notes").mkdir(parents=True)
    (vault / "Notes" / "alpha.md").write_text("hello [[world]]\n", encoding="utf-8")
    for protected in (".obsidian", "_Backups", "_Archive", ".trash"):
        (vault / protected).mkdir(parents=True)
        (vault / protected / "secret.md").write_text("do not copy\n", encoding="utf-8")
    return vault


def test_create_sandbox_vault_excludes_protected_paths(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    report = create_sandbox_vault(source_vault=vault, sandbox_root=tmp_path / "out" / "sandbox-vaults", name="case-1")
    sandbox = Path(report.sandbox_vault)

    assert report.copied_files == 1
    assert (sandbox / "Notes" / "alpha.md").read_text(encoding="utf-8") == "hello [[world]]\n"
    for protected in (".obsidian", "_Backups", "_Archive", ".trash"):
        assert not (sandbox / protected).exists()
    assert (vault / ".obsidian" / "secret.md").read_text(encoding="utf-8") == "do not copy\n"


def test_create_sandbox_vault_reset_is_explicit(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    sandbox_root = tmp_path / "out" / "sandbox-vaults"
    create_sandbox_vault(source_vault=vault, sandbox_root=sandbox_root, name="case-1")

    with pytest.raises(GuardrailError):
        create_sandbox_vault(source_vault=vault, sandbox_root=sandbox_root, name="case-1")

    (vault / "Notes" / "beta.md").write_text("beta\n", encoding="utf-8")
    report = create_sandbox_vault(source_vault=vault, sandbox_root=sandbox_root, name="case-1", reset=True)
    sandbox = Path(report.sandbox_vault)
    assert (sandbox / "Notes" / "beta.md").read_text(encoding="utf-8") == "beta\n"


def test_create_sandbox_vault_refuses_source_overlap(tmp_path: Path) -> None:
    vault = make_vault(tmp_path)
    with pytest.raises(GuardrailError):
        create_sandbox_vault(source_vault=vault, sandbox_root=vault / "out", name="bad")


def test_obsidian_sandbox_cli_writes_json_report(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    vault = make_vault(tmp_path)
    out = tmp_path / "sandbox-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_sandbox.py"),
            "--source-vault",
            str(vault),
            "--sandbox-root",
            str(tmp_path / "out" / "sandbox-vaults"),
            "--name",
            "cli-case",
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "ok"
    assert payload["copied_files"] == 1
    assert Path(payload["sandbox_vault"]).is_dir()
    assert not (Path(payload["sandbox_vault"]) / ".obsidian").exists()
