from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from obslayer.indexing_wrapper import INDEXING_WRAPPER_TOOL_ALLOWLIST


def mcp_text(payload: object) -> dict:
    return {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": json.dumps(payload)}]}}


def test_indexing_runtime_cli_writes_split_raw_and_sanitized_reports(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    sandbox = repo / "out" / "sandbox-vaults" / f"runtime-cli-{tmp_path.name}"
    (sandbox / "Notes").mkdir(parents=True, exist_ok=True)
    (sandbox / "Notes" / "alpha.md").write_text("# Alpha\nbody\n", encoding="utf-8")
    (sandbox / "Soul-Vault" / "_Archive").mkdir(parents=True, exist_ok=True)
    (sandbox / "Soul-Vault" / "_Archive" / "old.md").write_text("# Archived duplicate\n", encoding="utf-8")
    derived = repo / "out" / "external-indexing-spike" / f"runtime-cli-{tmp_path.name}"
    report_root = repo / "out" / "reports" / "external-indexing-spike" / f"runtime-cli-{tmp_path.name}"
    transcript = tmp_path / "raw-input.json"
    transcript.write_text(
        json.dumps(
            {
                "calls": [
                    {"kind": "list_tools", "message": mcp_text({"tools": list(INDEXING_WRAPPER_TOOL_ALLOWLIST)})},
                    {
                        "tool": "search_notes",
                        "message": mcp_text(
                            {
                                "results": [
                                    {
                                        "path": "Notes/alpha.md",
                                        "matched_sections": [
                                            {"line": 1, "snippet": "/home/hermesadmin/Obsidian should be sanitized"}
                                        ],
                                    }
                                ]
                            }
                        ),
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_indexing_runtime.py"),
            "--sandbox-vault",
            str(sandbox),
            "--derived-root",
            str(derived),
            "--raw-transcript",
            str(transcript),
            "--raw-report",
            str(report_root / "raw" / "transcript.json"),
            "--sanitized-report",
            str(report_root / "sanitized-transcript.json"),
            "--report-root",
            str(report_root),
            "--command",
            "node",
            "--command",
            "server.js",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["process_spec"]["env"]["OBSIDIAN_SEMANTIC_MCP_HOME"] == str(derived.resolve())
    assert "Soul-Vault/_Archive/" in payload["process_spec"]["env"]["OBSIDIAN_SEMANTIC_EXCLUDE"]
    raw = Path(payload["raw_report"]).read_text(encoding="utf-8")
    sanitized = Path(payload["sanitized_report"]).read_text(encoding="utf-8")
    assert "/home/hermesadmin/Obsidian" in raw
    assert "/home/hermesadmin/Obsidian" not in sanitized
    assert "<LIVE_VAULT>" in sanitized
