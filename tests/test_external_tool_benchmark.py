from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from obslayer.external_tool_benchmark import build_external_tool_benchmark_report, write_external_tool_benchmark_report


def test_build_external_tool_benchmark_report_is_read_only_and_no_write() -> None:
    report = build_external_tool_benchmark_report(benchmark_id="benchmark-test", created_at="2026-07-05T00:00:00Z")
    payload = report.to_dict()

    assert payload["mode"] == "external-tool-benchmark-v1"
    assert payload["behavior"] == "evidence-only"
    assert payload["live_mutation_authorized"] is False
    assert payload["approval_manifest_created"] is False
    assert payload["direct_write_disabled"] is True
    assert payload["no_write_sandbox"] is True
    assert payload["read_only_comparison"] is True
    assert payload["targets"] == []
    assert payload["tool_policy"]["direct_edits_allowed"] is False

    assert {tool["tool_id"] for tool in payload["reference_tools"]} == {
        "dataview-query-surface",
        "obsidian-api-link-semantics",
        "vault-inspector-readonly",
        "wikilink-linter-preview",
    }
    assert all(tool["executed"] is False for tool in payload["reference_tools"])
    assert all(tool["write_attempted"] is False for tool in payload["reference_tools"])


def test_differences_become_scorer_test_cases_and_proposals_not_edits() -> None:
    payload = build_external_tool_benchmark_report().to_dict()

    assert payload["differences"]
    assert len(payload["scorer_test_cases"]) == len(payload["differences"])
    assert len(payload["proposals"]) == len(payload["differences"])
    assert all(difference["direct_edit_allowed"] is False for difference in payload["differences"])
    assert all(test_case["live_mutation_authorized"] is False for test_case in payload["scorer_test_cases"])
    assert all(proposal["target_files"] == [] for proposal in payload["proposals"])
    assert all(proposal["live_mutation_authorized"] is False for proposal in payload["proposals"])


def test_write_external_tool_benchmark_report_outputs_json_and_markdown(tmp_path: Path) -> None:
    result = write_external_tool_benchmark_report(out_dir=tmp_path, benchmark_id="write-test")

    assert result == {
        "status": "ok",
        "report_json": str(tmp_path / "external-tool-benchmark.json"),
        "report_markdown": str(tmp_path / "REPORT.md"),
    }
    data = json.loads((tmp_path / "external-tool-benchmark.json").read_text(encoding="utf-8"))
    assert data["benchmark_id"] == "write-test"
    assert data["live_mutation_authorized"] is False
    markdown = (tmp_path / "REPORT.md").read_text(encoding="utf-8")
    assert "External tool benchmark" in markdown
    assert "deterministic read-only pattern simulation/comparison" in markdown
    assert "no external tool subprocess, API, or write mode is executed" in markdown


def test_obsidian_external_tool_benchmark_cli_writes_report(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "reports"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_external_tool_benchmark.py"),
            "--out-dir",
            str(out_dir),
            "--benchmark-id",
            "cli-test",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert Path(payload["report_json"]).is_file()
    assert Path(payload["report_markdown"]).is_file()
    report = json.loads(Path(payload["report_json"]).read_text(encoding="utf-8"))
    assert report["benchmark_id"] == "cli-test"
    assert report["direct_write_disabled"] is True

def test_obsidian_external_tool_benchmark_cli_accepts_candidate_scorer_v1_shape(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    scored_input = tmp_path / "candidate-scorer-v1.json"
    scored_input.write_text(
        json.dumps(
            {
                "packet_id": "candidate-scorer-v1-test",
                "scored_links": [
                    {
                        "source": "Memory/A.md",
                        "status": "ambiguous",
                        "old_link": "[[B]]",
                        "candidates": [
                            {"path": "Memory/B.md", "confidence": 0.7},
                            {"path": "_Archive/B.md", "confidence": 0.6},
                        ],
                        "review_required": True,
                        "hard_stop": False,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "reports"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_external_tool_benchmark.py"),
            "--scored-packets",
            str(scored_input),
            "--out-dir",
            str(out_dir),
            "--benchmark-id",
            "candidate-shape-test",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    report = json.loads(Path(payload["report_json"]).read_text(encoding="utf-8"))
    assert report["benchmark_id"] == "candidate-shape-test"
    assert len(report["scorer_packets"]) == 1
    assert report["live_mutation_authorized"] is False
    assert report["approval_manifest_created"] is False
    assert report["targets"] == []
    assert all(comparison["write_attempted"] is False for comparison in report["comparisons"])
