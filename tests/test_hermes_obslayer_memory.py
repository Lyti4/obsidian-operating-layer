from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "hermes_obslayer_memory.py"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_memory_bridge_returns_ranked_relative_json_hits(tmp_path: Path) -> None:
    (tmp_path / "Projects").mkdir()
    (tmp_path / "Projects" / "Hermes Memory.md").write_text(
        "Obsidian Operating Layer stores durable Hermes decisions.\n",
        encoding="utf-8",
    )

    completed = run_tool("Hermes decisions", "--vault", str(tmp_path), "--json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["hits"][0]["path"] == "Projects/Hermes Memory.md"


def test_memory_bridge_refuses_symlink_escape(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("private external marker\n", encoding="utf-8")
    (vault / "linked.md").symlink_to(outside)

    completed = run_tool("external marker", "--vault", str(vault), "--json")

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["hits"] == []
