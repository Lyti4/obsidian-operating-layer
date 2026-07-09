from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from obslayer import GuardrailError
from obslayer.graphify_incremental_index import run_graphify_incremental_index


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_id(tmp_path: Path) -> str:
    return f"{tmp_path.parent.name}-{tmp_path.name}"


def clean_test_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    return path


def make_sandbox(tmp_path: Path) -> tuple[Path, Path]:
    repo = repo_root()
    slug = run_id(tmp_path)
    sandbox = repo / "out" / "sandbox-vaults" / f"incremental-{slug}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    (sandbox / "Notes").mkdir(parents=True)
    (sandbox / "Notes" / "Alpha.md").write_text("# Alpha\nProtected paths and backup safety\n", encoding="utf-8")
    (sandbox / "Notes" / "Beta.md").write_text("# Beta\nHermes CLI settings and verification\n", encoding="utf-8")
    graph_dir = repo / "out" / "reports" / "graphify-embedding-handoff" / f"incremental-graph-{slug}" / "graphify-out"
    graph_dir.mkdir(parents=True, exist_ok=True)
    graph = graph_dir / "graph.json"
    graph.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "a", "source_file": "Notes/Alpha.md"},
                    {"id": "b", "source_file": str((sandbox / "Notes" / "Beta.md").resolve())},
                ],
                "links": [{"source": "a", "target": "b"}],
            }
        ),
        encoding="utf-8",
    )
    return sandbox, graph


def test_incremental_wrapper_dry_run_writes_delta_manifest_only(tmp_path: Path) -> None:
    sandbox, graph = make_sandbox(tmp_path)
    report = run_graphify_incremental_index(
        graph_json=graph,
        sandbox_vault=sandbox,
        out_dir=repo_root() / "out" / "reports" / "graphify-incremental-index" / f"dry-{run_id(tmp_path)}",
        derived_root=clean_test_dir(
            repo_root()
            / "out"
            / "external-indexing-spike"
            / "graphify-derived"
            / f"dry-derived-{run_id(tmp_path)}"
        ),
        provider="local-hashing-v1",
        allow_smoke_provider=True,
        max_candidates=2,
        max_delta_candidates=1,
    )

    assert report.status == "ready"
    assert report.dry_run is True
    assert report.delta_candidates == 1
    assert Path(report.delta_manifest).name == "embedding-manifest.json"
    assert Path(report.delta_manifest).is_file()
    assert report.embedding_run_json is None
    assert report.safety["live_vault_mutation"] is False
    assert report.safety["uses_existing_graphify_handoff"] is True


def test_incremental_wrapper_runs_bounded_smoke_and_query(tmp_path: Path) -> None:
    sandbox, graph = make_sandbox(tmp_path)
    report = run_graphify_incremental_index(
        graph_json=graph,
        sandbox_vault=sandbox,
        out_dir=repo_root() / "out" / "reports" / "graphify-incremental-index" / f"run-{run_id(tmp_path)}",
        derived_root=clean_test_dir(
            repo_root()
            / "out"
            / "external-indexing-spike"
            / "graphify-derived"
            / f"run-derived-{run_id(tmp_path)}"
        ),
        provider="local-hashing-v1",
        allow_smoke_provider=True,
        max_candidates=2,
        max_delta_candidates=2,
        dry_run=False,
        run_query_smoke=True,
        queries=["protected paths safety"],
    )

    assert report.status == "ready"
    assert report.embedding_run_json is not None
    assert report.query_smoke_json is not None
    run_payload = json.loads(Path(report.embedding_run_json).read_text(encoding="utf-8"))
    assert run_payload["safety"]["manifest_only"] is True
    assert run_payload["processed"] == 2
    query_payload = json.loads(Path(report.query_smoke_json).read_text(encoding="utf-8"))
    assert query_payload["queries"][0]["hits"]


def test_incremental_wrapper_rejects_unapproved_out_dir(tmp_path: Path) -> None:
    sandbox, graph = make_sandbox(tmp_path)
    with pytest.raises(GuardrailError, match="output dir must live under"):
        run_graphify_incremental_index(
            graph_json=graph,
            sandbox_vault=sandbox,
            out_dir=tmp_path / "bad-out",
            derived_root=clean_test_dir(
                repo_root()
                / "out"
                / "external-indexing-spike"
                / "graphify-derived"
                / f"bad-derived-{run_id(tmp_path)}"
            ),
            provider="local-hashing-v1",
            allow_smoke_provider=True,
        )
