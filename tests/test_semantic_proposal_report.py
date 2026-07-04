from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import GuardrailError, build_semantic_proposal_report


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_query_smoke(tmp_path: Path) -> Path:
    out = repo_root() / "out" / "reports" / "graphify-embedding-query-smoke" / f"semantic-proposal-{tmp_path.name}"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "graphify-embedding-query-smoke",
        "records": 3,
        "embedded_files": 3,
        "skipped": 0,
        "chunks_indexed": 5,
        "missing_embedding_files": [],
        "safety": {"derived_cache_only": True, "live_mutation": False},
        "queries": [
            {
                "query": "link hygiene",
                "top": [
                    {"path": "Memory-Vault/Hermes/Reports/A.md", "score": 0.9, "chunk_index": 0},
                    {"path": "Memory-Vault/Hermes/Reports/B.md", "score": 0.7, "chunk_index": 2},
                ],
            },
            {
                "query": "approval manifest",
                "top": [
                    {"path": "Memory-Vault/Hermes/Reports/A.md", "score": 0.8, "chunk_index": 1},
                ],
            },
        ],
    }
    path = out / "query-smoke.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_build_semantic_proposal_report_is_proposal_only(tmp_path: Path) -> None:
    query_json = write_query_smoke(tmp_path)

    report = build_semantic_proposal_report(query_smoke_json=query_json, proposal_id="p-test")

    assert report.mode == "semantic-query-proposal-only-report"
    assert report.status == "needs-review"
    assert report.targets == []
    assert report.live_mutation_authorized is False
    assert report.safety["proposal_only"] is True
    assert report.candidates[0].path == "Memory-Vault/Hermes/Reports/A.md"
    assert report.candidates[0].hit_count == 2


def test_semantic_proposal_report_rejects_missing_embeddings(tmp_path: Path) -> None:
    query_json = write_query_smoke(tmp_path)
    data = json.loads(query_json.read_text(encoding="utf-8"))
    data["missing_embedding_files"] = ["x.md"]
    query_json.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(GuardrailError, match="missing embedding files"):
        build_semantic_proposal_report(query_smoke_json=query_json)


def test_semantic_proposal_report_rejects_explicit_live_mutation(tmp_path: Path) -> None:
    query_json = write_query_smoke(tmp_path)
    data = json.loads(query_json.read_text(encoding="utf-8"))
    data["safety"]["live_mutation"] = True
    query_json.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(GuardrailError, match="live_mutation=true"):
        build_semantic_proposal_report(query_smoke_json=query_json)


def test_semantic_proposal_report_rejects_outside_query_json(tmp_path: Path) -> None:
    bad = tmp_path / "query-smoke.json"
    bad.write_text(json.dumps({"mode": "graphify-embedding-query-smoke"}), encoding="utf-8")

    with pytest.raises(GuardrailError, match="query-smoke.json must live under"):
        build_semantic_proposal_report(query_smoke_json=bad)


def test_semantic_proposal_report_cli_writes_outputs(tmp_path: Path) -> None:
    repo = repo_root()
    query_json = write_query_smoke(tmp_path)
    out_dir = repo / "out" / "proposals" / "semantic-query-reports" / f"cli-{tmp_path.name}"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_semantic_proposal_report.py"),
            "--query-smoke-json",
            str(query_json),
            "--out-dir",
            str(out_dir),
            "--proposal-id",
            "p-cli",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["targets"] == "0"
    assert Path(payload["proposal"]).is_file()
    assert Path(payload["report"]).is_file()
