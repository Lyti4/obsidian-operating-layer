from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import (
    GuardrailError,
    build_rag_graph_adapter_evaluation,
    load_rag_graph_adapter_record,
    normalize_rag_graph_findings,
)


def make_sandbox(tmp_path: Path) -> Path:
    sandbox = tmp_path / "out" / "sandbox-vaults" / "rag-case"
    (sandbox / "Projects").mkdir(parents=True)
    (sandbox / "Architecture").mkdir(parents=True)
    (sandbox / "Projects" / "Obsidian Operating Layer.md").write_text(
        "---\ntags: [automation, safety]\n---\n# Obsidian Operating Layer\nLinks to [[Safety Architecture]] and [[Missing Note]].\n",
        encoding="utf-8",
    )
    (sandbox / "Architecture" / "Safety Architecture.md").write_text(
        "---\ntags:\n  - automation\n  - safety\n---\n# Safety Architecture\n",
        encoding="utf-8",
    )
    (sandbox / "Inbox.md").write_text("# Inbox\nNo links yet.\n", encoding="utf-8")
    return sandbox


def adapter_record() -> Path:
    repo = Path(__file__).resolve().parents[1]
    return repo / "docs" / "spec-kit" / "research" / "sample-adapter-records" / "benmaster82-kwipu.json"


def test_load_rag_graph_adapter_record_enforces_sandbox_contract() -> None:
    record = load_rag_graph_adapter_record(adapter_record())

    assert record["kind"] == "rag-engine"
    assert record["direct_write_enabled"] is False
    assert record["sandbox_required"] is True
    assert "analyze" in record["capabilities"]
    assert "write-direct" in record["forbidden_capabilities"]


def test_load_rag_graph_adapter_record_rejects_live_write(tmp_path: Path) -> None:
    bad = json.loads(adapter_record().read_text(encoding="utf-8"))
    bad["direct_write_enabled"] = True
    bad_path = tmp_path / "bad-rag.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")

    with pytest.raises(GuardrailError):
        load_rag_graph_adapter_record(bad_path)


def test_normalize_rag_graph_findings_emits_proposal_only_records(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    findings = normalize_rag_graph_findings(sandbox)

    assert any(item["type"] == "nonexistent-link" and item["target"] == "Missing Note" for item in findings)
    assert any(item["type"] == "orphan-note" and item["source"] == "Inbox" for item in findings)
    assert any(item["type"] == "moc-candidate" and item["cluster"] == "automation" for item in findings)
    assert all(item["executed"] is False for item in findings)


def test_build_rag_graph_adapter_evaluation_uses_sandbox_and_normalizes_findings(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    evaluation = build_rag_graph_adapter_evaluation(adapter_record=adapter_record(), sandbox_vault=sandbox)

    assert evaluation.adapter == "benmaster82/Kwipu"
    assert evaluation.sandbox_vault == str(sandbox.resolve())
    assert evaluation.direct_write_disabled is True
    assert evaluation.verification["sandboxed"] is True
    assert evaluation.verification["normalized_findings_only"] is True
    assert evaluation.verification["notes_scanned"] == 3
    assert evaluation.verification["fixed_query_count"] == 5
    assert evaluation.verification["finding_count"] == len(evaluation.findings)
    assert evaluation.verification["benchmark_metrics"]["wall_time_ms"] >= 0
    assert evaluation.verification["benchmark_metrics"]["max_rss_kb"] > 0
    assert evaluation.verification["benchmark_metrics"]["cost_model"] == "local-wrapper-no-llm-call"


def test_rag_graph_adapter_cli_writes_json_and_markdown_reports(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    sandbox = make_sandbox(tmp_path)
    out_dir = tmp_path / "reports"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_rag_graph_adapter.py"),
            "--adapter-record",
            str(adapter_record()),
            "--sandbox-vault",
            str(sandbox),
            "--out-dir",
            str(out_dir),
            "--query",
            "Find notes related to Obsidian Operating Layer.",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["direct_write_disabled"] is True
    assert payload["normalized_findings_only"] is True
    assert payload["notes_scanned"] == 3
    assert Path(payload["json_report"]).is_file()
    assert Path(payload["markdown_report"]).is_file()
    report = json.loads(Path(payload["json_report"]).read_text(encoding="utf-8"))
    assert report["verification"]["notes_scanned"] == 3
