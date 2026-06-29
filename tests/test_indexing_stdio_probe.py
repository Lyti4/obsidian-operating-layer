from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_stdio_probe_runs_fake_mcp_through_sanitizing_wrapper(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    run_name = f"stdio-probe-pytest-{tmp_path.name}"
    sandbox = repo / "out" / "sandbox-vaults" / run_name
    derived = repo / "out" / "external-indexing-spike" / run_name
    report_root = repo / "out" / "reports" / "external-indexing-spike" / run_name
    for path in (sandbox, derived, report_root):
        if path.exists():
            shutil.rmtree(path)
    sandbox.mkdir(parents=True)
    (sandbox / "Notes").mkdir()
    (sandbox / "Notes" / "Safety.md").write_text("# Safety\nNo live mutation\n", encoding="utf-8")

    command = [
        sys.executable,
        str(repo / "tools" / "obsidian_indexing_stdio_probe.py"),
        "--sandbox-vault",
        str(sandbox),
        "--derived-root",
        str(derived),
        "--report-root",
        str(report_root),
        "--raw-report",
        str(report_root / "raw" / "transcript.json"),
        "--sanitized-report",
        str(report_root / "sanitized-transcript.json"),
        "--command",
        sys.executable,
        "--command",
        str(repo / "tests" / "fixtures" / "fake_jsonline_mcp_server.py"),
        "--query",
        "safety boundary",
        "--timeout-seconds",
        "5",
    ]
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=True)
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["calls"] >= 5

    raw = json.loads((report_root / "raw" / "transcript.json").read_text(encoding="utf-8"))
    sanitized = json.loads((report_root / "sanitized-transcript.json").read_text(encoding="utf-8"))
    assert len(raw["calls"]) == summary["calls"]
    assert sanitized["calls"][0]["kind"] == "list_tools"
    assert sanitized["calls"][0]["tools"] == ["search_notes", "read_note", "index_vault", "index_status"]
    assert any(call.get("tool") == "read_note" for call in sanitized["calls"])
    assert str(sandbox) not in json.dumps(sanitized, ensure_ascii=False)
