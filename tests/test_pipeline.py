import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"


def run(cmd):
    return subprocess.run(cmd, cwd=BASE, check=True, text=True, capture_output=True)


def make_test_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("# Note\n", encoding="utf-8")
    return vault


def test_observe_propose_verify(tmp_path):
    vault = make_test_vault(tmp_path)
    obs = tmp_path / "obs.json"
    propdir = tmp_path / "proposal"
    run([sys.executable, str(TOOLS / "obsidian_observe.py"), "--vault", str(vault), "--out", str(obs)])
    run([sys.executable, str(TOOLS / "obsidian_propose.py"), "--observe", str(obs), "--out-dir", str(propdir)])
    result = run([sys.executable, str(TOOLS / "obsidian_verify.py"), "--observe", str(obs), "--proposal", str(propdir / "proposal.json")])
    assert "verification ok" in result.stdout


def test_proposal_defaults_dry_run(tmp_path):
    vault = make_test_vault(tmp_path)
    obs = tmp_path / "obs.json"
    propdir = tmp_path / "proposal"
    run([sys.executable, str(TOOLS / "obsidian_observe.py"), "--vault", str(vault), "--out", str(obs)])
    run([sys.executable, str(TOOLS / "obsidian_propose.py"), "--observe", str(obs), "--out-dir", str(propdir)])
    data = json.loads((propdir / "proposal.json").read_text())
    assert data["mode"] == "dry-run"
    assert data["approval_required"] is True
