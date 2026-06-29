from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _stdio_probe_command(repo: Path, run_name: str, *, extra_args: list[str] | None = None) -> tuple[list[str], Path, Path]:
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
        "1",
    ]
    if extra_args:
        command.extend(extra_args)
    return command, report_root, sandbox


def test_stdio_probe_runs_fake_mcp_through_sanitizing_wrapper(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    command, report_root, sandbox = _stdio_probe_command(repo, f"stdio-probe-pytest-{tmp_path.name}")

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


def _run_failure(
    repo: Path,
    tmp_path: Path,
    *,
    mode: str | None = None,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_name = f"stdio-probe-fail-{mode or 'args'}-{tmp_path.name}"
    command, _, _ = _stdio_probe_command(repo, run_name, extra_args=extra_args)
    env = os.environ.copy()
    if mode:
        env["FAKE_MCP_MODE"] = mode
    return subprocess.run(command, cwd=repo, text=True, capture_output=True, env=env, check=False)


def test_stdio_probe_fails_closed_on_malformed_json(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="malformed-json")
    assert result.returncode == 2
    assert "malformed JSON" in result.stderr


def test_stdio_probe_fails_closed_on_failed_initialize(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="failed-initialize")
    assert result.returncode == 2
    assert "initialize" in result.stderr
    assert "returned error" in result.stderr


def test_stdio_probe_fails_closed_on_bad_initialize_shape(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="bad-initialize")
    assert result.returncode == 2
    assert "protocolVersion" in result.stderr


def test_stdio_probe_fails_closed_on_extra_or_missing_tools(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    extra = _run_failure(repo, tmp_path, mode="extra-tool")
    assert extra.returncode == 2
    assert "non-allowlisted" in extra.stderr

    missing = _run_failure(repo, tmp_path, mode="missing-tool")
    assert missing.returncode == 2
    assert "missing required" in missing.stderr


def test_stdio_probe_fails_closed_on_tools_list_error(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="failed-tools-list")
    assert result.returncode == 2
    assert "tools/list" in result.stderr
    assert "returned error" in result.stderr


def test_stdio_probe_fails_closed_on_tools_call_error(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="failed-tools-call")
    assert result.returncode == 2
    assert "tools/call" in result.stderr
    assert "returned error" in result.stderr


def test_stdio_probe_timeout_is_bounded(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, mode="timeout")
    assert result.returncode == 2
    assert "Timed out" in result.stderr


def test_stdio_probe_rejects_non_dry_run_intent(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = _run_failure(repo, tmp_path, extra_args=["--non-dry-run"])
    assert result.returncode == 2
    assert "refuses non-dry-run" in result.stderr
