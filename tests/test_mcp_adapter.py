from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import GuardrailError, build_mcp_adapter_evaluation, load_mcp_adapter_record, normalize_mcp_tool_request


def make_sandbox(tmp_path: Path) -> Path:
    sandbox = tmp_path / "out" / "sandbox-vaults" / "mcp-case"
    (sandbox / "Notes").mkdir(parents=True)
    (sandbox / "Notes" / "alpha.md").write_text("hello [[world]]\n", encoding="utf-8")
    return sandbox


def adapter_record() -> Path:
    repo = Path(__file__).resolve().parents[1]
    return repo / "docs" / "spec-kit" / "research" / "sample-adapter-records" / "cyanheads-obsidian-mcp-server.json"


def test_load_mcp_adapter_record_enforces_readonly_contract() -> None:
    record = load_mcp_adapter_record(adapter_record())

    assert record["kind"] == "mcp-server"
    assert record["direct_write_enabled"] is False
    assert record["sandbox_required"] is True
    assert "write-direct" in record["forbidden_capabilities"]


def test_load_mcp_adapter_record_rejects_direct_write(tmp_path: Path) -> None:
    bad = json.loads(adapter_record().read_text(encoding="utf-8"))
    bad["direct_write_enabled"] = True
    bad_path = tmp_path / "bad-mcp.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")

    with pytest.raises(GuardrailError):
        load_mcp_adapter_record(bad_path)


def test_normalize_mcp_tool_request_blocks_mutations() -> None:
    assert normalize_mcp_tool_request("read_note")["status"] == "allowed-for-sandbox-readonly"
    assert normalize_mcp_tool_request("search_notes")["status"] == "allowed-for-sandbox-readonly"

    for tool in ("write_note", "delete_note", "move_file", "patch_frontmatter", "read_env_token"):
        result = normalize_mcp_tool_request(tool, {"path": "Notes/alpha.md"})
        assert result["status"] == "refused"
        assert result["proposal_required"] is True
        assert result["executed"] is False


def test_build_mcp_adapter_evaluation_uses_sandbox_and_refuses_dangerous_tools(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    evaluation = build_mcp_adapter_evaluation(adapter_record=adapter_record(), sandbox_vault=sandbox)

    assert evaluation.adapter == "cyanheads/obsidian-mcp-server"
    assert evaluation.sandbox_vault == str(sandbox.resolve())
    assert evaluation.direct_write_disabled is True
    assert evaluation.verification["sandboxed"] is True
    assert evaluation.verification["dangerous_tools_refused"] is True
    assert evaluation.verification["probe_count"] == 5
    assert evaluation.verification["source_path_count"] == 1
    assert evaluation.verification["source_paths_sample"] == ["Notes/alpha.md"]
    assert evaluation.verification["benchmark_metrics"]["wall_time_ms"] >= 0
    assert evaluation.verification["benchmark_metrics"]["max_rss_kb"] > 0
    assert evaluation.verification["benchmark_metrics"]["cost_model"] == "local-wrapper-no-llm-call"
    assert any(item["tool"] == "write_note" and item["status"] == "refused" for item in evaluation.findings)


def test_obsidian_mcp_adapter_cli_writes_json_and_markdown_reports(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    sandbox = make_sandbox(tmp_path)
    out_dir = tmp_path / "reports"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_mcp_adapter.py"),
            "--adapter-record",
            str(adapter_record()),
            "--sandbox-vault",
            str(sandbox),
            "--out-dir",
            str(out_dir),
            "--probe-tool",
            "read_note",
            "--probe-tool",
            "write_note",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["direct_write_disabled"] is True
    assert payload["dangerous_tools_refused"] is True
    assert Path(payload["json_report"]).is_file()
    assert Path(payload["markdown_report"]).is_file()
    report = json.loads(Path(payload["json_report"]).read_text(encoding="utf-8"))
    assert report["verification"]["direct_write_disabled"] is True
