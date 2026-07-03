from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import GuardrailError, build_graphify_embedding_handoff


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def make_sandbox(tmp_path: Path) -> Path:
    sandbox = repo_root() / "out" / "sandbox-vaults" / f"graphify-embed-{tmp_path.name}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    (sandbox / "Notes").mkdir(parents=True)
    (sandbox / "Notes" / "alpha.md").write_text("# Alpha\n[[Beta]] safety graph\n", encoding="utf-8")
    (sandbox / "Notes" / "Beta.md").write_text("# Beta\nbackup apply verify\n", encoding="utf-8")
    (sandbox / ".obsidian").mkdir()
    (sandbox / ".obsidian" / "secret.md").write_text("# hidden\n", encoding="utf-8")
    return sandbox


def write_graph(tmp_path: Path, sandbox: Path) -> Path:
    out = repo_root() / "out" / "reports" / "graphify-embedding-handoff" / f"pytest-{tmp_path.name}" / "graphify-out"
    out.mkdir(parents=True, exist_ok=True)
    graph = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "a", "source_file": "Notes/alpha.md", "community": 1},
            {"id": "b", "source_file": str((sandbox / "Notes" / "Beta.md").resolve()), "community": 1},
            {"id": "hidden", "source_file": ".obsidian/secret.md", "community": 2},
            {"id": "external", "source_file": "/tmp/outside.md", "community": 3},
        ],
        "links": [
            {"source": "a", "target": "b"},
            {"source": "a", "target": "hidden"},
        ],
        "hyperedges": [],
        "built_at_commit": "test",
    }
    path = out / "graph.json"
    path.write_text(json.dumps(graph), encoding="utf-8")
    return path


def test_builds_embedding_manifest_from_graphify_sources_only(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    graph = write_graph(tmp_path, sandbox)

    handoff = build_graphify_embedding_handoff(
        graph_json=graph,
        sandbox_vault=sandbox,
        derived_root=repo_root() / "out" / "external-indexing-spike" / "graphify-derived" / f"pytest-{tmp_path.name}",
    )

    assert handoff.mode == "graphify-derived-embedding-manifest"
    assert handoff.embedding_policy["auto_execute"] is False
    assert handoff.safety["embeddings_started"] is False
    assert [item.path for item in handoff.candidates] == ["Notes/alpha.md", "Notes/Beta.md"]
    assert all(item.hash.startswith("sha256:") for item in handoff.candidates)
    assert handoff.graph_summary["source_files_in_graph"] == 2


def test_rejects_live_vault_and_unapproved_graph_paths(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps({"nodes": [], "links": []}), encoding="utf-8")

    with pytest.raises(GuardrailError, match="approved out"):
        build_graphify_embedding_handoff(graph_json=graph, sandbox_vault=sandbox)

    approved_graph = write_graph(tmp_path, sandbox)
    with pytest.raises(GuardrailError, match="live vault"):
        build_graphify_embedding_handoff(graph_json=approved_graph, sandbox_vault=Path("/home/hermesadmin/Obsidian"))


def test_cli_writes_report_and_manifest(tmp_path: Path) -> None:
    repo = repo_root()
    sandbox = make_sandbox(tmp_path)
    graph = write_graph(tmp_path, sandbox)
    out_dir = repo / "out" / "reports" / "graphify-embedding-handoff" / f"cli-{tmp_path.name}"
    derived = repo / "out" / "external-indexing-spike" / "graphify-derived" / f"cli-{tmp_path.name}"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_graphify_embedding_handoff.py"),
            "--graph-json",
            str(graph),
            "--sandbox-vault",
            str(sandbox),
            "--out-dir",
            str(out_dir),
            "--derived-root",
            str(derived),
            "--max-candidates",
            "1",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    manifest = Path(payload["manifest"])
    report = Path(payload["report"])
    assert manifest.is_file()
    assert report.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["embedding_policy"]["auto_execute"] is False
    assert len(data["candidates"]) == 1
