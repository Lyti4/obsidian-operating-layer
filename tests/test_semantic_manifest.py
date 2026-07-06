from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer.guardrails import GuardrailError
from obslayer.semantic_manifest import (
    build_semantic_manifest,
    doctor_semantic_manifest,
    semantic_manifest_to_markdown,
)


def _write_json(repo: Path, rel: str, payload: dict) -> Path:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _artifact_paths(repo: Path) -> dict[str, Path]:
    embedding_manifest = _write_json(
        repo,
        "out/reports/graphify-embedding-handoff/test/handoff/embedding-manifest.json",
        {
            "mode": "graphify-derived-embedding-manifest",
            "candidates": [{"path": "A.md", "hash": "sha256:x"}],
            "safety": {"live_mutation": False, "embeddings_started": False},
        },
    )
    embedding_run = _write_json(
        repo,
        "out/reports/graphify-embedding-runs/test/embedding-run.json",
        {
            "mode": "graphify-manifest-bounded-embedding-run",
            "manifest": str(embedding_manifest),
            "records": [],
            "processed": 0,
            "skipped": 0,
        },
    )
    query_smoke = _write_json(
        repo,
        "out/reports/graphify-embedding-query-smoke/test/query-smoke.json",
        {
            "mode": "graphify-embedding-query-smoke",
            "run_json": str(embedding_run),
            "records": 1,
            "processed": 1,
            "skipped": 0,
            "queries": [],
        },
    )
    semantic_proposal = _write_json(
        repo,
        "out/proposals/semantic-query-reports/test/proposal.json",
        {
            "mode": "semantic-query-proposal-only-report",
            "status": "proposal-only",
            "query_smoke_json": str(query_smoke),
            "targets": [],
            "live_mutation_authorized": False,
            "candidates": [],
        },
    )
    decision_packet = _write_json(
        repo,
        "out/proposals/semantic-candidate-decisions/test/decision-packet.json",
        {
            "mode": "semantic-candidate-decision-packet",
            "status": "ready-for-operator-review",
            "source_proposal": str(semantic_proposal),
            "targets": [],
            "live_mutation_authorized": False,
            "groups": [],
        },
    )
    targeted_proposal = _write_json(
        repo,
        "out/proposals/semantic-targeted-proposals/test/proposal.json",
        {
            "mode": "semantic-targeted-proposal",
            "status": "ready-for-operator-review",
            "source_decision_packet": str(decision_packet),
            "targets": [],
            "live_mutation_authorized": False,
            "approval_manifest_created": False,
            "candidate_paths": [],
        },
    )
    review_index = _write_json(
        repo,
        "out/proposals/semantic-review-indexes/test/review-index.json",
        {
            "mode": "semantic-review-index",
            "status": "ready-for-operator-review",
            "source_proposal": str(targeted_proposal),
            "live_mutation_authorized": False,
            "approval_manifest_created": False,
            "item_count": 0,
            "items": [],
        },
    )
    return {
        "embedding_manifest": embedding_manifest,
        "embedding_run": embedding_run,
        "query_smoke": query_smoke,
        "semantic_proposal": semantic_proposal,
        "decision_packet": decision_packet,
        "targeted_proposal": targeted_proposal,
        "review_index": review_index,
    }


def _manifest_path(repo: Path, payload: dict) -> Path:
    return _write_json(repo, "out/reports/semantic-manifests/test/semantic-manifest.json", payload)


def test_build_semantic_manifest_accepts_safe_artifact_chain(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)

    manifest = build_semantic_manifest(repo=tmp_path, created_at="2026-07-05T00:00:00Z", **paths)
    text = semantic_manifest_to_markdown(manifest)

    assert manifest.status == "ready-for-operator-review"
    assert manifest.summary["artifact_count"] == 7
    assert manifest.summary["safe_artifacts"] == 7
    assert manifest.live_mutation_authorized is False
    assert manifest.approval_manifest_created is False
    assert "Semantic Indexing Manifest" in text
    assert "- none" in text


def test_semantic_manifest_doctor_reports_ready_for_valid_generated_manifest(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    manifest = build_semantic_manifest(repo=tmp_path, created_at="2026-07-05T00:00:00Z", **paths)
    manifest_path = _manifest_path(tmp_path, manifest.to_dict())

    result = doctor_semantic_manifest(repo=tmp_path, manifest=manifest_path)

    assert result == {
        "status": "ready",
        "manifest": str(manifest_path),
        "repo": str(tmp_path),
        "findings": [],
    }


def test_semantic_manifest_doctor_blocks_manifest_findings(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    manifest = build_semantic_manifest(repo=tmp_path, created_at="2026-07-05T00:00:00Z", **paths).to_dict()
    manifest["findings"] = ["operator review required"]
    manifest_path = _manifest_path(tmp_path, manifest)

    result = doctor_semantic_manifest(repo=tmp_path, manifest=manifest_path)

    assert result["status"] == "blocked"
    assert result["findings"] == ["manifest findings must be empty"]


def test_semantic_manifest_doctor_blocks_live_mutation_authority(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    manifest = build_semantic_manifest(repo=tmp_path, created_at="2026-07-05T00:00:00Z", **paths).to_dict()
    manifest["live_mutation_authorized"] = True
    manifest["approval_manifest_created"] = True
    manifest["artifacts"][0]["safety_ok"] = False
    manifest["artifacts"][0]["summary"]["targets"] = 1
    manifest_path = _manifest_path(tmp_path, manifest)

    result = doctor_semantic_manifest(repo=tmp_path, manifest=manifest_path)

    assert result["status"] == "blocked"
    assert "live_mutation_authorized must be false" in result["findings"]
    assert "approval_manifest_created must be false" in result["findings"]
    assert "artifacts[0].safety_ok must be true" in result["findings"]
    assert "artifacts[0].summary.targets must be empty" in result["findings"]


def test_semantic_manifest_doctor_blocks_artifact_outside_repo_out(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    manifest = build_semantic_manifest(repo=tmp_path, created_at="2026-07-05T00:00:00Z", **paths).to_dict()
    manifest["artifacts"][0]["path"] = str(tmp_path / "elsewhere" / "artifact.json")
    manifest_path = _manifest_path(tmp_path, manifest)

    result = doctor_semantic_manifest(repo=tmp_path, manifest=manifest_path)

    assert result["status"] == "blocked"
    assert result["findings"] == ["artifacts[0].path must be under repo out/"]


def test_semantic_manifest_doctor_cli_returns_zero_for_ready(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    paths = _artifact_paths(tmp_path)
    manifest = build_semantic_manifest(repo=tmp_path, created_at="2026-07-05T00:00:00Z", **paths)
    manifest_path = _manifest_path(tmp_path, manifest.to_dict())

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_semantic_manifest_doctor.py"),
            "--repo",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    result = json.loads(completed.stdout)
    assert result["status"] == "ready"
    assert result["findings"] == []


def test_semantic_manifest_doctor_cli_returns_one_for_blocked(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    paths = _artifact_paths(tmp_path)
    manifest = build_semantic_manifest(repo=tmp_path, created_at="2026-07-05T00:00:00Z", **paths).to_dict()
    manifest["findings"] = ["blocked"]
    manifest_path = _manifest_path(tmp_path, manifest)

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_semantic_manifest_doctor.py"),
            "--repo",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1, completed.stderr + completed.stdout
    result = json.loads(completed.stdout)
    assert result["status"] == "blocked"
    assert result["findings"] == ["manifest findings must be empty"]


def test_build_semantic_manifest_accepts_repo_relative_chain_pointers_from_other_cwd(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    pointer_map = {
        "embedding_run": ("manifest", "embedding_manifest"),
        "query_smoke": ("run_json", "embedding_run"),
        "semantic_proposal": ("query_smoke_json", "query_smoke"),
        "decision_packet": ("source_proposal", "semantic_proposal"),
        "targeted_proposal": ("source_decision_packet", "decision_packet"),
        "review_index": ("source_proposal", "targeted_proposal"),
    }
    for source_name, (key, target_name) in pointer_map.items():
        payload = json.loads(paths[source_name].read_text(encoding="utf-8"))
        payload[key] = str(paths[target_name].relative_to(tmp_path))
        paths[source_name].write_text(json.dumps(payload), encoding="utf-8")

    other_cwd = tmp_path / "elsewhere"
    other_cwd.mkdir()
    path_literals = {key: str(value) for key, value in paths.items()}
    code = (
        "from obslayer.semantic_manifest import build_semantic_manifest; "
        f"paths = {path_literals!r}; "
        f"manifest = build_semantic_manifest(repo={str(tmp_path)!r}, **paths); "
        "print(manifest.status); print(manifest.findings)"
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
        ],
        cwd=other_cwd,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert completed.stdout.splitlines()[0] == "ready-for-operator-review"



def test_build_semantic_manifest_blocks_unsafe_semantic_artifact(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    payload = json.loads(paths["targeted_proposal"].read_text(encoding="utf-8"))
    payload["targets"] = [{"path": "live.md"}]
    paths["targeted_proposal"].write_text(json.dumps(payload), encoding="utf-8")

    manifest = build_semantic_manifest(repo=tmp_path, **paths)

    assert manifest.status == "blocked"
    assert any("must not contain edit targets" in finding for finding in manifest.findings)


def test_build_semantic_manifest_blocks_broken_chain_pointer(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    payload = json.loads(paths["query_smoke"].read_text(encoding="utf-8"))
    payload["run_json"] = str(tmp_path / "out" / "reports" / "graphify-embedding-runs" / "other" / "embedding-run.json")
    paths["query_smoke"].write_text(json.dumps(payload), encoding="utf-8")

    manifest = build_semantic_manifest(repo=tmp_path, **paths)

    assert manifest.status == "blocked"
    assert any("run_json does not point to embedding_run" in finding for finding in manifest.findings)


def test_semantic_manifest_refuses_artifacts_outside_repo_out(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    outside = tmp_path / "not-out" / "proposal.json"
    outside.parent.mkdir()
    outside.write_text("{}", encoding="utf-8")
    paths["semantic_proposal"] = outside

    with pytest.raises(GuardrailError, match="repo out"):
        build_semantic_manifest(repo=tmp_path, **paths)


def test_semantic_manifest_cli_writes_report(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    paths = _artifact_paths(repo)
    out_dir = repo / "out" / "reports" / "semantic-manifests" / f"cli-{tmp_path.name}"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_semantic_manifest.py"),
            "--repo",
            str(repo),
            "--embedding-manifest",
            str(paths["embedding_manifest"]),
            "--embedding-run",
            str(paths["embedding_run"]),
            "--query-smoke",
            str(paths["query_smoke"]),
            "--semantic-proposal",
            str(paths["semantic_proposal"]),
            "--decision-packet",
            str(paths["decision_packet"]),
            "--targeted-proposal",
            str(paths["targeted_proposal"]),
            "--review-index",
            str(paths["review_index"]),
            "--out-dir",
            str(out_dir),
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    result = json.loads(completed.stdout)
    assert result["status"] == "ready-for-operator-review"
    assert Path(result["manifest"]).is_file()
    assert Path(result["report"]).is_file()


def test_semantic_manifest_cli_writes_blocked_report_and_returns_failure(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    paths = _artifact_paths(repo)
    payload = json.loads(paths["targeted_proposal"].read_text(encoding="utf-8"))
    payload["targets"] = [{"path": "live.md"}]
    paths["targeted_proposal"].write_text(json.dumps(payload), encoding="utf-8")
    out_dir = repo / "out" / "reports" / "semantic-manifests" / f"cli-blocked-{tmp_path.name}"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_semantic_manifest.py"),
            "--repo",
            str(repo),
            "--embedding-manifest",
            str(paths["embedding_manifest"]),
            "--embedding-run",
            str(paths["embedding_run"]),
            "--query-smoke",
            str(paths["query_smoke"]),
            "--semantic-proposal",
            str(paths["semantic_proposal"]),
            "--decision-packet",
            str(paths["decision_packet"]),
            "--targeted-proposal",
            str(paths["targeted_proposal"]),
            "--review-index",
            str(paths["review_index"]),
            "--out-dir",
            str(out_dir),
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    assert result["status"] == "blocked"
    assert Path(result["manifest"]).is_file()
    assert Path(result["report"]).is_file()
